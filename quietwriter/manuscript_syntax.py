from __future__ import annotations

import re
from dataclasses import dataclass


_INLINE = {
    'bold': ('**', '**'),
    'italic': ('*', '*'),
    'underline': ('<u>', '</u>'),
    'strike': ('~~', '~~'),
    'code': ('`', '`'),
}

_ESCAPABLE_INLINE_CHARS = frozenset('\\*~`<')
_STRUCTURAL_ESCAPE_LEADS = frozenset('- >#!'.replace(' ', ''))


def _is_escaped(text: str, index: int) -> bool:
    """Return True when *index* is preceded by an odd backslash run."""
    slash_count = 0
    i = index - 1
    while i >= 0 and text[i] == '\\':
        slash_count += 1
        i -= 1
    return bool(slash_count % 2)


def escape_ranges(text: str) -> list[tuple[int, int]]:
    """Return presentation-only escape backslashes in source coordinates.

    This is the read-side escape grammar. Structural escapes only count at the
    start of a physical ``\\n`` line; inline escapes are valid anywhere.
    """
    source = text or ''
    ranges: list[tuple[int, int]] = []
    i = 0
    while i + 1 < len(source):
        if source[i] != '\\' or _is_escaped(source, i):
            i += 1
            continue
        nxt = source[i + 1]
        if nxt in _ESCAPABLE_INLINE_CHARS:
            ranges.append((i, i + 1)); i += 2; continue

        line_start = source.rfind('\n', 0, i) + 1
        local = i - line_start
        structural = (
            (local == 0 and nxt in _STRUCTURAL_ESCAPE_LEADS)
            or (nxt == '.' and re.fullmatch(r'\d+', source[line_start:i]))
        )
        if structural:
            ranges.append((i, i + 1)); i += 2; continue
        i += 1
    return ranges


def unescape_literal_text(text: str) -> str:
    """Remove only recognised QuietWriter literal-escape backslashes."""
    source = text or ''
    hidden = {i for a, b in escape_ranges(source) for i in range(a, b)}
    return ''.join(ch for i, ch in enumerate(source) if i not in hidden)


def is_scene_break_line(line: str) -> bool:
    """Return True for QuietWriter's protected scene-break sentinel."""
    return line.strip() == '***'


@dataclass(frozen=True)
class InlineSpan:
    """One paired inline-markup span in source coordinates."""

    kind: str
    open_start: int
    open_end: int
    content_start: int
    content_end: int
    close_start: int
    close_end: int

    @property
    def marker_ranges(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return ((self.open_start, self.open_end), (self.close_start, self.close_end))


def parse_inline_spans(text: str) -> list[InlineSpan]:
    """Parse QuietWriter's deliberately small inline-Markdown subset."""
    spans: list[InlineSpan] = []
    opened: dict[str, tuple[int, int]] = {}
    i = 0
    n = len(text)

    def open_or_close(kind: str, start: int, end: int, *, close_start: int | None = None, close_end: int | None = None):
        if kind in opened:
            o_start, o_end = opened.pop(kind)
            c_start = start if close_start is None else close_start
            c_end = end if close_end is None else close_end
            if c_start >= o_end:
                spans.append(InlineSpan(kind, o_start, o_end, o_end, c_start, c_start, c_end))
        else:
            opened[kind] = (start, end)

    while i < n:
        if 'code' in opened:
            if text.startswith('`', i) and not _is_escaped(text, i):
                open_or_close('code', i, i + 1)
                i += 1
            else:
                i += 1
            continue

        if text.startswith('</u>', i) and not _is_escaped(text, i):
            if 'underline' in opened:
                open_or_close('underline', i, i + 4)
            i += 4
            continue
        if text.startswith('<u>', i) and not _is_escaped(text, i):
            if 'underline' not in opened:
                opened['underline'] = (i, i + 3)
            i += 3
            continue
        if text.startswith('`', i) and not _is_escaped(text, i):
            open_or_close('code', i, i + 1)
            i += 1
            continue
        if text.startswith('~~', i) and not _is_escaped(text, i):
            open_or_close('strike', i, i + 2)
            i += 2
            continue
        if text.startswith('***', i) and not _is_escaped(text, i):
            bold_open = 'bold' in opened
            italic_open = 'italic' in opened
            if bold_open and italic_open:
                o_start, o_end = opened.pop('italic')
                if i >= o_end:
                    spans.append(InlineSpan('italic', o_start, o_end, o_end, i, i, i + 1))
                o_start, o_end = opened.pop('bold')
                if i + 1 >= o_end:
                    spans.append(InlineSpan('bold', o_start, o_end, o_end, i + 1, i + 1, i + 3))
            elif not bold_open and not italic_open:
                opened['bold'] = (i, i + 2)
                opened['italic'] = (i + 2, i + 3)
            else:
                if italic_open:
                    open_or_close('italic', i, i + 1)
                    opened['bold'] = (i + 1, i + 3)
                else:
                    open_or_close('bold', i, i + 2)
                    opened['italic'] = (i + 2, i + 3)
                i += 3
                continue
            i += 3
            continue
        if text.startswith('**', i) and not _is_escaped(text, i):
            open_or_close('bold', i, i + 2)
            i += 2
            continue
        if text.startswith('*', i) and not _is_escaped(text, i):
            open_or_close('italic', i, i + 1)
            i += 1
            continue
        i += 1

    spans.sort(key=lambda s: (s.open_start, -s.close_end, s.kind))
    return spans
