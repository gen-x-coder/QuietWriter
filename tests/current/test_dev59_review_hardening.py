"""Non-Qt contract regressions for the dev.59 review corrections."""
import json
from pathlib import Path
from quietwriter.ai.response_guard import guard_memory_claims
from quietwriter.ai.openrouter_provider import OpenRouterProvider
from unittest.mock import patch
import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_memory_claim_and_quotes_are_distinct():
    assert guard_memory_claims('„Ik heb het onthouden," zei Pip.') == '„Ik heb het onthouden," zei Pip.'
    assert guard_memory_claims("'Ik heb het onthouden.'") == "'Ik heb het onthouden.'"
    assert guard_memory_claims('QuietWriter bevestigt: Opgeslagen in Boekgeheugen.') == 'QuietWriter bevestigt: Opgeslagen in Boekgeheugen.'
    assert 'Gebruik **Onthouden**' in guard_memory_claims('Ik heb het opgeslagen in Boekgeheugen.')


def test_all_five_locales_have_openrouter_and_link_keys():
    keys = ['ai.link.title', 'ai.link.confirm', 'ai.link.open', 'ai.link.cancel',
            'settings.ai.openrouter_browser', 'settings.ai.openrouter_connect',
            'settings.ai.openrouter_disconnect', 'settings.ai.openrouter_login_failed',
            'settings.ai.openrouter_login_success', 'settings.ai.openrouter_removed', 'settings.ai.openrouter_wait']
    for locale in ['nl', 'en', 'de', 'fr', 'es']:
        data = json.loads((ROOT / 'quietwriter/locales' / (locale + '.json')).read_text(encoding='utf-8'))
        assert all(data.get(key) for key in keys), locale


def test_openrouter_incomplete_stream_is_reported():
    class Response:
        ok = True
        def iter_lines(self, decode_unicode=False):
            yield b'data: {"choices":[{"delta":{"content":"Incomplete"}}]}'
        def close(self):
            pass
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=Response()):
        with pytest.raises(RuntimeError, match='onderbroken'):
            list(OpenRouterProvider('test').stream_chat('test', []))


def test_non_object_sse_payload_is_ignored():
    class Response:
        ok = True
        def iter_lines(self, decode_unicode=False):
            yield b'data: [1,2]'
            yield b'data: {"choices":[{"delta":{"content":"OK"},"finish_reason":"stop"}]}'
            yield b'data: [DONE]'
        def close(self):
            pass
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=Response()):
        chunks = list(OpenRouterProvider('test').stream_chat('test', []))
    assert ''.join(c.content for c in chunks) == 'OK'


def test_same_section_dirty_editor_refreshes_after_approved_memory():
    source = (ROOT / 'quietwriter/ui/book_memory_page.py').read_text(encoding='utf-8')
    section = source.split('def add_suggestion(', 1)[1].split('def _resolve_external_change', 1)[0]
    assert 'if self._current_key == section_key:' in section
    assert 'if self._current_key == section_key and not self.dirty:' not in section
