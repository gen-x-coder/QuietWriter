from __future__ import annotations
import json
import threading
import requests
from .providers import AIProvider, StreamChunk


class OllamaProvider(AIProvider):
    name = 'ollama'

    def __init__(self, base_url='http://127.0.0.1:11434'):
        self.base_url = base_url.rstrip('/')
        self._response_lock = threading.Lock()
        self._active_response = None
        self._cancelled = False


    def _set_active(self, response):
        with self._response_lock:
            self._active_response = response
            self._cancelled = False

    def _clear_active(self, response=None):
        with self._response_lock:
            if response is None or self._active_response is response:
                self._active_response = None

    def cancel_active(self) -> None:
        with self._response_lock:
            self._cancelled = True
            response = self._active_response
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

    @staticmethod
    def _error_detail(r) -> str:
        try:
            data = r.json()
            detail = data.get('error') if isinstance(data, dict) else None
            if detail:
                return str(detail)
        except Exception:
            pass
        text = (getattr(r, 'text', '') or '').strip()
        return text[:500] if text else f'HTTP {r.status_code}'

    @classmethod
    def _raise_detailed(cls, r, prefix='Ollama'):
        if r.ok:
            return
        raise RuntimeError(f'{prefix}: {cls._error_detail(r)}')

    def list_models(self, timeout: float = 2.5) -> list[dict]:
        r = requests.get(f'{self.base_url}/api/tags', timeout=timeout)
        self._raise_detailed(r, 'Ollama modellen ophalen mislukt')
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
        r = requests.post(f'{self.base_url}/api/chat', json=payload, stream=True, timeout=(5, 900))
        self._set_active(r)
        try:
            self._raise_detailed(r, f'Ollama chat mislukt voor model {model}')
            for line in r.iter_lines(decode_unicode=True):
                if self._cancelled:
                    break
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
        finally:
            try: r.close()
            except Exception: pass
            self._clear_active(r)
        if not self._cancelled and state.get('buffer'):
            if state.get('thinking'): yield StreamChunk(thinking=state['buffer'])
            else: yield StreamChunk(content=state['buffer'])

