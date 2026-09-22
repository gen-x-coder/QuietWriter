
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox, QSizePolicy, QVBoxLayout, QWidget
)
from .current_page_stack import CurrentPageStack
from .. import APP_NAME
from ..ai.providers import ProviderFactory
from ..dictionary_catalog import DictionaryCatalog
from ..i18n import tr
from ..themes import THEMES, stylesheet
from ..typography import WritingTypography, available_families, typography_from_values
from ..font_catalog import recommended_families, system_families_excluding_recommended
from ..manuscript_markup import ManuscriptStyle
from .dialogs import confirm
from .about_page import AboutPage

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
        self.original_manuscript_style = ManuscriptStyle.from_settings(settings)
        self.available_models = list(models or [])
        self._settings_nav_buttons = []
        self._saved_form_state = None

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

        self.pages = CurrentPageStack()
        self.pages.setObjectName('settingsPages')
        body.addWidget(self.pages, 1)

        # Algemeen
        general, gl = self._make_settings_page(
            tr('settings.general', 'Algemeen'),
            'Basisgedrag van QuietWriter.'
        )
        self._add_settings_section(gl, 'Programma')
        self.language = QComboBox(); self.language.addItem('Nederlands', 'nl')
        self._add_settings_field(gl, 'Programmataal', self.language,
            'De interface is momenteel Nederlandstalig. De opzet is voorbereid op extra talen.')
        self._add_settings_section(gl, 'Opslaan')
        self.autosave = QCheckBox('Automatisch opslaan'); self.autosave.setChecked(settings.value('autosave', True, bool))
        self._add_settings_field(gl, 'Automatisch opslaan', self.autosave,
            'Slaat wijzigingen ongeveer drie seconden na je laatste toetsaanslag automatisch op. Staat dit uit, dan gebruik je Ctrl+S om handmatig op te slaan.')
        gl.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.general', 'Algemeen'), general)

        # Uiterlijk
        appearance, al = self._make_settings_page(
            tr('settings.appearance', 'Uiterlijk'),
            'Pas het thema en de schrijftypografie aan. Voorbeelden worden direct toegepast; Opslaan maakt de keuze blijvend.'
        )
        self._add_settings_section(al, 'Weergave')
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(settings.value('theme', 'Helder'))
        self._add_settings_field(al, 'Kleurenschema', self.theme,
            'Past de volledige interface direct als voorbeeld aan.')

        self._add_settings_section(al, 'Schrijftypografie')
        self.editor_font = QComboBox(); self._populate_font_combo(self.original_typography.family)
        self.font_preview = QLabel('De eerste zin van een nieuw verhaal begint vaak met één enkel idee.')
        self.font_preview.setObjectName('fontPreview'); self.font_preview.setWordWrap(True)
        font_control = QWidget()
        font_control.setObjectName('settingsInlineControl')
        fh = QHBoxLayout(font_control); fh.setContentsMargins(0, 0, 0, 0); fh.setSpacing(12)
        self.editor_font.setMinimumWidth(210); self.editor_font.setMaximumWidth(280)
        self.font_preview.setMinimumWidth(240); self.font_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        fh.addWidget(self.editor_font, 0); fh.addWidget(self.font_preview, 1)
        self._add_settings_field(al, 'Schrijflettertype', font_control,
            'Aanbevolen lettertypen worden door QuietWriter zelf geladen. Daaronder blijven alle beschikbare systeemlettertypen zichtbaar.')

        self.editor_font_size = QSpinBox(); self.editor_font_size.setRange(11, 24); self.editor_font_size.setSuffix(' pt'); self.editor_font_size.setValue(self.original_typography.point_size)
        self._add_settings_field(al, 'Tekstgrootte', self.editor_font_size)

        self._add_settings_section(al, 'Manuscript')
        self.manuscript_line_spacing = QSpinBox(); self.manuscript_line_spacing.setRange(120, 200); self.manuscript_line_spacing.setSuffix(' %'); self.manuscript_line_spacing.setValue(int(settings.value('manuscript_line_spacing', 155, int) or 155))
        self.manuscript_indent = QSpinBox(); self.manuscript_indent.setRange(0, 60); self.manuscript_indent.setSuffix(' px'); self.manuscript_indent.setValue(int(settings.value('manuscript_indent', 28, int) or 28))
        self.manuscript_paragraph_spacing = QSpinBox(); self.manuscript_paragraph_spacing.setRange(0, 24); self.manuscript_paragraph_spacing.setSuffix(' px'); self.manuscript_paragraph_spacing.setValue(int(settings.value('manuscript_paragraph_spacing', 8, int) or 8))
        self.smart_quotes = QCheckBox('Slimme aanhalingstekens'); self.smart_quotes.setChecked(settings.value('smart_quotes', True, bool))
        self._add_settings_field(al, 'Regelafstand', self.manuscript_line_spacing,
            'Bepaalt de verticale ruimte tussen regels in de schrijfeditor.')
        self._add_settings_field(al, 'Alinea-inspringing', self.manuscript_indent,
            'Vervolgalinea’s springen in. De eerste alinea van een hoofdstuk, na een lege regel, tussenkop of scènebreuk begint links.')
        self._add_settings_field(al, 'Ruimte na alinea', self.manuscript_paragraph_spacing,
            'Voegt subtiele extra ruimte tussen opeenvolgende alinea’s toe.')
        self._add_settings_field(al, 'Slimme aanhalingstekens', self.smart_quotes,
            'Zet een tijdens het typen ingevoerd recht dubbel aanhalingsteken om naar een typografisch openings- of sluitteken.')
        al.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.appearance', 'Uiterlijk'), appearance)

        # Opslag
        storage, slay = self._make_settings_page(
            tr('settings.storage', 'Opslag'),
            'Bepaal waar QuietWriter zijn boeken en ondersteunende bestanden bewaart.'
        )
        self._add_settings_section(slay, 'Werkmap')
        self.root = QLineEdit(settings.value('workspace', str(Path.home() / 'QuietWriter')))
        choose = QPushButton('Map kiezen…'); choose.clicked.connect(self.choose_root)
        box = QWidget(); h = QHBoxLayout(box); h.setContentsMargins(0,0,0,0); h.setSpacing(8); h.addWidget(self.root, 1); h.addWidget(choose)
        self._add_settings_field(slay, 'Werkmap', box,
            'Hier staan je boeken, planning, publicatiestructuur en lokale herstelgegevens. Een wijziging wordt na herstart gebruikt.')
        self.sync_warning = QLabel('')
        self.sync_warning.setObjectName('syncWarning'); self.sync_warning.setWordWrap(True)
        self._add_settings_full_width(slay, self.sync_warning)
        self.root.textChanged.connect(self.update_sync_warning)

        self._add_settings_section(slay, 'Metadata')
        self.cover_template = QLineEdit(settings.value('cover_header_template', '/{slug}.jpg')); self.cover_template.setPlaceholderText('/{slug}.jpg')
        self._add_settings_field(slay, 'Afbeeldingspad', self.cover_template,
            'Wordt gebruikt bij Markdown-metadata. Gebruik {slug}, bijvoorbeeld /{slug}.jpg of /images/{slug}.jpg.')
        slay.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.storage', 'Opslag'), storage)

        # AI
        ai, ail = self._make_settings_page(
            tr('settings.ai', 'AI'),
            'Kies de provider en het schrijfmodel. AI blijft een hulpmiddel naast je manuscript en wijzigt tekst nooit zelfstandig.'
        )
        self._add_settings_section(ail, 'Provider')
        self.ai_provider = QComboBox(); self.ai_provider.addItem('Ollama (lokaal)', 'ollama'); self.ai_provider.addItem('OpenRouter', 'openrouter')
        provider_value = str(settings.value('ai_provider', 'ollama') or 'ollama')
        idx = self.ai_provider.findData(provider_value); self.ai_provider.setCurrentIndex(max(0, idx))
        self.ollama = QLineEdit(settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.openrouter_key = QLineEdit(settings.value('openrouter_api_key', '')); self.openrouter_key.setEchoMode(QLineEdit.Password); self.openrouter_key.setPlaceholderText('API-key')
        self._add_settings_field(ail, 'AI-provider', self.ai_provider,
            'Ollama draait lokaal op je computer. OpenRouter gebruikt een externe API-key.')
        self._add_settings_field(ail, 'Ollama-adres', self.ollama,
            'Alleen relevant wanneer Ollama als provider is gekozen.')
        self._add_settings_field(ail, 'OpenRouter API-key', self.openrouter_key,
            'Alleen relevant wanneer OpenRouter als provider is gekozen. De sleutel wordt lokaal in je QuietWriter-instellingen bewaard.')

        self._add_settings_section(ail, 'Model')
        self.model = QComboBox(); self.model.setEditable(True)
        refresh = QPushButton('Modellen ophalen'); refresh.clicked.connect(self.refresh_models)
        modelbox = QWidget(); mh = QHBoxLayout(modelbox); mh.setContentsMargins(0,0,0,0); mh.setSpacing(8); mh.addWidget(self.model, 1); mh.addWidget(refresh)
        self._add_settings_field(ail, 'Schrijf- en analysemodel', modelbox,
            'QuietWriter stuurt alleen de context die je in de AI-zijbalk kiest, samen met je schrijverspersona.')
        ail.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.ai', 'AI'), ai)

        # Spelling
        spelling, spl = self._make_settings_page(
            tr('settings.spelling', 'Spelling'),
            'Beheer de spellingscontrole en de gevonden Hunspell-woordenboeken.'
        )
        self._add_settings_section(spl, 'Controle')
        self.spell_enabled = QCheckBox('Spellingscontrole inschakelen'); self.spell_enabled.setChecked(settings.value('spell_enabled', True, bool))
        self._add_settings_field(spl, 'Spellingscontrole', self.spell_enabled,
            'Onderstreept onbekende woorden in de editor. Je manuscripttekst zelf wordt nooit automatisch aangepast.')
        self.dictionary_catalog = DictionaryCatalog(Path(settings.value('workspace', str(Path.home() / 'QuietWriter'))) / 'dictionaries')
        self.spell_language = QComboBox(); self.spell_language.currentIndexChanged.connect(self.update_dictionary_info)
        self._add_settings_field(spl, 'Taal', self.spell_language,
            'QuietWriter gebruikt een gevonden Hunspell-woordenboek voor deze taal.')

        self._add_settings_section(spl, 'Woordenboeken')
        self.dictionary_info = QLabel(''); self.dictionary_info.setObjectName('muted'); self.dictionary_info.setWordWrap(True)
        self._add_settings_full_width(spl, self.dictionary_info)
        actions_widget = QWidget(); actions = QHBoxLayout(actions_widget); actions.setContentsMargins(0,0,0,0); actions.setSpacing(8)
        self.scan_dict_btn = QPushButton('Opnieuw zoeken'); self.scan_dict_btn.clicked.connect(self.refresh_dictionaries)
        self.add_dict_btn = QPushButton('Toevoegen…'); self.add_dict_btn.clicked.connect(self.choose_dictionary)
        self.remove_dict_btn = QPushButton('Verwijderen'); self.remove_dict_btn.clicked.connect(self.remove_dictionary)
        self.download_dict_btn = QPushButton('Downloadsite'); self.download_dict_btn.clicked.connect(self.open_dictionary_download)
        for btn in (self.scan_dict_btn, self.add_dict_btn, self.remove_dict_btn, self.download_dict_btn):
            actions.addWidget(btn)
        actions.addStretch(1)
        self._add_settings_field(spl, 'Beheer', actions_widget,
            'QuietWriter zoekt in de werkmap en in geïnstalleerde versies van ONLYOFFICE, LibreOffice en OpenOffice. Je kunt ook zelf een .dic/.aff-woordenboek toevoegen.')
        spl.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.spelling', 'Spelling'), spelling)

        # Over staat bewust onderaan de vaste instellingen-navigatie.
        nav_lay.addStretch(1)
        about = AboutPage(self)
        self.about_index = self.pages.count()
        self._add_settings_category(nav_lay, 'Over', about)

        self._populate_models(self.available_models)
        self.update_sync_warning()
        self.refresh_dictionaries(preserve_locale=str(settings.value('spell_language', 'nl_NL') or 'nl_NL'))

        # Eén vaste actie onderaan. De knop is alleen actief wanneer de formuliervelden
        # afwijken van de laatst opgeslagen instellingen.
        buttons = QHBoxLayout(); buttons.addStretch()
        self.save_btn = QPushButton(tr('common.save', 'Opslaan'))
        self.save_btn.setObjectName('primaryButton')
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setEnabled(False)
        buttons.addWidget(self.save_btn)
        root.addLayout(buttons)

        self.save_feedback = QLabel('Opgeslagen', self)
        self.save_feedback.setObjectName('settingsToast')
        self.save_feedback.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.save_feedback.hide()
        self._save_feedback_timer = QTimer(self)
        self._save_feedback_timer.setSingleShot(True)
        self._save_feedback_timer.setInterval(2200)
        self._save_feedback_timer.timeout.connect(self.save_feedback.hide)

        self.theme.currentTextChanged.connect(self._preview_appearance)
        self.editor_font.currentTextChanged.connect(self._preview_appearance)
        self.editor_font.currentTextChanged.connect(self._update_font_preview)
        self.editor_font_size.valueChanged.connect(self._preview_appearance)
        self.editor_font_size.valueChanged.connect(self._update_font_preview)
        self.manuscript_line_spacing.valueChanged.connect(self._preview_appearance)
        self.manuscript_indent.valueChanged.connect(self._preview_appearance)
        self.manuscript_paragraph_spacing.valueChanged.connect(self._preview_appearance)
        self.smart_quotes.toggled.connect(self._preview_appearance)

        self._wire_dirty_tracking()
        self._update_font_preview()
        self._saved_form_state = self._current_form_state()
        self._update_dirty_state()
        self._switch_settings_page(0)

    def _populate_font_combo(self, selected: str | None = None):
        families = available_families()
        recommended = recommended_families(families)
        system = system_families_excluding_recommended(families)
        model = QStandardItemModel(self.editor_font)
        if recommended:
            heading = QStandardItem('Aanbevolen')
            heading.setEnabled(False); heading.setSelectable(False)
            model.appendRow(heading)
            for family in recommended:
                model.appendRow(QStandardItem(family))
            separator = QStandardItem('────────────')
            separator.setEnabled(False); separator.setSelectable(False)
            model.appendRow(separator)
        heading = QStandardItem('Systeemfonts')
        heading.setEnabled(False); heading.setSelectable(False)
        model.appendRow(heading)
        for family in system:
            model.appendRow(QStandardItem(family))
        self.editor_font.setModel(model)
        target = typography_from_values(selected, self.original_editor_size).family
        index = self.editor_font.findText(target)
        if index >= 0:
            self.editor_font.setCurrentIndex(index)
        elif recommended:
            self.editor_font.setCurrentText(recommended[0])

    def _update_font_preview(self, *_):
        if not hasattr(self, 'font_preview'):
            return
        family = self.editor_font.currentText().strip() or self.original_editor_font
        if family in {'Aanbevolen', 'Systeemfonts', '────────────'}:
            return
        font = QFont(family)
        font.setPointSize(max(13, int(self.editor_font_size.value())))
        self.font_preview.setFont(font)

    def _make_settings_page(self, title: str, intro: str):
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea(page)
        scroll.setObjectName('settingsContentScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        content = QWidget()
        content.setObjectName('settingsContent')
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 0, 18, 24)
        layout.setSpacing(0)
        heading = QLabel(title); heading.setObjectName('settingsPageTitle'); layout.addWidget(heading)
        if intro:
            note = QLabel(intro); note.setObjectName('settingsPageIntro'); note.setWordWrap(True); note.setMaximumWidth(820)
            layout.addWidget(note)
        layout.addSpacing(22)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)
        return page, layout

    def _add_settings_section(self, layout: QVBoxLayout, title: str):
        if layout.count() > 0:
            layout.addSpacing(12)
        label = QLabel(title.upper())
        label.setObjectName('settingsSectionTitle')
        layout.addWidget(label, 0, Qt.AlignLeft)
        layout.addSpacing(4)

    def _add_settings_field(self, layout: QVBoxLayout, label_text: str, widget: QWidget, note: str | None = None):
        row = QFrame()
        row.setObjectName('settingsRow')
        row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 10, 0, 10)
        h.setSpacing(28)

        info = QWidget()
        info.setObjectName('settingsRowInfo')
        info.setMinimumWidth(190)
        info.setMaximumWidth(310)
        info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        iv = QVBoxLayout(info)
        iv.setContentsMargins(0, 0, 0, 0)
        iv.setSpacing(4)
        label = QLabel(label_text); label.setObjectName('settingsFieldLabel'); iv.addWidget(label)
        if note:
            detail = QLabel(note); detail.setObjectName('settingsFieldHelp'); detail.setWordWrap(True)
            iv.addWidget(detail)
        iv.addStretch(1)
        h.addWidget(info, 0, Qt.AlignTop)

        control_host = QWidget()
        control_host.setObjectName('settingsRowControl')
        control_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cv = QVBoxLayout(control_host)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        if isinstance(widget, QSpinBox):
            widget.setMinimumWidth(150); widget.setMaximumWidth(190)
        elif isinstance(widget, QComboBox):
            widget.setMinimumWidth(210); widget.setMaximumWidth(360)
        elif isinstance(widget, QLineEdit):
            widget.setMinimumWidth(240); widget.setMaximumWidth(520)
        elif not isinstance(widget, QCheckBox):
            widget.setMaximumWidth(620)
        cv.addWidget(widget, 0, Qt.AlignTop | Qt.AlignLeft)
        cv.addStretch(1)
        h.addWidget(control_host, 1, Qt.AlignTop)
        layout.addWidget(row)

    def _add_settings_full_width(self, layout: QVBoxLayout, widget: QWidget):
        host = QWidget()
        host.setObjectName('settingsFullWidth')
        h = QHBoxLayout(host)
        h.setContentsMargins(0, 4, 0, 8)
        h.setSpacing(0)
        widget.setMaximumWidth(820)
        h.addWidget(widget, 1, Qt.AlignLeft)
        layout.addWidget(host)

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
        if hasattr(self, 'save_btn'):
            self.save_btn.setVisible(index != getattr(self, 'about_index', -1))
            self._update_dirty_state()
        for i, button in enumerate(self._settings_nav_buttons):
            button.blockSignals(True)
            button.setChecked(i == index)
            button.blockSignals(False)

    def _current_form_state(self):
        return (
            self.language.currentData() or 'nl',
            bool(self.autosave.isChecked()),
            self.theme.currentText(),
            self.editor_font.currentText(),
            int(self.editor_font_size.value()),
            int(self.manuscript_line_spacing.value()),
            int(self.manuscript_indent.value()),
            int(self.manuscript_paragraph_spacing.value()),
            bool(self.smart_quotes.isChecked()),
            self.root.text(),
            self.cover_template.text(),
            self.ai_provider.currentData() or 'ollama',
            self.ollama.text(),
            self.openrouter_key.text(),
            self.model.currentText(),
            bool(self.spell_enabled.isChecked()),
            self.spell_language.currentData() or '',
        )

    def _wire_dirty_tracking(self):
        widgets = (
            self.language, self.autosave, self.theme, self.editor_font,
            self.editor_font_size, self.manuscript_line_spacing,
            self.manuscript_indent, self.manuscript_paragraph_spacing,
            self.smart_quotes, self.root, self.cover_template,
            self.ai_provider, self.ollama, self.openrouter_key, self.model,
            self.spell_enabled, self.spell_language,
        )
        for widget in widgets:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self._update_dirty_state)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self._update_dirty_state)
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(self._update_dirty_state)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self._update_dirty_state)

    def _update_dirty_state(self, *_):
        if not hasattr(self, 'save_btn'):
            return
        dirty = self._saved_form_state is not None and self._current_form_state() != self._saved_form_state
        visible_for_page = self.pages.currentIndex() != getattr(self, 'about_index', -1)
        self.save_btn.setEnabled(bool(dirty and visible_for_page))

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
        if win and hasattr(win, 'apply_manuscript_style'):
            win.apply_manuscript_style(ManuscriptStyle.from_values(
                self.manuscript_line_spacing.value(), self.manuscript_indent.value(),
                self.manuscript_paragraph_spacing.value(), self.smart_quotes.isChecked()))

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
        if win and hasattr(win, 'apply_manuscript_style'):
            win.apply_manuscript_style(self.original_manuscript_style)

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
        # Model discovery must not silently persist unsaved form values. Settings
        # remain transactional: only Opslaan writes them to QSettings.
        values = {
            'ai_provider': self.ai_provider.currentData() or 'ollama',
            'ollama_url': self.ollama.text(),
            'openrouter_api_key': self.openrouter_key.text(),
            'openrouter_url': self.settings.value('openrouter_url', 'https://openrouter.ai/api/v1'),
        }

        class FormSettings:
            def value(self, key, default=None):
                return values.get(key, default)

        try:
            provider = ProviderFactory.from_settings(FormSettings())
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_save_feedback()

    def _position_save_feedback(self):
        if not hasattr(self, 'save_feedback'):
            return
        self.save_feedback.adjustSize()
        margin = 24
        x = max(margin, self.width() - self.save_feedback.width() - margin)
        y = margin
        self.save_feedback.move(x, y)

    def _show_saved_feedback(self):
        self.save_feedback.setText('Opgeslagen')
        self.save_feedback.adjustSize()
        self._position_save_feedback()
        self.save_feedback.show()
        self.save_feedback.raise_()
        self._save_feedback_timer.start()

    def save_settings(self):
        old_root = self.settings.value('workspace', str(Path.home()/APP_NAME))
        self.settings.setValue('theme', self.theme.currentText())
        self.settings.setValue('editor_font', typography_from_values(self.editor_font.currentText(), self.editor_font_size.value()).family)
        self.settings.setValue('editor_font_size', int(self.editor_font_size.value()))
        self.settings.setValue('manuscript_line_spacing', int(self.manuscript_line_spacing.value()))
        self.settings.setValue('manuscript_indent', int(self.manuscript_indent.value()))
        self.settings.setValue('manuscript_paragraph_spacing', int(self.manuscript_paragraph_spacing.value()))
        self.settings.setValue('smart_quotes', self.smart_quotes.isChecked())
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
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            QMessageBox.warning(self, 'Instellingen opslaan', 'De instellingen konden niet betrouwbaar naar schijf worden geschreven. Controleer de toegangsrechten en probeer het opnieuw.')
            return
        self.original_theme = self.theme.currentText()
        self.original_editor_font = self.editor_font.currentText()
        self.original_editor_size = int(self.editor_font_size.value())
        self.original_manuscript_style = ManuscriptStyle.from_values(self.manuscript_line_spacing.value(), self.manuscript_indent.value(), self.manuscript_paragraph_spacing.value(), self.smart_quotes.isChecked())
        self._preview_theme = self.original_theme
        if self.parent() and hasattr(self.parent(), 'settings_saved'):
            self.parent().settings_saved(old_root)
        self._saved_form_state = self._current_form_state()
        self._update_dirty_state()
        self._show_saved_feedback()

    def begin_session(self):
        self.original_theme = self.settings.value('theme', 'Helder')
        self.original_typography = WritingTypography.from_settings(self.settings)
        self.original_editor_font = self.original_typography.family
        self.original_editor_size = self.original_typography.point_size
        self.original_manuscript_style = ManuscriptStyle.from_settings(self.settings)
        self._preview_theme = str(self.original_theme or 'Helder')
        for widget in (self.theme, self.editor_font, self.editor_font_size, self.manuscript_line_spacing, self.manuscript_indent, self.manuscript_paragraph_spacing, self.smart_quotes): widget.blockSignals(True)
        self.theme.setCurrentText(str(self.original_theme or 'Helder'))
        self.editor_font.setCurrentText(self.original_editor_font)
        self.editor_font_size.setValue(self.original_editor_size)
        self.manuscript_line_spacing.setValue(self.original_manuscript_style.line_spacing_percent)
        self.manuscript_indent.setValue(self.original_manuscript_style.paragraph_indent_px)
        self.manuscript_paragraph_spacing.setValue(self.original_manuscript_style.paragraph_spacing_px)
        self.smart_quotes.setChecked(self.original_manuscript_style.smart_quotes)
        for widget in (self.theme, self.editor_font, self.editor_font_size, self.manuscript_line_spacing, self.manuscript_indent, self.manuscript_paragraph_spacing, self.smart_quotes): widget.blockSignals(False)
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
        self._saved_form_state = self._current_form_state()
        self._update_dirty_state()
