from __future__ import annotations

import json
from pathlib import Path

from .storage import CorruptSourceError, _guard_existing_json, _safe_atomic_write_text


class OpenPointStore:
    """Fail-closed metadata store for notes attached to manuscript open points."""

    VERSION = 1

    def __init__(self, library):
        self.library = library

    def path(self, book) -> Path:
        return Path(book.path) / 'planning' / 'open_points.json'

    def load_notes(self, book) -> dict[str, str]:
        path = self.path(book)
        if not path.exists():
            return {}
        _guard_existing_json(path)
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CorruptSourceError(path) from exc
        version = data.get('version', 1)
        if version != self.VERSION or not isinstance(data.get('notes', {}), dict):
            raise CorruptSourceError(path)
        return {
            str(key): str(value or '')
            for key, value in data.get('notes', {}).items()
            if str(key)
        }

    def _save(self, book, notes: dict[str, str]) -> None:
        self.library.verify_book_unchanged(book)
        path = self.path(book)
        _guard_existing_json(path)
        # Re-read after the revision check so malformed/future metadata is never
        # replaced by an apparently valid empty object.
        if path.exists():
            self.load_notes(book)
        payload = {'version': self.VERSION, 'notes': dict(sorted(notes.items()))}
        _safe_atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))
        self.library.refresh_book_revision(book)

    def set_note(self, book, point_id: str, note: str) -> None:
        notes = self.load_notes(book)
        value = str(note or '').strip()
        if value:
            notes[str(point_id)] = value
        else:
            notes.pop(str(point_id), None)
        self._save(book, notes)

    def remove_note(self, book, point_id: str) -> None:
        path = self.path(book)
        if not path.exists():
            return
        notes = self.load_notes(book)
        if str(point_id) not in notes:
            return
        notes.pop(str(point_id), None)
        self._save(book, notes)
