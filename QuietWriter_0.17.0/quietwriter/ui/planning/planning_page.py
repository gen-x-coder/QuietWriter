from __future__ import annotations

import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from ...planning_storage import PlanningStore
from ...revisions import ExternalModificationError, RevisionVerificationError
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
        self.characters_button=self._nav(sl,'Personages',0)
        self.outline_button=self._nav(sl,'Outline',1)
        self.notes_button=self._nav(sl,'Notities',2)
        sl.addStretch()
        self.pages=QStackedWidget(); self.characters_page=CharactersPage(self); self.outline_page=OutlinePage(self); self.notes_page=NotesPage(self)
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

    def set_book(self,book):
        if self.book and self.book.id != getattr(book,'id',None):
            if self.notes_page.save() is False:
                return False
        self.book=book
        enabled=book is not None; self.setEnabled(enabled)
        if not enabled:return True
        self.characters_page.load(); self.outline_page.load(); self.notes_page.load(); return True

    def save_pending(self):
        return self.notes_page.save()

    def _planning_override_bytes(self, kind, value):
        if kind=='characters':
            return json.dumps({'version':1,'characters':[c.to_dict() for c in value]},ensure_ascii=False,indent=2)
        if kind=='scenes':
            return json.dumps({'version':1,'scenes':[s.to_dict() for s in value]},ensure_ascii=False,indent=2)
        return str(value)

    def _persist(self, kind, value, writer):
        if not self.book:return False
        try:
            writer(self.book,value); return True
        except RevisionVerificationError:
            QMessageBox.warning(self,'Opslaan tijdelijk niet mogelijk','QuietWriter kan de actuele bestanden tijdelijk niet betrouwbaar controleren. Er is niets overschreven. Probeer het zo opnieuw.'); return False
        except ExternalModificationError as exc:
            return self._resolve_external_change(kind,value,writer,exc)
        except Exception as exc:
            QMessageBox.critical(self,'Planning opslaan',f'Opslaan is mislukt.\n\n{exc}'); return False

    def _resolve_external_change(self,kind,value,writer,exc):
        changed='\n'.join('• '+name for name in exc.changed_files[:6])
        box=QMessageBox(self); box.setIcon(QMessageBox.Warning); box.setWindowTitle('Boek extern gewijzigd'); box.setText('Dit boek is buiten QuietWriter gewijzigd.')
        box.setInformativeText('QuietWriter heeft de planning niet overschreven.\n\nGewijzigd:\n'+changed+'\n\nWelke versie wil je gebruiken?')
        mine=box.addButton('Mijn planning gebruiken',QMessageBox.AcceptRole); disk=box.addButton('Versie op schijf gebruiken',QMessageBox.DestructiveRole); box.setDefaultButton(disk); box.exec()
        if box.clickedButton() not in (mine,disk): return False
        try:
            if box.clickedButton() is mine:
                # Preserve external disk state first. Then accept it as the new
                # baseline and overwrite only the selected planning file.
                self.main.library.create_version(self.book,kind='conflict_external')
                latest=self.main.library.load_book(self.book.path); self.main.library.track_book(latest); self.book=latest
                writer(latest,value)
                self.main.editor_page.book=latest
            else:
                # Preserve the unsaved local planning payload in History before
                # reloading the current disk state.
                relative={'characters':'planning/characters.json','scenes':'planning/outline.json','notes':'planning/notes.md'}[kind]
                self.main.library.create_version_with_file_overrides(self.book,{relative:self._planning_override_bytes(kind,value)},kind='conflict_local')
                latest=self.main.library.load_book(self.book.path); self.main.library.track_book(latest); self.book=latest; self.main.editor_page.book=latest
            self.set_book(self.book)
            return box.clickedButton() is mine
        except Exception as error:
            QMessageBox.critical(self,'Conflict niet opgelost',f'Er is niets bewust overschreven.\n\n{error}'); return False

    def persist_characters(self,characters): return self._persist('characters',characters,self.store.save_characters)
    def persist_scenes(self,scenes): return self._persist('scenes',scenes,self.store.save_scenes)
    def persist_notes(self,text): return self._persist('notes',text,self.store.save_notes)

    def remove_character_from_scenes(self,cid):
        scenes=self.store.load_scenes(self.book)
        changed=False
        for scene in scenes:
            if cid in scene.character_ids:
                scene.character_ids=[x for x in scene.character_ids if x!=cid]; changed=True
        if changed: self.persist_scenes(scenes); self.outline_page.load()
