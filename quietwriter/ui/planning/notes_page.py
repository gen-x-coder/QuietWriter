from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget
from ..manuscript_editor import ManuscriptEditor
from ...i18n import tr


class NotesPage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.dirty=False; self._clean_text=''
        lay=QVBoxLayout(self); lay.setContentsMargins(28,24,34,30); lay.setSpacing(12)
        top=QHBoxLayout(); title=QLabel(tr('planning.notes.title', 'Notities')); title.setObjectName('title'); top.addWidget(title); top.addStretch(); self.save_button=QPushButton(tr('common.save', 'Opslaan')); self.save_button.setObjectName('primaryButton'); self.save_button.setEnabled(False); self.save_button.clicked.connect(self.save); top.addWidget(self.save_button)
        info=QLabel(tr('planning.notes.description', 'Vrije notities voor dit boek. Onder water blijft dit gewone Markdown.')); info.setObjectName('muted')
        self.editor=ManuscriptEditor(); self.editor.setObjectName('planningNotesEditor'); self.editor.max_text_width = 100000; self.editor.min_side_margin = 8; self.editor._update_margins(); self.editor.textChanged.connect(self.changed)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(2500); self.timer.timeout.connect(self.save)
        lay.addLayout(top); lay.addWidget(info); lay.addSpacing(4); lay.addWidget(self.editor,1)
    def load(self):
        self.timer.stop(); self.editor.blockSignals(True)
        try:
            text = self.owner.store.load_notes(self.owner.book) if self.owner.book else ''
        except UnicodeDecodeError:
            self.editor.setPlainText(tr(
                'planning.notes.corrupt',
                'Dit notitiebestand is beschadigd en kan niet als UTF-8 worden gelezen.\n\nOpen Integriteit om het te controleren en zo mogelijk te herstellen.'
            ))
            self.editor.setReadOnly(True)
            self.editor.blockSignals(False)
            self._clean_text = self.editor.source_text()
            self.dirty=False; self.save_button.setEnabled(False)
            return
        self.editor.setPlainText(text); self.editor.setReadOnly(False)
        self.editor.blockSignals(False); self._clean_text = self.editor.source_text(); self.dirty=False; self.save_button.setEnabled(False)
    def restore_pending_text(self, text: str):
        self.timer.stop()
        self.editor.blockSignals(True); self.editor.setPlainText(text); self.editor.blockSignals(False)
        self.dirty=True; self.save_button.setEnabled(True); self.timer.start()

    def show_corrupt_adoption_message(self):
        QMessageBox.information(
            self,
            tr('planning.notes.corrupt_preserved_title', 'Lokale notities veilig bewaard'),
            tr(
                'planning.notes.corrupt_preserved_text',
                'Het notitiebestand op schijf is beschadigd en is alleen-lezen geopend. '
                'Je lokale notities staan apart in Versiegeschiedenis. Herstel het bronbestand via Integriteit.'
            ),
        )

    def changed(self):
        if self.editor.source_text() == self._clean_text:
            self.dirty=False; self.save_button.setEnabled(False); self.timer.stop(); return
        self.dirty=True; self.save_button.setEnabled(True); self.timer.start()
    def save(self):
        if not self.dirty or not self.owner.book:return True
        source_text = self.editor.source_text()
        result = self.owner.persist_notes(source_text)
        if result == 'mine':
            self._clean_text = source_text
            self.timer.stop(); self.dirty=False; self.save_button.setEnabled(False); return True
        if result == 'disk':
            # adopt_active_book() already reloaded the disk version into this page.
            return True
        return False
