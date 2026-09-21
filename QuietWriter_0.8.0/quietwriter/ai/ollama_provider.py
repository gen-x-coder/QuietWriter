from __future__ import annotations
import json
import requests
from .providers import AIProvider, StreamChunk


class OllamaProvider(AIProvider):
    name = 'ollama'

    def __init__(self, base_url='http://127.0.0.1:11434'):
        self.base_url = base_url.rstrip('/')

    def list_models(self) -> list[dict]:
        r = requests.get(f'{self.base_url}/api/tags', timeout=2.5)
        r.raise_for_status()
        return [
            {'name': m.get('name', ''), 'size': int(m.get('size', 0) or 0)}
            for m in r.json().get('models', []) if m.get('name')
        ]

    def is_available(self) -> bool:
        try:
            self.list_models(); return True
        except Exception:
            return False

    @staticmethod
    def _split_think_stream(text: str, state: dict):
        """Parse modellen die <think>...</think> in content streamen."""
        state['buffer'] = state.get('buffer', '') + text
        out = []
        while state['buffer']:
            if state.get('thinking', False):
                pos = state['buffer'].find('</think>')
                if pos >= 0:
                    if pos: out.append(StreamChunk(thinking=state['buffer'][:pos]))
                    state['buffer'] = state['buffer'][pos+8:]
                    state['thinking'] = False
                    continue
                # hou mogelijk begin van sluit-tag vast
                keep = 0
                for n in range(min(7, len(state['buffer'])), 0, -1):
                    if '</think>'.startswith(state['buffer'][-n:]): keep = n; break
                emit = state['buffer'][:-keep] if keep else state['buffer']
                if emit: out.append(StreamChunk(thinking=emit))
                state['buffer'] = state['buffer'][-keep:] if keep else ''
                break
            else:
                pos = state['buffer'].find('<think>')
                if pos >= 0:
                    if pos: out.append(StreamChunk(content=state['buffer'][:pos]))
                    state['buffer'] = state['buffer'][pos+7:]
                    state['thinking'] = True
                    continue
                keep = 0
                for n in range(min(6, len(state['buffer'])), 0, -1):
                    if '<think>'.startswith(state['buffer'][-n:]): keep = n; break
                emit = state['buffer'][:-keep] if keep else state['buffer']
                if emit: out.append(StreamChunk(content=emit))
                state['buffer'] = state['buffer'][-keep:] if keep else ''
                break
        return out

    def stream_chat(self, model: str, messages: list[dict], **options):
        payload = {'model': model, 'messages': messages, 'stream': True}
        if options:
            payload['options'] = {k: v for k, v in options.items() if v is not None}
        state = {'buffer': '', 'thinking': False}
        with requests.post(f'{self.base_url}/api/chat', json=payload, stream=True, timeout=(5, 900)) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line: continue
                data = json.loads(line)
                message = data.get('message') or {}
                thought = message.get('thinking') or ''
                if thought:
                    yield StreamChunk(thinking=thought)
                content = message.get('content') or ''
                if content:
                    yield from self._split_think_stream(content, state)
                if data.get('done'): break
        # restbuffer veilig legen
        if state.get('buffer'):
            if state.get('thinking'): yield StreamChunk(thinking=state['buffer'])
            else: yield StreamChunk(content=state['buffer'])

    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        r = requests.post(f'{self.base_url}/api/embed', json={'model': model, 'input': texts}, timeout=(5, 900))
        r.raise_for_status()
        data = r.json()
        return data.get('embeddings') or []
