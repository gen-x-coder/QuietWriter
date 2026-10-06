from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QAbstractButton, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ..dictionary_catalog import locale_label
from ..i18n import set_locale, tr
from ..icon_theme import set_icon_theme
from ..themes import THEMES, stylesheet
from ..workspace_path import normalize_workspace_path


class FirstRunWizard(QDialog):
    """Small transactional setup wizard for genuinely new QuietWriter users."""

    def __init__(self, settings, default_workspace: Path, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.default_workspace = Path(default_workspace)
        self.setModal(True)
        self.setWindowTitle(tr('first_run.title', 'Welkom bij QuietWriter'))
        self.setMinimumSize(720, 500)
        self.resize(780, 540)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 24)
        root.setSpacing(16)

        title = self._label('first_run.title', 'Welkom bij QuietWriter')
        title.setObjectName('title')
        root.addWidget(title)
        self.progress = QLabel('')
        self.progress.setObjectName('muted')
        root.addWidget(self.progress)

        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        self.language = QComboBox()
        self.language.addItem('Nederlands', 'nl')
        self.language.addItem('English', 'en')
        language = str(settings.value('language', 'nl') or 'nl')
        self.language.setCurrentIndex(max(0, self.language.findData(language)))
        self.language.currentIndexChanged.connect(self._language_changed)
        self.theme = QComboBox()
        self.theme.addItems(THEMES.keys())
        self.theme.setCurrentText(str(settings.value('theme', 'Helder') or 'Helder'))
        self.theme.currentTextChanged.connect(self._theme_changed)
        self.pages.addWidget(self._page_language())

        self.workspace = QLineEdit(str(settings.value('workspace', str(self.default_workspace)) or self.default_workspace))
        self.pages.addWidget(self._page_workspace())

        self.spell_enabled = self._button(QCheckBox(), 'first_run.spelling_enable', 'Spellingscontrole inschakelen')
        self.spell_enabled.setChecked(settings.value('spell_enabled', True, bool))
        self.spell_language = QComboBox()
        self._populate_dictionaries()
        spell_locale = str(settings.value('spell_language', 'nl_NL') or 'nl_NL')
        spell_index = self.spell_language.findData(spell_locale)
        if spell_index >= 0:
            self.spell_language.setCurrentIndex(spell_index)
        self.pages.addWidget(self._page_spelling())

        self.ai_none = self._button(QRadioButton(), 'first_run.ai_none', 'Geen AI gebruiken')
        self.ai_ollama = self._button(QRadioButton(), 'first_run.ai_ollama', 'Lokale AI via Ollama')
        self.ai_openrouter = self._button(QRadioButton(), 'first_run.ai_openrouter', 'Externe AI via OpenRouter')
        if settings.value('ai_enabled', False, bool):
            provider = str(settings.value('ai_provider', 'ollama') or 'ollama').lower()
            (self.ai_openrouter if provider == 'openrouter' else self.ai_ollama).setChecked(True)
        else:
            self.ai_none.setChecked(True)
        self.pages.addWidget(self._page_ai())

        self.auto_update_check = self._button(
            QCheckBox(), 'first_run.update_auto', 'Automatisch controleren op nieuwe versies'
        )
        self.auto_update_check.setChecked(settings.value('auto_update_check', False, bool))
        self.pages.addWidget(self._page_updates())

        self.tour_enabled = self._button(
            QCheckBox(), 'first_run.tour_enable', 'Laat mij kort zien waar alles zit'
        )
        self.tour_enabled.setChecked(True)
        self.tour_choice_index = self.pages.count()
        self.pages.addWidget(self._page_tour_choice())
        self.tour_start_index = self.pages.count()
        self.pages.addWidget(self._page_tour_books())
        self.pages.addWidget(self._page_tour_writing())
        self.pages.addWidget(self._page_tour_finish())

        nav = QHBoxLayout()
        self.back_btn = self._button(QPushButton(), 'first_run.back', 'Vorige')
        self.skip_btn = self._button(QPushButton(), 'first_run.skip', 'Overslaan')
        self.next_btn = QPushButton()
        self.next_btn.setObjectName('primaryButton')
        self.back_btn.clicked.connect(self._back)
        self.skip_btn.clicked.connect(self._skip)
        self.next_btn.clicked.connect(self._next)
        nav.addWidget(self.back_btn)
        nav.addWidget(self.skip_btn)
        nav.addStretch(1)
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

        self.pages.currentChanged.connect(self._update_nav)
        self.tour_enabled.toggled.connect(self._update_nav)
        self._update_nav()

    @staticmethod
    def _mark_i18n(widget: QWidget, key: str, default: str) -> QWidget:
        widget.setProperty('i18nKey', key)
        widget.setProperty('i18nDefault', default)
        return widget

    def _label(self, key: str, default: str) -> QLabel:
        label = QLabel(tr(key, default))
        return self._mark_i18n(label, key, default)

    def _button(self, button: QAbstractButton, key: str, default: str):
        button.setText(tr(key, default))
        return self._mark_i18n(button, key, default)

    def _language_changed(self, *_args) -> None:
        set_locale(str(self.language.currentData() or 'nl'))
        self._retranslate_ui()

    def _theme_changed(self, theme: str) -> None:
        theme = str(theme or 'Helder')
        set_icon_theme(theme)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet(theme))

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(tr('first_run.title', 'Welkom bij QuietWriter'))
        for widget in self.findChildren(QWidget):
            key = widget.property('i18nKey')
            default = widget.property('i18nDefault')
            if not key:
                continue
            text = tr(str(key), str(default or key))
            if isinstance(widget, QLabel):
                widget.setText(text)
            elif isinstance(widget, QAbstractButton):
                widget.setText(text)
        self._update_nav()

    def _shell(self, heading_key: str, heading_default: str, text_key: str, text_default: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(6, 8, 6, 8)
        lay.setSpacing(12)
        h = self._label(heading_key, heading_default)
        h.setObjectName('settingsPageTitle')
        lay.addWidget(h)
        note = self._label(text_key, text_default)
        note.setObjectName('settingsPageIntro')
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addSpacing(10)
        return page, lay

    def _row(self, label_key: str, label_default: str, widget: QWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName('settingsRow')
        row = QHBoxLayout(frame)
        row.setContentsMargins(0, 14, 0, 14)
        row.setSpacing(24)
        lab = self._label(label_key, label_default)
        lab.setMinimumWidth(210)
        lab.setObjectName('settingsFieldLabel')
        row.addWidget(lab, 0, Qt.AlignTop)
        row.addWidget(widget, 1)
        return frame

    def _page_language(self) -> QWidget:
        page, lay = self._shell(
            'first_run.language_title', 'Taal en uiterlijk',
            'first_run.language_text', 'Kies de programmataal en het kleurenschema. Alles blijft later wijzigbaar via Instellingen.',
        )
        lay.addWidget(self._row('settings.general.language', 'Programmataal', self.language))
        lay.addWidget(self._row('settings.appearance.theme', 'Kleurenschema', self.theme))
        preview = QFrame()
        preview.setObjectName('fontPreviewCard')
        pv = QVBoxLayout(preview)
        pv.setContentsMargins(18, 14, 18, 14)
        pv.setSpacing(5)
        sample = self._label('first_run.theme_preview_title', 'Een rustige plek om te schrijven')
        sample.setObjectName('settingsPageTitle')
        sample_text = self._label(
            'first_run.theme_preview_text',
            'Dit voorbeeld verandert meteen mee. Kies vooral wat prettig leest; je kunt het later altijd aanpassen.'
        )
        sample_text.setObjectName('muted')
        sample_text.setWordWrap(True)
        pv.addWidget(sample)
        pv.addWidget(sample_text)
        lay.addWidget(preview)
        lay.addStretch(1)
        return page

    def _page_workspace(self) -> QWidget:
        page, lay = self._shell(
            'first_run.workspace_title', 'Werkmap',
            'first_run.workspace_text', 'Hier bewaart QuietWriter je boeken, planning en lokale herstelgegevens. Voor productie en ontwikkeling kun je verschillende werkmappen gebruiken.',
        )
        host = QWidget()
        h = QHBoxLayout(host)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        h.addWidget(self.workspace, 1)
        choose = self._button(QPushButton(), 'first_run.choose', 'Kiezen…')
        choose.clicked.connect(self._choose_workspace)
        h.addWidget(choose)
        lay.addWidget(self._row('settings.storage.workspace', 'Werkmap', host))
        lay.addStretch(1)
        return page

    def _page_spelling(self) -> QWidget:
        page, lay = self._shell(
            'first_run.spelling_title', 'Spelling',
            'first_run.spelling_text', 'QuietWriter gebruikt Hunspell-woordenboeken. De portable build bevat standaard Nederlands; gevonden systeemwoordenboeken worden ook getoond.',
        )
        lay.addWidget(self.spell_enabled)
        lay.addWidget(self._row('settings.spelling.language', 'Taal', self.spell_language))
        lay.addStretch(1)
        return page

    def _page_ai(self) -> QWidget:
        page, lay = self._shell(
            'first_run.ai_title', 'AI',
            'first_run.ai_text', 'AI staat standaard uit. Ollama blijft lokaal. Bij OpenRouter kunnen de tekst en context die je bewust meestuurt je computer verlaten.',
        )
        lay.addWidget(self.ai_none)
        lay.addWidget(self.ai_ollama)
        lay.addWidget(self.ai_openrouter)
        lay.addStretch(1)
        return page


    def _page_updates(self) -> QWidget:
        page, lay = self._shell(
            'first_run.update_title', 'Updates',
            'first_run.update_text',
            'QuietWriter kan GitHub vragen of er een nieuwere stabiele versie is. Daarbij worden geen boeken, manuscripten of andere inhoud verstuurd. Handmatig controleren kan altijd via Instellingen.',
        )
        lay.addWidget(self.auto_update_check)
        privacy = self._label(
            'first_run.update_privacy',
            'Automatisch controleren betekent alleen een korte versiecontrole. QuietWriter downloadt of installeert niets zonder jouw actie.',
        )
        privacy.setObjectName('muted')
        privacy.setWordWrap(True)
        lay.addWidget(privacy)
        lay.addStretch(1)
        return page

    def _page_tour_choice(self) -> QWidget:
        page, lay = self._shell(
            'first_run.tour_title', 'Korte rondleiding',
            'first_run.tour_text',
            'Nieuwe schrijvers hoeven QuietWriter niet zelf uit te pluizen. De volgende schermen leggen kort uit waar je boeken, schrijfwerk, planning, Bewaarplaats, Meelezer, geschiedenis en export vindt.',
        )
        lay.addWidget(self.tour_enabled)
        note = self._label(
            'first_run.tour_optional',
            'De rondleiding is alleen uitleg. Je kunt hem overslaan; alle functies blijven gewoon beschikbaar.',
        )
        note.setObjectName('muted')
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addStretch(1)
        return page

    def _page_tour_books(self) -> QWidget:
        page, lay = self._shell(
            'first_run.tour_books_title', 'Boekenplank en schrijven',
            'first_run.tour_books_text',
            'Je boeken staan op de Boekenplank. Open een boek om hoofdstukken te schrijven en ordenen. QuietWriter slaat tijdens het schrijven automatisch op; Versiegeschiedenis helpt je eerdere versies terug te vinden.',
        )
        lay.addStretch(1)
        return page

    def _page_tour_writing(self) -> QWidget:
        page, lay = self._shell(
            'first_run.tour_planning_title', 'Planning en Bewaarplaats',
            'first_run.tour_planning_text',
            "Planning houdt scènes, personages en notities bij. In de Bewaarplaats geldt: Don't kill your darlings. Mooie stukken die niet meer passen kun je bewaren, later terugvinden en opnieuw gebruiken.",
        )
        lay.addStretch(1)
        return page

    def _page_tour_finish(self) -> QWidget:
        page, lay = self._shell(
            'first_run.tour_finish_title', 'Meelezer, export en herstel',
            'first_run.tour_finish_text',
            'De optionele Meelezer geeft feedback op jouw tekst, maar schrijft hem niet voor je. Via Export maak je onder meer EPUB, PDF en Markdown. Integriteit & herstel en de Prullenbak helpen wanneer je iets wilt controleren of terughalen.',
        )
        tip = self._label(
            'first_run.tour_finish_tip',
            'Je hoeft dit niet allemaal te onthouden. QuietWriter houdt de interface rustig en je kunt instellingen later altijd aanpassen.',
        )
        tip.setObjectName('muted')
        tip.setWordWrap(True)
        lay.addWidget(tip)
        lay.addStretch(1)
        return page

    def _populate_dictionaries(self) -> None:
        locales: set[str] = set()
        roots = [
            Path(__file__).resolve().parents[2] / 'dictionaries',
            Path(r'C:/Program Files/ONLYOFFICE/DesktopEditors/dictionaries'),
            Path(r'C:/Program Files (x86)/ONLYOFFICE/DesktopEditors/dictionaries'),
            Path(r'C:/Program Files/LibreOffice/share/extensions'),
            Path(r'C:/Program Files (x86)/LibreOffice/share/extensions'),
            Path(r'C:/Program Files/OpenOffice 4/share/extensions'),
            Path(r'C:/Program Files (x86)/OpenOffice 4/share/extensions'),
        ]
        for root in roots:
            if not root.exists():
                continue
            try:
                for dic in root.rglob('*.dic'):
                    if dic.name.lower().startswith('hyph_'):
                        continue
                    value = dic.stem.replace('-', '_')
                    if len(value) in {2, 5, 6}:
                        locales.add(value)
            except (OSError, PermissionError):
                continue
        if not locales:
            locales.add('nl_NL')
        for locale in sorted(locales, key=lambda x: locale_label(x).casefold()):
            self.spell_language.addItem(locale_label(locale), locale)
        idx = self.spell_language.findData('nl_NL')
        if idx >= 0:
            self.spell_language.setCurrentIndex(idx)

    def _choose_workspace(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self,
            tr('startup.choose_workspace_title', 'Kies QuietWriter-werkmap'),
            self.workspace.text() or str(self.default_workspace),
        )
        if chosen:
            self.workspace.setText(chosen)

    def _update_nav(self, *_args) -> None:
        index = self.pages.currentIndex()
        total = self.pages.count()
        if not self.tour_enabled.isChecked() and index <= self.tour_choice_index:
            total = self.tour_choice_index + 1
        self.progress.setText(tr('first_run.progress', 'Stap {step} van {total}', step=index + 1, total=total))
        self.back_btn.setEnabled(index > 0)
        finish_here = index == total - 1 or (index == self.tour_choice_index and not self.tour_enabled.isChecked())
        self.next_btn.setText(tr('first_run.finish', 'Voltooien') if finish_here else tr('first_run.next', 'Volgende'))

    def _back(self) -> None:
        if self.pages.currentIndex() > 0:
            self.pages.setCurrentIndex(self.pages.currentIndex() - 1)

    def _next(self) -> None:
        index = self.pages.currentIndex()
        if index == self.tour_choice_index and not self.tour_enabled.isChecked():
            self._commit(tour_seen=False)
            self.accept()
            return
        if index < self.pages.count() - 1:
            self.pages.setCurrentIndex(index + 1)
            return
        self._commit(tour_seen=True)
        self.accept()

    def _skip(self) -> None:
        # Keep the current/default selections. This makes --first-run safe for
        # deliberate testing on an existing profile: Skip never resets it.
        self._commit(tour_seen=False)
        self.accept()

    def _commit(self, *, tour_seen: bool | None = None) -> None:
        workspace = str(normalize_workspace_path(self.workspace.text(), self.default_workspace))
        self.workspace.setText(workspace)
        self.settings.setValue('language', str(self.language.currentData() or 'nl'))
        self.settings.setValue('theme', self.theme.currentText() or 'Helder')
        self.settings.setValue('workspace', workspace)
        self.settings.setValue('spell_enabled', bool(self.spell_enabled.isChecked()))
        self.settings.setValue('spell_language', str(self.spell_language.currentData() or 'nl_NL'))
        self.settings.setValue('auto_update_check', bool(self.auto_update_check.isChecked()))
        if self.ai_ollama.isChecked():
            self.settings.setValue('ai_enabled', True)
            self.settings.setValue('ai_provider', 'ollama')
        elif self.ai_openrouter.isChecked():
            self.settings.setValue('ai_enabled', True)
            self.settings.setValue('ai_provider', 'openrouter')
        else:
            self.settings.setValue('ai_enabled', False)
        self.settings.setValue('first_run_done', True)
        self.settings.remove('first_run_requested')
        if tour_seen is None:
            tour_seen = bool(self.tour_enabled.isChecked() and self.pages.currentIndex() >= self.tour_start_index)
        self.settings.setValue('first_run_tour_seen', bool(tour_seen))
        self.settings.sync()
