from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractButton, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ..dictionary_catalog import locale_label
from ..i18n import set_locale, tr
from ..themes import THEMES
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
        self.progress.setText(tr('first_run.progress', 'Stap {step} van {total}', step=index + 1, total=total))
        self.back_btn.setEnabled(index > 0)
        self.next_btn.setText(tr('first_run.finish', 'Voltooien') if index == total - 1 else tr('first_run.next', 'Volgende'))

    def _back(self) -> None:
        if self.pages.currentIndex() > 0:
            self.pages.setCurrentIndex(self.pages.currentIndex() - 1)

    def _next(self) -> None:
        if self.pages.currentIndex() < self.pages.count() - 1:
            self.pages.setCurrentIndex(self.pages.currentIndex() + 1)
            return
        self._commit()
        self.accept()

    def _skip(self) -> None:
        # Keep the current/default selections. This makes --first-run safe for
        # deliberate testing on an existing profile: Skip never resets it.
        self._commit()
        self.accept()

    def _commit(self) -> None:
        workspace = str(normalize_workspace_path(self.workspace.text(), self.default_workspace))
        self.workspace.setText(workspace)
        self.settings.setValue('language', str(self.language.currentData() or 'nl'))
        self.settings.setValue('theme', self.theme.currentText() or 'Helder')
        self.settings.setValue('workspace', workspace)
        self.settings.setValue('spell_enabled', bool(self.spell_enabled.isChecked()))
        self.settings.setValue('spell_language', str(self.spell_language.currentData() or 'nl_NL'))
        if self.ai_ollama.isChecked():
            self.settings.setValue('ai_enabled', True)
            self.settings.setValue('ai_provider', 'ollama')
        elif self.ai_openrouter.isChecked():
            self.settings.setValue('ai_enabled', True)
            self.settings.setValue('ai_provider', 'openrouter')
        else:
            self.settings.setValue('ai_enabled', False)
        self.settings.setValue('first_run_done', True)
        self.settings.sync()
