from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QRadioButton, QVBoxLayout, QWidget


class ContentsPage(QWidget):
    saveRequested = Signal(dict)
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.book = None
        self.library = None

        root = QVBoxLayout(self)
        root.setContentsMargins(42, 30, 42, 30)
        root.setSpacing(16)

        title = QLabel('Inhoudsopgave')
        title.setObjectName('title')
        root.addWidget(title)

        panel = QFrame()
        panel.setObjectName('softPanel')
        panel.setMaximumWidth(820)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(22, 18, 22, 18)
        pl.setSpacing(12)
        question = QLabel('Welke koppen wil je opnemen in de inhoudsopgave?')
        question.setWordWrap(True)
        pl.addWidget(question)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.chapters = QRadioButton('Alleen hoofdstuktitels')
        self.headings = QRadioButton('Hoofdstukken + tussenkoppen')
        for button in (self.chapters, self.headings):
            button.setObjectName('publicationRadio')
            self.group.addButton(button)
            pl.addWidget(button)
        root.addWidget(panel, 0, Qt.AlignLeft)

        preview_title = QLabel('Voorbeeld')
        preview_title.setObjectName('sectionTitle')
        root.addWidget(preview_title)
        self.preview = QLabel('')
        self.preview.setWordWrap(True)
        self.preview.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.preview.setObjectName('contentsPreview')
        self.preview.setMaximumWidth(820)
        root.addWidget(self.preview, 1, Qt.AlignLeft | Qt.AlignTop)

        buttons = QHBoxLayout()
        buttons.addStretch()
        save = QPushButton('Opslaan')
        save.setObjectName('primaryButton')
        save.clicked.connect(self._save)
        buttons.addWidget(save)
        root.addLayout(buttons)

        self.chapters.toggled.connect(self.refresh_preview)
        self.headings.toggled.connect(self.refresh_preview)
        self.group.buttonToggled.connect(lambda *_: self.changed.emit())

    def set_context(self, book, library, data: dict):
        self.book = book
        self.library = library
        if str(data.get('depth', 'chapters')) == 'headings':
            self.headings.setChecked(True)
        else:
            self.chapters.setChecked(True)
        self.refresh_preview()

    def refresh_preview(self):
        if not self.book:
            self.preview.setText('')
            return
        rows = []
        include_headings = self.headings.isChecked()
        for section in self.book.sections:
            for chapter in section.chapters:
                rows.append(chapter.title)
                if include_headings and self.library:
                    try:
                        text = self.library.read_chapter(self.book, chapter)
                    except Exception:
                        text = ''
                    for line in text.splitlines():
                        stripped = line.strip()
                        if stripped.startswith('## '):
                            rows.append('    ' + stripped[3:].strip())
        self.preview.setText('\n'.join(rows) if rows else 'Nog geen hoofdstukken.')

    def data(self):
        return {'depth': 'headings' if self.headings.isChecked() else 'chapters'}

    def _save(self):
        self.saveRequested.emit(self.data())
