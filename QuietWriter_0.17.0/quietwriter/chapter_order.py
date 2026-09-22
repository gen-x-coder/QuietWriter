from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DropTarget:
    """A logical drop target independent of the Qt tree widget."""
    target_type: str  # 'chapter' or 'section'
    target_id: str
    before: bool


def chapter_ids(sections: Iterable) -> list[str]:
    return [chapter.id for section in sections for chapter in section.chapters]


def validate_unique_chapters(sections: Iterable) -> None:
    ids = chapter_ids(sections)
    if len(ids) != len(set(ids)):
        raise ValueError('Dubbele hoofdstuk-id in boekstructuur')


def move_chapter(sections: list, chapter_id: str, target: DropTarget) -> bool:
    """Move one chapter without ever losing or duplicating it.

    Destination is resolved *before* the source is removed. The operation is then
    performed on copied chapter lists and committed only after invariants pass.
    This makes a malformed or stale drop target a no-op rather than destructive.
    """
    validate_unique_chapters(sections)
    before_ids = chapter_ids(sections)

    source_section = None
    source_index = None
    chapter = None
    for section in sections:
        for index, candidate in enumerate(section.chapters):
            if candidate.id == chapter_id:
                source_section = section
                source_index = index
                chapter = candidate
                break
        if chapter is not None:
            break
    if chapter is None:
        return False

    if target.target_type == 'chapter':
        if target.target_id == chapter_id:
            return False
        target_section = None
        target_index = None
        for section in sections:
            for index, candidate in enumerate(section.chapters):
                if candidate.id == target.target_id:
                    target_section = section
                    target_index = index
                    break
            if target_section is not None:
                break
        if target_section is None:
            return False
    elif target.target_type == 'section':
        target_section = next((section for section in sections if section.id == target.target_id), None)
        if target_section is None:
            return False
        target_index = 0 if target.before else len(target_section.chapters)
    else:
        return False

    # Work on independent lists. The live structure is untouched until the move
    # has been fully calculated and checked.
    work = {section.id: list(section.chapters) for section in sections}
    source_list = work[source_section.id]
    target_list = work[target_section.id]

    source_pos = next((i for i, c in enumerate(source_list) if c.id == chapter_id), None)
    if source_pos is None:
        return False

    if target.target_type == 'chapter':
        target_pos = next((i for i, c in enumerate(target_list) if c.id == target.target_id), None)
        if target_pos is None:
            return False
        insert_at = target_pos if target.before else target_pos + 1
    else:
        insert_at = 0 if target.before else len(target_list)

    # Removing an earlier item in the same list shifts the destination one place.
    source_list.pop(source_pos)
    if source_section.id == target_section.id and source_pos < insert_at:
        insert_at -= 1
    insert_at = max(0, min(insert_at, len(target_list)))
    target_list.insert(insert_at, chapter)

    after_ids = [c.id for section in sections for c in work[section.id]]
    if len(after_ids) != len(before_ids) or set(after_ids) != set(before_ids):
        raise RuntimeError('Veiligheidscontrole drag-and-drop mislukt')
    if len(after_ids) != len(set(after_ids)):
        raise RuntimeError('Drag-and-drop zou een hoofdstuk dupliceren')

    changed = any([c.id for c in section.chapters] != [c.id for c in work[section.id]] for section in sections)
    if not changed:
        return False

    for section in sections:
        section.chapters[:] = work[section.id]
    return True
