from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

_NEW_OPEN_RE = re.compile(r'<!--\s*qw:todo:([0-9a-fA-F-]{8,})\s*-->')
_LEGACY_OPEN_RE = re.compile(r'<!--\s*qw:todo\s+id=([0-9a-fA-F-]{8,})\s+note="([^"]*)"\s*-->')
_CLOSE_RE = re.compile(r'<!--\s*/qw:todo\s*-->')
_TOKEN_RE = re.compile(
    r'<!--\s*qw:todo:([0-9a-fA-F-]{8,})\s*-->'
    r'|<!--\s*qw:todo\s+id=([0-9a-fA-F-]{8,})\s+note="([^"]*)"\s*-->'
    r'|<!--\s*/qw:todo\s*-->'
)


@dataclass(frozen=True)
class OpenPoint:
    id: str
    note: str
    text: str
    start: int
    end: int
    content_start: int
    content_end: int


def new_open_point_id() -> str:
    # 12 hex characters are compact in the manuscript while still giving more
    # than enough collision space for one book. Existing UUID ids remain valid.
    return uuid.uuid4().hex[:12]


def marker_open(point_id: str, note: str = '') -> str:
    # Notes deliberately live outside manuscript prose in planning/open_points.json.
    # Keeping only an id here makes the managed marker short and stable.
    return f'<!--qw:todo:{point_id}-->'


def marker_close() -> str:
    return '<!--/qw:todo-->'


def wrap_open_point(
    text: str, start: int, end: int, note: str = '', *, point_id: str | None = None
) -> tuple[str, int, int, str]:
    source = text or ''
    start, end = sorted((max(0, int(start)), max(0, int(end))))
    start = min(start, len(source)); end = min(end, len(source))
    visible = source[start:end]
    if not visible:
        visible = '[…]'
    point_id = str(point_id or new_open_point_id())
    left = marker_open(point_id)
    right = marker_close()
    new = source[:start] + left + visible + right + source[end:]
    content_start = start + len(left)
    return new, content_start, content_start + len(visible), point_id


def _legacy_note(raw: str | None) -> str:
    if not raw:
        return ''
    # Legacy 1.2.4 markers URL-encoded notes in the source. Keep read support so
    # pre-release test books remain usable, but new writes never use this form.
    try:
        from urllib.parse import unquote
        return unquote(raw)
    except Exception:
        return str(raw)


def _is_escaped_marker(source: str, start: int) -> bool:
    slash_count = 0
    i = start - 1
    while i >= 0 and source[i] == '\\':
        slash_count += 1; i -= 1
    return bool(slash_count % 2)


def _token_matches(source: str):
    return (match for match in _TOKEN_RE.finditer(source) if not _is_escaped_marker(source, match.start()))


def parse_open_points(text: str, notes: dict[str, str] | None = None) -> list[OpenPoint]:
    source = text or ''
    note_map = notes or {}
    points: list[OpenPoint] = []
    stack: list[tuple[re.Match, str, str]] = []
    for match in _token_matches(source):
        new_id = match.group(1)
        legacy_id = match.group(2)
        if new_id or legacy_id:
            point_id = new_id or legacy_id
            embedded = _legacy_note(match.group(3)) if legacy_id else ''
            note = str(note_map.get(point_id, embedded) or '')
            stack.append((match, point_id, note))
            continue
        if not stack:
            continue
        opening, point_id, note = stack.pop()
        content_start = opening.end()
        content_end = match.start()
        points.append(OpenPoint(
            id=point_id,
            note=note,
            text=source[content_start:content_end],
            start=opening.start(),
            end=match.end(),
            content_start=content_start,
            content_end=content_end,
        ))
    return sorted(points, key=lambda p: p.start)


def strip_open_point_markers(text: str) -> str:
    """Remove QuietWriter todo syntax while preserving the writer-visible text."""
    source = text or ''
    parts = []; cursor = 0
    for match in _token_matches(source):
        parts.append(source[cursor:match.start()]); cursor = match.end()
    parts.append(source[cursor:])
    return ''.join(parts)


def mask_open_point_markers(text: str) -> str:
    """Blank marker syntax while preserving source offsets exactly."""
    source = text or ''
    chars = list(source)
    for start, end in marker_ranges(source):
        for index in range(start, min(end, len(chars))):
            chars[index] = ' '
    return ''.join(chars)


def marker_ranges(text: str) -> list[tuple[int, int]]:
    source = text or ''
    return [(m.start(), m.end()) for m in _token_matches(source)]


def open_point_content_ranges(text: str) -> list[tuple[int, int]]:
    return [(p.content_start, p.content_end) for p in parse_open_points(text)]


def count_open_points(text: str) -> int:
    return len(parse_open_points(text))


def open_point_at(text: str, position: int, notes: dict[str, str] | None = None) -> OpenPoint | None:
    pos = max(0, int(position))
    for point in parse_open_points(text, notes):
        if point.content_start <= pos <= point.content_end:
            return point
    return None


def resolve_open_point(text: str, point_id: str) -> tuple[str, int, int] | None:
    source = text or ''
    point = next((p for p in parse_open_points(source) if p.id == point_id), None)
    if point is None:
        return None
    visible = source[point.content_start:point.content_end]
    new = source[:point.start] + visible + source[point.end:]
    start = point.start
    return new, start, start + len(visible)


def normalize_open_point_marker(text: str, point_id: str) -> str | None:
    """Convert one legacy opening marker to the compact current representation."""
    source = text or ''
    point = next((p for p in parse_open_points(source) if p.id == point_id), None)
    if point is None:
        return None
    opening = source[point.start:point.content_start]
    compact = marker_open(point_id)
    if opening == compact:
        return source
    return source[:point.start] + compact + source[point.content_start:]


def update_open_point_note(text: str, point_id: str, note: str) -> str | None:
    """Compatibility helper.

    Notes no longer belong in manuscript source. The function now only upgrades a
    legacy marker to the compact form; callers persist the note via OpenPointStore.
    """
    return normalize_open_point_marker(text, point_id)
