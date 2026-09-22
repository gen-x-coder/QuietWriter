from __future__ import annotations

from dataclasses import asdict, dataclass, field
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Relation:
    id: str = field(default_factory=new_id)
    target_id: str = ''
    type: str = ''
    inverse_type: str = ''
    description: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'Relation':
        return cls(
            id=str(data.get('id') or new_id()),
            target_id=str(data.get('target_id') or ''),
            type=str(data.get('type') or ''),
            inverse_type=str(data.get('inverse_type') or ''),
            description=str(data.get('description') or ''),
        )


@dataclass
class Character:
    id: str = field(default_factory=new_id)
    name: str = 'Nieuw personage'
    role: str = ''
    description: str = ''
    personality: str = ''
    motivation: str = ''
    goals: str = ''
    fears: str = ''
    values: str = ''
    conflicts: str = ''
    background: str = ''
    voice: str = ''
    under_pressure: str = ''
    notes: str = ''
    relations: list[Relation] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        kwargs = {k: data.get(k, '') for k in (
            'name', 'role', 'description', 'personality', 'motivation', 'goals', 'fears',
            'values', 'conflicts', 'background', 'voice', 'under_pressure', 'notes'
        )}
        return cls(
            id=str(data.get('id') or new_id()),
            relations=[Relation.from_dict(x) for x in data.get('relations', []) if isinstance(x, dict)],
            **{k: str(v or '') for k, v in kwargs.items()},
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Scene:
    id: str = field(default_factory=new_id)
    chapter_id: str | None = None
    title: str = 'Nieuwe scène'
    synopsis: str = ''
    character_ids: list[str] = field(default_factory=list)
    location: str = ''
    goal: str = ''
    conflict: str = ''
    outcome: str = ''
    status: str = 'idee'
    notes: str = ''

    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        return cls(
            id=str(data.get('id') or new_id()),
            chapter_id=(str(data['chapter_id']) if data.get('chapter_id') else None),
            title=str(data.get('title') or 'Nieuwe scène'),
            synopsis=str(data.get('synopsis') or ''),
            character_ids=[str(x) for x in data.get('character_ids', [])],
            location=str(data.get('location') or ''),
            goal=str(data.get('goal') or ''),
            conflict=str(data.get('conflict') or ''),
            outcome=str(data.get('outcome') or ''),
            status=str(data.get('status') or 'idee'),
            notes=str(data.get('notes') or ''),
        )

    def to_dict(self) -> dict:
        return asdict(self)
