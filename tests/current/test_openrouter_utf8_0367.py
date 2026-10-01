from __future__ import annotations

import json
from unittest.mock import patch

from quietwriter.ai.openrouter_provider import OpenRouterProvider


class FakeUtf8Response:
    ok = True
    status_code = 200
    text = ''

    def iter_lines(self, decode_unicode=False):
        assert decode_unicode is False
        payload = {
            'choices': [{'delta': {'content': 'scène, één café, naïef, €'}}]
        }
        yield ('data: ' + json.dumps(payload, ensure_ascii=False)).encode('utf-8')
        yield b'data: [DONE]'

    def close(self):
        pass


def test_openrouter_stream_decodes_sse_as_utf8():
    provider = OpenRouterProvider('key')
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=FakeUtf8Response()):
        chunks = list(provider.stream_chat('model', [{'role': 'user', 'content': 'test'}]))
    assert ''.join(chunk.content for chunk in chunks) == 'scène, één café, naïef, €'
