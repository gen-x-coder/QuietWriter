from __future__ import annotations

import json
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from quietwriter.ai.ollama_provider import OllamaProvider
from quietwriter.ai.openrouter_provider import OpenRouterProvider
from quietwriter.markdown_io import insert_scene_break


class FakeResponse:
    def __init__(self, lines=(), *, ok=True, status_code=200, data=None, text=''):
        self.ok = ok
        self.status_code = status_code
        self._lines = list(lines)
        self._data = data if data is not None else {}
        self.text = text
        self.closed = False

    def json(self):
        return self._data

    def iter_lines(self, decode_unicode=True):
        yield from self._lines

    def close(self):
        self.closed = True


def _consume_in_thread(provider, response, patch_target, post_kwargs):
    entered = threading.Event()
    release = threading.Event()
    result = {'chunks': None, 'error': None}

    def fake_post(*args, **kwargs):
        entered.set()
        assert release.wait(2), 'test did not release the simulated connect'
        return response

    def consume():
        try:
            result['chunks'] = list(provider.stream_chat('model', [{'role': 'user', 'content': 'test'}]))
        except Exception as exc:  # pragma: no cover - diagnostic guard
            result['error'] = exc

    with patch(patch_target, side_effect=fake_post) as mocked:
        thread = threading.Thread(target=consume)
        thread.start()
        assert entered.wait(2), 'provider never entered requests.post'
        provider.cancel_active()
        release.set()
        thread.join(2)
        assert not thread.is_alive()
        mocked.assert_called_once()

    assert result['error'] is None
    assert result['chunks'] == []
    assert response.closed is True


def test_ollama_stop_during_connect_is_not_lost():
    response = FakeResponse([json.dumps({'message': {'content': 'mag niet komen'}, 'done': True})])
    _consume_in_thread(
        OllamaProvider(),
        response,
        'quietwriter.ai.ollama_provider.requests.post',
        {},
    )


def test_openrouter_stop_during_connect_is_not_lost():
    response = FakeResponse(['data: ' + json.dumps({'choices': [{'delta': {'content': 'mag niet komen'}}]}), 'data: [DONE]'])
    _consume_in_thread(
        OpenRouterProvider('key'),
        response,
        'quietwriter.ai.openrouter_provider.requests.post',
        {},
    )


def test_ollama_midstream_error_is_raised_with_detail():
    response = FakeResponse([
        json.dumps({'message': {'content': 'gedeeltelijk'}}),
        json.dumps({'error': 'model crashte tijdens genereren'}),
    ])
    provider = OllamaProvider()
    with patch('quietwriter.ai.ollama_provider.requests.post', return_value=response):
        stream = provider.stream_chat('model', [{'role': 'user', 'content': 'test'}])
        first = next(stream)
        assert first.content == 'gedeeltelijk'
        with pytest.raises(RuntimeError, match='model crashte tijdens genereren'):
            next(stream)
    assert response.closed is True


def test_openrouter_midstream_error_is_raised_with_detail():
    response = FakeResponse([
        'data: ' + json.dumps({'choices': [{'delta': {'content': 'gedeeltelijk'}}]}),
        'data: ' + json.dumps({'error': {'message': 'upstream provider failed', 'code': 502}}),
    ])
    provider = OpenRouterProvider('key')
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=response):
        stream = provider.stream_chat('model', [{'role': 'user', 'content': 'test'}])
        first = next(stream)
        assert first.content == 'gedeeltelijk'
        with pytest.raises(RuntimeError, match='upstream provider failed'):
            next(stream)
    assert response.closed is True


def test_scene_break_mid_sentence_moves_to_end_of_current_line():
    text = 'Hallo wereld, dit is een zin.'
    out, pos = insert_scene_break(text, 5)
    assert out == 'Hallo wereld, dit is een zin.\n\n***'
    assert pos == len(out)


def test_scene_break_at_start_of_line_stays_before_that_line():
    text = 'Eerste alinea.\n\nTweede alinea.'
    position = text.index('Tweede')
    out, pos = insert_scene_break(text, position)
    assert out == 'Eerste alinea.\n\n***\n\nTweede alinea.'
    assert out[:pos] == 'Eerste alinea.\n\n***\n\n'


def test_scene_break_trims_leading_space_from_right_hand_text():
    text = 'Eerste alinea.\n    Tweede alinea.'
    position = text.index('Tweede') - 2
    out, _ = insert_scene_break(text, position)
    assert out == 'Eerste alinea.\n    Tweede alinea.\n\n***'


def test_same_book_ai_set_book_has_fast_path_source_guard():
    source = Path(__file__).parents[2].joinpath('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert 'self._book_id = None' in source
    assert 'new_book_id == self._book_id' in source
    assert 'self.store = ConversationStore(book)' in source
    assert 'return' in source[source.index('new_book_id == self._book_id'):source.index('new_book_id == self._book_id') + 500]
