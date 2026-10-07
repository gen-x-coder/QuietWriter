from __future__ import annotations

import re
from dataclasses import dataclass, field

from .manuscript_syntax import (
    InlineSpan, escape_ranges, is_scene_break_line, parse_inline_spans, unescape_literal_text,
)
from .media.markup import image_reference_for_line
from .placeholders import marker_ranges


_BLOCK_NUMBERED_RE = re.compile(r'^\d+\.\s+')
_BLOCK_BULLET_RE = re.compile(r'^[-*]\s+')


@dataclass(frozen=True)
class DocumentDiagnostic:
    """Non-fatal observation about manuscript syntax.

    Diagnostics never rewrite source.  They exist so consumers can surface
    ambiguity without inventing their own parser rules.
    """

    code: str
    start: int
    end: int
    message: str


@dataclass(frozen=True)
class DocumentBlock:
    """One source block with stable source coordinates.

    QuietWriter 1.2.x is line-oriented: one physical source line represents one
    manuscript block.  The view records that fact without normalising bytes.
    """

    kind: str
    start: int
    end: int
    content_start: int
    content_end: int
    text: str
    inline_spans: tuple[InlineSpan, ...] = ()
    escape_ranges: tuple[tuple[int, int], ...] = ()
    attrs: dict = field(default_factory=dict)


@dataclass(frozen=True)
class InlineRun:
    """One writer-visible inline text run with semantic style names.

    Marker punctuation is omitted. Consumers such as DOCX/XHTML exporters no
    longer need to parse ``*``/``**`` themselves; they only render these runs.
    """

    text: str
    styles: frozenset[str] = frozenset()
    start: int = 0
    end: int = 0


@dataclass(frozen=True)
class DocumentView:
    """Read-only semantic interpretation of one manuscript source string.

    This object is deliberately not a serializer.  Existing 1.2.x manuscript
    bytes stay authoritative; DocumentView gives editor/export/search code one
    shared interpretation of those bytes.
    """

    source: str
    blocks: tuple[DocumentBlock, ...]
    hidden_ranges: tuple[tuple[int, int], ...] = ()
    protected_ranges: tuple[tuple[int, int], ...] = ()
    diagnostics: tuple[DocumentDiagnostic, ...] = ()

    def block_at(self, position: int) -> DocumentBlock | None:
        pos = max(0, min(int(position), len(self.source)))
        for block in self.blocks:
            if block.start <= pos <= block.end:
                return block
        return None


def image_reference_for_block_line(line: str):
    """Return the managed-image reference for one complete source line.

    Consumers use this wrapper instead of depending on media markup parsing
    directly. Image syntax remains implemented in ``media.markup`` for now, but
    DocumentView owns the interpretation boundary.
    """
    return image_reference_for_line(line)


def classify_block_line(line: str) -> str:
    """Return the canonical QuietWriter 1.2.x block kind for one source line."""
    text = line or ''
    stripped = text.strip()
    if not stripped:
        return 'empty'
    # Backslash-escaped prefixes are writer-literal prose, not structure.
    if (text.startswith(r'\#') or text.startswith(r'\>')
            or text.startswith(r'\-') or text.startswith(r'\*')
            or text.startswith(r'\!') or re.match(r'^\d+\\\.', text)):
        return 'paragraph'
    if is_scene_break_line(text):
        return 'scene'
    if image_reference_for_block_line(text):
        return 'image'
    if text.startswith('## '):
        return 'heading'
    if text.startswith('> '):
        return 'quote'
    if _BLOCK_BULLET_RE.match(text):
        return 'bullet'
    if _BLOCK_NUMBERED_RE.match(text):
        return 'numbered'
    return 'paragraph'


def _content_bounds(line: str, kind: str) -> tuple[int, int]:
    if kind == 'heading':
        return 3, len(line)
    if kind == 'quote':
        return 2, len(line)
    if kind == 'bullet':
        match = _BLOCK_BULLET_RE.match(line)
        return (match.end() if match else 0), len(line)
    if kind == 'numbered':
        match = _BLOCK_NUMBERED_RE.match(line)
        return (match.end() if match else 0), len(line)
    return 0, len(line)



def _image_attrs(line: str) -> dict:
    image = image_reference_for_block_line(line)
    if image is None:
        return {}
    return {
        'path': image.path,
        'alt': image.alt,
        'caption': image.caption,
        'width': image.width,
        'align': image.align,
        'wrap': image.wrap,
    }


