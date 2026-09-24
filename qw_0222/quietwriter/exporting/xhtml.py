from __future__ import annotations

import html
import re
from dataclasses import dataclass

from ..manuscript_markup import is_scene_break_line, parse_inline_spans


_HEADING_RE = re.compile(r'^(#{2,6})\s+(.+?)\s*$')
_BULLET_RE = re.compile(r'^[-*]\s+(.+)$')
_NUMBER_RE = re.compile(r'^\d+\.\s+(.+)$')
_TAGS = {
    'bold': ('<strong>', '</strong>'),
    'italic': ('<em>', '</em>'),
    'underline': ('<u>', '</u>'),
    'strike': ('<s>', '</s>'),
    'code': ('<code>', '</code>'),
}


@dataclass(frozen=True)
class RenderedHeading:
    anchor: str
    text: str
    level: int


@dataclass(frozen=True)
class RenderedMarkdown:
    html: str
    headings: tuple[RenderedHeading, ...]


def render_inline(text: str) -> str:
    """Render the small inline syntax QuietWriter itself can create.

    This intentionally is not a general HTML/Markdown passthrough: raw manuscript
    HTML is escaped, while only QuietWriter's paired formatting markers become
    XHTML elements.
    """

    spans = parse_inline_spans(text)
    if not spans:
        return html.escape(text)

    marker = [False] * len(text)
    opens: dict[int, list] = {}
    closes: dict[int, list] = {}
    for span in spans:
        for start, end in span.marker_ranges:
            for index in range(max(0, start), min(len(text), end)):
                marker[index] = True
        opens.setdefault(span.content_start, []).append(span)
        closes.setdefault(span.content_end, []).append(span)

    out: list[str] = []
    for index in range(len(text) + 1):
        # Inner spans close first; outer spans open first.
        for span in sorted(closes.get(index, ()), key=lambda item: item.content_start, reverse=True):
            out.append(_TAGS[span.kind][1])
        for span in sorted(opens.get(index, ()), key=lambda item: item.content_end, reverse=True):
            out.append(_TAGS[span.kind][0])
        if index < len(text) and not marker[index]:
            out.append(html.escape(text[index]))
    return ''.join(out)


def render_markdown(markdown: str, anchor_prefix: str = 'h') -> RenderedMarkdown:
    """Convert QuietWriter manuscript Markdown to conservative EPUB XHTML."""

    lines = markdown.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out: list[str] = []
    headings: list[RenderedHeading] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    quote_lines: list[str] = []
    heading_counter = 0

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            text = ' '.join(piece.strip() for piece in paragraph if piece.strip())
            if text:
                out.append(f'<p>{render_inline(text)}</p>')
            paragraph = []

    def close_list():
        nonlocal list_kind
        if list_kind:
            out.append(f'</{list_kind}>')
            list_kind = None

    def flush_quote():
        nonlocal quote_lines
        if quote_lines:
            text = ' '.join(piece.strip() for piece in quote_lines if piece.strip())
            out.append(f'<blockquote><p>{render_inline(text)}</p></blockquote>')
            quote_lines = []

    def flush_all():
        flush_paragraph(); close_list(); flush_quote()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_all()
            continue
        if is_scene_break_line(line):
            flush_all()
            out.append('<div class="scene-break" aria-label="Scene break">* * *</div>')
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_all()
            level = min(6, max(2, len(heading_match.group(1))))
            heading_counter += 1
            anchor = f'{anchor_prefix}-{heading_counter}'
            heading_text = heading_match.group(2).strip()
            headings.append(RenderedHeading(anchor=anchor, text=heading_text, level=level))
            out.append(f'<h{level} id="{html.escape(anchor, quote=True)}">{render_inline(heading_text)}</h{level}>')
            continue
        if stripped.startswith('> '):
            flush_paragraph(); close_list()
            quote_lines.append(stripped[2:].strip())
            continue
        bullet = _BULLET_RE.match(stripped)
        number = _NUMBER_RE.match(stripped)
        if bullet or number:
            flush_paragraph(); flush_quote()
            wanted = 'ul' if bullet else 'ol'
            if list_kind != wanted:
                close_list(); list_kind = wanted; out.append(f'<{wanted}>')
            value = (bullet or number).group(1)
            out.append(f'<li>{render_inline(value)}</li>')
            continue
        close_list(); flush_quote()
        paragraph.append(line)

    flush_all()
    return RenderedMarkdown('\n'.join(out), tuple(headings))


def xhtml_document(title: str, body: str, language: str = 'nl', body_class: str = '') -> str:
    class_attr = f' class="{html.escape(body_class, quote=True)}"' if body_class else ''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{html.escape(language, quote=True)}" lang="{html.escape(language, quote=True)}">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/book.css" />
</head>
<body{class_attr}>
{body}
</body>
</html>
'''
