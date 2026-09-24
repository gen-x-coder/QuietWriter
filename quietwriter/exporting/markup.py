from __future__ import annotations

import html
import re
from pathlib import Path

from ..manuscript_markup import is_scene_break_line, parse_inline_spans
from ..media.markup import image_reference_for_line


_TAGS = {
    'bold': ('<strong>', '</strong>'),
    'italic': ('<em>', '</em>'),
    'underline': ('<u>', '</u>'),
    'strike': ('<s>', '</s>'),
    'code': ('<code>', '</code>'),
}


def inline_to_xhtml(text: str) -> str:
    """Render QuietWriter's supported inline markup as balanced safe XHTML.

    QuietWriter deliberately allows crossed Markdown spans because formatting is
    selection-based. XML/XHTML does not: ``**one *two** three*`` cannot become
    ``<strong>one <em>two</strong> three</em>``. Render the visible source one
    character run at a time and transition between the active span stacks. When
    an outer span ends while an inner one continues, the inner tag is closed,
    the outer tag is closed, and the inner tag is reopened. The resulting XHTML
    is always properly nested while preserving the intended visual overlap.
    """
    spans = parse_inline_spans(text)
    if not spans:
        return html.escape(text, quote=False)

    marker_positions: set[int] = set()
    for span in spans:
        for a, b in span.marker_ranges:
            marker_positions.update(range(a, b))

    def active_at(position: int):
        active = [
            span for span in spans
            if span.content_start <= position < span.content_end and span.kind in _TAGS
        ]
        # Stable nesting order: spans that started first are outer. If starts are
        # equal, the one ending later is outer.
        active.sort(key=lambda span: (span.content_start, -span.content_end, span.kind))
        return active

    out: list[str] = []
    stack: list = []

    def transition(target: list):
        nonlocal stack
        common = 0
        while common < len(stack) and common < len(target) and stack[common] is target[common]:
            common += 1
        for span in reversed(stack[common:]):
            out.append(_TAGS[span.kind][1])
        for span in target[common:]:
            out.append(_TAGS[span.kind][0])
        stack = list(target)

    for i, ch in enumerate(text):
        if i in marker_positions:
            continue
        transition(active_at(i))
        out.append(html.escape(ch, quote=False))

    transition([])
    return ''.join(out)


def _image_href(reference: str, image_hrefs: dict[str, str] | None) -> str | None:
    if not image_hrefs:
        return None
    normalized = str(reference or '').replace('\\', '/')
    return image_hrefs.get(normalized) or image_hrefs.get(Path(normalized).name)


def _markdown_to_xhtml(
    text: str,
    image_hrefs: dict[str, str] | None = None,
    *,
    collect_headings: bool = False,
) -> tuple[str, list[tuple[str, str]]]:
    """Render QuietWriter manuscript Markdown and optionally collect h2 anchors."""
    text = (text or '').replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []
    headings: list[tuple[str, str]] = []
    heading_index = 0

    def flush_list():
        nonlocal list_kind, list_items
        if list_kind and list_items:
            tag = 'ol' if list_kind == 'ol' else 'ul'
            blocks.append(f'<{tag}>' + ''.join(f'<li>{inline_to_xhtml(item)}</li>' for item in list_items) + f'</{tag}>')
        list_kind = None
        list_items = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_list()
            # One Enter already creates a new paragraph in QuietWriter. A blank
            # source block is therefore an intentional extra paragraph break,
            # represented explicitly rather than being used to decide whether
            # neighbouring non-empty lines belong to the same paragraph.
            continue
        image = image_reference_for_line(stripped)
        if image:
            flush_list()
            href = _image_href(image.path, image_hrefs)
            if href:
                caption = f'<figcaption>{html.escape(image.caption)}</figcaption>' if image.caption else ''
                blocks.append(
                    '<figure class="manuscript-image">'
                    f'<img src="{html.escape(href, quote=True)}" alt="{html.escape(image.alt, quote=True)}"/>'
                    f'{caption}</figure>'
                )
            else:
                # Preflight normally blocks this situation. Keep the renderer
                # safe if called directly with an incomplete document.
                fallback = image.alt or image.caption or 'Afbeelding ontbreekt'
                blocks.append(f'<p class="missing-image">[{html.escape(fallback)}]</p>')
            continue
        if is_scene_break_line(stripped):
            flush_list(); blocks.append('<div class="scene-break" aria-label="Scene break">* * *</div>'); continue
        if stripped.startswith('## '):
            flush_list()
            label_source = stripped[3:].strip()
            heading_index += 1
            heading_id = f'h-{heading_index}'
            label_xhtml = inline_to_xhtml(label_source)
            blocks.append(f'<h2 id="{heading_id}">{label_xhtml}</h2>')
            if collect_headings:
                # Navigation labels are plain text. Strip QuietWriter's own inline
                # markers without attempting to derive text back from XHTML.
                marker_positions = {
                    pos
                    for span in parse_inline_spans(label_source)
                    for a, b in span.marker_ranges
                    for pos in range(a, b)
                }
                label = ''.join(ch for idx, ch in enumerate(label_source) if idx not in marker_positions)
                headings.append((heading_id, label))
            continue
        if stripped.startswith('> '):
            flush_list(); blocks.append(f'<blockquote><p>{inline_to_xhtml(stripped[2:].strip())}</p></blockquote>'); continue
        bullet = re.match(r'^[-*]\s+(.+)$', stripped)
        ordered = re.match(r'^\d+\.\s+(.+)$', stripped)
        if bullet or ordered:
            wanted = 'ol' if ordered else 'ul'
            if list_kind and list_kind != wanted:
                flush_list()
            list_kind = wanted
            list_items.append((ordered or bullet).group(1))
            continue
        if list_kind:
            flush_list()
        # In QuietWriter every QTextBlock is a manuscript paragraph: one Enter
        # creates the next paragraph. Do not apply CommonMark's soft-line folding.
        blocks.append(f'<p>{inline_to_xhtml(stripped)}</p>')

    flush_list()
    return '\n'.join(blocks), headings


def markdown_to_xhtml(text: str, image_hrefs: dict[str, str] | None = None) -> str:
    """Render QuietWriter's deliberately small manuscript Markdown subset."""
    body, _headings = _markdown_to_xhtml(text, image_hrefs, collect_headings=False)
    return body


def markdown_to_xhtml_with_headings(
    text: str, image_hrefs: dict[str, str] | None = None
) -> tuple[str, list[tuple[str, str]]]:
    """Render manuscript XHTML plus stable ``(id, label)`` h2 anchors."""
    return _markdown_to_xhtml(text, image_hrefs, collect_headings=True)
