from __future__ import annotations

from pathlib import Path

from .storage import CorruptSourceError

CURRENT_PLANNING_FORMAT = 1


class FuturePlanningFormatError(RuntimeError):
    """Planning data was written by a newer QuietWriter and must not be rolled back."""

    def __init__(self, path: Path, version):
        self.path = Path(path)
        self.version = version
        super().__init__(
            f"{self.path} gebruikt Planning-formaat {version}; deze QuietWriter ondersteunt "
            f"tot en met {CURRENT_PLANNING_FORMAT}. Werk QuietWriter bij."
        )


def validate_planning_payload(kind: str, value, path: Path):
    """Validate a Planning JSON payload without mutating it.

    A newer format is deliberately distinguished from corruption so Integrity
    never offers a destructive rollback for data created by a newer app.
    """
    path = Path(path)
    if not isinstance(value, dict):
        raise CorruptSourceError(path)
    version = value.get('version', 1)
    if not isinstance(version, int):
        raise CorruptSourceError(path)
    if version > CURRENT_PLANNING_FORMAT:
        raise FuturePlanningFormatError(path, version)
    if version < 1 or version != CURRENT_PLANNING_FORMAT:
        raise CorruptSourceError(path)

    if kind == 'characters':
        rows = value.get('characters', [])
        if not isinstance(rows, list):
            raise CorruptSourceError(path)
        for row in rows:
            if not isinstance(row, dict):
                raise CorruptSourceError(path)
            relations = row.get('relations', [])
            if not isinstance(relations, list) or any(not isinstance(item, dict) for item in relations):
                raise CorruptSourceError(path)
        return value

    if kind == 'scenes':
        rows = value.get('scenes', [])
        if not isinstance(rows, list):
            raise CorruptSourceError(path)
        for row in rows:
            if not isinstance(row, dict):
                raise CorruptSourceError(path)
            if not isinstance(row.get('character_ids', []), list):
                raise CorruptSourceError(path)
        return value

    raise ValueError(f'Onbekend Planning-payloadtype: {kind}')
