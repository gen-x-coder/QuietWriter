from __future__ import annotations

import json
from pathlib import Path

from .planning_models import Character, Scene
from .storage import _safe_atomic_write_text


class PlanningStore:
    """Storage for optional book-planning data.

    Planning files live inside the book folder and therefore participate in the
    same revision/conflict guard as the manuscript. The UI never writes these
    files directly.
    """

    def __init__(self, library):
        self.library = library

    def root(self, book) -> Path:
        return book.path / 'planning'

    def _read_json(self, path: Path, default):
        if not path.exists():
            return default
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
            return value
        except (OSError, json.JSONDecodeError):
            return default

    def load_characters(self, book) -> list[Character]:
        data = self._read_json(self.root(book) / 'characters.json', {'version': 1, 'characters': []})
        rows = data.get('characters', []) if isinstance(data, dict) else []
        return [Character.from_dict(row) for row in rows if isinstance(row, dict)]

    def save_characters(self, book, characters: list[Character]):
        self.library.verify_book_unchanged(book)
        payload = {'version': 1, 'characters': [c.to_dict() for c in characters]}
        _safe_atomic_write_text(self.root(book) / 'characters.json', json.dumps(payload, ensure_ascii=False, indent=2))
        self.library.refresh_book_revision(book)

    def load_scenes(self, book) -> list[Scene]:
        data = self._read_json(self.root(book) / 'outline.json', {'version': 1, 'scenes': []})
        rows = data.get('scenes', []) if isinstance(data, dict) else []
        return [Scene.from_dict(row) for row in rows if isinstance(row, dict)]

    def save_scenes(self, book, scenes: list[Scene]):
        self.library.verify_book_unchanged(book)
        payload = {'version': 1, 'scenes': [s.to_dict() for s in scenes]}
        _safe_atomic_write_text(self.root(book) / 'outline.json', json.dumps(payload, ensure_ascii=False, indent=2))
        self.library.refresh_book_revision(book)

    def load_notes(self, book) -> str:
        path = self.root(book) / 'notes.md'
        return path.read_text(encoding='utf-8') if path.exists() else ''

    def save_notes(self, book, text: str):
        self.library.verify_book_unchanged(book)
        _safe_atomic_write_text(self.root(book) / 'notes.md', text)
        self.library.refresh_book_revision(book)