def parse_block_line(line: str, *, source_start: int = 0) -> DocumentBlock:
    """Parse one physical manuscript line using the canonical block rules."""
    text = line or ''
    kind = classify_block_line(text)
    local_content_start, local_content_end = _content_bounds(text, kind)
    return DocumentBlock(
        kind=kind,
        start=source_start,
        end=source_start + len(text),
        content_start=source_start + local_content_start,
        content_end=source_start + local_content_end,
        text=text,
        inline_spans=tuple(parse_inline_spans(text)),
        escape_ranges=tuple(escape_ranges(text)),
        attrs=_image_attrs(text) if kind == 'image' else {},
    )


def parse_document(source: str) -> DocumentView:
    """Parse manuscript source into a read-only semantic view.

    Version 1 intentionally mirrors 1.2.x behaviour.  It does not silently fix
    ambiguous Markdown-like prose and does not rewrite or normalise the source.
    Inline parsing is performed per physical line so formatting never pairs
    across paragraph boundaries.
    """
    text = source or ''
    blocks: list[DocumentBlock] = []
    hidden: list[tuple[int, int]] = list(marker_ranges(text))
    protected: list[tuple[int, int]] = list(marker_ranges(text))
    diagnostics: list[DocumentDiagnostic] = []

    if text == '':
        return DocumentView(source='', blocks=())
    offset = 0
    parts = text.split('\n')

    for part_index, line in enumerate(parts):
        has_newline = part_index < len(parts) - 1
        start = offset
        end = start + len(line)
        kind = classify_block_line(line)
        local_content_start, local_content_end = _content_bounds(line, kind)

        local_spans = tuple(parse_inline_spans(line))
        local_escapes = tuple(escape_ranges(line))
        for a, b in local_escapes:
            hidden.append((start + a, start + b))
        for span in local_spans:
            for a, b in span.marker_ranges:
                hidden.append((start + a, start + b))

        attrs: dict = _image_attrs(line) if kind == 'image' else {}
        if kind == 'image' and attrs:
            # The current editor renders managed images as protected cards.
            protected.append((start, end))

        # These are current 1.2.x interpretations that are especially likely to
        # collide with ordinary novel prose.  Record them; do not change bytes or
        # semantics until an explicit escaping design is introduced.
        if kind == 'bullet' and line.startswith('- '):
            diagnostics.append(DocumentDiagnostic(
                'ambiguous-leading-dash', start, end,
                'Een regel die met "- " begint wordt in 1.2.x als lijst gelezen.',
            ))
        elif kind == 'numbered':
            diagnostics.append(DocumentDiagnostic(
                'ambiguous-leading-number', start, end,
                'Een regel die met "getal. " begint wordt in 1.2.x als lijst gelezen.',
            ))

        blocks.append(DocumentBlock(
            kind=kind,
            start=start,
            end=end,
            content_start=start + local_content_start,
            content_end=start + local_content_end,
            text=line,
            inline_spans=local_spans,
            escape_ranges=local_escapes,
            attrs=attrs,
        ))
        offset += len(line) + (1 if has_newline else 0)

    return DocumentView(
        source=text,
        blocks=tuple(blocks),
        hidden_ranges=tuple(sorted(set(hidden))),
        protected_ranges=tuple(sorted(set(protected))),
        diagnostics=tuple(diagnostics),
    )


def iter_content_blocks(source: str):
    """Yield parsed non-empty blocks for consumers that render manuscript content."""
    for block in parse_document(source).blocks:
        if block.kind != 'empty':
            yield block


def block_content_text(block: DocumentBlock) -> str:
    """Return the source content of a block without its structural prefix.

    Inline markup remains present. Consumers that render inline formatting can
    pass the result to the shared inline parser.
    """
    return block.text[block.content_start - block.start:block.content_end - block.start]


