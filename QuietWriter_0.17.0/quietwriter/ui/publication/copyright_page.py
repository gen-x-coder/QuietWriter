from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget


CLAUSE_LABELS = {
    'rights_reserved': 'Alle rechten voorbehouden',
    'fiction': 'Fictieverklaring',
    'moral_rights': 'Auteursvermelding / morele rechten',
    'external_content': 'Externe inhoud en links',
    'designations': 'Merken en handelsnamen',
}


class CopyrightPage(QWidget):
    saveRequested = Signal(dict)
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget(); root = QVBoxLayout(body); root.setContentsMargins(38,28,38,28); root.setSpacing(14)
        title = QLabel('Copyright'); title.setObjectName('title'); root.addWidget(title)
        info = QLabel('Vul alleen in wat voor jouw uitgave van toepassing is. De voorbeeldteksten zijn aanpasbaar en zijn geen juridisch advies.')
        info.setObjectName('muted'); info.setWordWrap(True); root.addWidget(info)
        form = QFormLayout(); form.setHorizontalSpacing(24); form.setVerticalSpacing(12)
        self.author = QLineEdit(); self.edition = QComboBox(); self.edition.setEditable(True); self.edition.addItems(['Eerste editie','Tweede editie','Herziene editie'])
        self.year = QLineEdit(); self.publisher = QLineEdit()
        form.addRow('Auteursnaam / pseudoniem', self.author); form.addRow('Editie', self.edition); form.addRow('Jaar van publicatie', self.year); form.addRow('Uitgever / imprint', self.publisher)
        root.addLayout(form)
        root.addWidget(self._section('ISBNs'))
        grid = QGridLayout(); self.isbn = {}
        for i,(key,label) in enumerate([('isbn_epub','EPUB'),('isbn_kindle','Kindle'),('isbn_paperback','Paperback'),('isbn_hardcover','Hardcover'),('isbn_pdf','PDF')]):
            edit=QLineEdit(); edit.setPlaceholderText('000-0-00-000000-0'); self.isbn[key]=edit
            box=QWidget(); bl=QHBoxLayout(box); bl.setContentsMargins(0,0,0,0); lab=QLabel(label); lab.setMinimumWidth(82); bl.addWidget(lab); bl.addWidget(edit,1)
            grid.addWidget(box, i//2, i%2)
        root.addLayout(grid)
        root.addWidget(self._section('Clausules'))
        self.clauses = {}
        for key,label in CLAUSE_LABELS.items():
            cb=QCheckBox(label); text=QTextEdit(); text.setMinimumHeight(76); text.setMaximumHeight(118); text.setPlaceholderText('Tekst van deze clausule')
            self.clauses[key]=(cb,text); cb.toggled.connect(lambda *_: self.changed.emit()); text.textChanged.connect(lambda *_: self.changed.emit()); root.addWidget(cb); root.addWidget(text)
        for edit in (self.author, self.year, self.publisher): edit.textEdited.connect(lambda *_: self.changed.emit())
        self.edition.currentTextChanged.connect(lambda *_: self.changed.emit())
        for edit in self.isbn.values(): edit.textEdited.connect(lambda *_: self.changed.emit())
        buttons=QHBoxLayout(); buttons.addStretch(); save=QPushButton('Opslaan'); save.setObjectName('primaryButton'); save.clicked.connect(self._save); buttons.addWidget(save); root.addLayout(buttons); root.addStretch()
        scroll.setWidget(body); outer.addWidget(scroll)

    def _section(self,text):
        label=QLabel(text); label.setObjectName('sectionTitle'); return label

    def set_data(self, data: dict):
        self.author.setText(str(data.get('author',''))); self.edition.setCurrentText(str(data.get('edition','Eerste editie'))); self.year.setText(str(data.get('year',''))); self.publisher.setText(str(data.get('publisher','')))
        for key,edit in self.isbn.items(): edit.setText(str(data.get(key,'')))
        clauses=data.get('clauses') or {}
        for key,(cb,text) in self.clauses.items():
            row=clauses.get(key) or {}; cb.setChecked(bool(row.get('enabled',False))); text.setPlainText(str(row.get('text','')))

    def data(self):
        return {
            'author':self.author.text().strip(),'edition':self.edition.currentText().strip(),'year':self.year.text().strip(),'publisher':self.publisher.text().strip(),
            **{key:edit.text().strip() for key,edit in self.isbn.items()},
            'clauses':{key:{'enabled':cb.isChecked(),'text':text.toPlainText().strip()} for key,(cb,text) in self.clauses.items()},
        }

    def _save(self): self.saveRequested.emit(self.data())
