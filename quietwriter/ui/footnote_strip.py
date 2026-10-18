"""Notenstrook onder de tekst (1.7): hier typ je de voetnoten van dit hoofdstuk.

Zoals in een tekstverwerker: in de tekst staat een klein nummer, onder de tekst
staat een streep met "1" en daarachter de noot, met een knipperende cursor zodra
je een noot toevoegt. Er is maar één bron: de noottekst staat in het manuscript
als ``^[…]`` op de plek van het nummer. De strook leest en schrijft precies dat
stuk tekst; Ongedaan maken, opslaan en zoeken werken dus zoals altijd.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QMimeData, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence, QTextCursor, QTextOption
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QScrollArea, QVBoxLayout, QWidget

from ..i18n import tr
from ..manuscript_markup import escape_literal_text, escape_literal_typed_char, toggle_inline
from ..manuscript_syntax import escape_ranges
from .presentation_highlighter import ManuscriptHighlighter


class NoteEdit(QPlainTextEdit):
    """Eén voetnoot. De tekst is QuietWriter-bron (met verborgen escapes en opmaak)."""

    finished = Signal()
    sourceEdited = Signal(str)

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.collapse_footnotes = False
        self._setting = False
        # De noottekst zoals die het laatst in het manuscript stond (gelezen of
        # door dit veld geschreven). Schrijven mag alleen als het manuscript
        # daar nog mee klopt (ChatGPT-review dev15).
        self.synced = ''
        self.setObjectName('footnoteEdit')
        self.setFrameShape(QFrame.NoFrame)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTabChangesFocus(True)
        self.setPlaceholderText(tr('footnotes.placeholder', 'Typ hier de voetnoot. Enter: terug naar de tekst.'))
        font = QFont(editor.font())
        font.setPointSizeF(max(7.0, float(editor.typography.point_size) - 2.0))
        self.setFont(font)
        self.document().setDocumentMargin(2)
        self.highlighter = ManuscriptHighlighter(self, spelling_source=getattr(editor, 'presentation_highlighter', None))
        self.textChanged.connect(self._changed)
        self.document().documentLayout().documentSizeChanged.connect(lambda *_: self._fit_height())

    # ManuscriptHighlighter vraagt deze twee aan "zijn" editor.
    def _theme(self):
        return self.editor._theme()

    @property
    def typography(self):
        return self.editor.typography

    def set_source(self, source: str):
        self.synced = source
        if source == self.toPlainText():
            return
        self._setting = True
        try:
            self.setPlainText(source)
        finally:
            self._setting = False
        self._fit_height()

    def _fit_height(self):
        lines = max(1, int(self.document().size().height()))
        height = self.fontMetrics().lineSpacing() * min(lines, 6) + 2 * int(self.document().documentMargin()) + 4
        if height != self.height():
            self.setFixedHeight(height)
            strip = self.parent()
            while strip is not None and not isinstance(strip, FootnoteStrip):
                strip = strip.parent()
            if strip is not None:
                strip.height_changed()

    def _changed(self):
        if not self._setting:
            self.sourceEdited.emit(self.toPlainText())

    def insertFromMimeData(self, source: QMimeData):
        # Plakken is gewone tekst: één regel, en nooit per ongeluk opmaak of een noot.
        text = source.text().replace('\r\n', ' ').replace('\n', ' ').replace(' ', ' ')
        self.textCursor().insertText(escape_literal_text(text, at_line_start=False))

    def _escape_pair_before(self, pos: int):
        for a, b in escape_ranges(self.toPlainText()):
            if b + 1 == pos:
                return a
        return None

    def _escape_pair_at(self, pos: int):
        for a, b in escape_ranges(self.toPlainText()):
            if a == pos:
                return b + 1
        return None

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        ctrl = bool(modifiers & Qt.ControlModifier)
        alt = bool(modifiers & Qt.AltModifier)
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape) or (key == Qt.Key_F and ctrl and alt):
            self.finished.emit()
            event.accept(); return
        if self.isReadOnly():
            super().keyPressEvent(event); return
        cursor = self.textCursor()
        if ctrl and not alt and cursor.hasSelection() and key in (Qt.Key_B, Qt.Key_I, Qt.Key_U):
            kind = {Qt.Key_B: 'bold', Qt.Key_I: 'italic', Qt.Key_U: 'underline'}[key]
            start, end = sorted((cursor.selectionStart(), cursor.selectionEnd()))
            new, a, b = toggle_inline(self.toPlainText(), start, end, kind)
            cursor.beginEditBlock()
            cursor.select(QTextCursor.Document)
            cursor.insertText(new)
            cursor.endEditBlock()
            cursor.setPosition(a); cursor.setPosition(b, QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
            event.accept(); return
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste(); event.accept(); return
        if key == Qt.Key_Backspace and not cursor.hasSelection():
            start = self._escape_pair_before(cursor.position())
            if start is not None:      # \] als één teken weghalen
                cursor.setPosition(start, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                event.accept(); return
        if key == Qt.Key_Delete and not cursor.hasSelection():
            end = self._escape_pair_at(cursor.position())
            if end is not None:
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                event.accept(); return
        text = event.text()
        if len(text) == 1 and text.isprintable() and not (ctrl or alt or modifiers & Qt.MetaModifier):
            cursor.insertText(escape_literal_typed_char(text, ''))
            event.accept(); return
        super().keyPressEvent(event)


class FootnoteRow(QWidget):
    def __init__(self, editor, index: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.setObjectName('footnoteRow')
        self.edit = NoteEdit(editor)
        self.number = QLabel(str(index + 1))
        self.number.setObjectName('footnoteNumber')
        self.number.setFont(self.edit.font())
        self.number.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.number.setFixedWidth(22)
        layout.addWidget(self.number, 0, Qt.AlignTop)
        layout.addWidget(self.edit, 1)


class FootnoteStrip(QFrame):
    """Alle voetnoten van het open hoofdstuk, onder de tekst. Leeg = onzichtbaar."""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setObjectName('footnoteStrip')
        self.rows: list[FootnoteRow] = []
        self._writing = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 8)
        outer.setSpacing(4)
        self.rule = QFrame()
        self.rule.setObjectName('footnoteRule')
        self.rule.setFixedHeight(1)
        self.rule.setFixedWidth(140)
        outer.addWidget(self.rule)
        self.scroll = QScrollArea()
        self.scroll.setObjectName('footnoteScroll')
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setMaximumHeight(220)
        self.body = QWidget()
        self.body.setObjectName('footnoteBody')
        self.rows_layout = QVBoxLayout(self.body)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(4)
        self.rows_layout.addStretch(1)
        self.scroll.setWidget(self.body)
        outer.addWidget(self.scroll)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self.refresh)
        editor.document().contentsChanged.connect(self._schedule)
        editor.footnoteEditRequested.connect(self.focus_note)
        main_highlighter = getattr(editor, 'presentation_highlighter', None)
        if main_highlighter is not None and hasattr(main_highlighter, 'add_follower'):
            main_highlighter.add_follower(self.rehighlight_notes)
        self.hide()

    def rehighlight_notes(self):
        """Spelling in de noten bijwerken (woordenboek gewisseld, woord toegevoegd, aan/uit)."""
        for row in self.rows:
            row.edit.highlighter.rehighlight()

    def select_in_note(self, index: int, start: int, end: int) -> bool:
        """Selecteer een stuk van noot ``index`` (posities binnen de noottekst)."""
        self.refresh()
        if not 0 <= index < len(self.rows):
            return False
        row = self.rows[index]
        self.scroll.ensureWidgetVisible(row)
        row.edit.setFocus()
        cursor = row.edit.textCursor()
        length = len(row.edit.toPlainText())
        cursor.setPosition(max(0, min(start, length)))
        cursor.setPosition(max(0, min(end, length)), QTextCursor.KeepAnchor)
        row.edit.setTextCursor(cursor)
        return True

    def desired_height(self) -> int:
        """Hoog genoeg voor alle noten (de editor begrenst dit tot een derde)."""
        margins = self.layout().contentsMargins()
        rows = sum(row.edit.height() for row in self.rows) + max(0, len(self.rows) - 1) * self.rows_layout.spacing()
        return margins.top() + margins.bottom() + 1 + self.layout().spacing() + rows + 12

    def height_changed(self):
        if hasattr(self.editor, '_update_margins') and self.isVisible():
            self.editor._update_margins()

    def _schedule(self):
        if not self._writing:
            self._timer.start()

    def _align_with_text(self):
        # Zelfde linkerkant als de tekstkolom op het blad.
        try:
            left = max(0, self.editor.cursorRect(QTextCursor(self.editor.document())).left())
            self.layout().setContentsMargins(left, 10, left, 6)
        except Exception:
            pass

    def setVisible(self, visible: bool):
        changed = visible != self.isVisible()
        super().setVisible(visible)
        if changed and hasattr(self.editor, '_update_margins'):
            self.editor._update_margins()

    def _apply_theme(self):
        # Eigen stylesheet: de strook ligt op het witte blad, niet op de app-achtergrond.
        try:
            t = self.editor._theme()
        except Exception:
            return
        sheet = (f"QFrame#footnoteStrip, QFrame#footnoteStrip QWidget {{ background: {t['editor']}; }}"
                 f"QFrame#footnoteStrip QFrame#footnoteRule {{ background: {t['muted']}; }}"
                 f"QLabel#footnoteNumber {{ color: {t['accent']}; font-weight: 600; padding-top: 2px; }}"
                 f"QPlainTextEdit#footnoteEdit {{ color: {t['text']}; border: 0; padding: 0; }}")
        if sheet != self.styleSheet():
            self.setStyleSheet(sheet)

    def changeEvent(self, event):
        super().changeEvent(event)
        # Ander thema gekozen: de app-stylesheet wisselt, de strook kleurt mee.
        if event.type() == QEvent.StyleChange and not getattr(self, '_styling', False):
            self._styling = True
            try:
                self._apply_theme()
                for row in self.rows:
                    row.edit.highlighter.rehighlight()
            finally:
                self._styling = False

    def refresh(self):
        self._timer.stop()
        self._apply_theme()
        spans = self.editor.footnote_spans()
        source = self.editor.source_text()
        contents = [source[cs:ce] for _s, cs, ce, _e in spans]
        if len(contents) != len(self.rows):
            self._rebuild(contents)
        for index, (row, content) in enumerate(zip(self.rows, contents)):
            row.number.setText(str(index + 1))
            if not row.edit.hasFocus():
                row.edit.set_source(content)
            elif content != row.edit.synced:
                # Met focus, maar het manuscript veranderde buiten dit veld om
                # (herladen, Ongedaan maken in de tekst): het manuscript wint.
                self._resync_focused(row.edit, content)
            row.edit.setReadOnly(self.editor.isReadOnly())
        if contents:
            self._align_with_text()
        self.setVisible(bool(contents))
        if contents and hasattr(self.editor, '_update_margins'):
            self.editor._update_margins()   # hoogte kan veranderd zijn

    @staticmethod
    def _resync_focused(edit, content: str):
        position = edit.textCursor().position()
        edit.set_source(content)
        cursor = edit.textCursor()
        cursor.setPosition(min(position, len(edit.toPlainText())))
        edit.setTextCursor(cursor)

    def _rebuild(self, contents):
        """Nieuwe rijen. Had een noot de focus, dan gaat die mee naar dezelfde noot
        (zelfde tekst, dichtst bij de oude plek), nooit naar een andere noot."""
        count = len(contents)
        focused = next((i for i, row in enumerate(self.rows) if row.edit.hasFocus()), None)
        focus_target = None
        cursor_position = 0
        if focused is not None:
            old = self.rows[focused].edit
            cursor_position = old.textCursor().position()
            matches = [i for i, content in enumerate(contents) if content == old.synced]
            if matches:
                focus_target = min(matches, key=lambda i: abs(i - focused))
        for row in self.rows:
            self.rows_layout.removeWidget(row)
            row.deleteLater()
        self.rows = []
        for index in range(count):
            row = FootnoteRow(self.editor, index, self.body)
            row.edit.set_source(contents[index])
            row.edit.sourceEdited.connect(lambda text, r=row: self._write(r, text))
            row.edit.finished.connect(lambda r=row: self._finish(r))
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
            self.rows.append(row)
        if focus_target is not None:
            edit = self.rows[focus_target].edit
            edit.setFocus()
            cursor = edit.textCursor()
            cursor.setPosition(min(cursor_position, len(edit.toPlainText())))
            edit.setTextCursor(cursor)
        elif focused is not None:
            # De noot met focus bestaat niet meer: terug naar de tekst.
            self.editor.setFocus()

    def _finish(self, row):
        if row in self.rows:
            self.editor.move_after_footnote(self.rows.index(row))

    def _write(self, row, text: str):
        """Schrijf de noot van deze rij terug, maar alleen in dezelfde noot.

        De rij hoort bij de noot op haar plek én met haar laatst bekende tekst.
        Klopt het manuscript daar niet meer mee (een noot ervoor toegevoegd of
        weggehaald, het hoofdstuk van schijf herladen), dan wordt er niets
        geschreven en neemt het veld de actuele noot over.
        """
        if isinstance(row, int):          # oude aanroep met een index
            row = self.rows[row] if 0 <= row < len(self.rows) else None
        if row is None or row not in self.rows:
            return
        index = self.rows.index(row)
        spans = self.editor.footnote_spans()
        source = self.editor.source_text()
        current = source[spans[index][1]:spans[index][2]] if index < len(spans) else None
        if current is None or current != row.edit.synced or len(spans) != len(self.rows):
            self.refresh()
            return
        normalized = (text or '').replace('\n', ' ').replace('\u2029', ' ')
        self._writing = True
        try:
            self.editor.replace_footnote_content(index, normalized)
            row.edit.synced = normalized
        finally:
            self._writing = False

    def focus_note(self, index: int):
        self.refresh()
        if not 0 <= index < len(self.rows):
            return
        row = self.rows[index]
        self.scroll.ensureWidgetVisible(row)
        row.edit.setFocus()
        cursor = row.edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        row.edit.setTextCursor(cursor)