def _mask_ranges(source: str, ranges: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> str:
    """Replace source ranges with spaces while preserving exact offsets."""
    chars = list(source or '')
    for start, end in ranges:
        for index in range(max(0, start), min(len(chars), end)):
            if chars[index] != '\n':
                chars[index] = ' '
    return ''.join(chars)


@dataclass(frozen=True)
class VisibleProjection:
    """Writer-visible manuscript text plus a map back to source positions."""

    text: str
    source_indices: tuple[int, ...]

    def source_range(self, start: int, end: int) -> tuple[int, int]:
        if end <= start or not self.source_indices:
            pos = self.source_indices[start] if 0 <= start < len(self.source_indices) else 0
            return pos, pos
        start = max(0, min(start, len(self.source_indices) - 1))
        end = max(start + 1, min(end, len(self.source_indices)))
        return self.source_indices[start], self.source_indices[end - 1] + 1


def visible_projection(source: str) -> VisibleProjection:
    """Return compact visible text for search/clipboard with source mapping.

    Unlike ``text_for_language_tools`` this removes technical characters instead
    of replacing them with spaces. Searches can therefore span formatting
    boundaries (``was **heel** moe`` -> ``was heel moe``) while results still map
    back to exact QTextDocument source offsets.
    """
    text = source or ''
    if not text:
        return VisibleProjection('', ())
    view = parse_document(text)
    hidden_global = set()
    from .placeholders import marker_ranges as _marker_ranges
    for a, b in _marker_ranges(text):
        hidden_global.update(range(a, b))
    out: list[str] = []
    mapping: list[int] = []

    for block_index, block in enumerate(view.blocks):
        if block.kind == 'scene':
            pass
        elif block.kind == 'image':
            # Keep natural alt/caption text searchable, not the managed path.
            image = image_reference_for_block_line(block.text)
            pieces = []
            if image is not None:
                if image.alt:
                    pos = block.text.find(image.alt)
                    if pos >= 0:
                        pieces.append((image.alt, block.start + pos))
                if image.caption and image.caption != image.alt:
                    pos = block.text.find(image.caption)
                    if pos >= 0:
                        pieces.append((image.caption, block.start + pos))
            for piece_index, (piece, src_start) in enumerate(pieces):
                if piece_index:
                    out.append(' '); mapping.append(src_start)
                for i, ch in enumerate(piece):
                    out.append(ch); mapping.append(src_start + i)
        else:
            local_start = max(0, block.content_start - block.start)
            hidden = set()
            for a, b in block.escape_ranges:
                hidden.update(range(a, b))
            for span in block.inline_spans:
                for a, b in span.marker_ranges:
                    hidden.update(range(a, b))
            for local_index in range(local_start, len(block.text)):
                source_index = block.start + local_index
                if local_index in hidden or source_index in hidden_global:
                    continue
                out.append(block.text[local_index]); mapping.append(source_index)

        # Preserve physical paragraph boundaries in the visible projection.
        newline_index = block.end
        if newline_index < len(text) and text[newline_index:newline_index + 1] == '\n':
            out.append('\n'); mapping.append(newline_index)

    return VisibleProjection(''.join(out), tuple(mapping))


def visible_text_for_source_range(source: str, start: int, end: int) -> str:
    """Return the writer-visible part of a source selection."""
    projection = visible_projection(source)
    chars = [ch for ch, pos in zip(projection.text, projection.source_indices) if start <= pos < end]
    return ''.join(chars)


def visible_text(source: str) -> str:
    """Return the compact writer-visible manuscript projection.

    This is the canonical plain-text view for consumers that do not need source
    offsets, such as FTS indexing, previews and clipboard fallbacks.
    """
    return visible_projection(source or '').text


def count_visible_words(source: str) -> int:
    """Count prose words from the central semantic interpretation.

    Structural syntax is never counted as prose. Managed image blocks keep the
    long-standing QuietWriter behaviour of contributing no manuscript words.
    """
    from .placeholders import strip_open_point_markers

    total = 0
    for block in parse_document(strip_open_point_markers(source or '')).blocks:
        if block.kind in {'empty', 'scene', 'image'}:
            continue
        text = visible_block_text(block)
        if text:
            total += len(text.split())
    return total


def text_for_language_tools(source: str) -> str:
    """Return offset-stable visible manuscript text for search and spelling.

    Structural prefixes, inline markup punctuation, scene-break syntax, managed
    image paths/layout metadata and Open-point markers are hidden. Natural image
    alt/caption text remains available through the existing media masking rule.
    """
    text = source or ''
    if not text:
        return ''

    # Keep the existing image contract: alt/caption remain searchable/spellable,
    # while UUID paths and layout metadata are masked. Import lazily to avoid an
    # import cycle while media.markup gradually moves onto DocumentView.
    from .media.markup import mask_image_paths
    masked = mask_image_paths(text)
    view = parse_document(text)
    ranges: list[tuple[int, int]] = list(view.hidden_ranges)
    for block in view.blocks:
        if block.kind == 'scene':
            ranges.append((block.start, block.end))
        elif block.kind in {'heading', 'quote', 'bullet', 'numbered'} and block.content_start > block.start:
            ranges.append((block.start, block.content_start))
    return _mask_ranges(masked, ranges)


def inline_runs(text: str, spans: tuple[InlineSpan, ...] | list[InlineSpan] | None = None) -> tuple[InlineRun, ...]:
    """Return writer-visible text runs with semantic inline styles in O(n + spans).

    Style boundaries are swept once instead of testing every span at every
    character. This matters for long or heavily formatted imported chapters.
    """
    source = text or ''
    parsed = tuple(spans) if spans is not None else tuple(parse_inline_spans(source))
    if not source:
        return ()

    marker_mask = bytearray(len(source))
    for span in parsed:
        for a, b in span.marker_ranges:
            marker_mask[max(0, a):min(len(source), b)] = b'\x01' * max(0, min(len(source), b) - max(0, a))
    for a, b in escape_ranges(source):
        marker_mask[max(0, a):min(len(source), b)] = b'\x01' * max(0, min(len(source), b) - max(0, a))

    events: dict[int, list[tuple[str, int]]] = {}
    for span in parsed:
        events.setdefault(span.content_start, []).append((span.kind, 1))
        events.setdefault(span.content_end, []).append((span.kind, -1))

    active_counts: dict[str, int] = {}
    active_styles: frozenset[str] = frozenset()
    runs: list[InlineRun] = []
    run_start: int | None = None

    def flush(end: int):
        nonlocal run_start
        if run_start is not None and end > run_start:
            runs.append(InlineRun(source[run_start:end], active_styles, run_start, end))
        run_start = None

    for index in range(len(source) + 1):
        changes = events.get(index)
        if changes:
            flush(index)
            for kind, delta in changes:
                count = active_counts.get(kind, 0) + delta
                if count > 0:
                    active_counts[kind] = count
                else:
                    active_counts.pop(kind, None)
            active_styles = frozenset(active_counts)
        if index == len(source):
            flush(index)
            break
        if marker_mask[index]:
            flush(index)
            continue
        if run_start is None:
            run_start = index

    return tuple(run for run in runs if run.text)


def content_inline_runs(block: DocumentBlock) -> tuple[InlineRun, ...]:
    """Return inline runs for only the semantic content of *block*."""
    local_start = max(0, block.content_start - block.start)
    local_end = max(local_start, block.content_end - block.start)
    content = block.text[local_start:local_end]
    adjusted: list[InlineSpan] = []
    for span in block.inline_spans:
        if span.open_start < local_start or span.close_end > local_end:
            continue
        adjusted.append(InlineSpan(
            span.kind,
            span.open_start - local_start, span.open_end - local_start,
            span.content_start - local_start, span.content_end - local_start,
            span.close_start - local_start, span.close_end - local_start,
        ))
    return inline_runs(content, adjusted)


def visible_inline_text(text: str, spans: tuple[InlineSpan, ...] | list[InlineSpan] | None = None) -> str:
    """Return inline source without QuietWriter formatting punctuation.

    Literal, unpaired punctuation remains untouched because it never becomes a
    formatting span.
    """
    return ''.join(run.text for run in inline_runs(text, spans))


def visible_block_text(block: DocumentBlock) -> str:
    """Return human-visible text for one block, without technical markers."""
    if block.kind in {'empty', 'scene'}:
        return ''
    if block.kind == 'image':
        alt = str(block.attrs.get('alt') or '').strip()
        caption = str(block.attrs.get('caption') or '').strip()
        label = alt or caption or 'afbeelding'
        if alt and caption and caption.casefold() != alt.casefold():
            label = f'{alt} — {caption}'
        return f'[Afbeelding: {label}]'

    local_start = max(0, block.content_start - block.start)
    text = block.text[local_start:]
    local_spans: list[InlineSpan] = []
    for span in block.inline_spans:
        if span.open_start < local_start:
            continue
        local_spans.append(InlineSpan(
            span.kind,
            span.open_start - local_start, span.open_end - local_start,
            span.content_start - local_start, span.content_end - local_start,
            span.close_start - local_start, span.close_end - local_start,
        ))
    return visible_inline_text(text, local_spans)


def text_for_ai_context(source: str) -> str:
    """Build manuscript context from the same semantic interpretation as export.

    The result contains writer-visible prose plus compact semantic markers for
    scene breaks and images. QuietWriter's technical source syntax is omitted.
    """
    from .placeholders import strip_open_point_markers

    view = parse_document(strip_open_point_markers(source or ''))
    lines: list[str] = []
    for block in view.blocks:
        if block.kind == 'empty':
            if lines and lines[-1] != '':
                lines.append('')
            continue
        if block.kind == 'scene':
            lines.append('[Scènebreuk]')
            continue
        visible = visible_block_text(block)
        if not visible:
            continue
        if block.kind == 'heading':
            lines.append(f'## {visible}')
        elif block.kind == 'quote':
            lines.append(f'> {visible}')
        elif block.kind == 'bullet':
            lines.append(f'- {visible}')
        elif block.kind == 'numbered':
            prefix_len = max(0, block.content_start - block.start)
            prefix = block.text[:prefix_len].strip() or '1.'
            lines.append(f'{prefix} {visible}')
        else:
            lines.append(visible)
    return '\n'.join(lines).strip()
