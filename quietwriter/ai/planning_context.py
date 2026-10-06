from __future__ import annotations

from dataclasses import dataclass, field

from ..planning_storage import PlanningStore
from ..chapter_context import build_chapter_context
from ..planning_validation import FuturePlanningFormatError
from ..storage import CorruptSourceError


@dataclass
class PlanningSelection:
    character_ids: set[str] = field(default_factory=set)
    scene_ids: set[str] = field(default_factory=set)
    include_notes: bool = False

    def is_empty(self) -> bool:
        return not self.character_ids and not self.scene_ids and not self.include_notes




@dataclass
class PlanningContextResult:
    text: str = ''
    labels: list[str] = field(default_factory=list)
    error: str = ''


@dataclass
class ChapterPlanningPreview:
    text: str = ''
    labels: list[str] = field(default_factory=list)
    error: str = ''

@dataclass(frozen=True)
class PlanningOption:
    id: str
    label: str


@dataclass
class PlanningOptions:
    characters: list[PlanningOption] = field(default_factory=list)
    scenes: list[PlanningOption] = field(default_factory=list)
    notes_available: bool = False
    error: str = ''


def _planning_unavailable_message(exc: Exception) -> str:
    if isinstance(exc, FuturePlanningFormatError):
        return 'Gemaakt met een nieuwere QuietWriter. Werk QuietWriter bij.'
    return 'Planning kan niet betrouwbaar worden gelezen.'


def options_for_book(library, book) -> PlanningOptions:
    if not book:
        return PlanningOptions()
    store = PlanningStore(library)
    try:
        characters = store.load_characters(book)
        scenes = store.load_scenes(book)
    except (CorruptSourceError, FuturePlanningFormatError) as exc:
        return PlanningOptions(error=_planning_unavailable_message(exc))
    return PlanningOptions(
        characters=[PlanningOption(c.id, c.name or 'Naamloos personage') for c in characters],
        scenes=[PlanningOption(s.id, s.title or 'Naamloze scène') for s in scenes],
        notes_available=bool(store.load_notes(book).strip()),
    )


def _line(label: str, value: str) -> str | None:
    value = (value or '').strip()
    return f'- {label}: {value}' if value else None


def build_planning_context_result(library, book, selection: PlanningSelection) -> PlanningContextResult:
    if not book or selection.is_empty():
        return PlanningContextResult()
    store = PlanningStore(library)
    try:
        characters = store.load_characters(book)
        scenes = store.load_scenes(book)
    except (CorruptSourceError, FuturePlanningFormatError) as exc:
        return PlanningContextResult(error=_planning_unavailable_message(exc))
    char_by_id = {c.id: c for c in characters}
    chapter_names = {c.id: c.title for sec in book.sections for c in sec.chapters}
    parts: list[str] = []
    labels: list[str] = []

    chosen_chars = [c for c in characters if c.id in selection.character_ids]
    if chosen_chars:
        parts.append('# Geselecteerde personages')
        labels.append(f'{len(chosen_chars)} personage' + ('s' if len(chosen_chars) != 1 else ''))
        for char in chosen_chars:
            parts.append(f'## {char.name}')
            rows = [
                _line('Rol', char.role), _line('Beschrijving', char.description),
                _line('Persoonlijkheid', char.personality), _line('Motivatie', char.motivation),
                _line('Doelen', char.goals), _line('Angsten', char.fears),
                _line('Waarden', char.values), _line('Conflicten', char.conflicts),
                _line('Achtergrond', char.background), _line('Stem', char.voice),
                _line('Onder druk', char.under_pressure), _line('Notities', char.notes),
            ]
            relation_rows = []
            for rel in char.relations:
                target = char_by_id.get(rel.target_id)
                target_name = target.name if target else rel.target_id
                relation = f'{rel.type or "relatie"} met {target_name}'
                if rel.description:
                    relation += f' — {rel.description.strip()}'
                relation_rows.append(relation)
            if relation_rows:
                rows.append('- Relaties: ' + '; '.join(relation_rows))
            parts.extend(row for row in rows if row)

    chosen_scenes = [s for s in scenes if s.id in selection.scene_ids]
    if chosen_scenes:
        parts.append('# Geselecteerde scènes')
        labels.append(f'{len(chosen_scenes)} scène' + ('s' if len(chosen_scenes) != 1 else ''))
        for scene in chosen_scenes:
            parts.append(f'## {scene.title}')
            names = [char_by_id[cid].name for cid in scene.character_ids if cid in char_by_id]
            rows = [
                _line('Hoofdstuk', chapter_names.get(scene.chapter_id or '', '') if scene.chapter_id else 'Los idee'),
                _line('Synopsis', scene.synopsis), _line('Personages', ', '.join(names)),
                _line('Locatie', scene.location), _line('Doel', scene.goal),
                _line('Conflict', scene.conflict), _line('Uitkomst', scene.outcome),
                _line('Status', scene.status), _line('Notities', scene.notes),
            ]
            parts.extend(row for row in rows if row)

    if selection.include_notes:
        notes = store.load_notes(book).strip()
        if notes:
            parts.append('# Planning-notities\n' + notes)
            labels.append('notities')

    return PlanningContextResult(text='\n\n'.join(parts).strip(), labels=labels)


def build_planning_context(library, book, selection: PlanningSelection) -> tuple[str, list[str]]:
    result = build_planning_context_result(library, book, selection)
    return result.text, result.labels


def chapter_planning_preview(library, book, chapter_id: str | None) -> ChapterPlanningPreview:
    if not book or not chapter_id:
        return ChapterPlanningPreview()
    store = PlanningStore(library)
    try:
        characters = store.load_characters(book)
        scenes = store.load_scenes(book)
    except (CorruptSourceError, FuturePlanningFormatError) as exc:
        return ChapterPlanningPreview(error=_planning_unavailable_message(exc))

    context = build_chapter_context(chapter_id, scenes, characters)
    if not context.scenes:
        return ChapterPlanningPreview(labels=['geen gekoppelde scènes'])

    parts = ['# Planning van dit hoofdstuk']
    if context.character_names:
        parts.append('Personages: ' + ', '.join(context.character_names))
    for scene in context.scenes:
        parts.append(f'## {scene.title or "Scène"}')
        rows = [
            _line('Status', scene.status), _line('Locatie', scene.location),
            _line('Synopsis', scene.synopsis), _line('Doel', scene.goal),
            _line('Conflict', scene.conflict), _line('Uitkomst', scene.outcome),
            _line('Notities', scene.notes), _line('Personages', ', '.join(scene.character_names)),
        ]
        parts.extend(row for row in rows if row)
    labels = [f'{len(context.scenes)} scène' + ('s' if len(context.scenes) != 1 else '')]
    if context.character_names:
        labels.append(f'{len(context.character_names)} personage' + ('s' if len(context.character_names) != 1 else ''))
    return ChapterPlanningPreview(text='\n\n'.join(parts).strip(), labels=labels)
