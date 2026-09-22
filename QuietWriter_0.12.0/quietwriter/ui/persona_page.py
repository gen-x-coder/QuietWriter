
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget
)
from .dialogs import confirm

class PersonaPage(QWidget):
    def __init__(self, library):
        super().__init__()
        self.library = library
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 30, 36, 30)
        top = QHBoxLayout()
        title = QLabel('Schrijverspersona')
        title.setObjectName('title')
        load_default = QPushButton('Meegeleverde schrijfwijzer laden')
        load_default.clicked.connect(self.load_default)
        top.addWidget(title); top.addStretch(); top.addWidget(load_default)
        info = QLabel('Deze persona wordt automatisch aan iedere AI-opdracht toegevoegd. QuietWriter wijzigt hem nooit automatisch.')
        info.setObjectName('muted')
        self.edit = QTextEdit()
        self.edit.setPlainText(library.read_persona())
        save = QPushButton('Opslaan'); save.setObjectName('primaryButton')
        save.clicked.connect(self.save)
        lay.addLayout(top)
        lay.addWidget(info)
        lay.addSpacing(12)
        lay.addWidget(self.edit)
        lay.addWidget(save, 0, Qt.AlignRight)

    def load_default(self):
        path = Path(__file__).resolve().parents[2] / 'schrijver.md'
        if not path.exists():
            QMessageBox.warning(self, 'Schrijfwijzer', 'De meegeleverde schrijfwijzer is niet gevonden.')
            return
        if confirm(self, 'Schrijfwijzer laden', 'De huidige tekst in de editor vervangen door de meegeleverde, geoptimaliseerde schrijfwijzer?'):
            self.edit.setPlainText(path.read_text(encoding='utf-8'))

    def save(self):
        self.library.save_persona(self.edit.toPlainText())
