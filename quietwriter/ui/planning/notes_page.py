from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from ..manuscript_editor import ManuscriptEditor
from ...i18n import tr


class NotesPage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.dirty=False
        lay=QVBoxLayout(self); lay.setContentsMargins(28,24,34,30); lay.setSpacing(12)
        top=QHBoxLayout(); title=QLabel(tr('planning.notes.title', 'Notities')); title.setObjectName('title'); top.addWidget(title); top.addStretch(); self.save_button=QPushButton(tr('common.save', 'Opslaan')); self.save_button.setObjectName('primaryButton'); self.save_button.setEnabled(False); self.save_button.clicked.connect(self.save); top.addWidget(self.save_button)
        info=QLabel(tr('planning.notes.description', 'Vrije notities voor dit boek. Onder water blijft dit gewone Markdown.')); info.setObjectName('muted')
        self.editor=ManuscriptEditor(); self.editor.setObjectName('planningNotesEditor'); self.editor.max_text_width = 100000; self.editor.min_side_margin = 8; self.editor._update_margins(); self.editor.textChanged.connect(self.changed)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(2500); self.timer.timeout.connect(self.save)
        lay.addLayout(top); lay.addWidget(info); lay.addSpacing(4); lay.addWidget(self.editor,1)
    def load(self):
        self.timer.stop(); self.editor.blockSignals(True); self.editor.setPlainText(self.owner.store.load_notes(self.owner.book) if self.owner.book else ''); self.editor.blockSignals(False); self.dirty=False; self.save_button.setEnabled(False)
    def changed(self):
        self.dirty=True; self.save_button.setEnabled(True); self.timer.start()
    def save(self):
        if not self.dirty or not self.owner.book:return True
        if self.owner.persist_notes(self.editor.toPlainText()): self.dirty=False; self.save_button.setEnabled(False); return True
        return False
