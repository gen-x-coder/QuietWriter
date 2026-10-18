"""Instellingen → Vertalingen (1.7): QuietWriter vertalen zonder technische kennis.

Links een rustige lijst van alle teksten (alleen kiezen, niet typen), rechts
één tekst tegelijk: de bekende taal groot bovenaan, daaronder een ruim
invoerveld voor je vertaling, met Vorige/Volgende. Dezelfde Nederlandse tekst
op meerdere plekken (bijvoorbeeld "Bijhouden") vertaal je één keer. Opslaan zet de vertaling in de werkmap
(``translations/<code>.json``); na een herstart staat de taal bij
Programmataal. Exporteren maakt één bestand om te mailen.

- Voor een meegeleverde taal (nl, en, de, fr, es) bewaart QuietWriter alleen
  wat je anders hebt dan de meegeleverde tekst. Zo blijven latere verbeteringen
  in QuietWriter zelf gewoon doorkomen.
- Een nieuwe taal wordt helemaal bewaard; wat nog leeg is, toont QuietWriter in
  het Engels.
- ``{naam}``-plekken moeten in de vertaling terugkomen. Een fout wordt
  gemarkeerd en blokkeert niets.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from dataclasses import dataclass, field

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from .. import __version__
from ..i18n import (
    BUILTIN_CODES, META_KEY, available_languages, builtin_locale, set_user_translation_dir, tr,
    user_locale, user_locale_meta, user_translation_dir, user_translation_path,
)
from ..storage import _safe_atomic_write_text
from .dialog_notices import notice_information, notice_warning

PLACEHOLDER_RE = re.compile(r'\{[^{}]+\}')
NEW_LANGUAGE = '__new__'
CODE_RE = re.compile(r'^[a-z]{2,3}$')


def placeholders(text: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(text or ''))


def reference_keys() -> list[str]:
    keys = set(builtin_locale('nl')) | set(builtin_locale('en'))
    return sorted(k for k in keys if not k.startswith('_'))


def effective_translation(code: str) -> dict[str, str]:
    data = dict(builtin_locale(code)) if code in BUILTIN_CODES else {}
    data.update(user_locale(code))
    return {k: v for k, v in data.items() if not k.startswith('_')}


def translation_to_save(code: str, values: dict[str, str]) -> dict[str, str]:
    """Wat er in het gebruikersbestand komt: bij een meegeleverde taal alleen de verschillen."""
    cleaned = {k: v for k, v in values.items() if isinstance(v, str) and v.strip() != ''}
    if code in BUILTIN_CODES:
        base = builtin_locale(code)
        cleaned = {k: v for k, v in cleaned.items() if base.get(k) != v}
    return dict(sorted(cleaned.items()))


def placeholder_problems(reference: dict[str, str], values: dict[str, str]) -> list[str]:
    return sorted(k for k, v in values.items()
                  if v and k in reference and placeholders(v) != placeholders(reference[k]))


@dataclass
class Entry:
    """Eén te vertalen tekst; kan voor meerdere sleutels gelden."""
    keys: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.keys[0]


def build_entries(keys: list[str], dutch: dict[str, str], target: dict[str, str],
                  english: dict[str, str] | None = None) -> list[Entry]:
    """Groepeer sleutels met dezelfde Nederlandse én Engelse tekst én dezelfde vertaling.

    Zo vertaalt iemand "Bijhouden" (Track) één keer. Betekent dezelfde
    Nederlandse tekst op verschillende plekken iets anders ("Toevoegen" is soms
    Add, soms Insert), dan blijven ze los.
    """
    english = english or {}
    groups: dict[tuple[str, str], Entry] = {}
    order: list[Entry] = []
    for key in keys:
        text = dutch.get(key)
        if not text:
            entry = Entry([key]); order.append(entry); continue
        group = (text, english.get(key, ''), target.get(key, ''))
        if group in groups:
            groups[group].keys.append(key)
        else:
            entry = Entry([key]); groups[group] = entry; order.append(entry)
    return order


class TranslationsPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._loading = False
        self._dirty = False
        self.values: dict[str, str] = {}
        self.entries: list[Entry] = []
        self._current: Entry | None = None
        self._reference: dict[str, str] = {}
        self._nl: dict[str, str] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 0, 28, 24)
        root.setSpacing(12)
        title = QLabel(tr('translations.title', 'Vertalingen')); title.setObjectName('settingsPageTitle')
        intro = QLabel(tr('translations.intro_170', 'Help QuietWriter vertalen of verbeter een bestaande vertaling. Kies links een tekst; rechts zie je hem in een taal die je kent en typ je de vertaling. Met Vorige en Volgende (of Ctrl+Enter) ga je door de lijst. Na opslaan en een herstart kies je de taal bij Algemeen → Programmataal.'))
        intro.setObjectName('settingsPageIntro'); intro.setWordWrap(True)
        root.addWidget(title); root.addWidget(intro)

        choose = QHBoxLayout(); choose.setSpacing(8)
        self.reference = QComboBox()
        for code, name in available_languages():
            if code in BUILTIN_CODES:
                self.reference.addItem(name, code)
        self.reference.setCurrentIndex(max(0, self.reference.findData('en')))
        self.target = QComboBox(); self.target.setMinimumWidth(220)
        choose.addWidget(QLabel(tr('translations.target_170', 'Ik vertaal naar'))); choose.addWidget(self.target)
        choose.addSpacing(16)
        choose.addWidget(QLabel(tr('translations.reference_170', 'Ik lees mee in'))); choose.addWidget(self.reference)
        choose.addStretch(1)
        root.addLayout(choose)

        self.new_row = QWidget()
        new_layout = QHBoxLayout(self.new_row); new_layout.setContentsMargins(0, 0, 0, 0); new_layout.setSpacing(8)
        self.new_name = QLineEdit(); self.new_name.setPlaceholderText(tr('translations.new_name', 'Naam van de taal, bijvoorbeeld Italiano'))
        self.new_code = QLineEdit(); self.new_code.setPlaceholderText(tr('translations.new_code', 'Code, bijvoorbeeld it')); self.new_code.setMaxLength(3); self.new_code.setFixedWidth(170)
        new_layout.addWidget(self.new_name, 1); new_layout.addWidget(self.new_code)
        root.addWidget(self.new_row)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 0, 0); ll.setSpacing(8)
        self.filter_text = QLineEdit(); self.filter_text.setPlaceholderText(tr('translations.search', 'Zoek in de teksten…')); self.filter_text.setClearButtonEnabled(True)
        self.only_missing = QCheckBox(tr('translations.only_missing', 'Alleen wat nog ontbreekt of een fout heeft'))
        self.status = QLabel(''); self.status.setObjectName('muted'); self.status.setWordWrap(True)
        self.list = QListWidget(); self.list.setObjectName('translationsList')
        self.list.setUniformItemSizes(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.ElideRight)
        ll.addWidget(self.filter_text); ll.addWidget(self.only_missing); ll.addWidget(self.status); ll.addWidget(self.list, 1)

        self.card = QFrame(); self.card.setObjectName('wizardCard')
        cl = QVBoxLayout(self.card); cl.setContentsMargins(20, 16, 20, 16); cl.setSpacing(8)
        self.position = QLabel(''); self.position.setObjectName('muted')
        self.ref_title = QLabel(''); self.ref_title.setObjectName('settingsSectionTitle')
        self.ref_text = QLabel(''); self.ref_text.setObjectName('translationsReference'); self.ref_text.setWordWrap(True)
        self.ref_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = self.ref_text.font(); font.setPointSizeF(font.pointSizeF() + 2); self.ref_text.setFont(font)
        self.dutch_text = QLabel(''); self.dutch_text.setObjectName('muted'); self.dutch_text.setWordWrap(True)
        self.target_title = QLabel(''); self.target_title.setObjectName('settingsSectionTitle')
        self.editor = QPlainTextEdit(); self.editor.setObjectName('translationsEditor')
        self.editor.setMinimumHeight(90); self.editor.setMaximumHeight(180); self.editor.setTabChangesFocus(True)
        self.placeholder_hint = QLabel(''); self.placeholder_hint.setObjectName('muted'); self.placeholder_hint.setWordWrap(True)
        self.shared = QLabel(''); self.shared.setObjectName('muted'); self.shared.setWordWrap(True)
        self.where = QLabel(''); self.where.setObjectName('muted'); self.where.setWordWrap(True)
        nav = QHBoxLayout(); nav.setSpacing(8)
        self.prev_btn = QPushButton(tr('translations.previous', '← Vorige')); self.prev_btn.setObjectName('secondaryButton')
        self.next_btn = QPushButton(tr('translations.next', 'Volgende →')); self.next_btn.setObjectName('secondaryButton')
        self.next_open_btn = QPushButton(tr('translations.next_open', 'Volgende die nog ontbreekt')); self.next_open_btn.setObjectName('secondaryButton')
        nav.addWidget(self.prev_btn); nav.addWidget(self.next_btn); nav.addStretch(1); nav.addWidget(self.next_open_btn)
        for widget in (self.position, self.ref_title, self.ref_text, self.dutch_text):
            cl.addWidget(widget)
        cl.addSpacing(8)
        cl.addWidget(self.target_title); cl.addWidget(self.editor); cl.addWidget(self.placeholder_hint)
        cl.addWidget(self.shared); cl.addWidget(self.where)
        cl.addStretch(1)
        cl.addLayout(nav)
        split.addWidget(left); split.addWidget(self.card)
        split.setStretchFactor(0, 2); split.setStretchFactor(1, 3)
        root.addWidget(split, 1)

        buttons = QHBoxLayout(); buttons.setSpacing(8)
        self.import_btn = QPushButton(tr('translations.import', 'Importeren…')); self.import_btn.setObjectName('secondaryButton')
        self.export_btn = QPushButton(tr('translations.export', 'Exporteren…')); self.export_btn.setObjectName('secondaryButton')
        self.folder_btn = QPushButton(tr('translations.open_folder', 'Map openen')); self.folder_btn.setObjectName('secondaryButton')
        self.save_btn = QPushButton(tr('translations.save', 'Vertaling opslaan')); self.save_btn.setObjectName('primaryButton')
        for b in (self.import_btn, self.export_btn, self.folder_btn):
            buttons.addWidget(b)
        buttons.addStretch(1); buttons.addWidget(self.save_btn)
        root.addLayout(buttons)

        self.reference.currentIndexChanged.connect(self._show_current)
        self.target.currentIndexChanged.connect(self._reload)
        self.filter_text.textChanged.connect(self._apply_filter)
        self.only_missing.toggled.connect(self._apply_filter)
        self.list.currentRowChanged.connect(self._row_changed)
        self.editor.textChanged.connect(self._editor_changed)
        self.prev_btn.clicked.connect(lambda: self._step(-1))
        self.next_btn.clicked.connect(lambda: self._step(1))
        self.next_open_btn.clicked.connect(self._next_open)
        QShortcut(QKeySequence('Ctrl+Return'), self.editor, activated=lambda: self._step(1))
        QShortcut(QKeySequence('Ctrl+Enter'), self.editor, activated=lambda: self._step(1))
        self.new_code.textChanged.connect(self._update_status)
        self.save_btn.clicked.connect(self.save)
        self.export_btn.clicked.connect(self.export_file)
        self.import_btn.clicked.connect(self.import_file)
        self.folder_btn.clicked.connect(self.open_folder)
        self._fill_targets()
        self._reload()

    # ------------------------------------------------------------------ data
    def _fill_targets(self, select: str | None = None):
        self.target.blockSignals(True)
        self.target.clear()
        for code, name in available_languages():
            self.target.addItem(f'{name} ({code})', code)
        self.target.addItem(tr('translations.new_language', 'Nieuwe taal…'), NEW_LANGUAGE)
        index = self.target.findData(select) if select else -1
        if index < 0:
            index = self.target.findData('nl')
        self.target.setCurrentIndex(max(0, index))
        self.target.blockSignals(False)

    def target_code(self) -> str:
        code = str(self.target.currentData() or '')
        if code == NEW_LANGUAGE:
            return self.new_code.text().strip().lower()
        return code

    def current_values(self) -> dict[str, str]:
        return dict(self.values)

    def set_translation(self, key: str, text: str) -> None:
        """Vul de vertaling van ``key`` (en zijn gelijke plekken) in, zoals de gebruiker zou doen."""
        for row, entry in enumerate(self.entries):
            if key in entry.keys:
                self.list.setCurrentRow(row)
                self.editor.setPlainText(text)
                return
        raise KeyError(key)

    def _reload(self, *_):
        self._loading = True
        is_new = self.target.currentData() == NEW_LANGUAGE
        self.new_row.setVisible(is_new)
        code = '' if is_new else self.target_code()
        self._nl = {k: v for k, v in builtin_locale('nl').items() if not k.startswith('_')}
        target = effective_translation(code) if code else {}
        keys = reference_keys()
        self.values = {k: target.get(k, '') for k in keys}
        self.entries = build_entries(keys, self._nl, self.values, builtin_locale('en'))
        self.list.clear()
        for entry in self.entries:
            item = QListWidgetItem()
            self.list.addItem(item)
        self._loading = False
        self._dirty = False
        self._refresh_items()
        self._apply_filter()
        if self.entries:
            self.list.setCurrentRow(self._first_visible_row())

    def _entry_state(self, entry: Entry) -> str:
        text = self.values.get(entry.key, '')
        if not text.strip():
            return 'missing'
        if placeholders(text) != placeholders(self._nl.get(entry.key, '')):
            return 'problem'
        return 'done'

    def _refresh_items(self, rows=None):
        reference_code = str(self.reference.currentData() or 'en')
        self._reference = {k: v for k, v in builtin_locale(reference_code).items() if not k.startswith('_')}
        marks = {'missing': '○', 'problem': '!', 'done': '✓'}
        for row in (rows if rows is not None else range(len(self.entries))):
            entry = self.entries[row]
            ref = self._reference.get(entry.key) or self._nl.get(entry.key, '')
            first_line = ' '.join(ref.split())
            item = self.list.item(row)
            item.setText(f'{marks[self._entry_state(entry)]}  {first_line}')
            item.setToolTip(ref)

    # ------------------------------------------------------------------ bewerken
    def _row_changed(self, row: int):
        self._current = self.entries[row] if 0 <= row < len(self.entries) else None
        self._show_current()

    def _show_current(self, *_):
        entry = self._current
        if entry is None:
            self.card.setEnabled(False)
            return
        self.card.setEnabled(True)
        reference_code = str(self.reference.currentData() or 'en')
        if not self._reference or self.reference.currentData() != getattr(self, '_reference_code', None):
            self._reference_code = reference_code
            self._refresh_items()
        visible = [r for r in range(self.list.count()) if not self.list.isRowHidden(r)]
        row = self.entries.index(entry)
        position = (visible.index(row) + 1) if row in visible else 0
        self.position.setText(tr('translations.position', 'Tekst {n} van {total}', n=position, total=len(visible)))
        self.ref_title.setText(self.reference.currentText().upper())
        self.ref_text.setText(self._reference.get(entry.key) or self._nl.get(entry.key, ''))
        dutch = self._nl.get(entry.key, '')
        show_dutch = reference_code != 'nl' and dutch and dutch != self.ref_text.text()
        self.dutch_text.setVisible(bool(show_dutch))
        self.dutch_text.setText(tr('translations.dutch_original', 'Origineel (Nederlands): {text}', text=dutch))
        self.target_title.setText((self.target.currentText() if self.target.currentData() != NEW_LANGUAGE
                                   else (self.new_name.text() or tr('translations.new_language_column', 'Nieuwe taal'))).upper())
        self._loading = True
        self.editor.setPlainText(self.values.get(entry.key, ''))
        self._loading = False
        wanted = placeholders(dutch)
        self.placeholder_hint.setVisible(bool(wanted))
        self.placeholder_hint.setText(tr('translations.placeholders_hint', 'Neem deze plekken letterlijk over: {names}. QuietWriter zet daar later een naam of getal neer.', names='  '.join(wanted)))
        self.shared.setVisible(len(entry.keys) > 1)
        self.shared.setText(tr('translations.shared', 'Deze tekst staat op {count} plekken in QuietWriter. Je vertaling geldt voor alle plekken.', count=len(entry.keys)))
        self.where.setText(tr('translations.where', 'Technische naam: {keys}', keys=', '.join(entry.keys)))
        self.prev_btn.setEnabled(position > 1)
        self.next_btn.setEnabled(0 < position < len(visible))
        self._mark_problem()

    def _mark_problem(self):
        entry = self._current
        problem = entry is not None and self._entry_state(entry) == 'problem'
        self.editor.setProperty('invalid', problem)
        self.editor.style().unpolish(self.editor); self.editor.style().polish(self.editor)
        if problem:
            self.placeholder_hint.setText(tr('translations.placeholder_problem', 'Neem deze plekken precies over: {names}',
                                             names='  '.join(placeholders(self._nl.get(entry.key, ''))) or '—'))

    def _editor_changed(self):
        if self._loading or self._current is None:
            return
        text = self.editor.toPlainText()
        for key in self._current.keys:
            self.values[key] = text
        self._dirty = True
        self._refresh_items([self.entries.index(self._current)])
        self._mark_problem()
        self._update_status()

    def _first_visible_row(self) -> int:
        for row in range(self.list.count()):
            if not self.list.isRowHidden(row):
                return row
        return -1

    def _step(self, direction: int):
        row = self.list.currentRow() + direction
        while 0 <= row < self.list.count() and self.list.isRowHidden(row):
            row += direction
        if 0 <= row < self.list.count():
            self.list.setCurrentRow(row)
            self.editor.setFocus()

    def _next_open(self):
        start = self.list.currentRow()
        for offset in range(1, len(self.entries) + 1):
            row = (start + offset) % len(self.entries)
            if not self.list.isRowHidden(row) and self._entry_state(self.entries[row]) != 'done':
                self.list.setCurrentRow(row)
                self.editor.setFocus()
                return

    def _apply_filter(self, *_):
        needle = self.filter_text.text().strip().casefold()
        only_missing = self.only_missing.isChecked()
        for row, entry in enumerate(self.entries):
            ref = self._reference.get(entry.key) or self._nl.get(entry.key, '')
            text = self.values.get(entry.key, '')
            hide = only_missing and self._entry_state(entry) == 'done'
            if needle and needle not in ref.casefold() and needle not in text.casefold() \
                    and needle not in self._nl.get(entry.key, '').casefold() and not any(needle in k for k in entry.keys):
                hide = True
            self.list.setRowHidden(row, bool(hide))
        if self.list.currentRow() < 0 or self.list.isRowHidden(self.list.currentRow()):
            first = self._first_visible_row()
            if first >= 0:
                self.list.setCurrentRow(first)
        self._update_status()
        self._show_current()

    def _update_status(self, *_):
        total = len(self.entries)
        done = sum(1 for e in self.entries if self._entry_state(e) == 'done')
        problems = sum(1 for e in self.entries if self._entry_state(e) == 'problem')
        text = tr('translations.status_170', '{done} van {total} teksten vertaald', done=done, total=total)
        if problems:
            text += ' · ' + tr('translations.status_problems', '{count} met een fout in de plekken tussen accolades', count=problems)
        if self._dirty:
            text += ' · ' + tr('translations.status_unsaved', 'niet opgeslagen')
        self.status.setText(text)

    # ------------------------------------------------------------------ acties
    def _valid_code(self) -> str | None:
        code = self.target_code()
        if CODE_RE.match(code or ''):
            return code
        notice_warning(self, tr('translations.title', 'Vertalingen'),
                       tr('translations.bad_code', 'Vul een taalcode van twee of drie letters in, bijvoorbeeld it voor Italiaans.'))
        return None

    def _payload(self, code: str, *, complete: bool) -> dict:
        values = self.current_values()
        body = ({k: v for k, v in sorted(values.items()) if v.strip()} if complete
                else translation_to_save(code, values))
        name = self.new_name.text().strip() if self.target.currentData() == NEW_LANGUAGE else \
            (user_locale_meta(code).get('name') or dict(available_languages()).get(code, code))
        return {META_KEY: {'code': code, 'name': name, 'quietwriter': __version__}, **body}

    def _ensure_folder(self) -> Path | None:
        folder = user_translation_dir()
        if folder is None:
            workspace = str(self.settings.value('workspace', '') or '') if self.settings is not None else ''
            if not workspace:
                return None
            folder = Path(workspace) / 'translations'
            set_user_translation_dir(folder)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def save(self) -> bool:
        code = self._valid_code()
        if not code:
            return False
        if self._ensure_folder() is None:
            notice_warning(self, tr('translations.title', 'Vertalingen'), tr('translations.no_workspace', 'Er is nog geen werkmap ingesteld.'))
            return False
        payload = self._payload(code, complete=False)
        _safe_atomic_write_text(user_translation_path(code), json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
        set_user_translation_dir(user_translation_dir())   # cache legen
        current_key = self._current.key if self._current else None
        self._fill_targets(select=code)
        self._reload()
        if current_key:
            for row, entry in enumerate(self.entries):
                if current_key in entry.keys:
                    self.list.setCurrentRow(row)
                    break
        notice_information(self, tr('translations.title', 'Vertalingen'),
                           tr('translations.saved', 'De vertaling is opgeslagen. Na een herstart kies je de taal bij Algemeen → Programmataal.'))
        return True

    def export_file(self):
        code = self._valid_code()
        if not code:
            return
        default = str(Path.home() / f'quietwriter-{code}.json')
        path, _ = QFileDialog.getSaveFileName(self, tr('translations.export', 'Exporteren…'), default, 'JSON (*.json)')
        if not path:
            return
        payload = self._payload(code, complete=True)
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        notice_information(self, tr('translations.title', 'Vertalingen'),
                           tr('translations.exported', 'Het bestand is gemaakt. Mail het naar de maker van QuietWriter; dan kan de vertaling in een volgende versie mee.'))

    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('translations.import', 'Importeren…'), str(Path.home()), 'JSON (*.json)')
        if not path:
            return
        self.load_file(Path(path))

    def load_file(self, path: Path) -> bool:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            notice_warning(self, tr('translations.title', 'Vertalingen'), tr('translations.import_bad', 'Dit bestand is geen QuietWriter-vertaling.'))
            return False
        meta = data.get(META_KEY) if isinstance(data.get(META_KEY), dict) else {}
        code = str(meta.get('code') or path.stem.split('-')[-1]).lower()
        if not CODE_RE.match(code):
            notice_warning(self, tr('translations.title', 'Vertalingen'), tr('translations.import_bad', 'Dit bestand is geen QuietWriter-vertaling.'))
            return False
        index = self.target.findData(code)
        if index >= 0:
            self.target.setCurrentIndex(index)
        else:
            self.target.setCurrentIndex(self.target.findData(NEW_LANGUAGE))
            self.new_code.setText(code)
            self.new_name.setText(str(meta.get('name') or code))
        for key in list(self.values):
            value = data.get(key)
            if isinstance(value, str):
                self.values[key] = value
        self._dirty = True
        self._refresh_items()
        self._apply_filter()
        return True

    def open_folder(self):
        folder = self._ensure_folder()
        if folder is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
