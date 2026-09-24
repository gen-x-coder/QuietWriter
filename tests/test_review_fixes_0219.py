from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quietwriter.ai.ollama_provider import OllamaProvider
from quietwriter.ai.openrouter_provider import OpenRouterProvider
from quietwriter.markdown_io import insert_scene_break
from quietwriter.ollama import OllamaClient


class FakeResponse:
    def __init__(self, *, ok=True, status_code=200, data=None, text=''):
        self.ok = ok
        self.status_code = status_code
        self._data = data if data is not None else {}
        self.text = text

    def json(self):
        return self._data

    def iter_lines(self, decode_unicode=True):
        return iter(())

    def close(self):
        pass


def test_ollama_client_forwards_model_info_timeout():
    client = OllamaClient()
    with patch.object(client.provider, 'list_models', return_value=[]) as mocked:
        client.model_info(timeout=1.8)
    mocked.assert_called_once_with(timeout=1.8)


def test_ollama_provider_uses_requested_model_timeout():
    response = FakeResponse(data={'models': []})
    with patch('quietwriter.ai.ollama_provider.requests.get', return_value=response) as mocked:
        OllamaProvider().list_models(timeout=1.25)
    assert mocked.call_args.kwargs['timeout'] == 1.25


def test_openrouter_model_error_contains_api_message():
    response = FakeResponse(
        ok=False,
        status_code=401,
        data={'error': {'message': 'Invalid API key'}},
    )
    with patch('quietwriter.ai.openrouter_provider.requests.get', return_value=response):
        with pytest.raises(RuntimeError, match='Invalid API key'):
            OpenRouterProvider('bad-key').list_models()


def test_scene_break_is_not_duplicated_when_cursor_is_before_existing_break():
    text = 'Eerste alinea.\n\n***\n\nTweede alinea.'
    out, _ = insert_scene_break(text, len('Eerste alinea.'))
    assert out == text


def test_scene_break_is_not_duplicated_when_cursor_is_after_existing_break():
    text = 'Eerste alinea.\n\n***\n\nTweede alinea.'
    out, _ = insert_scene_break(text, text.index('***') + 3)
    assert out == text


def test_image_insert_source_keeps_old_label_for_invalid_edit_candidate_source_guard():
    source = Path(__file__).parents[1].joinpath('quietwriter/ui/image_insert_widget.py').read_text(encoding='utf-8')
    assert "self.file_label.setText(self._display_name)" in source
    assert "if self._mode == 'insert':" in source
