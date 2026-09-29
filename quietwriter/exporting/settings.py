from __future__ import annotations

import copy
import json
from pathlib import Path

from ..storage import _safe_atomic_write_text, _guard_existing_json


def default_export_settings() -> dict:
    return {
        'version': 1,
        'format': 'epub',
        'epub': {
            'template': 'classic',
            'include_cover': True,
            # artwork_only: QuietWriter adds title/author to the artwork.
            # artwork_with_text: the supplied artwork is already complete.
            'cover_mode': 'artwork_only',
            'show_section_titles': True,
        },
        'pdf': {
            'template': 'classic',
            'paper_size': 'A5',
            'margin_preset': 'standard',
            'page_numbers': True,
            'running_header': True,
            'show_section_titles': True,
        },
        'markdown': {},
    }


class ExportSettingsStore:
    """Small per-book export preferences, kept separate from publication data."""

    def __init__(self, library=None):
        self.library = library

    def path(self, book) -> Path:
        return Path(book.path) / 'export' / 'settings.json'

    def validate_source(self, book):
        """Raise CorruptSourceError when existing settings cannot be safely rewritten."""
        _guard_existing_json(self.path(book))

    def load(self, book) -> dict:
        settings = default_export_settings()
        path = self.path(book)
        if not path.exists():
            return settings
        try:
            current = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return settings
        if isinstance(current, dict):
            if current.get('format') in {'epub', 'pdf', 'markdown'}:
                settings['format'] = current['format']
            if isinstance(current.get('epub'), dict):
                settings['epub'].update(current['epub'])
            if isinstance(current.get('pdf'), dict):
                settings['pdf'].update(current['pdf'])
        return settings

    def save(self, book, settings: dict):
        if self.library is not None:
            self.library.verify_book_unchanged(book)
        _guard_existing_json(self.path(book))
        payload = copy.deepcopy(default_export_settings())
        payload['format'] = settings.get('format', 'epub') if settings.get('format') in {'epub', 'pdf', 'markdown'} else 'epub'
        if isinstance(settings.get('epub'), dict):
            payload['epub'].update(settings['epub'])
        if isinstance(settings.get('pdf'), dict):
            payload['pdf'].update(settings['pdf'])
        _safe_atomic_write_text(self.path(book), json.dumps(payload, ensure_ascii=False, indent=2))
        if self.library is not None:
            self.library.refresh_book_revision(book)
