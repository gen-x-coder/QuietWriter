from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget

from ...i18n import tr


CLAUSE_LABEL_KEYS = {
    'rights_reserved': 'publication.copyright.rights_reserved',
    'fiction': 'publication.copyright.fiction',
    'moral_rights': 'publication.copyright.moral_rights',
    'external_content': 'publication.copyright.external_content',
    'designations': 'publication.copyright.designations',
}



class CopyrightPage(QWidget):
    saveRequested = Signal(dict)
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget(); root = QVBoxLayout(body); root.setContentsMargins(38,28,38,28); root.setSpacing(14)
        title = QLabel(tr('publication.copyright.title', 'Copyright')); title.setObjectName('title'); root.addWidget(title)
        info = QLabel(tr('publication.copyright.info', 'Vul alleen in wat voor jouw uitgave van toepassing is. De voorbeeldteksten zijn aanpasbaar en zijn geen juridisch advies.'))
        info.setObjectName('muted'); info.setWordWrap(True); root.addWidget(info)
        form = QFormLayout(); form.setHorizontalSpacing(24); form.setVerticalSpacing(12)
        self.author = QLineEdit(); self.edition = QComboBox(); self.edition.setEditable(True)
        self._edition_entries = [
            ('Eerste editie', tr('publication.edition.first', 'Eerste editie')),
            ('Tweede editie', tr('publication.edition.second', 'Tweede editie')),
            ('Herziene editie', tr('publication.edition.revised', 'Herziene editie')),
        ]
        self.edition.addItems([label for _value, label in self._edition_entries])
        self.year = QLineEdit(); self.publisher = QLineEdit()
        form.addRow(tr('publication.copyright.author', 'Auteursnaam / pseudoniem'), self.author); form.addRow(tr('publication.copyright.edition', 'Editie'), self.edition); form.addRow(tr('publication.copyright.year', 'Jaar van publicatie'), self.year); form.addRow(tr('publication.copyright.publisher', 'Uitgever / imprint'), self.publisher)
        root.addLayout(form)
        root.addWidget(self._section(tr('publication.copyright.isbns', 'ISBNs')))
        grid = QGridLayout(); self.isbn = {}
        for i,(key,label) in enumerate([('isbn_epub','EPUB'),('isbn_kindle','Kindle'),('isbn_paperback','Paperback'),('isbn_hardcover','Hardcover'),('isbn_pdf','PDF')]):
            edit=QLineEdit(); edit.setPlaceholderText('000-0-00-000000-0'); self.isbn[key]=edit
            box=QWidget(); bl=QHBoxLayout(box); bl.setContentsMargins(0,0,0,0); lab=QLabel(label); lab.setMinimumWidth(82); bl.addWidget(lab); bl.addWidget(edit,1)
            grid.addWidget(box, i//2, i%2)
        root.addLayout(grid)
        root.addWidget(self._section(tr('publication.copyright.clauses', 'Clausules')))
        self.clauses = {}
        for key,label_key in CLAUSE_LABEL_KEYS.items():
            cb=QCheckBox(tr(label_key, key)); text=QTextEdit(); text.setMinimumHeight(76); text.setMaximumHeight(118); text.setPlaceholderText(tr('publication.copyright.clause_placeholder', 'Tekst van deze clausule'))
            self.clauses[key]=(cb,text); cb.toggled.connect(self._changed); text.textChanged.connect(self._changed); root.addWidget(cb); root.addWidget(text)
        for edit in (self.author, self.year, self.publisher): edit.textEdited.connect(self._changed)
        self.edition.currentTextChanged.connect(self._changed)
        for edit in self.isbn.values(): edit.textEdited.connect(self._changed)
        buttons=QHBoxLayout(); buttons.addStretch(); self.save_button=QPushButton(tr('common.save', 'Opslaan')); self.save_button.setObjectName('primaryButton'); self.save_button.setEnabled(False); self.save_button.clicked.connect(self._save); buttons.addWidget(self.save_button); root.addLayout(buttons); root.addStretch()
        scroll.setWidget(body); outer.addWidget(scroll)

    def _section(self,text):
        label=QLabel(text); label.setObjectName('sectionTitle'); return label

    def set_data(self, data: dict):
        self.author.setText(str(data.get('author','')))
        edition_value = str(data.get('edition','Eerste editie'))
        edition_label = next((label for value, label in self._edition_entries if value == edition_value), edition_value)
        self.edition.setCurrentText(edition_label)
        self.year.setText(str(data.get('year',''))); self.publisher.setText(str(data.get('publisher','')))
        for key,edit in self.isbn.items(): edit.setText(str(data.get(key,'')))
        clauses=data.get('clauses') or {}
        for key,(cb,text) in self.clauses.items():
            row=clauses.get(key) or {}; cb.setChecked(bool(row.get('enabled',False))); text.setPlainText(str(row.get('text','')))
        self.save_button.setEnabled(False)

    def _changed(self, *_):
        self.save_button.setEnabled(True)
        self.changed.emit()

    def data(self):
        return {
            'author':self.author.text().strip(),'edition':self._edition_value(),'year':self.year.text().strip(),'publisher':self.publisher.text().strip(),
            **{key:edit.text().strip() for key,edit in self.isbn.items()},
            'clauses':{key:{'enabled':cb.isChecked(),'text':text.toPlainText().strip()} for key,(cb,text) in self.clauses.items()},
        }

    def _edition_value(self):
        current = self.edition.currentText().strip()
        return next((value for value, label in self._edition_entries if label == current), current)

    def _save(self): self.saveRequested.emit(self.data())
