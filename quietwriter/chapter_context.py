from __future__ import annotations

from dataclasses import dataclass

from .planning_models import Character, Scene


@dataclass(frozen=True)
class ChapterSceneContext:
    id: str
    title: str
    synopsis: str
    status: str
    location: str
    character_names: tuple[str, ...]
    goal: str
    conflict: str
    outcome: str
    notes: str


@dataclass(frozen=True)
class ChapterContext:
    chapter_id: str
    scenes: tuple[ChapterSceneContext, ...]
    character_names: tuple[str, ...]


def build_chapter_context(chapter_id: str, scenes: list[Scene], characters: list[Character]) -> ChapterContext:
    """Build a read-only chapter context from saved Planning data.

    Broken references are intentionally skipped. Planning remains the single
    source of truth; this function never repairs or writes planning data.
    """
    by_id = {character.id: character for character in characters}
    rows: list[ChapterSceneContext] = []
    seen_character_ids: list[str] = []

    for scene in scenes:
        if scene.chapter_id != chapter_id:
            continue
        names: list[str] = []
        for character_id in scene.character_ids:
            character = by_id.get(character_id)
            if character is None:
                continue
            names.append(character.name)
            if character_id not in seen_character_ids:
                seen_character_ids.append(character_id)
        rows.append(
            ChapterSceneContext(
                id=scene.id,
                title=scene.title,
                synopsis=scene.synopsis,
                status=scene.status,
                location=scene.location,
                character_names=tuple(names),
                goal=scene.goal,
                conflict=scene.conflict,
                outcome=scene.outcome,
                notes=scene.notes,
            )
        )

    return ChapterContext(
        chapter_id=chapter_id,
        scenes=tuple(rows),
        character_names=tuple(by_id[cid].name for cid in seen_character_ids if cid in by_id),
    )
