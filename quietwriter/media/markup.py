from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


# QuietWriter creates deliberately conservative block-image Markdown. Asset
# filenames are UUID based and never contain whitespace, which lets the parser
# stay small and deterministic rather than becoming a second Markdown engine.
#
# Layout is optional presentation metadata in a normal HTML comment, so the
# manuscript remains readable Markdown outside QuietWriter:
#   ![Alt](../assets/images/x.png "Caption") <!-- qw:image width=medium align=left wrap=true -->
# Existing image lines without the comment retain their historical behaviour.
_IMAGE_RE = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\((?P<path>[^\s\)]+)(?:\s+"(?P<caption>[^"]*)")?\)'
    r'(?P<layout>[ \t]*<!--[ \t]*qw:image[ \t]+(?P<layout_attrs>[^\r\n>]*)-->)?'
)
_LAYOUT_ATTR_RE = re.compile(r'\b(?P<key>width|align|wrap)\s*=\s*(?P<value>[A-Za-z]+)\b')

IMAGE_WIDTHS = ('small', 'medium', 'large', 'full')
IMAGE_ALIGNS = ('left', 'center', 'right')
DEFAULT_IMAGE_WIDTH = 'full'
DEFAULT_IMAGE_ALIGN = 'center'
DEFAULT_IMAGE_WRAP = False


@dataclass(frozen=True)
class ImageReference:
    alt: str
    path: str
    caption: str
    start: int
    end: int
    path_start: int
    path_end: int
    width: str = DEFAULT_IMAGE_WIDTH
    align: str = DEFAULT_IMAGE_ALIGN
    wrap: bool = DEFAULT_IMAGE_WRAP


def _unescape(value: str) -> str:
    return value.replace('\\"', '"').replace('\\]', ']').replace('\\\\', '\\')


def _escape_alt(value: str) -> str:
    return str(value or '').replace('\\', '\\\\').replace(']', '\\]')


def _escape_caption(value: str) -> str:
    return str(value or '').replace('\\', '\\\\').replace('"', '\\"')


def normalize_image_layout(width: str = DEFAULT_IMAGE_WIDTH, align: str = DEFAULT_IMAGE_ALIGN,
                           wrap: bool = DEFAULT_IMAGE_WRAP) -> tuple[str, str, bool]:
    width = str(width or '').strip().lower()
    align = str(align or '').strip().lower()
    if width not in IMAGE_WIDTHS:
        width = DEFAULT_IMAGE_WIDTH
    if align not in IMAGE_ALIGNS:
        align = DEFAULT_IMAGE_ALIGN
    wrap = bool(wrap)
    # Full width fills the available measure, so alignment no longer has a
    # visual meaning. Normalise it to centre and never combine it with wrap.
    if width == 'full':
        align = DEFAULT_IMAGE_ALIGN
        wrap = False
    elif align == 'center':
        wrap = False
    return width, align, wrap


def _layout_from_match(match: re.Match) -> tuple[str, str, bool]:
    attrs = {}
    raw = match.group('layout_attrs') or ''
    for item in _LAYOUT_ATTR_RE.finditer(raw):
        attrs[item.group('key').lower()] = item.group('value').lower()
    wrap_value = attrs.get('wrap', 'false')
    wrap = wrap_value in {'1', 'true', 'yes', 'on'}
    return normalize_image_layout(
        attrs.get('width', DEFAULT_IMAGE_WIDTH),
        attrs.get('align', DEFAULT_IMAGE_ALIGN),
        wrap,
    )


def _reference_from_match(match: re.Match, *, offset: int = 0) -> ImageReference:
    width, align, wrap = _layout_from_match(match)
    return ImageReference(
        alt=_unescape(match.group('alt') or ''),
        path=(match.group('path') or '').replace('\\', '/'),
        caption=_unescape(match.group('caption') or ''),
        start=offset + match.start(), end=offset + match.end(),
        path_start=offset + match.start('path'), path_end=offset + match.end('path'),
        width=width, align=align, wrap=wrap,
    )


