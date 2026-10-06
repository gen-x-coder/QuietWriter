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
    ranges: list[tuple[int, int]] = []
    offset = 0
    for raw in (text or '').splitlines(keepends=True):
        line = raw[:-1] if raw.endswith('\n') else raw
        if image_reference_for_line(line):
            ranges.append((offset, offset + len(line)))
        offset += len(raw)
    return ranges


def text_without_image_blocks(text: str) -> str:
    chars = list(text or '')
    for start, end in _block_image_line_ranges(text or ''):
        for index in range(start, min(end, len(chars))):
            chars[index] = ' '
    return ''.join(chars)


def count_words(text: str) -> int:
    # Preserve QuietWriter's historical whitespace word-count semantics while
    # excluding media syntax, alt text and captions from manuscript statistics.
    return len(text_without_image_blocks(text).split())


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
    """Whether ``[start:end]`` avoids protected image syntax entirely."""
    if start < 0 or end < start:
        return False
    for protected_start, protected_end in _protected_image_ranges(text or ''):
        if start < protected_end and end > protected_start:
            return False
    return True


def searchable_matches(text: str, pattern: re.Pattern) -> list[re.Match]:
    """Return regex matches that cannot cross into managed image syntax."""
    source = text or ''
    searchable = mask_image_paths(source)
    return [
        match for match in pattern.finditer(searchable)
        if is_searchable_range(source, match.start(), match.end())
    ]


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
    for match in matches:
        parts.append(source[cursor:match.start()])
        parts.append(replacement)
        cursor = match.end()
    parts.append(source[cursor:])
    return ''.join(parts)


def text_for_search(text: str) -> str:
    return mask_image_paths(text)


def text_for_ai(text: str) -> str:
    """Replace media source syntax with compact semantic context for AI."""
    source = text or ''

    def repl(match: re.Match) -> str:
        alt = _unescape(match.group('alt') or '').strip()
        caption = _unescape(match.group('caption') or '').strip()
        label = alt or caption or 'afbeelding'
        if alt and caption and caption.casefold() != alt.casefold():
            label = f'{alt} — {caption}'
        return f'[Afbeelding: {label}]'

    return _IMAGE_RE.sub(repl, source)


def relative_asset_reference(chapter_file: str, asset_file: str) -> str:
    chapter_dir = Path(chapter_file).parent
    # os.path.relpath is the clearest cross-platform way to compute the Markdown
    # source reference; convert back to POSIX because Markdown/EPUB use '/'.
    return Path(os.path.relpath(Path(asset_file), chapter_dir)).as_posix()
