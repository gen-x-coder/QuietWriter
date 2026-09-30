from __future__ import annotations

import json
from pathlib import Path

from .planning_models import Character, Scene
from .storage import CorruptSourceError, _safe_atomic_write_text, _guard_existing_utf8, _guard_existing_json
from .planning_validation import validate_planning_payload


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
            value = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            # Legacy contract: unreadable/invalid JSON loads as an empty Planning
            # view, while normal saves remain fail-closed via _guard_existing_json.
            return default
        return value

    def load_characters(self, book) -> list[Character]:
        path = self.root(book) / 'characters.json'
        data = self._read_json(path, {'version': 1, 'characters': []})
        validate_planning_payload('characters', data, path)
        result = []
        for row in data.get('characters', []):
            result.append(Character.from_dict(row))
        return result

    def save_characters(self, book, characters: list[Character]):
        self.library.verify_book_unchanged(book)
        _guard_existing_json(self.root(book) / 'characters.json')
        if (self.root(book) / 'characters.json').exists():
            self.load_characters(book)
        payload = {'version': 1, 'characters': [c.to_dict() for c in characters]}
        _safe_atomic_write_text(self.root(book) / 'characters.json', json.dumps(payload, ensure_ascii=False, indent=2))
        self.library.refresh_book_revision(book)

    def load_scenes(self, book) -> list[Scene]:
        path = self.root(book) / 'outline.json'
        data = self._read_json(path, {'version': 1, 'scenes': []})
        validate_planning_payload('scenes', data, path)
        result = []
        for row in data.get('scenes', []):
            result.append(Scene.from_dict(row))
        return result

    def save_scenes(self, book, scenes: list[Scene]):
        self.library.verify_book_unchanged(book)
        _guard_existing_json(self.root(book) / 'outline.json')
        if (self.root(book) / 'outline.json').exists():
            self.load_scenes(book)
        payload = {'version': 1, 'scenes': [s.to_dict() for s in scenes]}
        _safe_atomic_write_text(self.root(book) / 'outline.json', json.dumps(payload, ensure_ascii=False, indent=2))
        self.library.refresh_book_revision(book)

    def load_notes(self, book) -> str:
        path = self.root(book) / 'notes.md'
        return path.read_text(encoding='utf-8-sig') if path.exists() else ''

    def save_notes(self, book, text: str):
        self.library.verify_book_unchanged(book)
        _guard_existing_utf8(self.root(book) / 'notes.md')
        _safe_atomic_write_text(self.root(book) / 'notes.md', text)
        self.library.refresh_book_revision(book)