def find_image_references(text: str) -> tuple[ImageReference, ...]:
    return tuple(_reference_from_match(match) for match in _IMAGE_RE.finditer(text or ''))


def image_reference_for_line(line: str) -> ImageReference | None:
    stripped = (line or '').strip()
    match = _IMAGE_RE.fullmatch(stripped)
    if not match:
        return None
    return _reference_from_match(match)


def build_image_markdown(path: str, alt: str = '', caption: str = '', *,
                         width: str = DEFAULT_IMAGE_WIDTH,
                         align: str = DEFAULT_IMAGE_ALIGN,
                         wrap: bool = DEFAULT_IMAGE_WRAP) -> str:
    ref = str(path or '').replace('\\', '/')
    base = f'![{_escape_alt(alt)}]({ref}'
    if str(caption or '').strip():
        base += f' "{_escape_caption(str(caption).strip())}"'
    base += ')'
    width, align, wrap = normalize_image_layout(width, align, wrap)
    if (width, align, wrap) != (DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_ALIGN, DEFAULT_IMAGE_WRAP):
        wrap_value = 'true' if wrap else 'false'
        base += f' <!-- qw:image width={width} align={align} wrap={wrap_value} -->'
    return base


def insert_image_block(text: str, position: int, block: str) -> tuple[str, int]:
    """Insert one image as its own Markdown block and return the new cursor position."""
    text = text or ''
    position = max(0, min(int(position), len(text)))
    before = text[:position]
    after = text[position:]
    left = before.rstrip('\n')
    right = after.lstrip('\n')
    prefix = ('\n\n' if left else '')
    suffix = ('\n\n' if right else '')
    result = left + prefix + block.strip() + suffix + right
    cursor = len(left + prefix + block.strip())
    return result, cursor


def _block_image_line_ranges(text: str) -> list[tuple[int, int]]:
    from ..document_view import parse_document
    return [(block.start, block.end) for block in parse_document(text or '').blocks if block.kind == 'image']


def text_without_image_blocks(text: str) -> str:
    chars = list(text or '')
    for start, end in _block_image_line_ranges(text or ''):
        for index in range(start, min(end, len(chars))):
            chars[index] = ' '
    return ''.join(chars)


def count_words(text: str) -> int:
    """Compatibility wrapper around the central writer-visible word count."""
    from ..document_view import count_visible_words
    return count_visible_words(text or '')


def mask_image_paths(text: str) -> str:
    """Mask image syntax/paths while preserving alt and caption source offsets.

    The returned string has exactly the same length as the source. Search and
    spelling can therefore ignore UUID paths/layout metadata yet still select
    natural alt/caption text using the original QTextDocument offsets.
    """
    source = text or ''
    chars = list(source)
    for match in _IMAGE_RE.finditer(source):
        keep: list[tuple[int, int]] = [match.span('alt')]
        if match.group('caption') is not None:
            keep.append(match.span('caption'))
        for index in range(match.start(), match.end()):
            if not any(a <= index < b for a, b in keep):
                chars[index] = ' '
    return ''.join(chars)


def _protected_image_ranges(text: str) -> list[tuple[int, int]]:
    """Return source ranges that search/replace must never mutate.

    Alt text and captions are intentionally editable. Everything else in a
    managed Markdown image reference (delimiters, path, layout comment, quotes
    and separators) is protected, including literal spaces.
    """
    source = text or ''
    ranges: list[tuple[int, int]] = []
    for match in _IMAGE_RE.finditer(source):
        editable = [match.span('alt')]
        if match.group('caption') is not None:
            editable.append(match.span('caption'))
        editable.sort()
        cursor = match.start()
        for start, end in editable:
            if cursor < start:
                ranges.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < match.end():
            ranges.append((cursor, match.end()))
    return ranges


