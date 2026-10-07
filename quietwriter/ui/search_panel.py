
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget
)
from ..i18n import tr
from .panel_help import PanelHelp

class SearchPanel(QWidget):
    open_match = Signal(object)
    request_next = Signal()
    request_replace = Signal()
    request_replace_all = Signal()

    def __init__(self, settings=None):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18)
        self.panel_help = PanelHelp(settings, 'search', tr('search.title', 'Zoeken en vervangen'), tr('panel_help.search', 'Zoek in dit hoofdstuk, deze sectie of het hele boek. Vervang treffers één voor één, of allemaal tegelijk met Alles vervangen.'))
        self.scope = QComboBox(); self.scope.addItem(tr('search.scope.chapter', 'Huidig hoofdstuk'), 'chapter'); self.scope.addItem(tr('search.scope.section', 'Huidige sectie'), 'section'); self.scope.addItem(tr('search.scope.book', 'Hele boek'), 'book')
        self.query = QLineEdit(); self.query.setPlaceholderText(tr('search.placeholder', 'Zoeken…')); self.query.setClearButtonEnabled(True)
        self.replace = QLineEdit(); self.replace.setPlaceholderText(tr('search.replace_placeholder', 'Vervangen door…')); self.replace.setClearButtonEnabled(True)
        options = QHBoxLayout()
        self.case_sensitive = QCheckBox(tr('search.case_sensitive', 'Hoofdlettergevoelig'))
        self.whole_word = QCheckBox(tr('search.whole_word', 'Heel woord'))
        options.addWidget(self.case_sensitive); options.addWidget(self.whole_word); options.addStretch()
        self.summary = QLabel(''); self.summary.setObjectName('muted')
        self.empty = QLabel(tr('search.no_results', 'Geen resultaten gevonden.')); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter); self.empty.hide()
        self.results = QListWidget()
        # Mouse navigation is intentionally single-click: result rows are
        # navigation targets, not objects that need a separate selection step.
        # itemActivated remains for Enter/Return keyboard activation.
        self.results.itemClicked.connect(self._open_result_item)
        self.results.itemActivated.connect(self._open_result_item)
        buttons = QHBoxLayout()
        self.next_btn = QPushButton(tr('search.next','Volgende')); self.next_btn.clicked.connect(self.request_next.emit)
        self.replace_btn = QPushButton(tr('search.replace','Vervangen')); self.replace_btn.clicked.connect(self.request_replace.emit)
        self.replace_all_btn = QPushButton(tr('search.replace_all','Alles vervangen')); self.replace_all_btn.clicked.connect(self.request_replace_all.emit)
        buttons.addWidget(self.next_btn); buttons.addWidget(self.replace_btn); buttons.addWidget(self.replace_all_btn)
        lay.addWidget(self.panel_help); lay.addWidget(self.scope); lay.addWidget(self.query); lay.addLayout(options)
        lay.addWidget(self.summary); lay.addWidget(self.empty); lay.addWidget(self.results, 1)
        lay.addWidget(QLabel(tr('search.replace_label', 'Vervangen door'))); lay.addWidget(self.replace); lay.addLayout(buttons)
        # Creation order differs from visual order because the replacement field
        # is constructed before the option row. Keep Tab/Shift+Tab predictable.
        tab_order = (
            self.scope, self.query, self.case_sensitive, self.whole_word,
            self.results, self.replace, self.next_btn, self.replace_btn,
            self.replace_all_btn,
        )
        for first, second in zip(tab_order, tab_order[1:], strict=False):
            QWidget.setTabOrder(first, second)


    def _open_result_item(self, item):
        if item is not None:
            self.open_match.emit(item.data(Qt.UserRole))

    def show_results(self, rows):
        self.results.clear()
        active = bool(self.query.text().strip())
        self.empty.setVisible(active and not rows)
        self.results.setVisible(bool(rows) or not active)
        self.summary.setText((tr('search.result.one', '{count} resultaat', count=len(rows)) if len(rows) == 1 else tr('search.result.many', '{count} resultaten', count=len(rows))) if active else '')
        for row in rows:
            cid, title, snippet, start, length = row
            item = QListWidgetItem(f'{title}\n{snippet}')
            item.setData(Qt.UserRole, (cid, start, length))
            self.results.addItem(item)
