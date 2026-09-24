from __future__ import annotations

import copy
import json
from pathlib import Path

from ..storage import _safe_atomic_write_text


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
        'markdown': {},
    }


class ExportSettingsStore:
    """Small per-book export preferences, kept separate from publication data."""

    def path(self, book) -> Path:
        return Path(book.path) / 'export' / 'settings.json'

    def load(self, book) -> dict:
        settings = default_export_settings()
        path = self.path(book)
        if not path.exists():
            return settings
        try:
            current = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return settings
        if isinstance(current, dict):
            if current.get('format') in {'epub', 'markdown'}:
                settings['format'] = current['format']
            if isinstance(current.get('epub'), dict):
                settings['epub'].update(current['epub'])
        return settings

    def save(self, book, settings: dict):
        payload = copy.deepcopy(default_export_settings())
        payload['format'] = settings.get('format', 'epub') if settings.get('format') in {'epub', 'markdown'} else 'epub'
        if isinstance(settings.get('epub'), dict):
            payload['epub'].update(settings['epub'])
        _safe_atomic_write_text(self.path(book), json.dumps(payload, ensure_ascii=False, indent=2))
