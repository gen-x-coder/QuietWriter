
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor, QFont, QTextCursor, QTextCharFormat
from PySide6.QtWidgets import QTextEdit

from ..themes import THEMES
from ..typography import WritingTypography, typography_from_values

class ManuscriptEditor(QTextEdit):
    """Rustige schrijfruimte met begrensde tekstkolom en lichte scene-break styling."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_text_width = 850
        self.setAcceptRichText(False)
        self._formatting_scene_breaks = False
        settings = QSettings('QuietWriter', 'QuietWriter')
        self.apply_typography(WritingTypography.from_settings(settings))
        self._update_margins()

    def apply_typography(self, typography: WritingTypography):
        """Apply writing typography without coupling family, size or theme.

        The editor stores plain text. Font family/size therefore live entirely in
        the QTextDocument default font instead of being written into every
        character format. This makes switching fonts immediate and repeatable.
        """
        font = typography.body_font()
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.document().markContentsDirty(0, self.document().characterCount())
        self.apply_scene_break_formatting()
        self.viewport().update()

    def set_editor_font(self, preferred: str, point_size: int | None = None):
        # Backwards-compatible wrapper used by a few call sites.
        if point_size is None:
            point_size = QSettings('QuietWriter', 'QuietWriter').value('editor_font_size', 15, int)
        self.apply_typography(typography_from_values(preferred, point_size))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_margins()

    def _update_margins(self):
        side = max(42, (max(0, self.width()) - self.max_text_width) // 2)
        self.setViewportMargins(side, 30, side, 42)

    def apply_scene_break_formatting(self):
        """Render regels die exact *** bevatten als rustige gecentreerde scene break.

        De bron blijft platte Markdown; alleen de QTextDocument-opmaak verandert.
        """
        if self._formatting_scene_breaks:
            return
        self._formatting_scene_breaks = True
        signals_were_blocked = self.signalsBlocked()
        self.blockSignals(True)
        old_cursor = self.textCursor()
        old_pos, old_anchor = old_cursor.position(), old_cursor.anchor()
        try:
            block = self.document().begin()
            theme = THEMES.get(str(QSettings('QuietWriter','QuietWriter').value('theme','Helder')), THEMES['Helder'])
            muted = QColor(theme['muted'])
            while block.isValid():
                cur = QTextCursor(block)
                fmt = block.blockFormat()
                is_break = block.text().strip() == '***'
                was_centered = fmt.alignment() == Qt.AlignCenter
                if is_break:
                    if not was_centered or fmt.topMargin() != 14 or fmt.bottomMargin() != 14:
                        fmt.setAlignment(Qt.AlignCenter)
                        fmt.setTopMargin(14)
                        fmt.setBottomMargin(14)
                        cur.setBlockFormat(fmt)
                    cur.select(QTextCursor.BlockUnderCursor)
                    charfmt = QTextCharFormat()
                    charfmt.setForeground(muted)
                    charfmt.setFontLetterSpacing(160)
                    charfmt.setFontWeight(QFont.Weight.DemiBold)
                    cur.mergeCharFormat(charfmt)
                elif was_centered:
                    # Een voormalige scene break is gewone tekst geworden.
                    fmt.setAlignment(Qt.AlignLeft)
                    fmt.setTopMargin(0); fmt.setBottomMargin(0)
                    cur.setBlockFormat(fmt)
                    cur.select(QTextCursor.BlockUnderCursor)
                    charfmt = QTextCharFormat()
                    charfmt.clearForeground()
                    charfmt.setFontLetterSpacing(0)
                    charfmt.setFontWeight(QFont.Weight.Light)
                    cur.mergeCharFormat(charfmt)
                block = block.next()
        finally:
            restore = self.textCursor()
            restore.setPosition(min(old_anchor, max(0, self.document().characterCount()-1)))
            restore.setPosition(min(old_pos, max(0, self.document().characterCount()-1)), QTextCursor.KeepAnchor)
            self.setTextCursor(restore)
            self.blockSignals(signals_were_blocked)
            self._formatting_scene_breaks = False
