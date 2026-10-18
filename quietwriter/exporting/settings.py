from __future__ import annotations

import copy
import json
from pathlib import Path

from ..storage import _safe_atomic_write_text, _guard_existing_json
from .purposes import PURPOSES_BY_ID

_PURPOSE_IDS = frozenset(PURPOSES_BY_ID)
_FORMATS = frozenset({'epub', 'pdf', 'markdown', 'docx', 'qwbook', 'submission'})


def _clean_submission(values: dict) -> dict:
    """Alleen de vormgeving; contactgegevens nooit in het boek bewaren."""
    return {k: v for k, v in values.items() if k in ('font', 'line_spacing', 'running_header', 'anonymous')}


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
        'docx': {},
        # Exportdoel Inzenden (1.7). Contactgegevens staan niet hier maar in de
        # app-instellingen: ze horen bij de schrijver, niet bij het boek.
        'submission': {'font': 'times', 'line_spacing': 'double', 'running_header': True, 'anonymous': False},
        'qwbook': {'include_history': True, 'include_ai_chat': True},
        'purpose': None,
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
            if current.get('format') in _FORMATS:
                settings['format'] = current['format']
            if isinstance(current.get('epub'), dict):
                settings['epub'].update(current['epub'])
            if isinstance(current.get('pdf'), dict):
                settings['pdf'].update(current['pdf'])
            if isinstance(current.get('qwbook'), dict):
                settings['qwbook'].update(current['qwbook'])
            if isinstance(current.get('submission'), dict):
                settings['submission'].update(_clean_submission(current['submission']))
            if current.get('purpose') in _PURPOSE_IDS:
                settings['purpose'] = current['purpose']
        return settings

    def save(self, book, settings: dict):
        if self.library is not None:
            self.library.verify_book_unchanged(book)
        _guard_existing_json(self.path(book))
        payload = copy.deepcopy(default_export_settings())
        payload['format'] = settings.get('format', 'epub') if settings.get('format') in _FORMATS else 'epub'
        if isinstance(settings.get('epub'), dict):
            payload['epub'].update(settings['epub'])
        if isinstance(settings.get('pdf'), dict):
            payload['pdf'].update(settings['pdf'])
        if isinstance(settings.get('qwbook'), dict):
            payload['qwbook'].update(settings['qwbook'])
        if isinstance(settings.get('submission'), dict):
            payload['submission'].update(_clean_submission(settings['submission']))
        payload['purpose'] = settings.get('purpose') if settings.get('purpose') in _PURPOSE_IDS else None
        _safe_atomic_write_text(self.path(book), json.dumps(payload, ensure_ascii=False, indent=2))
        if self.library is not None:
            self.library.refresh_book_revision(book)
