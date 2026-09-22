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

_BLOCK_PREFIX_RE = re.compile(r'^(?:##\s+|>\s+|[-*]\s+|\d+\.\s+)')


def toggle_inline(text: str, start: int, end: int, kind: str) -> tuple[str, int, int]:
    """Toggle lightweight Markdown/HTML markup around a selection.

    Returns ``(new_text, new_start, new_end)`` where the new range selects the
    original content rather than the markup characters.  The function is pure so
    it can be regression-tested independently from Qt.
    """
    if kind not in _INLINE or start < 0 or end <= start or end > len(text):
        return text, start, end
    left, right = _INLINE[kind]
    selected = text[start:end]

    if selected.startswith(left) and selected.endswith(right) and len(selected) >= len(left) + len(right):
        inner = selected[len(left):len(selected)-len(right)]
        new = text[:start] + inner + text[end:]
        return new, start, start + len(inner)

    before = text[max(0, start-len(left)):start]
    after = text[end:end+len(right)]
    if before == left and after == right:
        new = text[:start-len(left)] + selected + text[end+len(right):]
        new_start = start - len(left)
        return new, new_start, new_start + len(selected)

    replacement = left + selected + right
    new = text[:start] + replacement + text[end:]
    new_start = start + len(left)
    return new, new_start, new_start + len(selected)


def selected_line_range(text: str, start: int, end: int) -> tuple[int, int]:
    start = max(0, min(start, len(text)))
    end = max(start, min(end, len(text)))
    line_start = text.rfind('\n', 0, start) + 1
    nl = text.find('\n', end)
    line_end = len(text) if nl < 0 else nl
    return line_start, line_end


def _strip_block_prefix(line: str) -> str:
    return _BLOCK_PREFIX_RE.sub('', line, count=1)


def apply_block_style(text: str, start: int, end: int, style: str) -> tuple[str, int, int]:
    """Apply/toggle a simple block style to all selected lines.

    ``heading`` deliberately uses ``##`` because a single ``#`` is reserved for
    QuietWriter chapter boundaries during Markdown import/export.
    """
    if not text:
        return text, start, end
    ls, le = selected_line_range(text, start, end)
    chunk = text[ls:le]
    lines = chunk.split('\n')

    if style == 'paragraph':
        out = [_strip_block_prefix(line) if line.strip() else line for line in lines]
    elif style == 'heading':
        all_set = all((not line.strip()) or line.startswith('## ') for line in lines)
        out = [(_strip_block_prefix(line) if all_set else ('## ' + _strip_block_prefix(line))) if line.strip() else line for line in lines]
    elif style == 'quote':
        all_set = all((not line.strip()) or line.startswith('> ') for line in lines)
        out = [(_strip_block_prefix(line) if all_set else ('> ' + _strip_block_prefix(line))) if line.strip() else line for line in lines]
    elif style == 'bullet':
        all_set = all((not line.strip()) or line.startswith('- ') for line in lines)
        out = [(_strip_block_prefix(line) if all_set else ('- ' + _strip_block_prefix(line))) if line.strip() else line for line in lines]
    elif style == 'numbered':
        numbered = [bool(re.match(r'^\d+\.\s+', line)) for line in lines if line.strip()]
        all_set = bool(numbered) and all(numbered)
        n = 1
        out = []
        for line in lines:
            if not line.strip():
                out.append(line); continue
            body = _strip_block_prefix(line)
            if all_set:
                out.append(body)
            else:
                out.append(f'{n}. {body}'); n += 1
    else:
        return text, start, end

    replacement = '\n'.join(out)
    new_text = text[:ls] + replacement + text[le:]
    # Keep the complete styled lines selected. This is predictable even when
    # prefixes changed the length of the source text.
    return new_text, ls, ls + len(replacement)


def smart_double_quote(text: str, position: int) -> str:
    """Return a typographic opening/closing double quote for the cursor context."""
    position = max(0, min(position, len(text)))
    before = text[:position]
    prev = before[-1] if before else ''
    if not prev or prev.isspace() or prev in '([{<—–-\n':
        return '“'
    return '”'


@dataclass(frozen=True)
class ManuscriptStyle:
    line_spacing_percent: int = 155
    paragraph_indent_px: int = 28
    paragraph_spacing_px: int = 8
    smart_quotes: bool = True

    @classmethod
    def from_settings(cls, settings):
        return cls.from_values(
            settings.value('manuscript_line_spacing', 155, int),
            settings.value('manuscript_indent', 28, int),
            settings.value('manuscript_paragraph_spacing', 8, int),
            settings.value('smart_quotes', True, bool),
        )

    @classmethod
    def from_values(cls, line_spacing=155, paragraph_indent=28, paragraph_spacing=8, smart_quotes=True):
        def _int(value, default, lo, hi):
            try: value = int(value)
            except (TypeError, ValueError): value = default
            return max(lo, min(hi, value))
        return cls(
            _int(line_spacing, 155, 120, 200),
            _int(paragraph_indent, 28, 0, 60),
            _int(paragraph_spacing, 8, 0, 24),
            bool(smart_quotes),
        )
