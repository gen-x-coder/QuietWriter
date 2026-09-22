
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSpinBox, QStackedWidget, QVBoxLayout, QWidget
)
from .. import APP_NAME
from ..ai.providers import ProviderFactory
from ..dictionary_catalog import DictionaryCatalog
from ..i18n import tr
from ..themes import THEMES, stylesheet
from ..typography import WritingTypography, available_families, typography_from_values
from .dialogs import confirm

class SettingsPage(QWidget):
    DICTIONARY_DOWNLOAD_URL = 'https://extensions.openoffice.org/'

    def __init__(self, settings: QSettings, parent=None, models=None):
        super().__init__(parent)
        self.settings = settings
        self.original_theme = settings.value('theme', 'Helder')
        self._preview_theme = str(self.original_theme or 'Helder')
        self.original_typography = WritingTypography.from_settings(settings)
        self.original_editor_font = self.original_typography.family
        self.original_editor_size = self.original_typography.point_size
        self.available_models = list(models or [])
        self._settings_nav_buttons = []

        root = QVBoxLayout(self)
        root.setContentsMargins(34, 28, 34, 26)
        root.setSpacing(16)
        page_title = QLabel(tr('settings.title', 'Instellingen'))
        page_title.setObjectName('title')
        root.addWidget(page_title)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(24)
        root.addLayout(body, 1)

        nav = QFrame()
        nav.setObjectName('settingsSidebar')
        nav.setFixedWidth(190)
        nav_lay = QVBoxLayout(nav)
        nav_lay.setContentsMargins(0, 0, 0, 0)
        nav_lay.setSpacing(4)
        body.addWidget(nav)

        self.pages = QStackedWidget()
        self.pages.setObjectName('settingsPages')
        body.addWidget(self.pages, 1)

        # Algemeen
        general, gl = self._make_settings_page(
            tr('settings.general', 'Algemeen'),
            'Basisgedrag van QuietWriter.'
        )
        self.language = QComboBox(); self.language.addItem('Nederlands', 'nl')
        self.autosave = QCheckBox('Automatisch opslaan'); self.autosave.setChecked(settings.value('autosave', True, bool))
        self._add_settings_field(gl, 'Programmataal', self.language)
        gl.addWidget(self.autosave)
        gl.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.general', 'Algemeen'), general)

        # Uiterlijk
        appearance, al = self._make_settings_page(
            tr('settings.appearance', 'Uiterlijk'),
            'Pas het thema en de schrijftypografie aan. Alleen het lettertype verandert wanneer je een ander font kiest; grootte en overige instellingen blijven onafhankelijk.'
        )
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(settings.value('theme', 'Helder'))
        self.editor_font = QComboBox(); self.editor_font.addItems(available_families()); self.editor_font.setCurrentText(self.original_typography.family)
        self.editor_font_size = QSpinBox(); self.editor_font_size.setRange(11, 24); self.editor_font_size.setSuffix(' pt'); self.editor_font_size.setValue(self.original_typography.point_size)
        self._add_settings_field(al, 'Kleurenschema', self.theme)
        self._add_settings_field(al, 'Schrijflettertype', self.editor_font)
        self._add_settings_field(al, 'Tekstgrootte', self.editor_font_size,
            'Lettertype en tekstgrootte zijn onafhankelijke instellingen. QuietWriter toont alle op deze computer beschikbare lettertypen. Wijzigingen worden direct in de editor getoond; Annuleren herstelt de vorige instellingen.')
        al.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.appearance', 'Uiterlijk'), appearance)

        # Opslag
        storage, slay = self._make_settings_page(
            tr('settings.storage', 'Opslag'),
            'Bepaal waar QuietWriter zijn boeken en ondersteunende bestanden bewaart.'
        )
        self.root = QLineEdit(settings.value('workspace', str(Path.home() / 'QuietWriter')))
        choose = QPushButton('Map kiezen…'); choose.clicked.connect(self.choose_root)
        box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0,0,0,0); h.setSpacing(8); h.addWidget(self.root, 1); h.addWidget(choose)
        self._add_settings_field(slay, 'Werkmap', box)
        self.sync_warning = QLabel('')
        self.sync_warning.setObjectName('syncWarning'); self.sync_warning.setWordWrap(True)
        slay.addWidget(self.sync_warning)
        self.root.textChanged.connect(self.update_sync_warning)
        self.cover_template = QLineEdit(settings.value('cover_header_template', '/{slug}.jpg')); self.cover_template.setPlaceholderText('/{slug}.jpg')
        self._add_settings_field(slay, 'Afbeeldingspad in metadata', self.cover_template,
            'Gebruik {slug}, bijvoorbeeld /{slug}.jpg of /images/{slug}.jpg. QuietWriter bewaart alleen het relatieve pad en kent geen websiteadres.')
        slay.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.storage', 'Opslag'), storage)

        # AI
        ai, ail = self._make_settings_page(
            tr('settings.ai', 'AI'),
            'Kies de provider en het schrijfmodel. De schrijfworkflow blijft hetzelfde ongeacht de provider.'
        )
        self.ai_provider = QComboBox(); self.ai_provider.addItem('Ollama (lokaal)', 'ollama'); self.ai_provider.addItem('OpenRouter', 'openrouter')
        provider_value = str(settings.value('ai_provider', 'ollama') or 'ollama')
        idx = self.ai_provider.findData(provider_value); self.ai_provider.setCurrentIndex(max(0, idx))
        self.ollama = QLineEdit(settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.openrouter_key = QLineEdit(settings.value('openrouter_api_key', '')); self.openrouter_key.setEchoMode(QLineEdit.Password); self.openrouter_key.setPlaceholderText('API-key')
        self.model = QComboBox(); self.model.setEditable(True)
        refresh = QPushButton('Modellen ophalen'); refresh.clicked.connect(self.refresh_models)
        modelbox = QWidget(); mh = QHBoxLayout(modelbox); mh.setContentsMargins(0,0,0,0); mh.setSpacing(8); mh.addWidget(self.model, 1); mh.addWidget(refresh)
        self._add_settings_field(ail, 'AI-provider', self.ai_provider)
        self._add_settings_field(ail, 'Ollama-adres', self.ollama)
        self._add_settings_field(ail, 'OpenRouter API-key', self.openrouter_key)
        self._add_settings_field(ail, 'Schrijf- en analysemodel', modelbox,
            'QuietWriter gebruikt je schrijverspersona en de gekozen context: selectie, huidig hoofdstuk, huidige sectie of hele boek.')
        ail.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.ai', 'AI'), ai)

        # Spelling
        spelling, spl = self._make_settings_page(
            tr('settings.spelling', 'Spelling'),
            'Beheer de spellingscontrole en de gevonden Hunspell-woordenboeken.'
        )
        self.spell_enabled = QCheckBox('Spellingscontrole inschakelen'); self.spell_enabled.setChecked(settings.value('spell_enabled', True, bool))
        spl.addWidget(self.spell_enabled)
        explanation = QLabel(
            'QuietWriter zoekt automatisch naar Hunspell-woordenboeken in de werkmap en in geïnstalleerde versies van ONLYOFFICE, LibreOffice en OpenOffice. '
            'Alle gevonden talen verschijnen hieronder. Heb je geen van deze programma’s, dan kun je zelf een .dic/.aff-woordenboek toevoegen of via de downloadknop naar een algemene woordenboeksite gaan.'
        )
        explanation.setObjectName('muted'); explanation.setWordWrap(True); explanation.setMaximumWidth(720); spl.addWidget(explanation)
        self.dictionary_catalog = DictionaryCatalog(Path(settings.value('workspace', str(Path.home() / 'QuietWriter'))) / 'dictionaries')
        self.spell_language = QComboBox(); self.spell_language.currentIndexChanged.connect(self.update_dictionary_info)
        self._add_settings_field(spl, 'Taal', self.spell_language)
        self.dictionary_info = QLabel(''); self.dictionary_info.setObjectName('muted'); self.dictionary_info.setWordWrap(True); self.dictionary_info.setMaximumWidth(720); spl.addWidget(self.dictionary_info)
        actions = QVBoxLayout(); actions.setSpacing(8)
        self.scan_dict_btn = QPushButton('Opnieuw zoeken'); self.scan_dict_btn.clicked.connect(self.refresh_dictionaries)
        self.add_dict_btn = QPushButton('Woordenboek toevoegen…'); self.add_dict_btn.clicked.connect(self.choose_dictionary)
        self.remove_dict_btn = QPushButton('Eigen woordenboek verwijderen'); self.remove_dict_btn.clicked.connect(self.remove_dictionary)
        self.download_dict_btn = QPushButton('Woordenboeken downloaden'); self.download_dict_btn.clicked.connect(self.open_dictionary_download)
        for btn in (self.scan_dict_btn, self.add_dict_btn, self.remove_dict_btn, self.download_dict_btn):
            btn.setMaximumWidth(300); actions.addWidget(btn)
        spl.addLayout(actions)
        spl.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.spelling', 'Spelling'), spelling)
        nav_lay.addStretch(1)

        self._populate_models(self.available_models)
        self.update_sync_warning()
        self.refresh_dictionaries(preserve_locale=str(settings.value('spell_language', 'nl_NL') or 'nl_NL'))

        buttons = QHBoxLayout(); buttons.addStretch()
        cancel_btn = QPushButton(tr('common.cancel', 'Annuleren')); cancel_btn.setObjectName('secondaryButton'); cancel_btn.clicked.connect(self.cancel)
        save_btn = QPushButton(tr('common.save', 'Opslaan')); save_btn.setObjectName('primaryButton'); save_btn.clicked.connect(self.save_settings)
        buttons.addWidget(cancel_btn); buttons.addWidget(save_btn); root.addLayout(buttons)
        self.theme.currentTextChanged.connect(self._preview_appearance)
        self.editor_font.currentTextChanged.connect(self._preview_appearance)
        self.editor_font_size.valueChanged.connect(self._preview_appearance)
        self._switch_settings_page(0)

    def _make_settings_page(self, title: str, intro: str):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(14)
        heading = QLabel(title); heading.setObjectName('settingsPageTitle'); layout.addWidget(heading)
        if intro:
            note = QLabel(intro); note.setObjectName('muted'); note.setWordWrap(True); note.setMaximumWidth(720); layout.addWidget(note)
        layout.addSpacing(6)
        return page, layout

    def _add_settings_field(self, layout: QVBoxLayout, label_text: str, widget: QWidget, note: str | None = None):
        label = QLabel(label_text); label.setObjectName('settingsFieldLabel')
        layout.addWidget(label, 0, Qt.AlignLeft)
        widget.setMaximumWidth(720)
        if isinstance(widget, QSpinBox):
            widget.setMinimumWidth(170)
        elif not isinstance(widget, QCheckBox):
            widget.setMinimumWidth(420)
        layout.addWidget(widget, 0, Qt.AlignLeft)
        if note:
            info = QLabel(note); info.setObjectName('muted'); info.setWordWrap(True); info.setMaximumWidth(720)
            layout.addWidget(info, 0, Qt.AlignLeft)
        layout.addSpacing(4)

    def _add_settings_category(self, nav_layout: QVBoxLayout, text: str, page: QWidget):
        index = self.pages.count()
        self.pages.addWidget(page)
        button = QPushButton(text)
        button.setObjectName('settingsNavButton')
        button.setCheckable(True)
        button.clicked.connect(lambda checked=False, i=index: self._switch_settings_page(i))
        nav_layout.addWidget(button)
        self._settings_nav_buttons.append(button)

    def _switch_settings_page(self, index: int):
        if index < 0 or index >= self.pages.count():
            return
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self._settings_nav_buttons):
            button.blockSignals(True)
            button.setChecked(i == index)
            button.blockSignals(False)

    def _preview_appearance(self, *_):
        theme = self.theme.currentText() or 'Helder'
        font = self.editor_font.currentText() or 'Merriweather'
        size = int(self.editor_font_size.value())
        # Re-polishing the complete QApplication for every font-family change is
        # unnecessary and on some Windows/Qt builds triggers
        # QFont::setPointSize(-1). Only a theme change needs a global QSS pass.
        if theme != self._preview_theme:
            win = self.parent()
            if win and hasattr(win, 'apply_theme'):
                win.apply_theme(theme)
            else:
                QApplication.instance().setStyleSheet(stylesheet(theme))
            self._preview_theme = theme
        win = self.parent()
        if win and hasattr(win, 'apply_writing_font'):
            win.apply_writing_font(font, size)

    def restore_preview(self):
        if self._preview_theme != str(self.original_theme or 'Helder'):
            win = self.parent()
            if win and hasattr(win, 'apply_theme'):
                win.apply_theme(str(self.original_theme or 'Helder'))
            else:
                QApplication.instance().setStyleSheet(stylesheet(self.original_theme))
            self._preview_theme = str(self.original_theme or 'Helder')
        win = self.parent()
        if win and hasattr(win, 'apply_writing_font'):
            win.apply_writing_font(self.original_editor_font, self.original_editor_size)

    def cancel(self):
        self.restore_preview()
        if self.parent() and hasattr(self.parent(), 'return_from_settings'):
            self.parent().return_from_settings()

    def update_sync_warning(self):
        path = self.root.text().strip()
        provider = None
        lowered = path.casefold().replace('\\', '/')
        checks = [
            ('Dropbox', 'dropbox'),
            ('OneDrive', 'onedrive'),
            ('Google Drive', 'google drive'),
            ('Google Drive', 'googledrive'),
            ('iCloud Drive', 'icloud'),
        ]
        for label, token in checks:
            if token in lowered:
                provider = label
                break
        if provider:
            self.sync_warning.setText(
                f'Let op: deze werkmap lijkt in {provider} te staan. Gesynchroniseerde mappen kunnen bestanden heel kort vergrendelen tijdens synchronisatie. '
                'QuietWriter vangt dit zo veel mogelijk op, maar sluit bij onverwachte opslagfouten eerst andere programma’s die dezelfde bestanden gebruiken.'
            )
            self.sync_warning.show()
        else:
            self.sync_warning.clear(); self.sync_warning.hide()

    def choose_root(self):
        p = QFileDialog.getExistingDirectory(self, 'Kies werkmap', self.root.text())
        if p:
            self.root.setText(p)

    def _dictionary_workspace(self) -> Path:
        return Path(self.root.text().strip() or str(Path.home() / 'QuietWriter')) / 'dictionaries'

    def refresh_dictionaries(self, checked=False, preserve_locale=None):
        current = preserve_locale or self.spell_language.currentData() or str(self.settings.value('spell_language', 'nl_NL') or 'nl_NL')
        self.dictionary_catalog = DictionaryCatalog(self._dictionary_workspace())
        self.spell_language.blockSignals(True)
        self.spell_language.clear()
        entries = self.dictionary_catalog.entries()
        for entry in entries:
            self.spell_language.addItem(entry.label, entry.locale)
        idx = self.spell_language.findData(current)
        if idx >= 0:
            self.spell_language.setCurrentIndex(idx)
        elif entries:
            self.spell_language.setCurrentIndex(0)
        self.spell_language.blockSignals(False)
        self.update_dictionary_info()

    def update_dictionary_info(self):
        locale = self.spell_language.currentData()
        entry = self.dictionary_catalog.get(locale) if locale else None
        if not entry:
            self.dictionary_info.setText('Geen woordenboeken gevonden. Installeer bijvoorbeeld ONLYOFFICE, LibreOffice of OpenOffice, of voeg zelf een Hunspell-woordenboek toe.')
            self.remove_dict_btn.setEnabled(False)
            return
        aff = 'met .aff-regels' if entry.aff else 'alleen .dic'
        self.dictionary_info.setText(f'Bron: {entry.source} · {entry.locale} · {aff}\n{entry.dic}')
        self.remove_dict_btn.setEnabled(entry.source == 'Werkmap')

    def choose_dictionary(self):
        p, _ = QFileDialog.getOpenFileName(self, 'Kies Hunspell-woordenboek', str(Path.home()), 'Hunspell woordenboek (*.dic);;Alle bestanden (*)')
        if not p:
            return
        self.dictionary_catalog = DictionaryCatalog(self._dictionary_workspace())
        entry = self.dictionary_catalog.add_custom(Path(p))
        self.refresh_dictionaries(preserve_locale=entry.locale)

    def remove_dictionary(self):
        locale = self.spell_language.currentData()
        entry = self.dictionary_catalog.get(locale) if locale else None
        if not entry or entry.source != 'Werkmap':
            QMessageBox.information(self, 'Woordenboek verwijderen', 'Alleen woordenboeken die je zelf aan QuietWriter hebt toegevoegd kunnen hier worden verwijderd. Woordenboeken van Office-programma’s blijven onaangeroerd.')
            return
        if not confirm(self, 'Woordenboek verwijderen', f'Wil je “{entry.label}” uit de QuietWriter-werkmap verwijderen?'):
            return
        if not self.dictionary_catalog.remove_custom(locale):
            QMessageBox.warning(self, 'Woordenboek verwijderen', 'Het woordenboek kon niet worden verwijderd.')
        self.refresh_dictionaries()

    def open_dictionary_download(self):
        QDesktopServices.openUrl(QUrl(self.DICTIONARY_DOWNLOAD_URL))

    def _populate_models(self, models):
        provider_name = str(self.settings.value('ai_provider', 'ollama') or 'ollama')
        current = self.settings.value('ollama_model', '') if provider_name == 'ollama' else self.settings.value('openrouter_model', '')
        self.model.clear()
        if provider_name == 'ollama':
            self.model.addItems(list(models or []))
        elif current:
            self.model.addItem(str(current))
        if current:
            self.model.setCurrentText(str(current))
        elif self.model.count():
            self.model.setCurrentIndex(0)

    def refresh_models(self):
        self.settings.setValue('ai_provider', self.ai_provider.currentData() or 'ollama')
        self.settings.setValue('ollama_url', self.ollama.text())
        self.settings.setValue('openrouter_api_key', self.openrouter_key.text())
        try:
            provider = ProviderFactory.from_settings(self.settings)
            infos = provider.list_models()
            models = [m['name'] for m in infos]
            current = self.model.currentText()
            self.model.clear(); self.model.addItems(models)
            if current in models:
                self.model.setCurrentText(current)
            elif models:
                self.model.setCurrentIndex(0)
            if self.parent() and hasattr(self.parent(), 'models'):
                self.parent().models = models
        except Exception as exc:
            QMessageBox.warning(self, 'AI', f'Modellen ophalen mislukt:\n\n{exc}')

    def save_settings(self):
        old_root = self.settings.value('workspace', str(Path.home()/APP_NAME))
        self.settings.setValue('theme', self.theme.currentText())
        self.settings.setValue('editor_font', typography_from_values(self.editor_font.currentText(), self.editor_font_size.value()).family)
        self.settings.setValue('editor_font_size', int(self.editor_font_size.value()))
        self.settings.setValue('autosave', self.autosave.isChecked())
        self.settings.setValue('workspace', self.root.text())
        provider = self.ai_provider.currentData() or 'ollama'
        self.settings.setValue('ai_provider', provider)
        self.settings.setValue('ollama_url', self.ollama.text())
        self.settings.setValue('openrouter_api_key', self.openrouter_key.text())
        if provider == 'openrouter': self.settings.setValue('openrouter_model', self.model.currentText())
        else: self.settings.setValue('ollama_model', self.model.currentText())
        self.settings.setValue('cover_header_template', self.cover_template.text().strip() or '/{slug}.jpg')
        self.settings.setValue('spell_enabled', self.spell_enabled.isChecked())
        self.settings.setValue('spell_language', self.spell_language.currentData() or '')
        self.original_theme = self.theme.currentText()
        self.original_editor_font = self.editor_font.currentText()
        self.original_editor_size = int(self.editor_font_size.value())
        self._preview_theme = self.original_theme
        if self.parent() and hasattr(self.parent(), 'settings_saved'):
            self.parent().settings_saved(old_root)

    def begin_session(self):
        self.original_theme = self.settings.value('theme', 'Helder')
        self.original_editor_font = str(self.settings.value('editor_font', 'Merriweather') or 'Merriweather')
        self.original_editor_size = int(self.settings.value('editor_font_size', 15, int) or 15)
        self._preview_theme = str(self.original_theme or 'Helder')
        for widget in (self.theme, self.editor_font, self.editor_font_size): widget.blockSignals(True)
        self.theme.setCurrentText(str(self.original_theme or 'Helder'))
        self.editor_font.setCurrentText(self.original_editor_font)
        self.editor_font_size.setValue(self.original_editor_size)
        for widget in (self.theme, self.editor_font, self.editor_font_size): widget.blockSignals(False)
        self.autosave.setChecked(self.settings.value('autosave', True, bool))
        self.root.setText(self.settings.value('workspace', str(Path.home()/APP_NAME)))
        self.cover_template.setText(self.settings.value('cover_header_template', '/{slug}.jpg'))
        provider = str(self.settings.value('ai_provider', 'ollama') or 'ollama')
        idx = self.ai_provider.findData(provider); self.ai_provider.setCurrentIndex(max(0, idx))
        self.ollama.setText(self.settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.openrouter_key.setText(self.settings.value('openrouter_api_key', ''))
        self._populate_models(self.available_models)
        self.spell_enabled.setChecked(self.settings.value('spell_enabled', True, bool))
        self.refresh_dictionaries(preserve_locale=str(self.settings.value('spell_language', 'nl_NL') or 'nl_NL'))
        self.update_sync_warning()
