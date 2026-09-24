from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quietwriter.ai.openrouter_provider import OpenRouterProvider

ROOT = Path(__file__).resolve().parents[1]


class _FakeResponse:
    def __init__(self, *, ok=False, status_code=429, data=None, text=''):
        self.ok = ok
        self.status_code = status_code
        self._data = data or {}
        self.text = text
        self.closed = False

    def json(self):
        return self._data

    def iter_lines(self, decode_unicode=True):
        return iter(())

    def close(self):
        self.closed = True


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')


def test_ai_model_combo_is_selection_only_and_refresh_has_feedback():
    source = _source('quietwriter/ui/settings_page.py')
    assert 'self.model = QComboBox(); self.model.setEditable(False)' in source
    assert "self.ai_model_status.setText(tr('settings.ai.fetching_models'" in source
    assert "self.ai_model_status.setText(tr('settings.ai.fetch_success'" in source
    assert 'count=len(models)' in source
    assert 'self.ai_refresh_button.setEnabled(False)' in source
    assert "self.ai_refresh_button.setEnabled(bool(self.ai_enabled.isChecked()))" in source


def test_ai_model_feedback_locale_keys_exist_in_both_locales():
    import json
    nl = json.loads((ROOT / 'quietwriter/locales/nl.json').read_text(encoding='utf-8'))
    en = json.loads((ROOT / 'quietwriter/locales/en.json').read_text(encoding='utf-8'))
    for key in ('settings.ai.fetching_models', 'settings.ai.fetch_success', 'settings.ai.fetch_failed_short'):
        assert key in nl
        assert key in en


def test_openrouter_stream_error_keeps_api_detail_and_closes_response():
    response = _FakeResponse(data={'error': {'message': 'Rate limit exceeded'}})
    provider = OpenRouterProvider('key')
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=response):
        with pytest.raises(RuntimeError, match='Rate limit exceeded'):
            list(provider.stream_chat('model', [{'role': 'user', 'content': 'test'}]))
    assert response.closed is True


def test_book_details_has_single_active_markdown_export_route():
    source = _source('quietwriter/ui/book_details.py')
    assert '    def export_markdown(self):' not in source
    export_page = _source('quietwriter/ui/export_page.py')
    assert 'export_markdown(self.document, destination, self.export_settings)' in export_page


def test_bookshelf_reuses_word_count_and_does_not_construct_qsettings_in_paint():
    source = _source('quietwriter/ui/bookshelf.py')
    assert "self.settings = QSettings('QuietWriter', 'QuietWriter')" in source
    paint = source[source.index('    def paintEvent(self, event):'):source.index('\n\nclass BookCard', source.index('    def paintEvent(self, event):'))]
    assert "QSettings('QuietWriter', 'QuietWriter')" not in paint
    assert 'word_counts = {}' in source
    assert 'if key not in word_counts:' in source
    assert 'BookCard(self.library, book, words=word_count(book))' in source


def test_epub_section_pairing_is_strict_but_adjacent_ui_pairing_is_not():
    epub = _source('quietwriter/exporting/epub_exporter.py')
    assert 'zip(document.sections, section_paths, strict=True)' in epub
    for relative in (
        'quietwriter/ui/main_window.py',
        'quietwriter/ui/editor_page.py',
        'quietwriter/ui/presentation_highlighter.py',
        'quietwriter/ui/search_panel.py',
        'quietwriter/ui/spell_panel.py',
    ):
        source = _source(relative)
        assert 'zip(' in source
        assert 'strict=False' in source
