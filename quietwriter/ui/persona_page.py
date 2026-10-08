from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget
)

from ..i18n import tr
from ..persona_profile import EXAMPLE_PERSONAS, SECTIONS, default_persona_markdown, empty_profile, parse_persona, render_persona
from ..storage import CorruptSourceError, PersonaExternalModificationError
from .dialogs import confirm


class ExamplePersonaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('persona.examples.title', 'Voorbeeldpersona kiezen'))
        self.setMinimumSize(700, 420)
        self._keys = list(EXAMPLE_PERSONAS)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        self.list = QListWidget()
        self.list.setMinimumWidth(260)
        for key in self._keys:
            template = EXAMPLE_PERSONAS[key]
            item = QListWidgetItem(f"{template['name']}\n{template['subtitle']}")
            item.setData(Qt.UserRole, key)
            self.list.addItem(item)
        root.addWidget(self.list, 0)

        right = QVBoxLayout()
        self.name = QLabel(); self.name.setObjectName('title')
        self.subtitle = QLabel(); self.subtitle.setObjectName('sectionTitle')
        self.description = QLabel(); self.description.setObjectName('muted'); self.description.setWordWrap(True)
        note = QLabel(tr(
            'persona.examples.note',
            'Voorbeelden zijn bewerkbare startprofielen op basis van brede, bekende stijlkenmerken. QuietWriter kopieert geen teksten van de auteur.'
        ))
        note.setObjectName('muted'); note.setWordWrap(True)
        right.addWidget(self.name)
        right.addWidget(self.subtitle)
        right.addSpacing(8)
        right.addWidget(self.description)
        right.addSpacing(16)
        right.addWidget(note)
        right.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        use = buttons.button(QDialogButtonBox.Ok)
        cancel = buttons.button(QDialogButtonBox.Cancel)
        if use is not None:
            use.setText(tr('persona.examples.use', 'Dit profiel gebruiken'))
            use.setObjectName('primaryButton')
        if cancel is not None:
            cancel.setText(tr('common.cancel', 'Annuleren'))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        right.addWidget(buttons)
        root.addLayout(right, 1)

        self.list.currentItemChanged.connect(self._selection_changed)
        self.list.itemDoubleClicked.connect(lambda _item: self.accept())
        self.list.setCurrentRow(0)

    def _selection_changed(self, item, _previous=None):
        if item is None:
            return
        template = EXAMPLE_PERSONAS[item.data(Qt.UserRole)]
        self.name.setText(str(template['name']))
        self.subtitle.setText(str(template['subtitle']))
        self.description.setText(str(template['description']))

    def selected_key(self) -> str | None:
        item = self.list.currentItem()
        return item.data(Qt.UserRole) if item is not None else None


