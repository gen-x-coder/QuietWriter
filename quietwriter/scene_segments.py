"""Scènes in de tekst en scènes in Planning, zonder verborgen markers.

Besluit 1.7 (zie ``documents/design/SCENES_IN_TEXT_DESIGN.md``): een hoofdstuk
wordt door scènebreuken (``***``) in segmenten verdeeld. De *n*-de scène die in
Planning aan dit hoofdstuk hangt (in de volgorde van de outline) hoort bij het
*n*-de segment. Er komt niets in het manuscript bij: geen ID's, geen
commentaar, geen nieuwe syntax.

Alles hier is puur en alleen-lezend. Niets schrijft naar Planning of naar het
manuscript; de UI beslist wat ermee gebeurt.
"""
from __future__ import annotations

from dataclasses import dataclass

from .document_view import classify_block_line, visible_text
from .placeholders import strip_open_point_markers

EXCERPT_WORDS = 8


@dataclass(frozen=True)
class TextSegment:
    index: int          # 0 = vóór de eerste scènebreuk
    first_line: int     # bronregel waar het segment begint (na de breuk)
    excerpt: str        # eerste woorden van de eerste niet-lege alinea
    has_text: bool


def _excerpt(line: str) -> str:
    words = visible_text(strip_open_point_markers(line)).split()
    if not words:
        return ''
    text = ' '.join(words[:EXCERPT_WORDS])
    return text + ('…' if len(words) > EXCERPT_WORDS else '')


def chapter_segments(source: str) -> list[TextSegment]:
    """Segmenten van een hoofdstuk, ook lege (voor de juiste nummering)."""
    lines = (source or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    segments: list[TextSegment] = []
    start = 0
    excerpt = ''
    has_text = False

    def close(index: int):
        segments.append(TextSegment(index=index, first_line=start, excerpt=excerpt, has_text=has_text))

    for number, line in enumerate(lines):
        kind = classify_block_line(line)
        if kind == 'scene':
            close(len(segments))
            start, excerpt, has_text = number + 1, '', False
            continue
        if kind in ('empty',):
            continue
        if kind == 'image':
            has_text = True
            continue
        if not excerpt:
            excerpt = _excerpt(line)
        has_text = True
    close(len(segments))
    return segments


def segment_index_for_line(source_lines: list[str], line_number: int) -> int:
    """In welk segment staat deze regel? (aantal scènebreuken ervóór)."""
    count = 0
    for line in source_lines[:max(0, line_number)]:
        if classify_block_line(line) == 'scene':
            count += 1
    return count


def scenes_for_chapter(scenes, chapter_id: str) -> list:
    """Planningscènes van één hoofdstuk, in outlinevolgorde."""
    return [scene for scene in scenes if getattr(scene, 'chapter_id', None) == chapter_id]


@dataclass(frozen=True)
class SceneSegmentMap:
    planned: tuple            # planningscènes van het hoofdstuk, op volgorde
    segments: tuple           # TextSegment's
    unplanned: tuple          # segmenten met tekst zonder planningscène

    def scene_for_segment(self, index: int):
        return self.planned[index] if 0 <= index < len(self.planned) else None

    def segment_for_scene(self, scene_id: str):
        for index, scene in enumerate(self.planned):
            if getattr(scene, 'id', None) == scene_id:
                return self.segments[index] if index < len(self.segments) else None
        return None


def map_scenes(chapter_scenes, source: str) -> SceneSegmentMap:
    planned = tuple(chapter_scenes)
    segments = tuple(chapter_segments(source))
    unplanned = tuple(seg for seg in segments[len(planned):] if seg.has_text)
    return SceneSegmentMap(planned=planned, segments=segments, unplanned=unplanned)


def scene_title_from_excerpt(excerpt: str, fallback: str) -> str:
    text = (excerpt or '').strip()
    return text if text else fallback
