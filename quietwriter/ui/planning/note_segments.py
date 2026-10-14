"""Lossless views onto the existing Markdown-based Planning notes file.

A level-two heading starts a note, except inside a fenced code block.
No file format migration or reserialization is performed here.
"""
from __future__ import annotations

import re

# Only CR, LF and CRLF are Markdown line boundaries. str.splitlines() also
# splits on Unicode separators (NEL, VT, FF, U+2028, U+2029), corrupting
# source offsets when those characters occur inside a note.
_SOURCE_LINE = re.compile(r'[^\r\n]*(?:\r\n|\r|\n|$)')

_HEADING = re.compile(r'^## ([^\r\n]+)\r?$', re.MULTILINE)
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')


def split_notes(source: str) -> list[tuple[int, int, str | None, str]]:
    """Return (start, end, title, body) slices into *unaltered* source."""
    headings = []
    fence_char = None
    fence_size = 0
    offset = 0
    for match_line in _SOURCE_LINE.finditer(source):
        line = match_line.group(0)
        if not line:
            continue
        logical = line.rstrip('\r\n')
        fence = _FENCE.match(logical)
        if fence:
            marker, rest = fence.groups()
            if fence_char is None:
                fence_char, fence_size = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size and not rest.strip():
                fence_char, fence_size = None, 0
        elif fence_char is None:
            match = _HEADING.fullmatch(logical)
            if match and match.group(1).strip():
                headings.append((offset, offset + len(logical), match.group(1).strip()))
        offset += len(line)
    result = []
    start = headings[0][0] if headings else len(source)
    if not headings or source[:start].strip():
        result.append((0, start, None, source[:start]))
    for index, (begin, body_start, title) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(source)
        result.append((begin, end, title, source[body_start:end]))
    return result


def replace_note(source: str, start: int, end: int, replacement: str) -> str:
    """Replace exactly one currently parsed card, leaving every other byte alone.

    Offsets from stale cards must never be allowed to remove a different note.
    The caller is responsible for converting the edited title/body to Markdown.
    """
    if not any(a == start and b == end for a, b, _, _ in split_notes(source)):
        raise ValueError('De notitie is tussentijds veranderd; laad de kaarten opnieuw.')
    return source[:start] + replacement + source[end:]
