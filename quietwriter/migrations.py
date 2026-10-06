from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path

from .storage import _safe_atomic_write_text, slugify

CURRENT_BOOK_FORMAT = 2


class MigrationError(RuntimeError):
    pass


class FutureBookFormatError(MigrationError):
    pass


@dataclass(frozen=True)
class MigrationResult:
    source_format: int
    target_format: int
    changed: bool


def detected_book_format(data: dict) -> int:
    if not isinstance(data, dict):
        raise MigrationError('book.json bevat geen JSON-object.')
    raw = data.get('format', 1)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise MigrationError(f'Ongeldige boekformaatversie: {raw!r}.')
    if raw < 1:
        raise MigrationError(f'Ongeldige boekformaatversie: {raw}.')
    return raw


def validate_manifest_structure(data: dict, *, allow_legacy: bool = True) -> int:
    """Validate exactly the structural fields Library.load_book relies on."""
    fmt = detected_book_format(data)
    if fmt > CURRENT_BOOK_FORMAT:
        raise FutureBookFormatError(
            f'Dit boek gebruikt formaat {fmt}; deze QuietWriter ondersteunt maximaal {CURRENT_BOOK_FORMAT}.'
        )
    if not allow_legacy and fmt < CURRENT_BOOK_FORMAT:
        raise MigrationError(f'Boekformaat {fmt} moet eerst worden gemigreerd.')
    if not isinstance(data.get('id'), str) or not data['id'].strip():
        raise MigrationError('Boek-id ontbreekt of is ongeldig.')
    if not isinstance(data.get('title'), str) or not data['title'].strip():
        raise MigrationError('Boektitel ontbreekt of is ongeldig.')
    metadata = data.get('metadata')
    if metadata is not None and not isinstance(metadata, dict):
        raise MigrationError('metadata moet null of een JSON-object zijn.')

    sections = data.get('sections', [])
    if not isinstance(sections, list):
        raise MigrationError('sections is geen lijst.')
    for section in sections:
        if not isinstance(section, dict):
            raise MigrationError('Een sectie heeft een ongeldig formaat.')
        if not isinstance(section.get('id'), str) or not section['id'].strip():
            raise MigrationError('Sectie-id ontbreekt of is ongeldig.')
        if not isinstance(section.get('title'), str):
            raise MigrationError('Sectietitel ontbreekt of is ongeldig.')
        chapters = section.get('chapters', [])
        if not isinstance(chapters, list):
            raise MigrationError('Een hoofdstuklijst heeft een ongeldig formaat.')
        for chapter in chapters:
            if not isinstance(chapter, dict):
                raise MigrationError('Een hoofdstuk heeft een ongeldig formaat.')
            for key in ('id', 'title', 'file'):
                value = chapter.get(key)
                if not isinstance(value, str) or (key != 'title' and not value.strip()):
                    raise MigrationError(f'Hoofdstukveld {key} ontbreekt of is ongeldig.')
    return fmt


def migrate_manifest_data(data: dict, *, target: int = CURRENT_BOOK_FORMAT):
    source = detected_book_format(data)
    if source > target:
        raise FutureBookFormatError(
            f'Dit boek gebruikt formaat {source}; deze QuietWriter ondersteunt maximaal {target}.'
        )
    work = copy.deepcopy(data)
    version = source
    while version < target:
        if version == 1:
            title = str(work.get('title') or 'Naamloos boek')
            metadata = work.get('metadata')
            if not isinstance(metadata, dict):
                metadata = {}
            metadata = dict(metadata)
            metadata.setdefault('slug', slugify(title))
            work['metadata'] = metadata
            work['format'] = 2
            version = 2
            continue
        raise MigrationError(f'Geen migratiepad beschikbaar vanaf formaat {version}.')
    return work, MigrationResult(source, target, work != data)


def migrate_manifest_file(path: Path, *, target: int = CURRENT_BOOK_FORMAT) -> MigrationResult:
    path = Path(path)
    try:
        original = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationError(f'book.json kan niet worden gemigreerd: {exc}') from exc
    migrated, result = migrate_manifest_data(original, target=target)
    if not result.changed:
        return result
    _safe_atomic_write_text(path, json.dumps(migrated, ensure_ascii=False, indent=2))
    return result
