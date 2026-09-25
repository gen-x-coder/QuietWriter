from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QTextEdit, QVBoxLayout, QWidget
)

from ..book_profile import SECTIONS, empty_book_profile, parse_book_profile, render_book_profile
from ..i18n import tr
from ..revisions import ExternalModificationError, RevisionVerificationError


class BookProfilePage(QWidget):
    """Structured editor for the book-local, human-readable AI profile."""

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.book = None
        self.profile = empty_book_profile()
        self._loaded_profile = empty_book_profile()
        self._current_key: str | None = None
        self._loading = False
        self.dirty = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 26, 36, 30)
        outer.setSpacing(14)

        title = QLabel(tr('book_profile.title', 'Boekprofiel')); title.setObjectName('title')
        info = QLabel(tr(
            'book_profile.info',
            'Dit profiel geldt alleen voor het geopende boek. Het verfijnt je schrijverspersona en wordt automatisch als projectspecifieke context aan AI meegegeven.'
        ))
        info.setObjectName('muted'); info.setWordWrap(True)
        outer.addWidget(title); outer.addWidget(info)

        self.path_label = QLabel(); self.path_label.setObjectName('muted'); self.path_label.setWordWrap(True)
        outer.addWidget(self.path_label)

        body = QHBoxLayout(); body.setSpacing(18)
        nav_host = QFrame(); nav_host.setObjectName('settingsNav')
        nav_layout = QVBoxLayout(nav_host); nav_layout.setContentsMargins(8, 8, 8, 8); nav_layout.setSpacing(6)
        nav_title = QLabel(tr('book_profile.sections', 'Onderdelen')); nav_title.setObjectName('sectionTitle')
        nav_layout.addWidget(nav_title)
        self.sections = QListWidget(); self.sections.setObjectName('bookProfileSectionList')
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
        self.edit.setPlaceholderText(tr('book_profile.placeholder', 'Beschrijf hier wat specifiek voor dit boek belangrijk is…'))
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
            self.profile[self._current_key] = self.edit.toPlainText()

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
            self.edit.setPlainText(self.profile.get(key, ''))
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
                tr('book_profile.unsaved', 'Niet-opgeslagen wijzigingen') if self.dirty
                else tr('book_profile.saved', 'Opgeslagen in ai/boekprofiel.md')
            )

    def set_book(self, book, *, force: bool = False):
        if self.book and book and self.book.id != book.id and self.dirty and not force:
            if self.save() is False:
                return False
        self.book = book
        self.setEnabled(book is not None)
        if book is None:
            self.profile = empty_book_profile()
            self._loaded_profile = empty_book_profile()
            self._current_key = None
            self.edit.clear()
            self.path_label.setText('')
            self._set_dirty(False)
            return True
        self.path_label.setText(tr(
            'book_profile.file_help',
            'Bronbestand: {path}. Het blijft gewone Markdown en is ook buiten QuietWriter leesbaar en bewerkbaar.'
        ).format(path=str(self.main.library.book_profile_path(book))))
        return self.reload(force=force)

    def adopt_book(self, book):
        """Rebind same-book live state and merge untouched fields from disk."""
        same_book = bool(self.book and book and self.book.id == book.id)
        if same_book and self.dirty:
            self._store_editor()
            disk_profile = parse_book_profile(self.main.library.read_book_profile(book))
            merged = {}
            for section in SECTIONS:
                key = section.key
                local = self.profile.get(key, '')
                baseline = self._loaded_profile.get(key, '')
                merged[key] = local if local != baseline else disk_profile.get(key, '')
            self.book = book
            self.profile = merged
            self._loaded_profile = deepcopy(disk_profile)
            self.path_label.setText(tr(
                'book_profile.file_help',
                'Bronbestand: {path}. Het blijft gewone Markdown en is ook buiten QuietWriter leesbaar en bewerkbaar.'
            ).format(path=str(self.main.library.book_profile_path(book))))
            self._loading = True
            try:
                item = self.sections.currentItem()
                if item is not None:
                    key = item.data(Qt.UserRole)
                    self._current_key = key
                    self.edit.setPlainText(self.profile.get(key, ''))
            finally:
                self._loading = False
            self._set_dirty(self.profile != disk_profile)
            return True
        return self.set_book(book, force=True)

    def reload(self, *, force: bool = False):
        if not self.book:
            return True
        if self.dirty and not force:
            return True
        self._loading = True
        try:
            self.profile = parse_book_profile(self.main.library.read_book_profile(self.book))
            self._loaded_profile = deepcopy(self.profile)
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
                self.edit.setPlainText(self.profile.get(key, ''))
        finally:
            self._loading = False
        self._set_dirty(False)
        return True

    def save(self):
        if not self.book:
            return True
        self._store_editor()
        text = render_book_profile(self.profile)
        try:
            self.main.library.save_book_profile(self.book, text)
        except RevisionVerificationError:
            QMessageBox.warning(
                self,
                tr('book_profile.save_unavailable_title', 'Boekprofiel tijdelijk niet opgeslagen'),
                tr('book_profile.save_unavailable', 'QuietWriter kan de actuele bestanden tijdelijk niet betrouwbaar controleren. Er is niets overschreven. Probeer het zo opnieuw.')
            )
            return False
        except ExternalModificationError as exc:
            return self._resolve_external_change(text, exc)
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr('book_profile.save_error_title', 'Boekprofiel'),
                tr('book_profile.save_error', 'Opslaan mislukt:\n{error}').format(error=exc)
            )
            return False
        self._loaded_profile = deepcopy(self.profile)
        self._set_dirty(False)
        return True

    def _resolve_external_change(self, local_text: str, exc):
        changed = '\n'.join('• ' + name for name in exc.changed_files[:6])
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr('book_profile.conflict_title', 'Boek extern gewijzigd'))
        box.setText(tr('book_profile.conflict_text', 'Dit boek is buiten QuietWriter gewijzigd.'))
        box.setInformativeText(tr(
            'book_profile.conflict_info',
            'QuietWriter heeft het boekprofiel niet overschreven.\n\nGewijzigd:\n{changed}\n\nWelke versie wil je gebruiken? Beide keuzes maken eerst automatisch een herstelversie.'
        ).format(changed=changed))
        mine = box.addButton(tr('book_profile.conflict_mine', 'Mijn boekprofiel gebruiken'), QMessageBox.AcceptRole)
        disk = box.addButton(tr('book_profile.conflict_disk', 'Versie op schijf gebruiken'), QMessageBox.DestructiveRole)
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
                self.main.library.save_book_profile(latest, local_text)
                result = 'mine'
            else:
                self.main.library.create_version_with_file_overrides(
                    old_book, {'ai/boekprofiel.md': local_text}, kind='conflict_local'
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
        except Exception as error:
            QMessageBox.critical(
                self,
                tr('book_profile.conflict_failed_title', 'Conflict niet opgelost'),
                tr('book_profile.conflict_failed', 'Er is niets bewust overschreven.\n\n{error}').format(error=error)
            )
            return False
