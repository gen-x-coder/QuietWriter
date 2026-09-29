from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QTextEdit, QVBoxLayout, QWidget
)

from ..book_memory import SECTIONS, append_memory_entry, empty_book_memory, parse_book_memory, render_book_memory
from ..i18n import tr
from ..field_merge import merge_scalar_fields
from ..revisions import ExternalModificationError, RevisionVerificationError
from ..migrations import FutureBookFormatError


class BookMemoryPage(QWidget):
    """Structured editor for transparent, book-local AI memory."""

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.book = None
        self.memory = empty_book_memory()
        self._loaded_memory = empty_book_memory()
        self._current_key: str | None = None
        self._loading = False
        self.dirty = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 26, 36, 30)
        outer.setSpacing(14)

        title = QLabel(tr('book_memory.title', 'Boekgeheugen')); title.setObjectName('title')
        info = QLabel(tr(
            'book_memory.info',
            'Dit geheugen geldt alleen voor het geopende boek. Bewaar hier wat AI bij volgende gesprekken moet blijven weten. AI kan een geheugenregel voorstellen, maar alleen jouw expliciete keuze Onthouden schrijft naar dit bestand.'
        ))
        info.setObjectName('muted'); info.setWordWrap(True)
        outer.addWidget(title); outer.addWidget(info)

        self.path_label = QLabel(); self.path_label.setObjectName('muted'); self.path_label.setWordWrap(True)
        outer.addWidget(self.path_label)

        body = QHBoxLayout(); body.setSpacing(18)
        nav_host = QFrame(); nav_host.setObjectName('settingsNav')
        nav_layout = QVBoxLayout(nav_host); nav_layout.setContentsMargins(8, 8, 8, 8); nav_layout.setSpacing(6)
        nav_title = QLabel(tr('book_memory.sections', 'Onderdelen')); nav_title.setObjectName('sectionTitle')
        nav_layout.addWidget(nav_title)
        self.sections = QListWidget(); self.sections.setObjectName('bookMemorySectionList')
        self.sections.setMinimumWidth(230); self.sections.setMaximumWidth(280)
        for section in SECTIONS:
            item = QListWidgetItem(section.title)
            item.setData(Qt.UserRole, section.key)
            self.sections.addItem(item)
        nav_layout.addWidget(self.sections, 1)
        body.addWidget(nav_host, 0)

        detail = QVBoxLayout(); detail.setSpacing(8)
        self.section_title = QLabel(); self.section_title.setObjectName('sectionTitle')
        self.section_help = QLabel(); self.section_help.setObjectName('muted'); self.section_help.setWordWrap(True)
        self.edit = QTextEdit(); self.edit.setAcceptRichText(False)
        self.edit.setPlaceholderText(tr('book_memory.placeholder', 'Leg hier vast wat AI bij volgende gesprekken over dit boek moet blijven weten…'))
        detail.addWidget(self.section_title)
        detail.addWidget(self.section_help)
        detail.addSpacing(4)
        detail.addWidget(self.edit, 1)
        body.addLayout(detail, 1)
        outer.addLayout(body, 1)

        bottom = QHBoxLayout()
        self.status = QLabel(); self.status.setObjectName('muted')
        self.save_button = QPushButton(tr('common.save', 'Opslaan')); self.save_button.setObjectName('primaryButton')
        self.save_button.clicked.connect(self.save)
        bottom.addWidget(self.status); bottom.addStretch(); bottom.addWidget(self.save_button)
        outer.addLayout(bottom)

        self.sections.currentItemChanged.connect(self._section_changed)
        self.edit.textChanged.connect(self._edited)
        self.setEnabled(False)
        self._set_dirty(False)

    def _section_for_key(self, key: str):
        return next(section for section in SECTIONS if section.key == key)

    def _store_editor(self):
        if self._current_key is not None:
            self.memory[self._current_key] = self.edit.toPlainText()

    def _section_changed(self, item, _previous=None):
        if item is None:
            return
        if not self._loading:
            self._store_editor()
        key = item.data(Qt.UserRole)
        section = self._section_for_key(key)
        self._current_key = key
        self._loading = True
        try:
            self.section_title.setText(section.title)
            self.section_help.setText(section.help)
            self.edit.setPlainText(self.memory.get(key, ''))
        finally:
            self._loading = False

    def _edited(self):
        if self._loading:
            return
        self._store_editor()
        self._set_dirty(True)

    def _set_dirty(self, dirty: bool):
        self.dirty = bool(dirty)
        self.save_button.setEnabled(bool(self.book) and self.dirty)
        if not self.book:
            self.status.setText('')
        else:
            self.status.setText(
                tr('book_memory.unsaved', 'Niet-opgeslagen wijzigingen') if self.dirty
                else tr('book_memory.saved', 'Opgeslagen in ai/memory.md')
            )

    def set_book(self, book, *, force: bool = False):
        if self.book and book and self.book.id != book.id and self.dirty and not force:
            if self.save() is False:
                return False
        self.book = book
        self.setEnabled(book is not None)
        if book is None:
            self.memory = empty_book_memory()
            self._loaded_memory = empty_book_memory()
            self._current_key = None
            self.edit.clear()
            self.path_label.setText('')
            self._set_dirty(False)
            return True
        self.path_label.setText(tr(
            'book_memory.file_help',
            'Bronbestand: {path}. Het blijft gewone Markdown en is ook buiten QuietWriter leesbaar en bewerkbaar. Planning blijft de bron voor personages en scènes.'
        ).format(path=str(self.main.library.book_memory_path(book))))
        return self.reload(force=force)

    def adopt_book(self, book):
        """Rebind same-book live state and merge untouched fields from disk."""
        same_book = bool(self.book and book and self.book.id == book.id)
        if same_book and self.dirty:
            self._store_editor()
            local_memory = deepcopy(self.memory)
            disk_memory = parse_book_memory(self.main.library.read_book_memory(book))
            keys = [section.key for section in SECTIONS]
            merged, conflicts = merge_scalar_fields(local_memory, self._loaded_memory, disk_memory, keys)
            if conflicts:
                self.main.library.create_version_with_file_overrides(
                    book, {'ai/memory.md': render_book_memory(local_memory)}, kind='conflict_local'
                )
            self.book = book
            self.memory = merged
            self._loaded_memory = deepcopy(disk_memory)
            self.path_label.setText(tr(
                'book_memory.file_help',
                'Bronbestand: {path}. Het blijft gewone Markdown en is ook buiten QuietWriter leesbaar en bewerkbaar. Planning blijft de bron voor personages en scènes.'
            ).format(path=str(self.main.library.book_memory_path(book))))
            self._loading = True
            try:
                item = self.sections.currentItem()
                if item is not None:
                    key = item.data(Qt.UserRole)
                    self._current_key = key
                    self.edit.setPlainText(self.memory.get(key, ''))
            finally:
                self._loading = False
            self._set_dirty(self.memory != disk_memory)
            if conflicts:
                QMessageBox.information(
                    self,
                    tr('book_memory.merge_conflict_title', 'Lokale invoer veilig bewaard'),
                    tr(
                        'book_memory.merge_conflict_text',
                        'Dit boekgeheugen is op twee plaatsen in dezelfde velden gewijzigd. '
                        'De versie op schijf is voor die velden geladen; je lokale invoer staat apart in Versiegeschiedenis.'
                    ),
                )
            return True
        return self.set_book(book, force=True)

    def reload(self, *, force: bool = False):
        if not self.book:
            return True
        if self.dirty and not force:
            return True
        self._loading = True
        try:
            self.memory = parse_book_memory(self.main.library.read_book_memory(self.book))
            self._loaded_memory = deepcopy(self.memory)
            row = self.sections.currentRow()
            if row < 0:
                row = 0
            self.sections.setCurrentRow(row)
            item = self.sections.item(row)
            if item is not None:
                key = item.data(Qt.UserRole)
                section = self._section_for_key(key)
                self._current_key = key
                self.section_title.setText(section.title)
                self.section_help.setText(section.help)
                self.edit.setPlainText(self.memory.get(key, ''))
        finally:
            self._loading = False
        self._set_dirty(False)
        return True

    def _persist_memory_state(self) -> bool:
        """Persist ``self.memory`` exactly as it currently stands.

        This deliberately does *not* read from the visible editor again.  Callers
        that originate from the form use :meth:`save`, which first synchronizes
        the current field.  Programmatic mutations such as an approved AI memory
        proposal already updated ``self.memory`` and must not be overwritten by a
        stale editor widget immediately before the disk write.
        """
        if not self.book:
            return True
        text = render_book_memory(self.memory)
        try:
            self.main.library.save_book_memory(self.book, text)
        except RevisionVerificationError:
            QMessageBox.warning(
                self,
                tr('book_memory.save_unavailable_title', 'Boekgeheugen tijdelijk niet opgeslagen'),
                tr('book_memory.save_unavailable', 'QuietWriter kan de actuele bestanden tijdelijk niet betrouwbaar controleren. Er is niets overschreven. Probeer het zo opnieuw.')
            )
            return False
        except ExternalModificationError as exc:
            return self._resolve_external_change(text, exc)
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr('book_memory.save_error_title', 'Boekgeheugen'),
                tr('book_memory.save_error', 'Opslaan mislukt:\n{error}').format(error=exc)
            )
            return False
        self._loaded_memory = deepcopy(self.memory)
        self._set_dirty(False)
        return True

    def save(self):
        if not self.book:
            return True
        self._store_editor()
        return self._persist_memory_state()


    def add_suggestion(self, section_key: str, text: str) -> bool:
        """Persist one user-approved AI proposal, independent of page visibility."""
        active = self.main.active_book()
        if active is not None and (self.book is None or self.book.id != active.id):
            if self.adopt_book(active) is False:
                return False
        if not self.book:
            return False
        clean = (text or '').strip()
        if not clean:
            return False
        self._store_editor()
        before = deepcopy(self.memory)
        source = render_book_memory(self.memory)
        rendered, changed = append_memory_entry(source, section_key, clean)
        if not changed:
            # Already present counts as successfully remembered.
            parsed = parse_book_memory(rendered)
            if section_key in parsed:
                normalized = clean.lstrip('-*').strip().casefold()
                existing = {line.strip().lstrip('-*').strip().casefold() for line in parsed[section_key].splitlines() if line.strip()}
                if normalized in existing:
                    return True
            return False
        self.memory = parse_book_memory(rendered)
        self._set_dirty(self.memory != self._loaded_memory)
        if self._persist_memory_state() is False:
            self.memory = before
            self._loading = True
            try:
                if self._current_key is not None:
                    self.edit.setPlainText(self.memory.get(self._current_key, ''))
            finally:
                self._loading = False
            self._set_dirty(self.memory != self._loaded_memory)
            return False
        normalized = clean.lstrip('-*').strip().casefold()
        saved_lines = {line.strip().lstrip('-*').strip().casefold() for line in (self.memory.get(section_key) or '').splitlines() if line.strip()}
        if normalized not in saved_lines:
            return False
        if self._current_key == section_key:
            self._loading = True
            try:
                self.edit.setPlainText(self.memory.get(section_key, ''))
            finally:
                self._loading = False
        return True

    def _resolve_external_change(self, local_text: str, exc):
        changed = '\n'.join('• ' + name for name in exc.changed_files[:6])
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr('book_memory.conflict_title', 'Boek extern gewijzigd'))
        box.setText(tr('book_memory.conflict_text', 'Dit boek is buiten QuietWriter gewijzigd.'))
        box.setInformativeText(tr(
            'book_memory.conflict_info',
            'QuietWriter heeft het boekgeheugen niet overschreven.\n\nGewijzigd:\n{changed}\n\nWelke versie wil je gebruiken? Beide keuzes maken eerst automatisch een herstelversie.'
        ).format(changed=changed))
        mine = box.addButton(tr('book_memory.conflict_mine', 'Mijn boekgeheugen gebruiken'), QMessageBox.AcceptRole)
        disk = box.addButton(tr('book_memory.conflict_disk', 'Versie op schijf gebruiken'), QMessageBox.DestructiveRole)
        box.setDefaultButton(disk)
        box.exec()
        if box.clickedButton() not in (mine, disk):
            return False

        old_book = self.book
        preferred_chapter_id = self.main.editor_page.chapter.id if self.main.editor_page.chapter else None
        try:
            if box.clickedButton() is mine:
                self.main.library.create_version(old_book, kind='conflict_external')
                latest = self.main.library.load_book(old_book.path)
                self.main.library.track_book(latest)
                self.main.library.save_book_memory(latest, local_text)
                result = 'mine'
            else:
                self.main.library.create_version_with_file_overrides(
                    old_book, {'ai/memory.md': local_text}, kind='conflict_local'
                )
                latest = self.main.library.load_book(old_book.path)
                result = 'disk'
            self.main.adopt_active_book(latest, preferred_chapter_id)
            if result == 'disk':
                self.set_book(latest, force=True)
            else:
                self.book = latest
                self._set_dirty(False)
            return True
        except FutureBookFormatError:
            ok = self.main.preserve_local_and_close_future_book(old_book, file_overrides={'ai/memory.md': local_text}, context='boekgeheugen')
            return False if ok else False
        except Exception as error:
            QMessageBox.critical(
                self,
                tr('book_memory.conflict_failed_title', 'Conflict niet opgelost'),
                tr('book_memory.conflict_failed', 'Er is niets bewust overschreven.\n\n{error}').format(error=error)
            )
            return False
