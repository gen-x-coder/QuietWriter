from __future__ import annotations

import re

from PySide6.QtCore import QPoint, QSettings, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QTextBlockFormat, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QApplication, QTextEdit

from ..manuscript_markup import ManuscriptStyle, apply_block_style, smart_double_quote, toggle_inline
from ..themes import THEMES
from ..typography import WritingTypography, typography_from_values
from .selection_toolbar import SelectionToolbar


class ManuscriptEditor(QTextEdit):
    """Rustige Markdown-editor met manuscriptweergave en lichte opmaaklaag.

    De bron blijft altijd platte Markdown. De visuele laag gebruikt alleen Qt
    character/block formats; opslaan via ``toPlainText()`` blijft dus volledig
    voorspelbaar en exporteerbaar.
    """

    INLINE_PATTERNS = (
        ('code', re.compile(r'`([^`\n]+)`')),
        ('underline', re.compile(r'<u>(.+?)</u>')),
        ('strike', re.compile(r'~~(.+?)~~')),
        ('bold', re.compile(r'\*\*(.+?)\*\*')),
        ('italic', re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_text_width = 850
        self.setAcceptRichText(False)
        self._formatting = False
        self._selection_range: tuple[int, int] | None = None
        self.settings = QSettings('QuietWriter', 'QuietWriter')
        self.typography = WritingTypography.from_settings(self.settings)
        self.manuscript_style = ManuscriptStyle.from_settings(self.settings)

        self._format_timer = QTimer(self)
        self._format_timer.setSingleShot(True)
        self._format_timer.setInterval(90)
        self._format_timer.timeout.connect(self.apply_visual_formatting)

        self._selection_timer = QTimer(self)
        self._selection_timer.setSingleShot(True)
        self._selection_timer.setInterval(1000)
        self._selection_timer.timeout.connect(self._show_selection_toolbar)
        self.selectionChanged.connect(self._selection_changed)
        self.textChanged.connect(self.schedule_formatting)

        self.selection_toolbar = SelectionToolbar()
        self.selection_toolbar.actionRequested.connect(self.apply_format_action)

        self.apply_typography(self.typography)
        self._update_margins()

    def apply_typography(self, typography: WritingTypography):
        self.typography = typography
        font = typography.body_font()
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.document().markContentsDirty(0, self.document().characterCount())
        self.schedule_formatting(immediate=True)
        self.viewport().update()

    def apply_manuscript_style(self, style: ManuscriptStyle):
        self.manuscript_style = style
        self.schedule_formatting(immediate=True)

    def reload_manuscript_style(self):
        self.apply_manuscript_style(ManuscriptStyle.from_settings(self.settings))

    def set_editor_font(self, preferred: str, point_size: int | None = None):
        if point_size is None:
            point_size = self.settings.value('editor_font_size', 15, int)
        self.apply_typography(typography_from_values(preferred, point_size))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_margins()

    def _update_margins(self):
        side = max(42, (max(0, self.width()) - self.max_text_width) // 2)
        self.setViewportMargins(side, 30, side, 42)

    def schedule_formatting(self, *_args, immediate: bool = False):
        if self._formatting:
            return
        if immediate:
            self._format_timer.stop()
            self.apply_visual_formatting()
        else:
            self._format_timer.start()

    # Compatibility with existing call sites from before the manuscript-style
    # iteration. Scene breaks are now one part of the complete visual pass.
    def apply_scene_break_formatting(self):
        self.schedule_formatting(immediate=True)

    def _theme(self):
        return THEMES.get(str(self.settings.value('theme', 'Helder')), THEMES['Helder'])

    def _selection_changed(self):
        self._selection_timer.stop()
        cursor = self.textCursor()
        if not cursor.hasSelection() or self.isReadOnly():
            self._selection_range = None
            self.selection_toolbar.hide()
            return
        start, end = sorted((cursor.selectionStart(), cursor.selectionEnd()))
        if end <= start:
            return
        self._selection_range = (start, end)
        self._selection_timer.start()

    def _show_selection_toolbar(self):
        if not self._selection_range or self.isReadOnly():
            return
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        end_cursor = QTextCursor(self.document())
        end_cursor.setPosition(self._selection_range[1])
        rect = self.cursorRect(end_cursor)
        self.selection_toolbar.adjustSize()
        global_pos = self.viewport().mapToGlobal(QPoint(rect.left(), rect.bottom() + 8))
        screen = QApplication.screenAt(global_pos)
        if screen:
            area = screen.availableGeometry()
            w = self.selection_toolbar.sizeHint().width()
            h = self.selection_toolbar.sizeHint().height()
            x = min(max(global_pos.x(), area.left() + 8), area.right() - w - 8)
            y = global_pos.y()
            if y + h > area.bottom() - 8:
                start_cursor = QTextCursor(self.document())
                start_cursor.setPosition(self._selection_range[0])
                start_rect = self.cursorRect(start_cursor)
                y = self.viewport().mapToGlobal(start_rect.topLeft()).y() - h - 8
            global_pos = QPoint(x, max(area.top() + 8, y))
        self.selection_toolbar.move(global_pos)
        self.selection_toolbar.show()
        self.selection_toolbar.raise_()

    def hide_selection_toolbar(self):
        self._selection_timer.stop()
        self.selection_toolbar.hide()

    def keyPressEvent(self, event):
        self.hide_selection_toolbar()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier and self.textCursor().hasSelection():
            shortcuts = {Qt.Key_B: 'bold', Qt.Key_I: 'italic', Qt.Key_U: 'underline'}
            if event.key() in shortcuts and not (modifiers & (Qt.AltModifier | Qt.MetaModifier)):
                cursor = self.textCursor(); self._selection_range = (cursor.selectionStart(), cursor.selectionEnd())
                self.apply_format_action(shortcuts[event.key()]); return
            if event.key() == Qt.Key_S and modifiers & Qt.ShiftModifier:
                cursor = self.textCursor(); self._selection_range = (cursor.selectionStart(), cursor.selectionEnd())
                self.apply_format_action('strike'); return
        if (self.manuscript_style.smart_quotes and event.text() == '"'
                and not (event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier))):
            cursor = self.textCursor()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            quote = smart_double_quote(self.toPlainText(), cursor.position())
            cursor.insertText(quote)
            self.setTextCursor(cursor)
            return
        super().keyPressEvent(event)

    def apply_format_action(self, action: str):
        if not self._selection_range or self.isReadOnly():
            self.hide_selection_toolbar(); return
        old = self.toPlainText()
        start, end = self._selection_range
        if action in {'bold', 'italic', 'underline', 'strike', 'code'}:
            new, new_start, new_end = toggle_inline(old, start, end, action)
        elif action in {'paragraph', 'heading', 'bullet', 'numbered', 'quote'}:
            new, new_start, new_end = apply_block_style(old, start, end, action)
        else:
            self.hide_selection_toolbar(); return
        self._replace_changed_text(old, new, new_start, new_end)
        self.hide_selection_toolbar()
        self.setFocus()
        self.schedule_formatting(immediate=True)

    def _replace_changed_text(self, old: str, new: str, select_start: int, select_end: int):
        if old == new:
            return
        prefix = 0
        max_prefix = min(len(old), len(new))
        while prefix < max_prefix and old[prefix] == new[prefix]:
            prefix += 1
        suffix = 0
        max_suffix = min(len(old) - prefix, len(new) - prefix)
        while suffix < max_suffix and old[len(old)-1-suffix] == new[len(new)-1-suffix]:
            suffix += 1
        old_end = len(old) - suffix
        new_end = len(new) - suffix
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(prefix)
        cursor.setPosition(old_end, QTextCursor.KeepAnchor)
        cursor.insertText(new[prefix:new_end])
        cursor.endEditBlock()
        max_pos = max(0, self.document().characterCount() - 1)
        cursor.setPosition(min(select_start, max_pos))
        cursor.setPosition(min(select_end, max_pos), QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self._selection_range = (min(select_start, max_pos), min(select_end, max_pos))

    def _set_block_format(self, block, kind: str, previous_kind: str | None):
        cursor = QTextCursor(block)
        fmt = QTextBlockFormat()
        fmt.setAlignment(Qt.AlignLeft)
        fmt.setLineHeight(self.manuscript_style.line_spacing_percent, QTextBlockFormat.ProportionalHeight)
        fmt.setBottomMargin(float(self.manuscript_style.paragraph_spacing_px))
        fmt.setTopMargin(0)
        fmt.setLeftMargin(0)
        fmt.setRightMargin(0)
        fmt.setTextIndent(0)

        if kind == 'normal' and previous_kind == 'normal':
            fmt.setTextIndent(float(self.manuscript_style.paragraph_indent_px))
        elif kind == 'heading':
            fmt.setTopMargin(14); fmt.setBottomMargin(10)
        elif kind == 'quote':
            fmt.setLeftMargin(22); fmt.setBottomMargin(10)
        elif kind in {'bullet', 'numbered'}:
            fmt.setLeftMargin(24)
        elif kind == 'scene':
            fmt.setAlignment(Qt.AlignCenter); fmt.setTopMargin(18); fmt.setBottomMargin(18)
        elif kind == 'empty':
            fmt.setBottomMargin(2)
        if block.blockFormat() != fmt:
            cursor.setBlockFormat(fmt)

    @staticmethod
    def _block_kind(text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return 'empty'
        if stripped == '***':
            return 'scene'
        if text.startswith('## '):
            return 'heading'
        if text.startswith('> '):
            return 'quote'
        if re.match(r'^[-*]\s+', text):
            return 'bullet'
        if re.match(r'^\d+\.\s+', text):
            return 'numbered'
        return 'normal'

    def _extra_selection(self, block, start: int, length: int, fmt: QTextCharFormat):
        if length <= 0:
            return None
        selection = QTextEdit.ExtraSelection()
        cursor = QTextCursor(self.document())
        cursor.setPosition(block.position() + start)
        cursor.setPosition(block.position() + start + length, QTextCursor.KeepAnchor)
        selection.cursor = cursor
        selection.format = fmt
        return selection

    def _marker_selection(self, block, start: int, length: int, background: QColor):
        fmt = QTextCharFormat()
        fmt.setForeground(background)
        fmt.setFontPointSize(1.0)
        return self._extra_selection(block, start, length, fmt)

    def _apply_inline_formats(self, block, text: str, content_offset: int, extras: list):
        theme = self._theme()
        background = QColor(theme['editor'])
        for kind, rx in self.INLINE_PATTERNS:
            for match in rx.finditer(text):
                full_start, full_end = match.span(0)
                inner_start, inner_end = match.span(1)
                opening = self._marker_selection(block, content_offset + full_start, inner_start - full_start, background)
                closing = self._marker_selection(block, content_offset + inner_end, full_end - inner_end, background)
                if opening: extras.append(opening)
                if closing: extras.append(closing)
                fmt = QTextCharFormat()
                if kind == 'bold': fmt.setFontWeight(QFont.Weight.Bold)
                elif kind == 'italic': fmt.setFontItalic(True)
                elif kind == 'underline': fmt.setFontUnderline(True)
                elif kind == 'strike': fmt.setFontStrikeOut(True)
                elif kind == 'code':
                    fmt.setFontFamilies(['Consolas', 'Courier New'])
                    fmt.setBackground(QColor(theme['panel2']))
                styled = self._extra_selection(block, content_offset + inner_start, inner_end - inner_start, fmt)
                if styled: extras.append(styled)

    def apply_visual_formatting(self):
        if self._formatting:
            return
        self._formatting = True
        signals_were_blocked = self.signalsBlocked()
        self.blockSignals(True)
        old = self.textCursor()
        old_pos, old_anchor = old.position(), old.anchor()
        extras = []
        try:
            theme = self._theme()
            background = QColor(theme['editor'])
            muted = QColor(theme['muted'])
            previous_kind = None
            block = self.document().begin()
            while block.isValid():
                text = block.text()
                kind = self._block_kind(text)
                self._set_block_format(block, kind, previous_kind)

                content_offset = 0
                display_text = text
                if kind == 'scene':
                    hidden = self._marker_selection(block, 0, len(text), background)
                    if hidden: extras.append(hidden)
                elif kind == 'heading':
                    hidden = self._marker_selection(block, 0, 3, background)
                    if hidden: extras.append(hidden)
                    content_offset = 3; display_text = text[3:]
                    fmt = QTextCharFormat(); fmt.setFontWeight(QFont.Weight.DemiBold); fmt.setFontPointSize(float(self.typography.point_size + 2))
                    styled = self._extra_selection(block, content_offset, len(display_text), fmt)
                    if styled: extras.append(styled)
                elif kind == 'quote':
                    hidden = self._marker_selection(block, 0, 2, background)
                    if hidden: extras.append(hidden)
                    content_offset = 2; display_text = text[2:]
                    fmt = QTextCharFormat(); fmt.setFontItalic(True); fmt.setForeground(muted)
                    styled = self._extra_selection(block, content_offset, len(display_text), fmt)
                    if styled: extras.append(styled)
                else:
                    self._apply_inline_formats(block, text, 0, extras)

                if kind in {'heading', 'quote'}:
                    self._apply_inline_formats(block, display_text, content_offset, extras)
                previous_kind = kind
                block = block.next()
            self.setExtraSelections(extras)
        finally:
            max_pos = max(0, self.document().characterCount() - 1)
            restore = QTextCursor(self.document())
            restore.setPosition(min(old_anchor, max_pos))
            restore.setPosition(min(old_pos, max_pos), QTextCursor.KeepAnchor)
            self.setTextCursor(restore)
            self.blockSignals(signals_were_blocked)
            self._formatting = False
            self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Scene breaks are stored as literal *** but rendered as a quiet divider.
        painter = QPainter(self.viewport())
        theme = self._theme()
        color = QColor(theme['muted'])
        color.setAlpha(145)
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        block = self.document().begin()
        while block.isValid():
            if block.text().strip() == '***':
                cursor = QTextCursor(block)
                rect = self.cursorRect(cursor)
                y = rect.center().y() + max(4, rect.height() // 2)
                width = self.viewport().width()
                center = width // 2
                gap = 48
                extent = min(180, max(70, width // 4))
                painter.drawLine(center - extent, y, center - gap, y)
                painter.drawLine(center + gap, y, center + extent, y)
                painter.drawText(center - 28, y - 8, 56, 16, Qt.AlignCenter, '•  •  •')
            block = block.next()
        painter.end()
