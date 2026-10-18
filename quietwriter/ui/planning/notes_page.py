from PySide6.QtCore import QTimer, Qt, QEvent
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QDialog, QDialogButtonBox, QLineEdit, QPlainTextEdit, QScrollArea, QFrame
from ..manuscript_editor import ManuscriptEditor
from ..dialog_notices import notice_information
from ...i18n import tr
from .note_segments import replace_note, split_notes


class NotesPage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.dirty=False; self._clean_text=''
        lay=QVBoxLayout(self); lay.setContentsMargins(28,24,34,30); lay.setSpacing(12)
        top=QHBoxLayout(); title=QLabel(tr('planning.notes.title', 'Notities')); title.setObjectName('settingsPageTitle'); top.addWidget(title); top.addStretch(); self.save_button=QPushButton(tr('common.save', 'Opslaan')); self.save_button.setObjectName('primaryButton'); self.save_button.setEnabled(False); self.save_button.clicked.connect(self.save); top.addWidget(self.save_button)
        self.new_note_button=QPushButton(tr('planning.notes.new', 'Nieuwe notitie')); self.new_note_button.clicked.connect(self.add_note); top.insertWidget(top.count()-1,self.new_note_button)
        info=QLabel(tr('planning.notes.description', 'Vrije notities voor dit boek. Onder water blijft dit gewone Markdown.')); info.setObjectName('muted')
        self.editor=ManuscriptEditor(settings=self.owner.main.settings); self.editor.setObjectName('planningNotesEditor'); self.editor.max_text_width = 100000; self.editor.min_side_margin = 8; self.editor._update_margins(); self.editor.textChanged.connect(self.changed)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(2500); self.timer.timeout.connect(self.save)
        # The manuscript-style editor remains the canonical Markdown buffer for
        # planning conflict handling, autosave and existing recovery mechanisms.
        # Cards are only another view onto that same buffer.
        self.editor.hide()
        self._last_card_columns = None
        self._card_rows = 0
        self.card_scroll=QScrollArea(); self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setFrameShape(QFrame.NoFrame)
        self.cards_outer=QWidget(); outer_layout=QHBoxLayout(self.cards_outer)
        outer_layout.setContentsMargins(0,0,0,0); outer_layout.setSpacing(0)
        self.cards_host=QWidget(); self.cards_host.setMaximumWidth(1320)
        self.cards_layout=QGridLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0,0,12,12); self.cards_layout.setHorizontalSpacing(12); self.cards_layout.setVerticalSpacing(12)
        outer_layout.addWidget(self.cards_host,1); outer_layout.addStretch(0)
        self.card_scroll.setWidget(self.cards_outer)
        self.card_scroll.viewport().installEventFilter(self)
        lay.addLayout(top); lay.addWidget(info); lay.addWidget(self.card_scroll,1); lay.addWidget(self.editor)

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
            self.dirty=False; self.save_button.setEnabled(False); self.refresh_notes()
            return
        self.editor.setPlainText(text); self.editor.setReadOnly(False)
        self.editor.blockSignals(False); self._clean_text = self.editor.source_text(); self.dirty=False; self.save_button.setEnabled(False); self.refresh_notes()
    def restore_pending_text(self, text: str):
        self.timer.stop()
        self.editor.blockSignals(True); self.editor.setPlainText(text); self.editor.blockSignals(False)
        self.dirty=True; self.save_button.setEnabled(True); self.timer.start(); self.refresh_notes()

    def show_corrupt_adoption_message(self):
        notice_information(
            self,
            tr('planning.notes.corrupt_preserved_title', 'Lokale notities veilig bewaard'),
            tr(
                'planning.notes.corrupt_preserved_text',
                'Het notitiebestand op schijf is beschadigd en is alleen-lezen geopend. '
                'Je lokale notities staan apart in Versiegeschiedenis. Herstel het bronbestand via Integriteit.'
            ),
        )

    def eventFilter(self, watched, event):
        if watched is self.card_scroll.viewport() and event.type() == QEvent.Resize:
            # The scroll area may change size without the page itself resizing.
            # Defer rebuilding until Qt has finished the current layout pass.
            QTimer.singleShot(0, self._refresh_if_columns_changed)
        return super().eventFilter(watched, event)

    def _refresh_if_columns_changed(self):
        if self._card_columns() != self._last_card_columns:
            self.refresh_notes()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_if_columns_changed()

    def _card_columns(self):
        available = min(max(self.card_scroll.viewport().width() - 16, 0), 1320)
        if available >= 1020:
            return 3
        if available >= 680:
            return 2
        return 1

    @staticmethod
    def _segments(source):
        return split_notes(source)

    def refresh_notes(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        source = self.editor.source_text()
        columns = self._card_columns()
        self._last_card_columns = columns
        segments = self._segments(source)
        # Clear previous stretch factors too when moving from three columns to one.
        for column in range(3):
            self.cards_layout.setColumnStretch(column, 1 if column < columns else 0)
        if not segments:
            empty = QLabel(tr('planning.notes.empty', 'Nog geen tekst'))
            empty.setObjectName('muted')
            self.cards_layout.addWidget(empty, 0, 0)
        for index, (start, end, title, body) in enumerate(segments):
            card = QFrame()
            card.setObjectName('planningNoteCard')
            card.setMinimumHeight(132)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(8)
            heading = QHBoxLayout()
            label = QLabel(title if title is not None else tr('planning.notes.legacy', 'Algemene notities'))
            label.setObjectName('sectionTitle')
            label.setWordWrap(True)
            heading.addWidget(label, 1)
            edit = QPushButton(tr('planning.outline.edit', 'Bewerken'))
            edit.setObjectName('compactButton')
            edit.clicked.connect(lambda _=False, a=start, b=end: self.edit_note(a, b))
            heading.addWidget(edit)
            layout.addLayout(heading)
            preview = body.strip().replace('\n', ' ') or tr('planning.notes.empty', 'Nog geen tekst')
            description = QLabel(preview[:180] + ('…' if len(preview) > 180 else ''))
            description.setObjectName('muted')
            description.setWordWrap(True)
            layout.addWidget(description, 1)
            self.cards_layout.addWidget(card, index // columns, index % columns)
        rows = (len(segments) + columns - 1) // columns
        # QGridLayout retains stretch factors after takeAt(): reset the old
        # spacer row when notes are deleted or the column count changes.
        for row in range(max(rows, self._card_rows) + 1):
            self.cards_layout.setRowStretch(row, 1 if row == rows else 0)
        self._card_rows = rows

    def _note_dialog(self, title='', content='', *, new=False, legacy=False):
        dialog=QDialog(self)
        dialog.setWindowTitle(tr('planning.notes.new','Nieuwe notitie') if new else
                              tr('planning.outline.edit','Bewerken'))
        # Do not force this dialog beyond the available area on smaller laptops.
        screen = QApplication.screenAt(self.mapToGlobal(self.rect().center())) or QApplication.primaryScreen()
        if screen:
            bounds = screen.availableGeometry()
            dialog.resize(min(620, max(320, bounds.width() - 48)),
                          min(480, max(240, bounds.height() - 64)))
        else:
            dialog.resize(620, 480)
        dialog.setMinimumSize(320, 240)
        layout=QVBoxLayout(dialog)
        title_field=QLineEdit(title,dialog)
        if not legacy:
            layout.addWidget(QLabel(tr('planning.notes.name','Titel van de notitie')))
            layout.addWidget(title_field)
        layout.addWidget(QLabel(tr('planning.notes.content','Inhoud')))
        body_field=QPlainTextEdit(dialog); body_field.setPlainText(content.strip('\n'))
        layout.addWidget(body_field,1)
        buttons=QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr('common.save','Opslaan'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('common.cancel','Annuleren'))
        if not legacy:
            save_button = buttons.button(QDialogButtonBox.Save)
            save_button.setEnabled(bool(title_field.text().strip()))
            title_field.textChanged.connect(lambda text: save_button.setEnabled(bool(text.strip())))
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec()!=QDialog.Accepted:
            return None
        chosen_title=title_field.text().strip().replace('\n',' ')
        if not legacy and not chosen_title:
            return None
        # A heading must stay on one source line, otherwise it could split notes.
        chosen_title=chosen_title.replace('\r',' ').replace('\n',' ')
        content=body_field.toPlainText().strip('\n')
        if legacy:
            return (content+'\n\n') if content else ''
        return '## '+chosen_title+'\n\n'+(content+'\n\n' if content else '')

    def _replace_source(self, source):
        self.editor.setPlainText(source)
        self.changed()

    def edit_note(self,start,end):
        if not self.owner.book or self.editor.isReadOnly(): return
        source=self.editor.source_text()
        segment=next((s for s in self._segments(source) if s[0]==start and s[1]==end),None)
        if segment is None:return
        _,_,title,body=segment
        replacement=self._note_dialog(title or '',body,legacy=title is None)
        if replacement is None:return
        self._replace_source(replace_note(source, start, end, replacement))

    def add_note(self):
        if not self.owner.book or self.editor.isReadOnly():return
        replacement=self._note_dialog(new=True)
        if replacement is None:return
        source=self.editor.source_text()
        separator='' if not source.strip() else ('\n' if source.endswith('\n') else '\n\n')
        self._replace_source(source+separator+replacement)

    def changed(self):
        self.refresh_notes()
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
