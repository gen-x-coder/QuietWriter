from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter

from ..manuscript_markup import parse_inline_spans
from ..spell_engine import WORD_RE


class ManuscriptHighlighter(QSyntaxHighlighter):
    """Compose manuscript Markdown styles without changing the source text."""

    def __init__(self, editor):
        super().__init__(editor.document())
        self.editor = editor
        self.dictionary = None
        self.spell_active = False

    def set_dictionary(self, dictionary):
        self.dictionary = dictionary
        self.rehighlight()

    def set_active(self, active: bool):
        self.spell_active = bool(active)
        self.rehighlight()

    def _hidden_marker_format(self) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.editor._theme()['editor']))
        # DirectWrite can fail to outline glyphs at pathological sub-point
        # sizes on some Windows/PySide6 combinations. One point keeps syntax
        # visually collapsed without asking the font engine for 0.1pt glyphs.
        fmt.setFontPointSize(1.0)
        return fmt

    def _base_format(self, kind: str) -> QTextCharFormat:
        fmt = QTextCharFormat()
        if kind == 'heading':
            fmt.setFontWeight(QFont.Weight.DemiBold)
            fmt.setFontPointSize(float(self.editor.typography.point_size + 2))
        elif kind == 'quote':
            fmt.setFontItalic(True)
            fmt.setForeground(QColor(self.editor._theme()['muted']))
        return fmt

    @staticmethod
    def _prefix(text: str, kind: str) -> tuple[int, str]:
        import re
        if kind == 'heading' and text.startswith('## '):
            return 3, text[3:]
        if kind == 'quote' and text.startswith('> '):
            return 2, text[2:]
        if kind == 'bullet':
            m = re.match(r'^[-*]\s+', text)
            if m:
                return m.end(), text[m.end():]
        if kind == 'numbered':
            m = re.match(r'^\d+\.\s+', text)
            if m:
                return m.end(), text[m.end():]
        return 0, text

    def _composed_format(self, base: QTextCharFormat, styles: set[str]) -> QTextCharFormat:
        fmt = QTextCharFormat(base)
        if 'bold' in styles:
            fmt.setFontWeight(QFont.Weight.Bold)
        if 'italic' in styles:
            fmt.setFontItalic(True)
        if 'underline' in styles:
            fmt.setFontUnderline(True)
        if 'strike' in styles:
            fmt.setFontStrikeOut(True)
        if 'code' in styles:
            fmt.setFontFamilies(['Consolas', 'Courier New'])
            fmt.setBackground(QColor(self.editor._theme()['panel2']))
        return fmt

    def _apply_inline(self, text: str, offset: int, base: QTextCharFormat, marker_ranges: list[tuple[int, int]]):
        spans = parse_inline_spans(text)
        if not spans:
            return

        # Compose all active styles per source segment.  Calling setFormat once
        # per composed run is essential: applying italic after bold must not
        # overwrite the bold weight (and vice versa).
        boundaries = {0, len(text)}
        for span in spans:
            boundaries.add(span.content_start)
            boundaries.add(span.content_end)
            for a, b in span.marker_ranges:
                marker_ranges.append((offset + a, offset + b))
                boundaries.add(a); boundaries.add(b)
        points = sorted(boundaries)
        for a, b in zip(points, points[1:]):
            if b <= a:
                continue
            styles = {
                span.kind for span in spans
                if span.content_start <= a and b <= span.content_end
            }
            if styles:
                self.setFormat(offset + a, b - a, self._composed_format(base, styles))

        # Markers are hidden last so no composed style can make them visible.
        hidden = self._hidden_marker_format()
        for span in spans:
            for a, b in span.marker_ranges:
                self.setFormat(offset + a, b - a, hidden)

    @staticmethod
    def _inside_ranges(position: int, ranges: list[tuple[int, int]]) -> bool:
        return any(start <= position < end for start, end in ranges)

    def _apply_spelling(self, text: str, marker_ranges: list[tuple[int, int]]):
        if not self.spell_active or not self.dictionary or not self.dictionary.words:
            return
        for match in WORD_RE.finditer(text):
            if self._inside_ranges(match.start(), marker_ranges):
                continue
            if self.dictionary.known(match.group(0)):
                continue
            fmt = QTextCharFormat(self.format(match.start()))
            fmt.setUnderlineColor(QColor('#c84b4b'))
            fmt.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
            self.setFormat(match.start(), len(match.group(0)), fmt)

    def highlightBlock(self, text: str):
        kind = self.editor._block_kind(text)
        hidden = self._hidden_marker_format()
        marker_ranges: list[tuple[int, int]] = []

        if kind == 'scene':
            if text:
                self.setFormat(0, len(text), hidden)
                marker_ranges.append((0, len(text)))
            return

        prefix_len, visible_text = self._prefix(text, kind)
        if prefix_len:
            self.setFormat(0, prefix_len, hidden)
            marker_ranges.append((0, prefix_len))

        base = self._base_format(kind)
        if visible_text and kind in {'heading', 'quote'}:
            self.setFormat(prefix_len, len(visible_text), base)

        self._apply_inline(visible_text, prefix_len, base, marker_ranges)
        self._apply_spelling(text, marker_ranges)
