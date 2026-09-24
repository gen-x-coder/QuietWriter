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
    """Render QuietWriter's supported inline markup as safe XHTML."""
    spans = parse_inline_spans(text)
    marker_positions: set[int] = set()
    starts: dict[int, list] = {}
    ends: dict[int, list] = {}
    for span in spans:
        for a, b in span.marker_ranges:
            marker_positions.update(range(a, b))
        starts.setdefault(span.content_start, []).append(span)
        ends.setdefault(span.content_end, []).append(span)
    for bucket in starts.values():
        bucket.sort(key=lambda s: (-(s.content_end - s.content_start), s.kind))
    for bucket in ends.values():
        bucket.sort(key=lambda s: ((s.content_end - s.content_start), s.kind))

    out: list[str] = []
    for i in range(len(text) + 1):
        for span in ends.get(i, ()):
            out.append(_TAGS[span.kind][1])
        for span in starts.get(i, ()):
            out.append(_TAGS[span.kind][0])
        if i < len(text) and i not in marker_positions:
            out.append(html.escape(text[i], quote=False))
    return ''.join(out)


def _image_href(reference: str, image_hrefs: dict[str, str] | None) -> str | None:
    if not image_hrefs:
        return None
    normalized = str(reference or '').replace('\\', '/')
    return image_hrefs.get(normalized) or image_hrefs.get(Path(normalized).name)


def markdown_to_xhtml(text: str, image_hrefs: dict[str, str] | None = None) -> str:
    """Render QuietWriter's deliberately small manuscript Markdown subset."""
    text = (text or '').replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    blocks: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            value = ' '.join(part.strip() for part in paragraph).strip()
            if value:
                blocks.append(f'<p>{inline_to_xhtml(value)}</p>')
            paragraph = []

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
            flush_paragraph(); flush_list(); continue
        image = image_reference_for_line(stripped)
        if image:
            flush_paragraph(); flush_list()
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
            flush_paragraph(); flush_list(); blocks.append('<div class="scene-break" aria-label="Scene break">* * *</div>'); continue
        if stripped.startswith('## '):
            flush_paragraph(); flush_list(); blocks.append(f'<h2>{inline_to_xhtml(stripped[3:].strip())}</h2>'); continue
        if stripped.startswith('> '):
            flush_paragraph(); flush_list(); blocks.append(f'<blockquote><p>{inline_to_xhtml(stripped[2:].strip())}</p></blockquote>'); continue
        bullet = re.match(r'^[-*]\s+(.+)$', stripped)
        ordered = re.match(r'^\d+\.\s+(.+)$', stripped)
        if bullet or ordered:
            flush_paragraph()
            wanted = 'ol' if ordered else 'ul'
            if list_kind and list_kind != wanted:
                flush_list()
            list_kind = wanted
            list_items.append((ordered or bullet).group(1))
            continue
        if list_kind:
            flush_list()
        paragraph.append(stripped)

    flush_paragraph(); flush_list()
    return '\n'.join(blocks)
