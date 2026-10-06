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


    def _begin_request(self):
        with self._response_lock:
            self._active_response = None
            self._cancelled = False

    def _set_active(self, response):
        with self._response_lock:
            self._active_response = response

    def _is_cancelled(self) -> bool:
        with self._response_lock:
            return self._cancelled

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

    @staticmethod
    def _thinking_capability(show_data: dict) -> dict:
        """Normalize Ollama /api/show thinking metadata for the UI.

        A brain marker means QuietWriter can explicitly request think=false.
        `values: [false]` is Ollama's documented "no thinking support" case,
        so it deliberately does not receive the marker.
        """
        if not isinstance(show_data, dict):
            show_data = {}
        thinking = show_data.get('thinking')
        if isinstance(thinking, dict):
            values = list(thinking.get('values') or [])
            has_thinking_mode = any(value is not False for value in values)
            return {
                'thinking_supported': bool(has_thinking_mode),
                'thinking_can_disable': bool(has_thinking_mode and any(value is False for value in values)),
                'thinking_control_known': True,
                'thinking_values': values,
                'thinking_default': thinking.get('default'),
            }

        # Older/current Ollama builds and some model manifests expose only the
        # generic capability list (the same information printed by
        # `ollama show`).  That is enough to know the model can think, but not
        # enough to prove that this exact model variant honours think=false.
        capabilities = show_data.get('capabilities') or []
        has_capability = any(str(value).strip().lower() == 'thinking' for value in capabilities)
        if has_capability:
            return {
                'thinking_supported': True,
                'thinking_can_disable': None,
                'thinking_control_known': False,
                'thinking_values': [],
                'thinking_default': None,
            }
        return {
            'thinking_supported': None,
            'thinking_can_disable': None,
            'thinking_control_known': False,
            'thinking_values': [],
            'thinking_default': None,
        }

    def _show_model(self, model: str, timeout: float) -> dict:
        r = requests.post(f'{self.base_url}/api/show', json={'model': model}, timeout=timeout)
        self._raise_detailed(r, f'Ollama modelinformatie ophalen mislukt voor {model}')
        data = r.json()
        return data if isinstance(data, dict) else {}

    def list_models(self, timeout: float = 2.5, include_capabilities: bool = True) -> list[dict]:
        r = requests.get(f'{self.base_url}/api/tags', timeout=timeout)
        self._raise_detailed(r, 'Ollama modellen ophalen mislukt')
        models = []
        for row in r.json().get('models', []):
            name = row.get('name', '')
            if not name:
                continue
            info = {'name': name, 'size': int(row.get('size', 0) or 0)}
            if include_capabilities:
                try:
                    info.update(self._thinking_capability(self._show_model(name, timeout)))
                except Exception:
                    # Capability discovery is informative. A single model with
                    # incomplete/older metadata must not make model refresh fail.
                    info.update(self._thinking_capability({}))
            models.append(info)
        return models


    def is_available(self) -> bool:
        try:
            self.list_models(include_capabilities=False); return True
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
        # Ollama's native /api/chat expects `think` at the top level, not
        # inside the generic model `options` object. Omitting it keeps the
        # model's own default; False explicitly requests non-thinking mode.
        think = options.pop('think', None)
        if think is not None:
            payload['think'] = bool(think)
        if options:
            payload['options'] = {k: v for k, v in options.items() if v is not None}
        state = {'buffer': '', 'thinking': False}
        self._begin_request()
        r = requests.post(f'{self.base_url}/api/chat', json=payload, stream=True, timeout=(5, 900))
        self._set_active(r)
        try:
            # Stop may have been pressed while requests.post() was still waiting
            # for response headers/model startup. Never clear that cancellation
            # merely because the response object became available afterwards.
            if self._is_cancelled():
                return
            self._raise_detailed(r, f'Ollama chat mislukt voor model {model}')
            for line in r.iter_lines(decode_unicode=True):
                if self._is_cancelled():
                    break
                if not line:
                    continue
                data = json.loads(line)
                error = data.get('error') if isinstance(data, dict) else None
                if error:
                    detail = error.get('message') if isinstance(error, dict) else error
                    raise RuntimeError(f'Ollama stream mislukt: {detail}')
                message = data.get('message') or {}
                thought = message.get('thinking') or ''
                if thought:
                    yield StreamChunk(thinking=thought)
                content = message.get('content') or ''
                if content:
                    yield from self._split_think_stream(content, state)
                if data.get('done'):
                    break
        finally:
            try:
                r.close()
            except Exception:
                pass
            self._clear_active(r)
        if not self._is_cancelled() and state.get('buffer'):
            if state.get('thinking'):
                yield StreamChunk(thinking=state['buffer'])
            else:
                yield StreamChunk(content=state['buffer'])

