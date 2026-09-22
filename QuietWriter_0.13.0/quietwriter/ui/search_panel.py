
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget
)
from ..i18n import tr

class SearchPanel(QWidget):
    open_match = Signal(object)
    request_next = Signal()
    request_replace = Signal()
    request_replace_all = Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(18,18,18,18)
        lab = QLabel(tr('search.title', 'Zoeken en vervangen')); lab.setObjectName('sectionTitle')
        self.scope = QComboBox(); self.scope.addItems(['Huidig hoofdstuk', 'Huidige sectie', 'Hele boek'])
        self.query = QLineEdit(); self.query.setPlaceholderText('Zoeken…'); self.query.setClearButtonEnabled(True)
        self.replace = QLineEdit(); self.replace.setPlaceholderText('Vervangen door…'); self.replace.setClearButtonEnabled(True)
        options = QHBoxLayout()
        self.case_sensitive = QCheckBox('Hoofdlettergevoelig')
        self.whole_word = QCheckBox('Heel woord')
        options.addWidget(self.case_sensitive); options.addWidget(self.whole_word); options.addStretch()
        self.summary = QLabel(''); self.summary.setObjectName('muted')
        self.empty = QLabel(tr('search.no_results', 'Geen resultaten gevonden.')); self.empty.setObjectName('muted'); self.empty.setAlignment(Qt.AlignCenter); self.empty.hide()
        self.results = QListWidget()
        self.results.itemActivated.connect(lambda i: self.open_match.emit(i.data(Qt.UserRole)))
        buttons = QHBoxLayout()
        self.next_btn = QPushButton(tr('search.next','Volgende')); self.next_btn.clicked.connect(self.request_next.emit)
        self.replace_btn = QPushButton(tr('search.replace','Vervangen')); self.replace_btn.clicked.connect(self.request_replace.emit)
        self.replace_all_btn = QPushButton(tr('search.replace_all','Alles vervangen')); self.replace_all_btn.clicked.connect(self.request_replace_all.emit)
        buttons.addWidget(self.next_btn); buttons.addWidget(self.replace_btn); buttons.addWidget(self.replace_all_btn)
        lay.addWidget(lab); lay.addWidget(self.scope); lay.addWidget(self.query); lay.addLayout(options)
        lay.addWidget(self.summary); lay.addWidget(self.empty); lay.addWidget(self.results, 1)
        lay.addWidget(QLabel('Vervangen door')); lay.addWidget(self.replace); lay.addLayout(buttons)

    def show_results(self, rows):
        self.results.clear()
        active = bool(self.query.text().strip())
        self.empty.setVisible(active and not rows)
        self.results.setVisible(bool(rows) or not active)
        self.summary.setText((f'{len(rows)} resultaat' if len(rows) == 1 else f'{len(rows)} resultaten') if active else '')
        for row in rows:
            cid, title, snippet, start, length = row
            item = QListWidgetItem(f'{title}\n{snippet}')
            item.setData(Qt.UserRole, (cid, start, length))
            self.results.addItem(item)
