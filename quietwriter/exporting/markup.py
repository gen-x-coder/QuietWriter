from __future__ import annotations

import html
import re
from pathlib import Path

from ..document_view import (content_inline_runs, inline_runs, iter_content_blocks, note_groups,
                             visible_inline_text)


_TAGS = {
    'bold': ('<strong>', '</strong>'),
    'italic': ('<em>', '</em>'),
    'underline': ('<u>', '</u>'),
    'strike': ('<s>', '</s>'),
    'code': ('<code>', '</code>'),
}


def _soft(text: str) -> str:
    """Escape for XHTML; QuietWriter's zachte regeleinde (U+2028, Shift+Enter) wordt <br/>."""
    return html.escape(text or '', quote=False).replace('\u2028', '<br/>')


class NoteCollector:
    """Nummert voetnoten binnen één hoofdstuk en bewaart hun XHTML (1.7).

    *links* is False voor PDF: Qt's rich text heeft geen pop-upnoten nodig, alleen
    een nummer. In EPUB wordt het een echte ``noteref`` met link heen en terug.
    """

    def __init__(self, *, links: bool = True):
        self.links = links
        self.notes: list[str] = []

    def reference(self, runs) -> str:
        number = len(self.notes) + 1
        self.notes.append(_render_runs(runs))
        if not self.links:
            return f'<sup class="noteref">{number}</sup>'
        return (f'<a class="noteref" epub:type="noteref" id="fnref-{number}" href="#fn-{number}">'
                f'<sup>{number}</sup></a>')

    def section(self) -> str:
        if not self.notes:
            return ''
        if not self.links:
            items = ''.join(f'<p class="footnote"><sup>{n}</sup> {body}</p>' for n, body in enumerate(self.notes, 1))
            return f'<hr class="footnotes-rule"/>{items}'
        items = ''.join(
            f'<aside class="footnote" epub:type="footnote" id="fn-{n}">'
            f'<p><a href="#fnref-{n}">{n}.</a> {body}</p></aside>'
            for n, body in enumerate(self.notes, 1)
        )
        return f'<section class="footnotes" epub:type="footnotes"><hr class="footnotes-rule"/>{items}</section>'


def inline_to_xhtml(text: str, runs=None, notes: NoteCollector | None = None) -> str:
    """Render semantic inline runs as balanced safe XHTML.

    When *runs* is omitted the central DocumentView inline parser is used.
    Exporters that already have a parsed DocumentBlock pass its runs directly,
    so source markup is interpreted only once. Voetnoten worden een nummer via
    *notes*; zonder verzamelaar staan ze tussen haakjes in de tekst.
    """
    semantic_runs = tuple(runs) if runs is not None else inline_runs(text)
    if not semantic_runs:
        return _soft(text)
    out: list[str] = []
    pending: list = []
    for kind, value in note_groups(semantic_runs):
        if kind == 'text':
            pending.append(value)
            continue
        out.append(_render_runs(pending)); pending = []
        out.append(notes.reference(value) if notes is not None else f' ({_render_runs(value)})')
    out.append(_render_runs(pending))
    return ''.join(out)


def _render_runs(semantic_runs) -> str:
    if not semantic_runs:
        return ''

    out: list[str] = []
    stack: list[str] = []

    def ordered(styles):
        # Stable canonical tag nesting independent of source marker order.
        order = ('bold', 'italic', 'underline', 'strike', 'code')
        return [kind for kind in order if kind in styles and kind in _TAGS]

    for run in semantic_runs:
        target = ordered(run.styles)
        common = 0
        while common < len(stack) and common < len(target) and stack[common] == target[common]:
            common += 1
        for kind in reversed(stack[common:]):
            out.append(_TAGS[kind][1])
        for kind in target[common:]:
            out.append(_TAGS[kind][0])
        stack = list(target)
        out.append(_soft(run.text))

    for kind in reversed(stack):
        out.append(_TAGS[kind][1])
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
    """Render QuietWriter manuscript semantics as XHTML.

    Block interpretation comes from DocumentView; this renderer only decides
    how those semantic blocks become XHTML.
    """
    source = (text or '').replace('\r\n', '\n').replace('\r', '\n')
    blocks: list[str] = []
    notes = NoteCollector()
    list_kind: str | None = None
    list_items: list[tuple[str, tuple]] = []
    headings: list[tuple[str, str]] = []
    heading_index = 0

    def flush_list():
        nonlocal list_kind, list_items
        if list_kind and list_items:
            tag = 'ol' if list_kind == 'ol' else 'ul'
            blocks.append(f'<{tag}>' + ''.join(f'<li>{inline_to_xhtml(item, runs, notes)}</li>' for item, runs in list_items) + f'</{tag}>')
        list_kind = None
        list_items = []

    for block in iter_content_blocks(source):
        if block.kind == 'image':
            flush_list()
            attrs = block.attrs or {}
            path = str(attrs.get('path') or '')
            href = _image_href(path, image_hrefs)
            alt = str(attrs.get('alt') or '')
            caption_text = str(attrs.get('caption') or '')
            if href:
                caption = f'<figcaption>{html.escape(caption_text)}</figcaption>' if caption_text else ''
                width = str(attrs.get('width') or 'medium')
                align = str(attrs.get('align') or 'center')
                classes = ['manuscript-image', f'image-width-{width}', f'image-align-{align}']
                if bool(attrs.get('wrap')):
                    classes.extend(['image-wrap', f'image-wrap-{align}'])
                blocks.append(
                    f'<figure class="{" ".join(classes)}">'
                    f'<img src="{html.escape(href, quote=True)}" alt="{html.escape(alt, quote=True)}"/>'
                    f'{caption}</figure>'
                )
            else:
                fallback = alt or caption_text or 'Afbeelding ontbreekt'
                blocks.append(f'<p class="missing-image">[{html.escape(fallback)}]</p>')
            continue

        if block.kind == 'scene':
            flush_list()
            blocks.append('<div class="scene-break" aria-label="Scene break">* * *</div>')
            continue

        content = block.text[block.content_start-block.start:block.content_end-block.start].strip()
        runs = content_inline_runs(block)
        if block.kind == 'heading':
            flush_list()
            heading_index += 1
            heading_id = f'h-{heading_index}'
            blocks.append(f'<h2 id="{heading_id}">{inline_to_xhtml(content, runs, notes)}</h2>')
            if collect_headings:
                headings.append((heading_id, ''.join(v.text for k, v in note_groups(runs) if k == 'text').strip()))
            continue
        if block.kind == 'quote':
            flush_list()
            blocks.append(f'<blockquote><p>{inline_to_xhtml(content, runs, notes)}</p></blockquote>')
            continue
        if block.kind in {'bullet', 'numbered'}:
            wanted = 'ol' if block.kind == 'numbered' else 'ul'
            if list_kind and list_kind != wanted:
                flush_list()
            list_kind = wanted
            list_items.append((content, runs))
            continue

        if list_kind:
            flush_list()
        blocks.append(f'<p>{inline_to_xhtml(content, runs, notes)}</p>')

    flush_list()
    if notes.notes:
        blocks.append(notes.section())
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