def is_searchable_range(text: str, start: int, end: int) -> bool:
    """Whether ``[start:end]`` avoids protected image and open-point syntax."""
    if start < 0 or end < start:
        return False
    from ..placeholders import marker_ranges
    protected = _protected_image_ranges(text or '') + marker_ranges(text or '')
    for protected_start, protected_end in protected:
        if start < protected_end and end > protected_start:
            return False
    return True


@dataclass(frozen=True)
class SearchableMatch:
    source_start: int
    source_end: int
    visible_start: int
    visible_end: int
    visible_text: str

    def start(self) -> int:
        return self.source_start

    def end(self) -> int:
        return self.source_end


def searchable_matches(text: str, pattern: re.Pattern) -> list[SearchableMatch]:
    """Match writer-visible text and map every result back to source offsets."""
    source = text or ''
    from ..document_view import visible_projection
    projection = visible_projection(source)
    results: list[SearchableMatch] = []
    for match in pattern.finditer(projection.text):
        if match.end() <= match.start():
            continue
        source_start, source_end = projection.source_range(match.start(), match.end())
        from ..manuscript_markup import escape_ranges
        if any(a == source_start - 1 and b == source_start for a, b in escape_ranges(source)):
            source_start -= 1
        if not is_searchable_range(source, source_start, source_end):
            continue
        results.append(SearchableMatch(
            source_start, source_end, match.start(), match.end(), match.group(0)
        ))
    return results



def replacement_crosses_inline_boundary(source: str, start: int, end: int) -> bool:
    """Return True when replacing this source range would split formatting.

    Search is allowed across hidden Markdown markers, but replacement must not
    leave only one side of a paired inline span behind. A match wholly inside
    formatted content or wholly covering the complete span is safe.
    """
    from ..document_view import parse_document
    for block in parse_document(source or '').blocks:
        if end <= block.start or start >= block.end:
            continue
        for span in block.inline_spans:
            open_start = block.start + span.open_start
            content_start = block.start + span.content_start
            content_end = block.start + span.content_end
            close_end = block.start + span.close_end
            if end <= open_start or start >= close_end:
                continue
            wholly_inside = start >= content_start and end <= content_end
            wholly_covers = start <= open_start and end >= close_end
            if not (wholly_inside or wholly_covers):
                return True
    return False

def replace_searchable_text(text: str, pattern: re.Pattern, replacement: str) -> str:
    """Replace search matches without ever mutating protected image syntax/paths.

    ``mask_image_paths`` preserves source length, so matches found in the masked
    text map one-to-one to offsets in the original Markdown. Alt text and
    captions intentionally remain searchable/editable; only the managed image
    syntax, asset path and QuietWriter layout metadata stay protected.
    Replacement text is literal, matching the editor's existing semantics.
    """
    source = text or ''
    matches = searchable_matches(source, pattern)
    if not matches:
        return source
    parts: list[str] = []
    cursor = 0
    from ..manuscript_markup import escape_literal_text
    for match in matches:
        if replacement_crosses_inline_boundary(source, match.start(), match.end()):
            continue
        parts.append(source[cursor:match.start()])
        at_line_start = match.start() == 0 or source[match.start() - 1] == '\n'
        parts.append(escape_literal_text(replacement, at_line_start=at_line_start))
        cursor = match.end()
    parts.append(source[cursor:])
    return ''.join(parts)


def text_for_search(text: str) -> str:
    from ..document_view import visible_text
    return visible_text(text)


def text_for_ai(text: str) -> str:
    """Return semantic manuscript context using the central DocumentView."""
    from ..document_view import text_for_ai_context
    return text_for_ai_context(text)


def relative_asset_reference(chapter_file: str, asset_file: str) -> str:
    chapter_dir = Path(chapter_file).parent
    # os.path.relpath is the clearest cross-platform way to compute the Markdown
    # source reference; convert back to POSIX because Markdown/EPUB use '/'.
    return Path(os.path.relpath(Path(asset_file), chapter_dir)).as_posix()
