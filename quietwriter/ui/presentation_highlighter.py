from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontMetricsF, QTextCharFormat, QSyntaxHighlighter

from ..document_view import parse_block_line, text_for_language_tools
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
        # sizes on some Windows/PySide6 combinations. One point keeps ordinary
        # Markdown syntax visually unobtrusive without changing its geometry.
        fmt.setFontPointSize(1.0)
        return fmt

    def _hidden_todo_marker_format(self) -> QTextCharFormat:
        """Collapse a QuietWriter todo marker without pulling prose backwards.

        A fixed negative spacing (for example -2 px) is unsafe: at 1 pt the
        glyph itself is much narrower, so surrounding manuscript text overlaps.
        Use the actual average glyph width of the 1 pt editor font instead.
        This makes the marker close to zero-width while keeping normal hidden
        Markdown markers (such as ** around bold text) untouched.
        """
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.editor._theme()['editor']))
        font = QFont(self.editor.font())
        font.setPointSizeF(1.0)
        fmt.setFont(font)
        try:
            width = float(QFontMetricsF(font).averageCharWidth())
            if width > 0:
                fmt.setFontLetterSpacingType(QFont.SpacingType.AbsoluteSpacing)
                fmt.setFontLetterSpacing(-width)
        except Exception:
            pass
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

    def _apply_inline(self, text: str, offset: int, base: QTextCharFormat, marker_ranges: list[tuple[int, int]], spans=None):
        spans = list(spans if spans is not None else parse_block_line(text).inline_spans)
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
        for a, b in zip(points, points[1:], strict=False):
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
        block_view = parse_block_line(text)
        kind = 'normal' if block_view.kind == 'paragraph' else block_view.kind
        hidden = self._hidden_marker_format()
        marker_ranges: list[tuple[int, int]] = []

        # Open points are source-level QuietWriter markers, but writers should see
        # only their own text. Hide marker comments and give the visible payload a
        # restrained highlight. QTextHighlighter block state carries a placeholder
        # across paragraph boundaries without changing the source document.
        in_todo = self.previousBlockState() == 1
        token_re = __import__('re').compile(
            r'<!--\s*qw:todo:[0-9a-fA-F-]{8,}\s*-->'
            r'|<!--\s*qw:todo\s+id=[^>]+-->'
            r'|<!--\s*/qw:todo\s*-->'
        )
        todo_fmt = QTextCharFormat()
        todo_fmt.setBackground(QColor(self.editor._theme().get('accent_soft', self.editor._theme().get('panel2'))))
        hidden_todo = self._hidden_todo_marker_format()
        cursor = 0
        active = in_todo
        for match in token_re.finditer(text):
            if active and match.start() > cursor:
                self.setFormat(cursor, match.start() - cursor, todo_fmt)
            self.setFormat(match.start(), match.end() - match.start(), hidden_todo)
            marker_ranges.append((match.start(), match.end()))
            if 'qw:todo' in match.group(0) and '/qw:todo' not in match.group(0):
                active = True
            else:
                active = False
            cursor = match.end()
        if active and cursor < len(text):
            self.setFormat(cursor, len(text) - cursor, todo_fmt)
        self.setCurrentBlockState(1 if active else 0)

        if kind == 'scene':
            if text:
                self.setFormat(0, len(text), hidden)
                marker_ranges.append((0, len(text)))
            return

        if kind == 'image':
            # Managed image Markdown remains the canonical source, but the writer
            # interacts with a protected overlay card. Collapse the source line so
            # UUID paths and Markdown syntax are never presented as editable prose.
            if text:
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(self.editor._theme()['editor']))
                fmt.setFontPointSize(1.0)
                self.setFormat(0, len(text), fmt)
            return

        prefix_len = max(0, block_view.content_start - block_view.start)
        visible_text = text[prefix_len:]
        if prefix_len:
            self.setFormat(0, prefix_len, hidden)
            marker_ranges.append((0, prefix_len))

        base = self._base_format(kind)
        if visible_text and kind in {'heading', 'quote'}:
            self.setFormat(prefix_len, len(visible_text), base)

        # Literal escape backslashes are persistent syntax but not writer-visible.
        # Hide them before spelling/inline presentation; the escaped punctuation
        # itself remains visible and is deliberately not interpreted as markup.
        for a, b in block_view.escape_ranges:
            self.setFormat(a, b - a, hidden)
            marker_ranges.append((a, b))

        inline_spans = []
        for span in block_view.inline_spans:
            if span.open_start < prefix_len:
                continue
            from dataclasses import replace
            inline_spans.append(replace(
                span,
                open_start=span.open_start-prefix_len, open_end=span.open_end-prefix_len,
                content_start=span.content_start-prefix_len, content_end=span.content_end-prefix_len,
                close_start=span.close_start-prefix_len, close_end=span.close_end-prefix_len,
            ))
        self._apply_inline(visible_text, prefix_len, base, marker_ranges, inline_spans)
        self._apply_spelling(text_for_language_tools(text), marker_ranges)
