import json
from unittest.mock import patch
from quietwriter.ai.openrouter_provider import OpenRouterProvider

class FakeResponse:
    ok = True
    status_code = 200
    def iter_lines(self, decode_unicode=False):
        rows = [
            {'model': 'cohere/north-mini-code:free', 'choices': [{'delta': {'reasoning': 'thinking'}}]},
            {'model': 'cohere/north-mini-code:free', 'choices': [{'delta': {'content': 'Hallo Pip'}}]},
        ]
        for row in rows:
            yield ('data: ' + json.dumps(row)).encode('utf-8')
        yield b'data: [DONE]'
    def close(self):
        pass

def test_actual_model_arrives_separately_from_content():
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=FakeResponse()):
        chunks = list(OpenRouterProvider('secret').stream_chat('openrouter/free', [{'role':'user','content':'Hallo'}]))
    assert ''.join(c.content for c in chunks) == 'Hallo Pip'
    assert ''.join(c.thinking for c in chunks) == 'thinking'
    assert {c.model for c in chunks if c.model} == {'cohere/north-mini-code:free'}

def test_response_without_model_does_not_invent_one():
    class NoModelResponse(FakeResponse):
        def iter_lines(self, decode_unicode=False):
            yield b'data: {"choices":[{"delta":{"content":"Hallo"}}]}'
            yield b'data: [DONE]'
    with patch('quietwriter.ai.openrouter_provider.requests.post', return_value=NoModelResponse()):
        chunks = list(OpenRouterProvider('secret').stream_chat('openrouter/free', []))
    assert not any(c.model for c in chunks)
