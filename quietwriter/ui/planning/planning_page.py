from __future__ import annotations

import json
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ..current_page_stack import CurrentPageStack
from ...planning_storage import PlanningStore
from ...revisions import ExternalModificationError, RevisionVerificationError
from ...migrations import FutureBookFormatError
from ...i18n import tr
from .characters_page import CharactersPage
from .outline_page import OutlinePage
from .notes_page import NotesPage


PLANNING_PANEL_WIDTH = 190


class PlanningPage(QWidget):
    """Book-planning mode: Characters, Outline and Notes.

    The page owns no persistence rules. All data access goes through PlanningStore,
    which in turn uses the Library revision guard so planning data has the same
    external-change protection as manuscript files.
    """

    def __init__(self, main):
        super().__init__(); self.main=main; self.book=None; self.store=PlanningStore(main.library)
        root=QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        side=QFrame(); side.setObjectName('planningSidebar'); side.setFixedWidth(PLANNING_PANEL_WIDTH)
        sl=QVBoxLayout(side); sl.setContentsMargins(12,22,12,22); sl.setSpacing(5)
        self.buttons=[]
        self.characters_button=self._nav(sl,tr('planning.nav.characters', 'Personages'),0)
        self.outline_button=self._nav(sl,tr('planning.nav.outline', 'Outline'),1)
        self.notes_button=self._nav(sl,tr('planning.nav.notes', 'Notities'),2)
        sl.addStretch()
        self.pages=CurrentPageStack(); self.characters_page=CharactersPage(self); self.outline_page=OutlinePage(self); self.notes_page=NotesPage(self)
        for p in (self.characters_page,self.outline_page,self.notes_page): self.pages.addWidget(p)
        self.characters_page.changed.connect(self.outline_page.refresh)
        root.addWidget(side); root.addWidget(self.pages,1)
        self.show_section(0)

    def _nav(self,layout,text,index):
        button=QPushButton(text); button.setObjectName('planningNavButton'); button.setCheckable(True); button.setAutoExclusive(True); button.clicked.connect(lambda _=False,i=index:self.show_section(i))
        layout.addWidget(button); self.buttons.append(button); return button

    def show_section(self,index):
        self.pages.setCurrentIndex(index)
        for i,b in enumerate(self.buttons): b.setChecked(i==index)

    def set_book(self,book, *, force=False):
        # A forced detach is used only after all local planning state has already
        # been preserved in a conflict_local History snapshot. It must never run
        # save_pending(): the live book may now belong to a newer QuietWriter.
        if not force and self.book and self.book.id != getattr(book,'id',None):
            if self.save_pending() is False:
                return False
        self.book=book
        enabled=book is not None; self.setEnabled(enabled)
        if not enabled:
            if force:
                self.characters_page.load(); self.outline_page.load(); self.notes_page.load()
            return True
        self.characters_page.load(); self.outline_page.load(); self.notes_page.load(); return True

    @staticmethod
    def _changed_paths(changed_files) -> set[str]:
        return {str(path).replace('\\', '/').lstrip('./') for path in (changed_files or [])}

    def adopt_book(self, book, *, reload_kind=None, changed_files=None):
        """Rebind a freshly loaded Book without silently merging a real conflict.

        Unrelated pending input is restored only when its own backing file did
        not change externally.  If it did, ``_resolve_external_change`` stores
        the local draft in a recovery version and this method deliberately loads
        the authoritative disk text instead.
        """
        same_book = bool(self.book and book and self.book.id == book.id)
        changed = self._changed_paths(changed_files)
        pending_notes = None
        pending_character = None
        if same_book:
            if (reload_kind != 'notes' and self.notes_page.dirty
                    and 'planning/notes.md' not in changed):
                pending_notes = self.notes_page.editor.toPlainText()
            if (reload_kind != 'characters'
                    and 'planning/characters.json' not in changed):
                pending_character = self.characters_page.pending_editor_snapshot()

        self.book = book
        enabled = book is not None; self.setEnabled(enabled)
        if not enabled:
            return True
        self.characters_page.load(); self.outline_page.load(); self.notes_page.load()
        if pending_notes is not None:
            self.notes_page.restore_pending_text(pending_notes)
        if pending_character is not None:
            self.characters_page.restore_editor_snapshot(pending_character)
        return True

    def _pending_overrides(self, conflict_kind):
        """Return all unrelated unsaved planning input for a recovery snapshot."""
        overrides = {}
        if conflict_kind != 'notes' and self.notes_page.dirty:
            overrides['planning/notes.md'] = self.notes_page.editor.toPlainText()
        if conflict_kind != 'characters':
            snapshot = self.characters_page.pending_editor_snapshot()
            if snapshot is not None:
                characters = self.characters_page.characters_with_snapshot(snapshot)
                overrides['planning/characters.json'] = self._planning_override_bytes('characters', characters)
        return overrides

    def save_pending(self):
        if self.characters_page.save_pending() is False:
            return False
        return self.notes_page.save()

    def _planning_override_bytes(self, kind, value):
        if kind=='characters':
            return json.dumps({'version':1,'characters':[c.to_dict() for c in value]},ensure_ascii=False,indent=2)
        if kind=='scenes':
            return json.dumps({'version':1,'scenes':[s.to_dict() for s in value]},ensure_ascii=False,indent=2)
        return str(value)

    def _persist(self, kind, value, writer):
        """Persist one planning payload and report the conflict outcome explicitly.

        ``disk`` is not a failure: it means the user deliberately accepted the
        freshly reloaded disk state. Callers must therefore not roll their old
        in-memory snapshot back over that state.
        """
        if not self.book:
            return 'failed'
        try:
            writer(self.book, value)
            return 'mine'
        except RevisionVerificationError:
            QMessageBox.warning(self,tr('planning.save_unavailable.title', 'Opslaan tijdelijk niet mogelijk'),tr('planning.save_unavailable.text', 'QuietWriter kan de actuele bestanden tijdelijk niet betrouwbaar controleren. Er is niets overschreven. Probeer het zo opnieuw.'))
            return 'failed'
        except ExternalModificationError as exc:
            return self._resolve_external_change(kind,value,writer,exc)
        except Exception as exc:
            QMessageBox.critical(self,tr('planning.save_error.title', 'Planning opslaan'),tr('planning.save_error.text', 'Opslaan is mislukt.\n\n{error}', error=exc))
            return 'failed'

    def _resolve_external_change(self,kind,value,writer,exc):
        # An unreadable notes source cannot safely participate in the normal
        # mine/disk write choice. MainWindow preflight will preserve the dirty
        # local notes and commit the existing read-only corrupt state instead.
        if kind == 'notes':
            try:
                self.store.load_notes(self.book)
            except UnicodeDecodeError:
                old_book = self.book
                preferred_chapter_id = self.main.editor_page.chapter.id if self.main.editor_page.chapter else None
                try:
                    latest = self.main.library.load_book(old_book.path)
                    changed_files = set(exc.changed_files)
                    changed_files.add('planning/notes.md')
                    self.main.adopt_active_book(
                        latest, preferred_chapter_id, planning_reload_kind='notes',
                        planning_changed_files=sorted(changed_files),
                    )
                    return 'disk'
                except Exception as error:
                    QMessageBox.critical(
                        self, tr('planning.conflict.failed_title', 'Conflict niet opgelost'),
                        tr('planning.conflict.failed_text', 'Er is niets bewust overschreven.\n\n{error}', error=error)
                    )
                    return 'failed'
        # A modal conflict dialog runs a nested Qt event loop. Pause an unrelated
        # dirty Notes autosave so its 2.5 s timer cannot fire re-entrantly while
        # the user is still choosing how to resolve another planning file.
        paused_notes = kind != 'notes' and self.notes_page.dirty
        if paused_notes:
            self.notes_page.timer.stop()
        changed='\n'.join('• '+name for name in exc.changed_files[:6])
        box=QMessageBox(self); box.setIcon(QMessageBox.Warning); box.setWindowTitle(tr('planning.conflict.title', 'Boek extern gewijzigd')); box.setText(tr('planning.conflict.text', 'Dit boek is buiten QuietWriter gewijzigd.'))
        box.setInformativeText(tr('planning.conflict.info', 'QuietWriter heeft de planning niet overschreven.\n\nGewijzigd:\n{changed}\n\nWelke versie wil je gebruiken?', changed=changed))
        mine=box.addButton(tr('planning.conflict.mine', 'Mijn planning gebruiken'),QMessageBox.AcceptRole); disk=box.addButton(tr('planning.conflict.disk', 'Versie op schijf gebruiken'),QMessageBox.DestructiveRole); box.setDefaultButton(disk); box.exec()
        if box.clickedButton() not in (mine,disk):
            if paused_notes:
                self.notes_page.timer.start()
            return 'failed'
        old_book = self.book
        preferred_chapter_id = self.main.editor_page.chapter.id if self.main.editor_page.chapter else None
        changed_paths = self._changed_paths(exc.changed_files)
        pending_overrides = self._pending_overrides(kind)
        conflicting_pending = [
            path for path in pending_overrides
            if path in changed_paths
        ]
        try:
            if box.clickedButton() is mine:
                # Keep unrelated local drafts in a recovery snapshot.  They are
                # restored into the live UI only when their own file was not one
                # of the externally changed files.
                if pending_overrides:
                    self.main.library.create_version_with_file_overrides(
                        old_book, pending_overrides, kind='conflict_local'
                    )
                self.main.library.create_version(old_book,kind='conflict_external')
                latest=self.main.library.load_book(old_book.path)
                self.main.library.track_book(latest)
                writer(latest,value)
                result='mine'
            else:
                # Preserve the selected local payload plus every unrelated local
                # draft in one recovery version, but leave the live disk state
                # untouched when the user explicitly chooses "schijf".
                relative={'characters':'planning/characters.json','scenes':'planning/outline.json','notes':'planning/notes.md'}[kind]
                overrides={relative:self._planning_override_bytes(kind,value)}
                overrides.update(pending_overrides)
                self.main.library.create_version_with_file_overrides(old_book,overrides,kind='conflict_local')
                latest=self.main.library.load_book(old_book.path)
                result='disk'
            self.main.adopt_active_book(
                latest, preferred_chapter_id, planning_reload_kind=kind,
                planning_changed_files=exc.changed_files,
            )
            if conflicting_pending:
                labels = []
                if 'planning/notes.md' in conflicting_pending:
                    labels.append(tr('planning.nav.notes', 'Notities'))
                if 'planning/characters.json' in conflicting_pending:
                    labels.append(tr('planning.nav.characters', 'Personages'))
                QMessageBox.information(
                    self,
                    tr('planning.pending_conflict.title', 'Lokale planning veilig bewaard'),
                    tr(
                        'planning.pending_conflict.text',
                        'Ook je niet-opgeslagen {items} waren extern gewijzigd. '
                        'De versie op schijf is geladen; je lokale invoer staat apart in Versiegeschiedenis.',
                        items=', '.join(labels),
                    ),
                )
            return result
        except FutureBookFormatError:
            relative={'characters':'planning/characters.json','scenes':'planning/outline.json','notes':'planning/notes.md'}[kind]
            overrides={relative:self._planning_override_bytes(kind,value)}
            overrides.update(pending_overrides)
            ok = self.main.preserve_local_and_close_future_book(old_book, file_overrides=overrides, context='planning')
            if not ok and paused_notes and self.notes_page.dirty:
                self.notes_page.timer.start()
            return 'failed'
        except Exception as error:
            if paused_notes and self.notes_page.dirty:
                self.notes_page.timer.start()
            QMessageBox.critical(self,tr('planning.conflict.failed_title', 'Conflict niet opgelost'),tr('planning.conflict.failed_text', 'Er is niets bewust overschreven.\n\n{error}', error=error))
            return 'failed'

    def persist_characters(self,characters): return self._persist('characters',characters,self.store.save_characters)
    def persist_scenes(self,scenes): return self._persist('scenes',scenes,self.store.save_scenes)
    def persist_notes(self,text): return self._persist('notes',text,self.store.save_notes)

    def remove_character_from_scenes(self,cid):
        scenes=self.store.load_scenes(self.book)
        changed=False
        for scene in scenes:
            if cid in scene.character_ids:
                scene.character_ids=[x for x in scene.character_ids if x!=cid]; changed=True
        if not changed:
            return True
        result = self.persist_scenes(scenes)
        if result != 'mine':
            return False
        self.outline_page.load()
        return True
