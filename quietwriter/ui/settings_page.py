
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QGridLayout, QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox, QSizePolicy, QVBoxLayout, QWidget
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
        self._ai_models_by_provider = {'ollama': list(self.available_models), 'openrouter': []}
        self._ai_model_drafts = {
            'ollama': str(settings.value('ollama_model', '') or ''),
            'openrouter': str(settings.value('openrouter_model', '') or ''),
        }
        self._last_ai_provider = str(settings.value('ai_provider', 'ollama') or 'ollama')
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
            tr('settings.general.intro', 'Basisgedrag van QuietWriter.')
        )
        self._add_settings_section(gl, tr('settings.section.program', 'Programma'))
        self.language = QComboBox()
        self.language.addItem(tr('language.dutch', 'Nederlands'), 'nl')
        self.language.addItem(tr('language.english', 'Engels'), 'en')
        language_value = str(settings.value('language', 'nl') or 'nl')
        language_index = self.language.findData(language_value)
        self.language.setCurrentIndex(language_index if language_index >= 0 else 0)
        self._add_settings_field(gl, tr('settings.general.language', 'Programmataal'), self.language,
            tr('settings.general.language_help', 'De gekozen taal wordt na een herstart van QuietWriter toegepast.'))
        self._add_settings_section(gl, tr('settings.section.saving', 'Opslaan'))
        self.autosave = QCheckBox(tr('settings.general.autosave', 'Automatisch opslaan')); self.autosave.setChecked(settings.value('autosave', True, bool))
        self._add_settings_field(gl, tr('settings.general.autosave', 'Automatisch opslaan'), self.autosave,
            tr('settings.general.autosave_help', 'Slaat wijzigingen ongeveer drie seconden na je laatste toetsaanslag automatisch op. Staat dit uit, dan gebruik je Ctrl+S om handmatig op te slaan.'))
        gl.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.general', 'Algemeen'), general)

        # Uiterlijk
        appearance, al = self._make_settings_page(
            tr('settings.appearance', 'Uiterlijk'),
            tr('settings.appearance.intro', 'Pas het thema en de schrijftypografie aan. Voorbeelden worden direct toegepast; Opslaan maakt de keuze blijvend.')
        )
        self._add_settings_section(al, tr('settings.section.display', 'Weergave'))
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(settings.value('theme', 'Helder'))
        self._add_settings_field(al, tr('settings.appearance.theme', 'Kleurenschema'), self.theme,
            tr('settings.appearance.theme_help', 'Past de volledige interface direct als voorbeeld aan.'))

        self._add_settings_section(al, tr('settings.section.typography', 'Schrijftypografie'))
        self.editor_font = QComboBox(); self._populate_font_combo(self.original_typography.family)
        self.font_preview = QLabel(tr('settings.appearance.font_sample', 'De eerste zin van een nieuw verhaal begint vaak met één enkel idee.'))
        self.font_preview.setObjectName('fontPreviewSample'); self.font_preview.setWordWrap(True)
        self.font_preview_meta = QLabel('')
        self.font_preview_meta.setObjectName('fontPreviewMeta')
        preview_card = QFrame()
        preview_card.setObjectName('fontPreviewCard')
        pv = QVBoxLayout(preview_card); pv.setContentsMargins(16, 12, 16, 12); pv.setSpacing(5)
        pv.addWidget(self.font_preview)
        pv.addWidget(self.font_preview_meta)
        font_control = QWidget()
        font_control.setObjectName('settingsInlineControl')
        fh = QHBoxLayout(font_control); fh.setContentsMargins(0, 0, 0, 0); fh.setSpacing(16)
        self.editor_font.setMinimumWidth(280); self.editor_font.setMaximumWidth(340)
        preview_card.setMinimumWidth(420); preview_card.setMaximumWidth(560); preview_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        fh.addWidget(self.editor_font, 0, Qt.AlignTop); fh.addWidget(preview_card, 1)
        self._add_settings_field(al, tr('settings.appearance.font', 'Schrijflettertype'), font_control,
            tr('settings.appearance.font_help', 'Aanbevolen lettertypen worden door QuietWriter zelf geladen. Daaronder blijven alle beschikbare systeemlettertypen zichtbaar.'))

        self.editor_font_size = QSpinBox(); self.editor_font_size.setRange(11, 24); self.editor_font_size.setSuffix(' pt'); self.editor_font_size.setValue(self.original_typography.point_size)
        self._add_settings_field(al, tr('settings.appearance.font_size', 'Tekstgrootte'), self.editor_font_size)

        self._add_settings_section(al, tr('settings.section.manuscript', 'Manuscript'))
        self.manuscript_line_spacing = QSpinBox(); self.manuscript_line_spacing.setRange(120, 200); self.manuscript_line_spacing.setSuffix(' %'); self.manuscript_line_spacing.setValue(int(settings.value('manuscript_line_spacing', 155, int) or 155))
        self.manuscript_indent = QSpinBox(); self.manuscript_indent.setRange(0, 60); self.manuscript_indent.setSuffix(' px'); self.manuscript_indent.setValue(int(settings.value('manuscript_indent', 28, int) or 28))
        self.manuscript_paragraph_spacing = QSpinBox(); self.manuscript_paragraph_spacing.setRange(0, 24); self.manuscript_paragraph_spacing.setSuffix(' px'); self.manuscript_paragraph_spacing.setValue(int(settings.value('manuscript_paragraph_spacing', 8, int) or 8))
        self.smart_quotes = QCheckBox(tr('settings.appearance.smart_quotes', 'Slimme aanhalingstekens')); self.smart_quotes.setChecked(settings.value('smart_quotes', True, bool))
        self._add_settings_field(al, tr('settings.appearance.line_spacing', 'Regelafstand'), self.manuscript_line_spacing,
            tr('settings.appearance.line_spacing_help', 'Bepaalt de verticale ruimte tussen regels in de schrijfeditor.'))
        self._add_settings_field(al, tr('settings.appearance.indent', 'Alinea-inspringing'), self.manuscript_indent,
            tr('settings.appearance.indent_help', 'Vervolgalinea’s springen in. De eerste alinea van een hoofdstuk, na een lege regel, tussenkop of scènebreuk begint links.'))
        self._add_settings_field(al, tr('settings.appearance.paragraph_spacing', 'Ruimte na alinea'), self.manuscript_paragraph_spacing,
            tr('settings.appearance.paragraph_spacing_help', 'Voegt subtiele extra ruimte tussen opeenvolgende alinea’s toe.'))
        self._add_settings_field(al, tr('settings.appearance.smart_quotes', 'Slimme aanhalingstekens'), self.smart_quotes,
            tr('settings.appearance.smart_quotes_help', 'Zet een tijdens het typen ingevoerd recht dubbel aanhalingsteken om naar een typografisch openings- of sluitteken.'))
        al.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.appearance', 'Uiterlijk'), appearance)

        # Opslag
        storage, slay = self._make_settings_page(
            tr('settings.storage', 'Opslag'),
            tr('settings.storage.intro', 'Bepaal waar QuietWriter zijn boeken en ondersteunende bestanden bewaart.')
        )
        self._add_settings_section(slay, tr('settings.section.workspace', 'Werkmap'))
        self.root = QLineEdit(settings.value('workspace', str(Path.home() / 'QuietWriter')))
        choose = QPushButton(tr('settings.storage.choose_folder', 'Map kiezen…')); choose.clicked.connect(self.choose_root)
        box = QWidget(); box.setMinimumWidth(680); box.setMaximumWidth(860); h = QHBoxLayout(box); h.setContentsMargins(0,0,0,0); h.setSpacing(10); self.root.setMinimumWidth(540); h.addWidget(self.root, 1); h.addWidget(choose)
        self._add_settings_field(slay, tr('settings.storage.workspace', 'Werkmap'), box,
            tr('settings.storage.workspace_help', 'Hier staan je boeken, planning, publicatiestructuur en lokale herstelgegevens. Een wijziging wordt na herstart gebruikt.'))
        self.sync_warning = QLabel('')
        self.sync_warning.setObjectName('syncWarning'); self.sync_warning.setWordWrap(True)
        self._add_settings_full_width(slay, self.sync_warning)
        self.root.textChanged.connect(self.update_sync_warning)

        self._add_settings_section(slay, tr('settings.section.metadata', 'Metadata'))
        self.cover_template = QLineEdit(settings.value('cover_header_template', '/{slug}.jpg')); self.cover_template.setPlaceholderText('/{slug}.jpg')
        self._add_settings_field(slay, tr('settings.storage.cover_path', 'Afbeeldingspad'), self.cover_template,
            tr('settings.storage.cover_path_help', 'Wordt gebruikt bij Markdown-metadata. Gebruik {slug}, bijvoorbeeld /{slug}.jpg of /images/{slug}.jpg.'))
        slay.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.storage', 'Opslag'), storage)

        # AI
        ai, ail = self._make_settings_page(
            tr('settings.ai', 'AI'),
            tr('settings.ai.intro', 'De AI-assistent helpt alleen wanneer jij daarom vraagt, bijvoorbeeld voor feedback of analyse. Hij wijzigt je manuscript nooit zelfstandig. QuietWriter bevat zelf geen AI-model: je verbindt een lokaal model via Ollama of een extern model via OpenRouter.')
        )
        self._add_settings_section(ail, tr('settings.section.ai_usage', 'Gebruik'))
        self.ai_enabled = QCheckBox(tr('settings.ai.enable', 'AI-assistent gebruiken'))
        self.ai_enabled.setChecked(settings.value('ai_enabled', True, bool))
        self._add_settings_field(ail, tr('settings.ai.enable', 'AI-assistent gebruiken'), self.ai_enabled,
            tr('settings.ai.enable_help', 'Toont de AI-assistent in de editor. Staat dit uit, dan blijven de AI-instellingen bewaard maar zijn ze niet actief en wordt er geen AI-provider gebruikt.'))

        self._add_settings_section(ail, tr('settings.section.provider', 'Provider'))
        self.ai_provider = QComboBox(); self.ai_provider.addItem(tr('settings.ai.ollama_local', 'Ollama (lokaal)'), 'ollama'); self.ai_provider.addItem('OpenRouter', 'openrouter')
        provider_value = str(settings.value('ai_provider', 'ollama') or 'ollama')
        idx = self.ai_provider.findData(provider_value); self.ai_provider.setCurrentIndex(max(0, idx))
        self.ollama = QLineEdit(settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.openrouter_key = QLineEdit(settings.value('openrouter_api_key', '')); self.openrouter_key.setEchoMode(QLineEdit.Password); self.openrouter_key.setPlaceholderText('API-key')
        self._add_settings_field(ail, tr('settings.ai.provider', 'AI-provider'), self.ai_provider,
            tr('settings.ai.provider_help', 'Ollama draait lokaal op je computer. OpenRouter gebruikt een externe API-key.'))
        self._add_settings_field(ail, tr('settings.ai.ollama_url', 'Ollama-adres'), self.ollama,
            tr('settings.ai.ollama_url_help', 'Alleen relevant wanneer Ollama als provider is gekozen.'))
        self._add_settings_field(ail, tr('settings.ai.openrouter_key', 'OpenRouter API-key'), self.openrouter_key,
            tr('settings.ai.openrouter_key_help', 'Alleen relevant wanneer OpenRouter als provider is gekozen. De sleutel wordt lokaal in je QuietWriter-instellingen bewaard.'))

        self._add_settings_section(ail, tr('settings.section.model', 'Model'))
        self.model = QComboBox(); self.model.setEditable(False)
        self.ai_refresh_button = QPushButton(tr('settings.ai.refresh_models', 'Modellen ophalen')); self.ai_refresh_button.clicked.connect(self.refresh_models)
        modelbox = QWidget(); mv = QVBoxLayout(modelbox); mv.setContentsMargins(0,0,0,0); mv.setSpacing(5)
        modelrow = QWidget(); mh = QHBoxLayout(modelrow); mh.setContentsMargins(0,0,0,0); mh.setSpacing(8); mh.addWidget(self.model, 1); mh.addWidget(self.ai_refresh_button)
        self.ai_model_status = QLabel(''); self.ai_model_status.setObjectName('settingsFieldHelp'); self.ai_model_status.hide()
        mv.addWidget(modelrow); mv.addWidget(self.ai_model_status)
        self._add_settings_field(ail, tr('settings.ai.model', 'Schrijf- en analysemodel'), modelbox,
            tr('settings.ai.model_help', 'QuietWriter stuurt alleen de context die je in de AI-zijbalk kiest, samen met je schrijverspersona.'))
        self._ai_controls = (self.ai_provider, self.ollama, self.openrouter_key, self.model, self.ai_refresh_button)
        self.ai_enabled.toggled.connect(self._update_ai_controls)
        self.ai_provider.currentIndexChanged.connect(self._ai_provider_changed)
        self._update_ai_controls()
        ail.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.ai', 'AI'), ai)

        # Spelling
        spelling, spl = self._make_settings_page(
            tr('settings.spelling', 'Spelling'),
            tr('settings.spelling.intro', 'Beheer de spellingscontrole en de gevonden Hunspell-woordenboeken.')
        )
        self._add_settings_section(spl, tr('settings.section.checking', 'Controle'))
        self.spell_enabled = QCheckBox(tr('settings.spelling.enable', 'Spellingscontrole inschakelen')); self.spell_enabled.setChecked(settings.value('spell_enabled', True, bool))
        self._add_settings_field(spl, tr('settings.spelling.check', 'Spellingscontrole'), self.spell_enabled,
            tr('settings.spelling.check_help', 'Onderstreept onbekende woorden in de editor. Je manuscripttekst zelf wordt nooit automatisch aangepast.'))
        self.dictionary_catalog = DictionaryCatalog(Path(settings.value('workspace', str(Path.home() / 'QuietWriter'))) / 'dictionaries')
        self.spell_language = QComboBox(); self.spell_language.currentIndexChanged.connect(self.update_dictionary_info)
        self._add_settings_field(spl, tr('settings.spelling.language', 'Taal'), self.spell_language,
            tr('settings.spelling.language_help', 'QuietWriter gebruikt een gevonden Hunspell-woordenboek voor deze taal.'))

        self._add_settings_section(spl, tr('settings.section.dictionaries', 'Woordenboeken'))
        self.dictionary_info = QLabel(''); self.dictionary_info.setObjectName('muted'); self.dictionary_info.setWordWrap(True)
        self._add_settings_full_width(spl, self.dictionary_info)
        actions_widget = QWidget(); actions = QHBoxLayout(actions_widget); actions.setContentsMargins(0,0,0,0); actions.setSpacing(8)
        self.scan_dict_btn = QPushButton(tr('settings.spelling.rescan', 'Opnieuw zoeken')); self.scan_dict_btn.clicked.connect(self.refresh_dictionaries)
        self.add_dict_btn = QPushButton(tr('settings.spelling.add_dictionary', 'Toevoegen…')); self.add_dict_btn.clicked.connect(self.choose_dictionary)
        self.remove_dict_btn = QPushButton(tr('common.delete', 'Verwijderen')); self.remove_dict_btn.clicked.connect(self.remove_dictionary)
        self.download_dict_btn = QPushButton(tr('settings.spelling.download_site', 'Downloadsite')); self.download_dict_btn.clicked.connect(self.open_dictionary_download)
        for btn in (self.scan_dict_btn, self.add_dict_btn, self.remove_dict_btn, self.download_dict_btn):
            actions.addWidget(btn)
        actions.addStretch(1)
        self._add_settings_field(spl, tr('settings.spelling.manage', 'Beheer'), actions_widget,
            tr('settings.spelling.manage_help', 'QuietWriter zoekt in de werkmap en in geïnstalleerde versies van ONLYOFFICE, LibreOffice en OpenOffice. Je kunt ook zelf een .dic/.aff-woordenboek toevoegen.'))
        spl.addStretch(1)
        self._add_settings_category(nav_lay, tr('settings.spelling', 'Spelling'), spelling)

        # Over volgt direct op Spelling; de vrije ruimte blijft onder de laatste categorie.
        about = AboutPage(self)
        self.about_index = self.pages.count()
        self._add_settings_category(nav_lay, tr('settings.about', 'Over'), about)
        nav_lay.addStretch(1)

        self._populate_models()
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

        self.save_feedback = QLabel(tr('settings.saved', 'Opgeslagen'), self)
        self.save_feedback.setObjectName('settingsToast')
        self.save_feedback.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.save_feedback.hide()
        self._save_feedback_timer = QTimer(self)
        self._save_feedback_timer.setSingleShot(True)
        self._save_feedback_timer.setInterval(2200)
        self._save_feedback_timer.timeout.connect(self.save_feedback.hide)

        self.theme.currentTextChanged.connect(self._preview_appearance)
        self.editor_font.currentTextChanged.connect(self._update_font_preview)
        self.editor_font_size.valueChanged.connect(self._update_font_preview)

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
            heading = QStandardItem(tr('settings.fonts.recommended', 'Aanbevolen'))
            heading.setEnabled(False); heading.setSelectable(False)
            model.appendRow(heading)
            for family in recommended:
                model.appendRow(QStandardItem(family))
            separator = QStandardItem('────────────')
            separator.setEnabled(False); separator.setSelectable(False)
            model.appendRow(separator)
        heading = QStandardItem(tr('settings.fonts.system', 'Systeemfonts'))
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
        if family in {tr('settings.fonts.recommended', 'Aanbevolen'), tr('settings.fonts.system', 'Systeemfonts'), '────────────'}:
            return
        size = int(self.editor_font_size.value())
        font = typography_from_values(family, max(14, size)).body_font()
        self.font_preview.setFont(font)
        self.font_preview_meta.setText(tr('settings.appearance.font_preview_meta', '{family} · {size} pt', family=family, size=size))

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
        layout.setContentsMargins(8, 0, 28, 32)
        layout.setSpacing(0)
        heading = QLabel(title); heading.setObjectName('settingsPageTitle'); layout.addWidget(heading)
        if intro:
            note = QLabel(intro); note.setObjectName('settingsPageIntro'); note.setWordWrap(True); note.setMaximumWidth(1040)
            layout.addWidget(note)
        layout.addSpacing(22)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)
        return page, layout

    def _add_settings_section(self, layout: QVBoxLayout, title: str):
        if layout.count() > 0:
            layout.addSpacing(20)
        label = QLabel(title.upper())
        label.setObjectName('settingsSectionTitle')
        layout.addWidget(label, 0, Qt.AlignLeft)
        layout.addSpacing(8)

    def _add_settings_field(self, layout: QVBoxLayout, label_text: str, widget: QWidget, note: str | None = None):
        """Add one settings row using stable, invisible information/control columns."""
        row = QFrame()
        row.setObjectName('settingsRow')
        row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        grid = QGridLayout(row)
        grid.setContentsMargins(0, 14, 0, 14)
        grid.setHorizontalSpacing(38)
        grid.setVerticalSpacing(0)
        grid.setColumnMinimumWidth(0, 320)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        info = QWidget()
        info.setObjectName('settingsRowInfo')
        info.setFixedWidth(320)
        info.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        iv = QVBoxLayout(info)
        iv.setContentsMargins(0, 0, 0, 0)
        iv.setSpacing(5)
        label = QLabel(label_text)
        label.setObjectName('settingsFieldLabel')
        iv.addWidget(label)
        if note:
            detail = QLabel(note)
            detail.setObjectName('settingsFieldHelp')
            detail.setWordWrap(True)
            detail.setMaximumWidth(310)
            iv.addWidget(detail)
        iv.addStretch(1)
        grid.addWidget(info, 0, 0, Qt.AlignTop | Qt.AlignLeft)

        control_host = QWidget()
        control_host.setObjectName('settingsRowControl')
        control_host.setMinimumWidth(320)
        control_host.setMaximumWidth(860)
        control_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        cv = QVBoxLayout(control_host)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        if isinstance(widget, QSpinBox):
            widget.setMinimumWidth(160); widget.setMaximumWidth(200)
        elif isinstance(widget, QComboBox):
            widget.setMinimumWidth(260); widget.setMaximumWidth(380)
        elif isinstance(widget, QLineEdit):
            widget.setMinimumWidth(360); widget.setMaximumWidth(680)
        elif not isinstance(widget, QCheckBox):
            widget.setMaximumWidth(860)
        cv.addWidget(widget, 0, Qt.AlignTop | Qt.AlignLeft)
        cv.addStretch(1)
        grid.addWidget(control_host, 0, 1, Qt.AlignTop | Qt.AlignLeft)
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
            bool(self.ai_enabled.isChecked()),
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
            self.ai_enabled, self.ai_provider, self.ollama, self.openrouter_key, self.model,
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
        # Theme is application chrome and can be previewed safely. Writing font
        # and manuscript block layout deliberately stay inside this settings page
        # until Save: applying them to the hidden editor creates presentation-only
        # QTextBlockFormat commands in the manuscript Undo history. The font card
        # above already provides an accurate family/size preview.
        theme = self.theme.currentText() or 'Helder'
        if theme != self._preview_theme:
            win = self.parent()
            if win and hasattr(win, 'apply_theme'):
                win.apply_theme(theme)
            else:
                QApplication.instance().setStyleSheet(stylesheet(theme))
            self._preview_theme = theme

    def restore_preview(self):
        # Only theme is live-previewed. Font/manuscript style were never applied
        # to the editor, so restoring them here would itself pollute Undo.
        if self._preview_theme != str(self.original_theme or 'Helder'):
            win = self.parent()
            if win and hasattr(win, 'apply_theme'):
                win.apply_theme(str(self.original_theme or 'Helder'))
            else:
                QApplication.instance().setStyleSheet(stylesheet(self.original_theme))
            self._preview_theme = str(self.original_theme or 'Helder')

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
                tr('settings.storage.sync_warning', 'Let op: deze werkmap lijkt in {provider} te staan. Gesynchroniseerde mappen kunnen bestanden heel kort vergrendelen tijdens synchronisatie. QuietWriter vangt dit zo veel mogelijk op, maar sluit bij onverwachte opslagfouten eerst andere programma’s die dezelfde bestanden gebruiken.', provider=provider)
            )
            self.sync_warning.show()
        else:
            self.sync_warning.clear(); self.sync_warning.hide()

    def choose_root(self):
        p = QFileDialog.getExistingDirectory(self, tr('settings.storage.choose_workspace', 'Kies werkmap'), self.root.text())
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
            self.dictionary_info.setText(tr('settings.spelling.no_dictionaries', 'Geen woordenboeken gevonden. Installeer bijvoorbeeld ONLYOFFICE, LibreOffice of OpenOffice, of voeg zelf een Hunspell-woordenboek toe.'))
            self.remove_dict_btn.setEnabled(False)
            return
        aff = tr('settings.spelling.aff_rules', 'met .aff-regels') if entry.aff else tr('settings.spelling.dic_only', 'alleen .dic')
        self.dictionary_info.setText(tr('settings.spelling.dictionary_info', 'Bron: {source} · {locale} · {kind}\n{path}', source=entry.source, locale=entry.locale, kind=aff, path=entry.dic))
        self.remove_dict_btn.setEnabled(entry.source == 'Werkmap')

    def choose_dictionary(self):
        p, _ = QFileDialog.getOpenFileName(self, tr('settings.spelling.choose_dictionary', 'Kies Hunspell-woordenboek'), str(Path.home()), tr('settings.spelling.dictionary_filter', 'Hunspell woordenboek (*.dic);;Alle bestanden (*)'))
        if not p:
            return
        self.dictionary_catalog = DictionaryCatalog(self._dictionary_workspace())
        entry = self.dictionary_catalog.add_custom(Path(p))
        self.refresh_dictionaries(preserve_locale=entry.locale)

    def remove_dictionary(self):
        locale = self.spell_language.currentData()
        entry = self.dictionary_catalog.get(locale) if locale else None
        if not entry or entry.source != 'Werkmap':
            QMessageBox.information(self, tr('settings.spelling.remove_title', 'Woordenboek verwijderen'), tr('settings.spelling.remove_info', 'Alleen woordenboeken die je zelf aan QuietWriter hebt toegevoegd kunnen hier worden verwijderd. Woordenboeken van Office-programma’s blijven onaangeroerd.'))
            return
        if not confirm(self, tr('settings.spelling.remove_title', 'Woordenboek verwijderen'), tr('settings.spelling.remove_confirm', 'Wil je “{label}” uit de QuietWriter-werkmap verwijderen?', label=entry.label)):
            return
        if not self.dictionary_catalog.remove_custom(locale):
            QMessageBox.warning(self, tr('settings.spelling.remove_title', 'Woordenboek verwijderen'), tr('settings.spelling.remove_failed', 'Het woordenboek kon niet worden verwijderd.'))
        self.refresh_dictionaries()

    def open_dictionary_download(self):
        QDesktopServices.openUrl(QUrl(self.DICTIONARY_DOWNLOAD_URL))

    def _remember_current_ai_model(self, provider_name: str | None = None):
        provider_name = provider_name or self._last_ai_provider
        if provider_name in self._ai_model_drafts:
            self._ai_model_drafts[provider_name] = self.model.currentText().strip()

    def _populate_models(self, provider_name: str | None = None):
        # Use the live form selection, never the already-persisted ai_provider.
        # This prevents an Ollama model from remaining visible when the user
        # switches the unsaved settings form to OpenRouter (and vice versa).
        provider_name = str(provider_name or self.ai_provider.currentData() or 'ollama')
        current = self._ai_model_drafts.get(provider_name, '')
        models = list(self._ai_models_by_provider.get(provider_name, []))
        self.model.blockSignals(True)
        self.model.clear()
        self.model.addItems(models)
        if current:
            if self.model.findText(current) < 0:
                self.model.addItem(current)
            self.model.setCurrentText(current)
        elif self.model.count():
            self.model.setCurrentIndex(0)
        self.model.blockSignals(False)

    def _ai_provider_changed(self, *_):
        new_provider = str(self.ai_provider.currentData() or 'ollama')
        old_provider = str(self._last_ai_provider or 'ollama')
        if old_provider != new_provider:
            self._remember_current_ai_model(old_provider)
            self._last_ai_provider = new_provider
            self._populate_models(new_provider)
            self.ai_model_status.clear()
            self.ai_model_status.hide()
        self._update_ai_controls()
        self._update_dirty_state()

    def _update_ai_controls(self, *_):
        enabled = bool(self.ai_enabled.isChecked())
        for control in self._ai_controls:
            control.setEnabled(enabled)

    def refresh_models(self):
        # Model discovery must not silently persist unsaved form values. Settings
        # remain transactional: only Opslaan writes them to QSettings.
        provider_name = str(self.ai_provider.currentData() or 'ollama')
        values = {
            'ai_provider': provider_name,
            'ollama_url': self.ollama.text(),
            'openrouter_api_key': self.openrouter_key.text(),
            'openrouter_url': self.settings.value('openrouter_url', 'https://openrouter.ai/api/v1'),
        }

        class FormSettings:
            def value(self, key, default=None):
                return values.get(key, default)

        self.ai_model_status.setText(tr('settings.ai.fetching_models', 'Modellen ophalen…'))
        self.ai_model_status.show()
        self.ai_refresh_button.setEnabled(False)
        QApplication.processEvents()
        try:
            provider = ProviderFactory.from_settings(FormSettings())
            infos = provider.list_models()
            models = [m['name'] for m in infos]
            previous = self.model.currentText().strip()
            self._ai_models_by_provider[provider_name] = models
            if previous in models:
                self._ai_model_drafts[provider_name] = previous
            elif models:
                self._ai_model_drafts[provider_name] = models[0]
            else:
                self._ai_model_drafts[provider_name] = ''
            self._populate_models(provider_name)
            if provider_name == 'ollama':
                self.available_models = list(models)
                if self.parent() and hasattr(self.parent(), 'models'):
                    self.parent().models = models
            self.ai_model_status.setText(tr('settings.ai.fetch_success', 'Modellen opgehaald: {count}', count=len(models)))
            self.ai_model_status.show()
            self._update_dirty_state()
        except Exception as exc:
            self.ai_model_status.setText(tr('settings.ai.fetch_failed_short', 'Modellen ophalen mislukt'))
            self.ai_model_status.show()
            QMessageBox.warning(self, 'AI', tr('settings.ai.fetch_failed', 'Modellen ophalen mislukt:\n\n{error}', error=exc))
        finally:
            self.ai_refresh_button.setEnabled(bool(self.ai_enabled.isChecked()))

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

    def _show_saved_feedback(self, language_restart=False):
        self.save_feedback.setText(
            tr('settings.saved_restart_language', 'Opgeslagen · taal wordt na herstart toegepast')
            if language_restart else tr('settings.saved', 'Opgeslagen')
        )
        self.save_feedback.adjustSize()
        self._position_save_feedback()
        self.save_feedback.show()
        self.save_feedback.raise_()
        self._save_feedback_timer.start()

    def save_settings(self):
        old_root = self.settings.value('workspace', str(Path.home()/APP_NAME))
        old_language = str(self.settings.value('language', 'nl') or 'nl')
        new_language = str(self.language.currentData() or 'nl')
        new_typography = typography_from_values(self.editor_font.currentText(), self.editor_font_size.value())
        new_manuscript_style = ManuscriptStyle.from_values(
            self.manuscript_line_spacing.value(), self.manuscript_indent.value(),
            self.manuscript_paragraph_spacing.value(), self.smart_quotes.isChecked()
        )
        writing_layout_changed = (
            new_typography != self.original_typography
            or new_manuscript_style.line_spacing_percent != self.original_manuscript_style.line_spacing_percent
            or new_manuscript_style.paragraph_indent_px != self.original_manuscript_style.paragraph_indent_px
            or new_manuscript_style.paragraph_spacing_px != self.original_manuscript_style.paragraph_spacing_px
        )
        self.settings.setValue('language', new_language)
        self.settings.setValue('theme', self.theme.currentText())
        self.settings.setValue('editor_font', new_typography.family)
        self.settings.setValue('editor_font_size', int(self.editor_font_size.value()))
        self.settings.setValue('manuscript_line_spacing', int(self.manuscript_line_spacing.value()))
        self.settings.setValue('manuscript_indent', int(self.manuscript_indent.value()))
        self.settings.setValue('manuscript_paragraph_spacing', int(self.manuscript_paragraph_spacing.value()))
        self.settings.setValue('smart_quotes', self.smart_quotes.isChecked())
        self.settings.setValue('autosave', self.autosave.isChecked())
        self.settings.setValue('workspace', self.root.text())
        self.settings.setValue('ai_enabled', self.ai_enabled.isChecked())
        provider = str(self.ai_provider.currentData() or 'ollama')
        self._remember_current_ai_model(provider)
        self.settings.setValue('ai_provider', provider)
        self.settings.setValue('ollama_url', self.ollama.text())
        self.settings.setValue('openrouter_api_key', self.openrouter_key.text())
        self.settings.setValue('ollama_model', self._ai_model_drafts.get('ollama', ''))
        self.settings.setValue('openrouter_model', self._ai_model_drafts.get('openrouter', ''))
        self.settings.setValue('cover_header_template', self.cover_template.text().strip() or '/{slug}.jpg')
        self.settings.setValue('spell_enabled', self.spell_enabled.isChecked())
        self.settings.setValue('spell_language', self.spell_language.currentData() or '')
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            QMessageBox.warning(self, tr('settings.save_error_title', 'Instellingen opslaan'), tr('settings.save_error', 'De instellingen konden niet betrouwbaar naar schijf worden geschreven. Controleer de toegangsrechten en probeer het opnieuw.'))
            return
        self.original_theme = self.theme.currentText()
        self.original_typography = new_typography
        self.original_editor_font = new_typography.family
        self.original_editor_size = new_typography.point_size
        self.original_manuscript_style = new_manuscript_style
        self._preview_theme = self.original_theme
        if self.parent() and hasattr(self.parent(), 'settings_saved'):
            self.parent().settings_saved(old_root, writing_layout_changed=writing_layout_changed)
        self._saved_form_state = self._current_form_state()
        self._update_dirty_state()
        self._show_saved_feedback(language_restart=(new_language != old_language))

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
        language_value = str(self.settings.value('language', 'nl') or 'nl')
        language_index = self.language.findData(language_value)
        self.language.setCurrentIndex(language_index if language_index >= 0 else 0)
        self.autosave.setChecked(self.settings.value('autosave', True, bool))
        self.root.setText(self.settings.value('workspace', str(Path.home()/APP_NAME)))
        self.cover_template.setText(self.settings.value('cover_header_template', '/{slug}.jpg'))
        self.ai_enabled.setChecked(self.settings.value('ai_enabled', True, bool))
        provider = str(self.settings.value('ai_provider', 'ollama') or 'ollama')
        self._ai_model_drafts = {
            'ollama': str(self.settings.value('ollama_model', '') or ''),
            'openrouter': str(self.settings.value('openrouter_model', '') or ''),
        }
        self._ai_models_by_provider['ollama'] = list(self.available_models)
        self.ai_provider.blockSignals(True)
        idx = self.ai_provider.findData(provider); self.ai_provider.setCurrentIndex(max(0, idx))
        self.ai_provider.blockSignals(False)
        self._last_ai_provider = provider
        self.ollama.setText(self.settings.value('ollama_url', 'http://127.0.0.1:11434'))
        self.openrouter_key.setText(self.settings.value('openrouter_api_key', ''))
        self._populate_models(provider)
        self._update_ai_controls()
        self.spell_enabled.setChecked(self.settings.value('spell_enabled', True, bool))
        self.refresh_dictionaries(preserve_locale=str(self.settings.value('spell_language', 'nl_NL') or 'nl_NL'))
        self.update_sync_warning()
        self._saved_form_state = self._current_form_state()
        self._update_dirty_state()