class PersonaPage(QWidget):
    def __init__(self, library):
        super().__init__()
        self.library = library
        self.profile = empty_profile()
        self._current_key: str | None = None
        self._loading = False
        self.dirty = False
        self._loaded_revision = None
        self._corrupt_source = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 26, 36, 30)
        outer.setSpacing(14)

        top = QHBoxLayout()
        title_box = QVBoxLayout(); title_box.setSpacing(3)
        title = QLabel(tr('persona.title', 'Schrijverspersona')); title.setObjectName('title')
        info = QLabel(tr(
            'persona.info',
            'Je schrijverspersona helpt de Meelezer jou als schrijver te leren kennen. Je legt hier vast wat kenmerkend is voor jouw stem, toon, ritme, woordkeuze en redactionele voorkeuren. Daardoor kan de Meelezer gerichter aangeven wanneer een passage wel of juist niet bij jouw eigen stijl past, zonder die stijl voor je te gaan schrijven.'
        ))
        info.setObjectName('muted'); info.setWordWrap(True)
        title_box.addWidget(title); title_box.addWidget(info)
        top.addLayout(title_box, 1)
        self.example_button = QPushButton(tr('persona.examples.button', 'Voorbeeldpersona…'))
        self.example_button.clicked.connect(self.choose_example)
        top.addWidget(self.example_button, 0, Qt.AlignTop)
        outer.addLayout(top)

        body = QHBoxLayout(); body.setSpacing(18)
        nav_host = QFrame(); nav_host.setObjectName('settingsNav')
        nav_layout = QVBoxLayout(nav_host); nav_layout.setContentsMargins(8, 8, 8, 8); nav_layout.setSpacing(6)
        nav_title = QLabel(tr('persona.sections', 'Onderdelen')); nav_title.setObjectName('sectionTitle')
        nav_layout.addWidget(nav_title)
        self.sections = QListWidget(); self.sections.setObjectName('personaSectionList')
        self.sections.setMinimumWidth(230); self.sections.setMaximumWidth(280)
        for section in SECTIONS:
            item = QListWidgetItem(tr(f'persona.section.{section.key}.title', section.title))
            item.setData(Qt.UserRole, section.key)
            self.sections.addItem(item)
        nav_layout.addWidget(self.sections, 1)
        body.addWidget(nav_host, 0)

        detail = QVBoxLayout(); detail.setSpacing(8)
        self.section_title = QLabel(); self.section_title.setObjectName('sectionTitle')
        self.section_help = QLabel(); self.section_help.setObjectName('muted'); self.section_help.setWordWrap(True)
        self.edit = QTextEdit(); self.edit.setAcceptRichText(False)
        self.edit.setPlaceholderText(tr('persona.placeholder', 'Beschrijf hier wat voor jouw schrijfstijl belangrijk is…'))
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
        self.reload(force=True)

    def _section_for_key(self, key: str):
        return next(section for section in SECTIONS if section.key == key)

    def _store_editor(self):
        if self._current_key is not None:
            self.profile[self._current_key] = self.edit.toPlainText()

    def _section_changed(self, item, _previous=None):
        if item is None or self._corrupt_source:
            return
        if not self._loading:
            self._store_editor()
        key = item.data(Qt.UserRole)
        section = self._section_for_key(key)
        self._current_key = key
        self._loading = True
        try:
            self.section_title.setText(tr(f'persona.section.{section.key}.title', section.title))
            self.section_help.setText(tr(f'persona.section.{section.key}.help', section.help))
            self.edit.setPlainText(self.profile.get(key, ''))
        finally:
            self._loading = False

    def _edited(self):
        if self._loading:
            return
        self._store_editor()
        self._set_dirty(True)

    def _set_dirty(self, dirty: bool):
        self.dirty = dirty
        self.save_button.setEnabled(dirty)
        self.status.setText(
            tr('persona.unsaved', 'Niet-opgeslagen wijzigingen') if dirty
            else ''
        )

    def reload(self, *, force: bool = False):
        if self.dirty and not force:
            return
        self._loading = True
        try:
            try:
                self.profile = parse_persona(self.library.read_persona())
            except UnicodeDecodeError:
                self._corrupt_source = True
                self._loaded_revision = self.library.capture_persona_revision()
                self.profile = empty_profile()
                self.sections.setEnabled(False)
                self.example_button.setEnabled(False)
                self.edit.setReadOnly(True)
                self.edit.setPlainText(tr(
                    'persona.corrupt_readonly',
                    'schrijver.md is beschadigd en kan niet als UTF-8 worden gelezen. Het bestand wordt niet overschreven.\n\nHerstel of vervang schrijver.md buiten QuietWriter. Lokale herstelkopieën staan in archive/persona/.'
                ))
                self.save_button.setEnabled(False)
                self.status.setText(tr('corrupt_text.status', 'Beschadigd · alleen-lezen'))
                self.dirty = False
                return
            self._corrupt_source = False
            self.sections.setEnabled(True)
            self.example_button.setEnabled(True)
            self.edit.setReadOnly(False)
            self._loaded_revision = self.library.capture_persona_revision()
            row = self.sections.currentRow()
            if row < 0:
                row = 0
            self.sections.setCurrentRow(row)
            item = self.sections.item(row)
            if item is not None:
                key = item.data(Qt.UserRole)
                section = self._section_for_key(key)
                self._current_key = key
                self.section_title.setText(tr(f'persona.section.{section.key}.title', section.title))
                self.section_help.setText(tr(f'persona.section.{section.key}.help', section.help))
                self.edit.setPlainText(self.profile.get(key, ''))
        finally:
            self._loading = False
        self._set_dirty(False)

    def choose_example(self):
        dialog = ExamplePersonaDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        key = dialog.selected_key()
        if not key:
            return
        template = EXAMPLE_PERSONAS[key]
        if not confirm(
            self,
            tr('persona.examples.confirm_title', 'Voorbeeldpersona laden'),
            tr(
                'persona.examples.confirm',
                'Je huidige velden worden vervangen door het voorbeeld “{name}”. Er wordt pas naar schrijver.md geschreven wanneer je op Opslaan klikt.'
            ).format(name=template['name'])
        ):
            return
        self.profile = deepcopy(template['values'])
        self._loading = True
        try:
            item = self.sections.currentItem()
            if item is None:
                self.sections.setCurrentRow(0)
                item = self.sections.currentItem()
            if item is not None:
                key = item.data(Qt.UserRole)
                self._current_key = key
                self.edit.setPlainText(self.profile.get(key, ''))
        finally:
            self._loading = False
        self._set_dirty(True)

    def save(self):
        if self._corrupt_source:
            return True
        self._store_editor()
        local_text = render_persona(self.profile)
        try:
            self._loaded_revision = self.library.save_persona(
                local_text, expected_revision=self._loaded_revision
            )
        except PersonaExternalModificationError:
            return self._resolve_external_change(local_text)
        except CorruptSourceError as exc:
            return self._preserve_local_after_source_problem(local_text, exc)
        except OSError as exc:
            QMessageBox.critical(
                self,
                tr('persona.save_error_title', 'Schrijverspersona'),
                tr('persona.save_error', 'Opslaan mislukt:\n{error}').format(error=exc)
            )
            return False
        self._set_dirty(False)
        return True

    def _resolve_external_change(self, local_text: str) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr('persona.conflict_title', 'Schrijverspersona extern gewijzigd'))
        box.setText(tr('persona.conflict_text', 'Je schrijverspersona is buiten QuietWriter gewijzigd.'))
        box.setInformativeText(tr(
            'persona.conflict_info',
            'QuietWriter heeft niets overschreven. Welke versie wil je gebruiken? Beide keuzes bewaren eerst de versie die anders verloren zou gaan als herstelkopie.'
        ))
        mine = box.addButton(tr('persona.conflict_mine', 'Mijn versie gebruiken'), QMessageBox.AcceptRole)
        disk = box.addButton(tr('persona.conflict_disk', 'Versie op schijf gebruiken'), QMessageBox.DestructiveRole)
        box.setDefaultButton(disk)
        box.exec()
        if box.clickedButton() not in (mine, disk):
            return False

        try:
            current_revision = self.library.capture_persona_revision()

            if box.clickedButton() is mine:
                if current_revision is not None:
                    disk_text = self.library.read_persona()
                    self.library.create_persona_recovery(disk_text, kind='conflict_external')
                self._loaded_revision = self.library.save_persona(
                    local_text, expected_revision=current_revision
                )
                self._set_dirty(False)
                return True

            self.library.create_persona_recovery(local_text, kind='conflict_local')
            if current_revision is None:
                self._loaded_revision = self.library.save_persona(
                    default_persona_markdown(), expected_revision=None
                )
            self.reload(force=True)
            return True
        except PersonaExternalModificationError:
            QMessageBox.warning(
                self,
                tr('persona.conflict_changed_again_title', 'Schrijverspersona opnieuw gewijzigd'),
                tr('persona.conflict_changed_again', 'Het bestand veranderde opnieuw terwijl het conflict werd opgelost. Er is niets overschreven. Probeer opnieuw.')
            )
            return False
        except Exception as exc:
            QMessageBox.critical(
                self,
                tr('persona.conflict_failed_title', 'Conflict niet opgelost'),
                tr('persona.conflict_failed', 'Er is niets bewust overschreven.\n\n{error}').format(error=exc)
            )
            return False


    def _preserve_local_after_source_problem(self, local_text: str, exc: Exception) -> bool:
        """Preserve local persona edits when the live persona cannot be safely replaced."""
        try:
            recovery = self.library.create_persona_recovery(local_text, kind='conflict_local')
        except Exception as recovery_exc:
            QMessageBox.critical(
                self,
                tr('persona.recovery_failed_title', 'Schrijverspersona niet veiliggesteld'),
                tr(
                    'persona.recovery_failed',
                    'schrijver.md kon niet veilig worden opgeslagen en ook de herstelkopie mislukte.\n\n{error}'
                ).format(error=recovery_exc)
            )
            return False

        self._loaded_revision = self.library.capture_persona_revision()
        self._set_dirty(False)
        self.status.setText(tr(
            'persona.recovery_saved_status',
            'Niet opgeslagen in schrijver.md; herstelkopie gemaakt.'
        ))
        QMessageBox.warning(
            self,
            tr('persona.recovery_saved_title', 'Schrijverspersona veiliggesteld'),
            tr(
                'persona.recovery_saved',
                'schrijver.md is beschadigd en is niet overschreven. Je lokale wijzigingen zijn veiliggesteld als herstelkopie:\n{path}\n\n{error}'
            ).format(path=recovery, error=exc)
        )
        return True
