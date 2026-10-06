from __future__ import annotations

import json
from pathlib import Path

from .publication_models import PublicationData, item_definition
from .storage import _safe_atomic_write_text, _guard_existing_utf8, _guard_existing_json


class PublicationStore:
    """Persistent publication structure for one book.

    Content is deliberately separate from planning data. Publication files are
    part of the book revision guard and version snapshots.
    """

    def __init__(self, library):
        self.library = library

    def root(self, book) -> Path:
        return book.path / 'publication'

    def config_path(self, book) -> Path:
        return self.root(book) / 'publication.json'

    def text_path(self, book, key: str) -> Path:
        return self.root(book) / 'texts' / f'{key}.md'

    def load(self, book) -> PublicationData:
        path = self.config_path(book)
        if not path.exists():
            return PublicationData.defaults_for_book(book)
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
        defaults = PublicationData.defaults_for_book(book)
        loaded = PublicationData.from_dict(payload)
        # Old/partial files inherit sensible defaults without rewriting disk.
        for name in ('title_page', 'copyright', 'epigraph', 'contents'):
            merged = dict(getattr(defaults, name))
            current = dict(getattr(loaded, name))
            if name == 'copyright':
                clauses = dict(merged.get('clauses') or {})
                clauses.update(current.get('clauses') or {})
                merged.update(current)
                merged['clauses'] = clauses
            else:
                merged.update(current)
            setattr(loaded, name, merged)
        return loaded

    def save(self, book, data: PublicationData):
        self.library.verify_book_unchanged(book)
        _guard_existing_json(self.config_path(book))
        _safe_atomic_write_text(self.config_path(book), json.dumps(data.to_dict(), ensure_ascii=False, indent=2))
        self.library.refresh_book_revision(book)

    def load_text(self, book, key: str) -> str:
        definition = item_definition(key)
        if not definition or definition['kind'] != 'text':
            return ''
        path = self.text_path(book, key)
        if not path.exists():
            return ''
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return ''

    def text_is_corrupt(self, book, key: str) -> bool:
        path = self.text_path(book, key)
        if not path.exists():
            return False
        try:
            path.read_bytes().decode('utf-8')
            return False
        except UnicodeDecodeError:
            return True

    def save_text(self, book, key: str, text: str):
        definition = item_definition(key)
        if not definition or definition['kind'] != 'text':
            raise ValueError(f'{key} is geen vrij tekstonderdeel.')
        self.library.verify_book_unchanged(book)
        _guard_existing_utf8(self.text_path(book, key))
        _safe_atomic_write_text(self.text_path(book, key), text)
        self.library.refresh_book_revision(book)
