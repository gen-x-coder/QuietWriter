from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QRadioButton, QVBoxLayout, QWidget


class ContentsPage(QWidget):
    saveRequested = Signal(dict)
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent); self.book=None; self.library=None
        root=QVBoxLayout(self); root.setContentsMargins(42,30,42,30); root.setSpacing(14)
        title=QLabel('Inhoudsopgave'); title.setObjectName('title'); root.addWidget(title)
        panel=QFrame(); panel.setObjectName('softPanel'); pl=QVBoxLayout(panel); pl.setContentsMargins(22,18,22,18); pl.setSpacing(9)
        pl.addWidget(QLabel('Welke koppen wil je opnemen in de inhoudsopgave?'))
        self.group=QButtonGroup(self); self.chapters=QRadioButton('Alleen hoofdstuktitels'); self.headings=QRadioButton('Hoofdstukken + tussenkoppen')
        self.group.addButton(self.chapters); self.group.addButton(self.headings); pl.addWidget(self.chapters); pl.addWidget(self.headings); root.addWidget(panel)
        preview_title=QLabel('Voorbeeld'); preview_title.setObjectName('sectionTitle'); root.addWidget(preview_title)
        self.preview=QLabel(''); self.preview.setWordWrap(True); self.preview.setAlignment(self.preview.alignment() | 1); root.addWidget(self.preview,1)
        buttons=QHBoxLayout(); buttons.addStretch(); save=QPushButton('Opslaan'); save.setObjectName('primaryButton'); save.clicked.connect(self._save); buttons.addWidget(save); root.addLayout(buttons)
        self.chapters.toggled.connect(self.refresh_preview); self.headings.toggled.connect(self.refresh_preview); self.group.buttonToggled.connect(lambda *_: self.changed.emit())

    def set_context(self, book, library, data: dict):
        self.book=book; self.library=library
        if str(data.get('depth','chapters'))=='headings': self.headings.setChecked(True)
        else: self.chapters.setChecked(True)
        self.refresh_preview()

    def refresh_preview(self):
        if not self.book:
            self.preview.setText(''); return
        rows=[]
        include_headings=self.headings.isChecked()
        for section in self.book.sections:
            for chapter in section.chapters:
                rows.append(chapter.title)
                if include_headings and self.library:
                    try: text=self.library.read_chapter(self.book,chapter)
                    except Exception: text=''
                    for line in text.splitlines():
                        stripped=line.strip()
                        if stripped.startswith('## '): rows.append('    '+stripped[3:].strip())
        self.preview.setText('\n'.join(rows) if rows else 'Nog geen hoofdstukken.')

    def data(self): return {'depth':'headings' if self.headings.isChecked() else 'chapters'}

    def _save(self): self.saveRequested.emit(self.data())
