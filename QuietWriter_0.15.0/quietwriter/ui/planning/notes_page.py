from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from ..manuscript_editor import ManuscriptEditor


class NotesPage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.dirty=False
        lay=QVBoxLayout(self); lay.setContentsMargins(34,28,34,34); lay.setSpacing(8)
        title=QLabel('Notities'); title.setObjectName('title'); info=QLabel('Vrije notities voor dit boek. Onder water blijft dit gewone Markdown.'); info.setObjectName('muted')
        self.editor=ManuscriptEditor(); self.editor.setObjectName('planningNotesEditor'); self.editor.textChanged.connect(self.changed)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(2500); self.timer.timeout.connect(self.save)
        lay.addWidget(title); lay.addWidget(info); lay.addSpacing(8); lay.addWidget(self.editor,1)
    def load(self):
        self.timer.stop(); self.editor.blockSignals(True); self.editor.setPlainText(self.owner.store.load_notes(self.owner.book) if self.owner.book else ''); self.editor.blockSignals(False); self.dirty=False
    def changed(self):
        self.dirty=True; self.timer.start()
    def save(self):
        if not self.dirty or not self.owner.book:return True
        if self.owner.persist_notes(self.editor.toPlainText()): self.dirty=False; return True
        return False
