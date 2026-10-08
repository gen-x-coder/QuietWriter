from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from ..fragment_store import FragmentExternalModificationError, FragmentStore
from ..document_view import visible_text
from ..i18n import tr


class DarlingsPage(QWidget):
    """Workspace-wide browser for saved text fragments.

    Fragment text is deliberately read-only in this first UI slice. Only title,
    note and tags are editable; their save path always carries the revision that
    was loaded with the selected fragment.
    """

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.store = FragmentStore(main.library.root)
        self._loading = False
        self._loaded_fragment = None
        self.dirty = False
        self._conflict_pending = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 26, 36, 30)
        outer.setSpacing(14)

        title = QLabel(tr('darlings.title', 'Bewaarplaats'))
        title.setObjectName('title')
        info = QLabel(tr(
            'darlings.info',
            "Don't kill your darlings. "
            'Soms schrijf je een zin, alinea of scène waar je eigenlijk geen afscheid van wilt nemen. '
            'Toch past hij niet meer in het verhaal. '
            'In de Bewaarplaats kun je zulke fragmenten bewaren zonder ze definitief kwijt te zijn. '
            'Haal ze gerust uit je manuscript, geef ze hier een plek en gebruik ze later opnieuw als ze ergens anders beter tot hun recht komen.'
        ))
        info.setObjectName('muted')
        info.setWordWrap(True)
        outer.addWidget(title)
        outer.addWidget(info)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr('darlings.search', 'Zoeken in titel, notitie, tags en tekst…'))
        self.tag_filter = QComboBox()
        self.tag_filter.setMinimumWidth(180)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.tag_filter, 0)
        outer.addLayout(filters)

        self.warning = QLabel()
        self.warning.setObjectName('muted')
        self.warning.setWordWrap(True)
        self.warning.hide()
        outer.addWidget(self.warning)

        body = QHBoxLayout()
        body.setSpacing(18)

        left = QFrame()
        left.setObjectName('settingsNav')
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)
        list_title = QLabel(tr('darlings.fragments', 'Fragmenten'))
        list_title.setObjectName('sectionTitle')
        self.list = QListWidget()
        self.list.setObjectName('darlingsList')
        self.list.setMinimumWidth(285)
        self.list.setMaximumWidth(360)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
        left_layout.addWidget(list_title)
        left_layout.addWidget(self.list, 1)
        body.addWidget(left, 0)

        right = QVBoxLayout()
        right.setSpacing(8)
        self.detail_title = QLabel(tr('darlings.detail', 'Fragment'))
        self.detail_title.setObjectName('sectionTitle')
        right.addWidget(self.detail_title)

        origin = QFrame()
        origin.setObjectName('insertChoiceCard')
        origin_layout = QVBoxLayout(origin)
        origin_layout.setContentsMargins(12, 10, 12, 10)
        origin_layout.setSpacing(3)
        origin_title = QLabel(tr('darlings.origin', 'Herkomst'))
        origin_title.setObjectName('sectionTitle')
        self.source_book = QLabel()
        self.source_book.setObjectName('muted')
        self.source_book.setWordWrap(True)
        self.source_chapter = QLabel()
        self.source_chapter.setObjectName('muted')
        self.source_chapter.setWordWrap(True)
        origin_layout.addWidget(origin_title)
        origin_layout.addWidget(self.source_book)
        origin_layout.addWidget(self.source_chapter)
        right.addWidget(origin)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(tr('darlings.title_placeholder', 'Titel (optioneel)'))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText(tr('darlings.tags_placeholder', 'Tags, gescheiden door komma’s'))
        self.note_edit = QTextEdit()
        self.note_edit.setAcceptRichText(False)
        self.note_edit.setMaximumHeight(110)
        self.note_edit.setPlaceholderText(tr('darlings.note_placeholder', 'Notitie (optioneel)'))
        self.preview = QTextEdit()
        self.preview.setAcceptRichText(False)
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText(tr('darlings.preview_placeholder', 'Selecteer een fragment om het te bekijken.'))

        right.addWidget(QLabel(tr('darlings.field.title', 'Titel')))
        right.addWidget(self.title_edit)
        right.addWidget(QLabel(tr('darlings.field.tags', 'Tags')))
        right.addWidget(self.tags_edit)
        right.addWidget(QLabel(tr('darlings.field.note', 'Notitie')))
        right.addWidget(self.note_edit)
        right.addWidget(QLabel(tr('darlings.field.text', 'Tekst')))
        right.addWidget(self.preview, 1)

        save_row = QHBoxLayout()
        self.status = QLabel()
        self.status.setObjectName('muted')
        self.insert_button = QPushButton(tr('darlings.insert_at_cursor', 'Invoegen bij cursor'))
        self.insert_button.setObjectName('secondaryButton')
        self.insert_button.clicked.connect(self.insert_at_cursor)
        self.trash_button = QPushButton(tr('darlings.move_to_trash', 'Naar prullenbak'))
        self.trash_button.setObjectName('secondaryButton')
        self.trash_button.clicked.connect(self.move_current_to_trash)
        self.save_button = QPushButton(tr('common.save', 'Opslaan'))
        self.save_button.setObjectName('primaryButton')
        self.save_button.clicked.connect(self.save_metadata)
        save_row.addWidget(self.status)
        save_row.addStretch()
        save_row.addWidget(self.insert_button)
        save_row.addWidget(self.trash_button)
        save_row.addWidget(self.save_button)
        right.addLayout(save_row)
        body.addLayout(right, 1)
        outer.addLayout(body, 1)

        self.search.textChanged.connect(self.refresh)
        self.tag_filter.currentIndexChanged.connect(self.refresh)
        self.list.currentItemChanged.connect(self._selection_changed)
        self.title_edit.textChanged.connect(self._mark_dirty)
        self.tags_edit.textChanged.connect(self._mark_dirty)
        self.note_edit.textChanged.connect(self._mark_dirty)
        self._set_detail_enabled(False)
        self.refresh()

    @staticmethod
    def _first_text_line(text: str) -> str:
        projected = visible_text(text)
        return next((line.strip() for line in projected.splitlines() if line.strip()), '')

    def display_name(self, fragment) -> str:
        if fragment.title.strip():
            return fragment.title.strip()
        first = self._first_text_line(fragment.text)
        return first[:80] if first else tr('darlings.untitled', 'Naamloos fragment')

    def _item_text(self, fragment) -> str:
        source = ' · '.join(part for part in (fragment.source_book_title, fragment.source_chapter_title) if part)
        return self.display_name(fragment) + (f'\n{source}' if source else '')

    def _set_detail_enabled(self, enabled: bool):
        for widget in (self.title_edit, self.tags_edit, self.note_edit, self.preview, self.trash_button, self.save_button):
            widget.setEnabled(enabled)
        editor_page = getattr(self.main, 'editor_page', None)
        can_insert = bool(
            enabled and editor_page is not None and editor_page.book and editor_page.chapter
            and not editor_page.preview_live_book and not editor_page._chapter_corrupt
        )
        self.insert_button.setEnabled(can_insert)
        if not enabled:
            self.source_book.clear()
            self.source_chapter.clear()
            self.status.clear()

    def _set_conflict_pending(self, pending: bool):
        self._conflict_pending = bool(pending)
        self.search.setEnabled(not pending)
        self.tag_filter.setEnabled(not pending)

    def _show_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if item is None:
            return
        self.list.setCurrentItem(item)
        fragment = item.data(Qt.UserRole)
        if fragment is None:
            return
        menu = QMenu(self)
        insert_action = menu.addAction(tr('darlings.insert_at_cursor', 'Invoegen bij cursor'))
        insert_action.setEnabled(self.insert_button.isEnabled())
        trash_action = menu.addAction(tr('darlings.move_to_trash', 'Naar prullenbak'))
        chosen = menu.exec(self.list.viewport().mapToGlobal(pos))
        if chosen is insert_action:
            self.insert_at_cursor()
        elif chosen is trash_action:
            self.move_current_to_trash()

    def _confirm_move_to_trash(self) -> bool:
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Warning)
        message.setWindowTitle(tr('darlings.trash_title', 'Fragment naar prullenbak'))
        message.setText(tr('darlings.trash_text', 'Wil je dit fragment naar de prullenbak verplaatsen?'))
        move = message.addButton(tr('darlings.move_to_trash', 'Naar prullenbak'), QMessageBox.DestructiveRole)
        cancel = message.addButton(tr('common.cancel', 'Annuleren'), QMessageBox.RejectRole)
        message.setDefaultButton(cancel)
        message.setEscapeButton(cancel)
        message.exec()
        return message.clickedButton() is move

    def move_current_to_trash(self):
        fragment = self._loaded_fragment
        if fragment is None:
            return False
        if self.dirty and not self._save_current_fields():
            return False
        if not self._confirm_move_to_trash():
            return False
        try:
            self.store.move_to_trash(fragment.id)
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr('darlings.trash_failed_title', 'Fragment niet verplaatst'),
                tr('darlings.trash_failed_text', 'Het fragment kon niet veilig naar de prullenbak worden verplaatst.\n\n{error}', error=exc),
            )
            return False
        self._loaded_fragment = None
        self.dirty = False
        self._set_conflict_pending(False)
        self.refresh()
        self.status.setText(tr('darlings.trashed', 'Fragment staat in de prullenbak'))
        return True

    def refresh(self, *_args, select_id: str | None = None):
        if self._loading:
            return
        if self._conflict_pending:
            return
        # Filtering must never discard unsaved metadata. Save first; on a
        # conflict/error keep the user's fields intact and leave the list as-is.
        if self.dirty and not self.save_pending():
            return
        current_id = select_id
        if current_id is None and self._loaded_fragment is not None:
            current_id = self._loaded_fragment.id

        fragments = self.store.list_fragments()
        demo_mode = bool(getattr(self.main, 'start', None) and self.main.start.demo_mode_enabled())
        if demo_mode:
            source_ids = {fragment.source_book_id for fragment in fragments if fragment.source_book_id}
            visible_ids = self.main.library.shelves.visible_book_ids(source_ids, demo_mode=True)
            fragments = [
                fragment for fragment in fragments
                if not fragment.source_book_id or fragment.source_book_id in visible_ids
            ]
        errors = [] if demo_mode else list(self.store.last_list_errors)
        all_tags = sorted({tag for fragment in fragments for tag in fragment.tags}, key=str.casefold)

        self._loading = True
        try:
            selected_tag = self.tag_filter.currentData() or ''
            self.tag_filter.clear()
            self.tag_filter.addItem(tr('darlings.all_tags', 'Alle tags'), '')
            for tag in all_tags:
                self.tag_filter.addItem(tag, tag)
            idx = self.tag_filter.findData(selected_tag)
            self.tag_filter.setCurrentIndex(idx if idx >= 0 else 0)
            tag_cf = str(self.tag_filter.currentData() or '').casefold()
            query = self.search.text().strip().casefold()

            self.list.clear()
            selected_row = -1
            for fragment in fragments:
                if tag_cf and not any(tag.casefold() == tag_cf for tag in fragment.tags):
                    continue
                haystack = '\n'.join((
                    fragment.title, fragment.note, visible_text(fragment.text),
                    fragment.source_book_title, fragment.source_chapter_title,
                    ' '.join(fragment.tags),
                )).casefold()
                if query and query not in haystack:
                    continue
                item = QListWidgetItem(self._item_text(fragment))
                item.setData(Qt.UserRole, fragment)
                self.list.addItem(item)
                if fragment.id == current_id:
                    selected_row = self.list.count() - 1

            if errors:
                self.warning.setText(tr(
                    'darlings.read_errors',
                    'Niet alle fragmenten konden worden gelezen ({count}). De overige fragmenten blijven beschikbaar.',
                    count=len(errors),
                ))
                self.warning.show()
            else:
                self.warning.clear()
                self.warning.hide()

            if self.list.count():
                self.list.setCurrentRow(selected_row if selected_row >= 0 else 0)
            else:
                self._loaded_fragment = None
                self._clear_detail()
        finally:
            self._loading = False

        if self.list.currentItem() is not None:
            self._selection_changed(self.list.currentItem())

    def _clear_detail(self):
        self._loading = True
        try:
            self.title_edit.clear()
            self.tags_edit.clear()
            self.note_edit.clear()
            self.preview.clear()
            self.dirty = False
            self._set_conflict_pending(False)
            self._set_detail_enabled(False)
        finally:
            self._loading = False

    def _selection_changed(self, item, previous=None):
        if self._loading:
            return
        if self.dirty and self._loaded_fragment is not None and item is not None:
            next_fragment = item.data(Qt.UserRole)
            if next_fragment is not None and next_fragment.id != self._loaded_fragment.id:
                if not self._save_current_fields():
                    old_id = self._loaded_fragment.id if self._loaded_fragment is not None else None
                    self._loading = True
                    try:
                        for row in range(self.list.count()):
                            candidate = self.list.item(row).data(Qt.UserRole)
                            if candidate is not None and candidate.id == old_id:
                                self.list.setCurrentRow(row)
                                break
                    finally:
                        self._loading = False
                    return
                if previous is not None:
                    previous.setData(Qt.UserRole, self._loaded_fragment)
                    previous.setText(self._item_text(self._loaded_fragment))
        if item is None:
            self._loaded_fragment = None
            self._clear_detail()
            return
        fragment = item.data(Qt.UserRole)
        if fragment is None:
            return
        self._loaded_fragment = fragment
        self._loading = True
        try:
            self._set_detail_enabled(True)
            self.title_edit.setText(fragment.title)
            self.tags_edit.setText(', '.join(fragment.tags))
            self.note_edit.setPlainText(fragment.note)
            self.preview.setPlainText(visible_text(fragment.text))
            self.source_book.setText(tr(
                'darlings.source_book', 'Boek: {book}',
                book=fragment.source_book_title or tr('darlings.source_unknown_short', 'niet vastgelegd'),
            ))
            self.source_chapter.setText(tr(
                'darlings.source_chapter', 'Hoofdstuk: {chapter}',
                chapter=fragment.source_chapter_title or tr('darlings.source_unknown_short', 'niet vastgelegd'),
            ))
            self.status.setText(tr('darlings.saved', 'Opgeslagen'))
            self.dirty = False
            self._set_conflict_pending(False)
            self.save_button.setEnabled(False)
        finally:
            self._loading = False

    def _mark_dirty(self, *_args):
        if self._loading or self._loaded_fragment is None:
            return
        self.dirty = True
        self.status.setText(tr('darlings.unsaved', 'Niet-opgeslagen wijzigingen'))
        self.save_button.setEnabled(True)

    def _save_current_fields(self):
        fragment = self._loaded_fragment
        if fragment is None or not self.dirty:
            return True
        tags = [part.strip() for part in self.tags_edit.text().split(',') if part.strip()]
        try:
            updated = self.store.update_metadata(
                fragment.id,
                expected_revision=fragment.revision,
                title=self.title_edit.text(),
                note=self.note_edit.toPlainText(),
                tags=tags,
            )
        except FragmentExternalModificationError:
            return self._resolve_external_conflict(fragment, tags)
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr('darlings.save_failed_title', 'Fragment niet opgeslagen'),
                tr('darlings.save_failed_text', 'De fragmentgegevens konden niet veilig worden opgeslagen.\n\n{error}', error=exc),
            )
            return False
        self._loaded_fragment = updated
        self.dirty = False
        self._set_conflict_pending(False)
        self.status.setText(tr('darlings.saved', 'Opgeslagen'))
        self.save_button.setEnabled(False)
        return True


    @staticmethod
    def _short_note(text: str, limit: int = 320) -> str:
        clean = text.strip()
        return clean if len(clean) <= limit else clean[:limit].rstrip() + '…'

    def _choose_external_conflict(self, current) -> str:
        disk_title = current.title or tr('darlings.untitled', 'Naamloos fragment')
        disk_tags = ', '.join(current.tags) or tr('darlings.none', 'geen')
        disk_note = self._short_note(current.note) or tr('darlings.none', 'geen')
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Warning)
        message.setWindowTitle(tr('darlings.external_title', 'Fragment extern gewijzigd'))
        message.setText(tr(
            'darlings.external_choice_text',
            'Dit fragment is elders gewijzigd. Kies welke metadata je wilt gebruiken.\n\n'
            'Versie op schijf:\nTitel: {title}\nTags: {tags}\nNotitie: {note}',
            title=disk_title, tags=disk_tags, note=disk_note,
        ))
        keep_local = message.addButton(
            tr('darlings.keep_local', 'Mijn invoer bewaren'), QMessageBox.AcceptRole
        )
        use_disk = message.addButton(
            tr('darlings.use_disk', 'Versie op schijf gebruiken'), QMessageBox.DestructiveRole
        )
        cancel = message.addButton(
            tr('common.cancel', 'Annuleren'), QMessageBox.RejectRole
        )
        message.setDefaultButton(use_disk)
        message.setEscapeButton(cancel)
        message.exec()
        if message.clickedButton() is keep_local:
            return 'local'
        if message.clickedButton() is use_disk:
            return 'disk'
        return 'cancel'

    def _resolve_external_conflict(self, previous, local_tags):
        """Resolve a metadata race immediately; never leave a silently savable conflict."""
        try:
            current = self.store.load(previous.id)
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr('darlings.save_failed_title', 'Fragment niet opgeslagen'),
                tr('darlings.save_failed_text', 'De fragmentgegevens konden niet veilig worden opgeslagen.\n\n{error}', error=exc),
            )
            return False

        choice = self._choose_external_conflict(current)
        if choice == 'cancel':
            self.dirty = True
            self._set_conflict_pending(True)
            self.status.setText(tr('darlings.external_cancelled', 'Conflict niet opgelost · kies Opslaan'))
            self.save_button.setEnabled(True)
            return False

        if choice == 'local':
            try:
                updated = self.store.update_metadata(
                    current.id,
                    expected_revision=current.revision,
                    title=self.title_edit.text(),
                    note=self.note_edit.toPlainText(),
                    tags=local_tags,
                )
            except FragmentExternalModificationError:
                self._loaded_fragment = self.store.load(current.id)
                self.dirty = True
                self.status.setText(tr('darlings.external_pending', 'Opnieuw extern gewijzigd'))
                self.save_button.setEnabled(True)
                QMessageBox.warning(
                    self,
                    tr('darlings.external_title', 'Fragment extern gewijzigd'),
                    tr('darlings.external_again', 'Het fragment is opnieuw elders gewijzigd. Er is niets overschreven; probeer Opslaan opnieuw.'),
                )
                return False
            self._loaded_fragment = updated
            self.dirty = False
            self._set_conflict_pending(False)
            self.status.setText(tr('darlings.saved', 'Opgeslagen'))
            self.save_button.setEnabled(False)
            return True

        self._loaded_fragment = current
        self._loading = True
        try:
            self.title_edit.setText(current.title)
            self.tags_edit.setText(', '.join(current.tags))
            self.note_edit.setPlainText(current.note)
        finally:
            self._loading = False
        self.dirty = False
        self._set_conflict_pending(False)
        self.status.setText(tr('darlings.disk_version_loaded', 'Versie op schijf geladen'))
        self.save_button.setEnabled(False)
        return True

    def insert_at_cursor(self):
        fragment = self._loaded_fragment
        if fragment is None:
            return False
        if self.dirty and not self._save_current_fields():
            return False
        if not self.main.editor_page.insert_darling_at_cursor(fragment):
            return False
        self.main.show_editor()
        return True

    def save_pending(self):
        return self._save_current_fields()

    def save_metadata(self):
        fragment_id = self._loaded_fragment.id if self._loaded_fragment is not None else None
        if not self._save_current_fields():
            return False
        if fragment_id:
            self.refresh(select_id=fragment_id)
        return True

    def add_fragment(self, fragment):
        self.refresh(select_id=fragment.id)
