from __future__ import annotations
import json
import threading
from urllib.parse import urlsplit
from decimal import Decimal, InvalidOperation
import requests
from .providers import AIProvider, StreamChunk


class OpenRouterProvider(AIProvider):
    """OpenRouter-provider. De AI-functies blijven provider-onafhankelijk."""
    name = 'openrouter'

    def __init__(self, api_key: str, base_url='https://openrouter.ai/api/v1'):
        self.api_key = api_key.strip()
        self.base_url = self._validated_base_url(base_url)
        self._response_lock = threading.Lock()
        self._active_response = None
        self._cancelled = False

    @staticmethod
    def _validated_base_url(base_url: str) -> str:
        """Never send an OpenRouter bearer token to a substituted endpoint."""
        candidate = str(base_url or '').strip().rstrip('/')
        parsed = urlsplit(candidate)
        if (parsed.scheme.lower() != 'https' or parsed.hostname != 'openrouter.ai'
                or parsed.port not in (None, 443) or parsed.username is not None
                or parsed.password is not None or parsed.path != '/api/v1'
                or parsed.query or parsed.fragment):
            raise ValueError('Ongeldig OpenRouter-adres: alleen https://openrouter.ai/api/v1 is toegestaan.')
        return 'https://openrouter.ai/api/v1'

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

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
            try: response.close()
            except Exception: pass

    def is_available(self) -> bool:
        if not self.api_key: return False
        try:
            self.list_models(); return True
        except Exception:
            return False


    @staticmethod
    def _error_detail(r) -> str:
        try:
            data = r.json()
            if isinstance(data, dict):
                error = data.get('error')
                if isinstance(error, dict):
                    detail = error.get('message') or error.get('code')
                    if detail:
                        return str(detail)
                elif error:
                    return str(error)
                detail = data.get('message')
                if detail:
                    return str(detail)
        except Exception:
            pass
        text = (getattr(r, 'text', '') or '').strip()
        return text[:500] if text else f'HTTP {r.status_code}'

    @classmethod
    def _raise_detailed(cls, r, prefix='OpenRouter'):
        if r.ok:
            return
        raise RuntimeError(f'{prefix}: {cls._error_detail(r)}')

    @staticmethod
    def _supports_reasoning(row: dict) -> bool:
        supported = row.get('supported_parameters') or []
        if isinstance(supported, dict):
            supported = supported.keys()
        names = {str(value) for value in supported}
        return 'reasoning' in names


    @staticmethod
    def _is_free_model(row: dict) -> bool:
        model_id = str(row.get('id') or '')
        if model_id == 'openrouter/free' or model_id.endswith(':free'):
            return True
        pricing = row.get('pricing') or {}
        prompt = pricing.get('prompt')
        completion = pricing.get('completion')
        if prompt is None or completion is None:
            return False
        try:
            return Decimal(str(prompt)) == 0 and Decimal(str(completion)) == 0
        except (InvalidOperation, ValueError, TypeError):
            return False

    def list_models(self) -> list[dict]:
        if not self.api_key: return []
        r = requests.get(f'{self.base_url}/models', headers=self.headers, timeout=8)
        self._raise_detailed(r, 'OpenRouter modellen ophalen mislukt')
        rows = r.json().get('data', [])
        return [
            {
                'name': x.get('id', ''),
                'description': x.get('description') or '',
                'output_modalities': (x.get('architecture') or {}).get('output_modalities'),
                'size': 0,
                # Parameter support does not imply an endpoint permits disabling reasoning.
                'thinking_supported': self._supports_reasoning(x),
                'thinking_can_disable': self._supports_reasoning(x),
                'thinking_values': [],
                'thinking_default': None,
                'free': self._is_free_model(x),
                'prompt_price': (x.get('pricing') or {}).get('prompt'),
                'completion_price': (x.get('pricing') or {}).get('completion'),
            }
            for x in rows if x.get('id')
        ]

    def stream_chat(self, model: str, messages: list[dict], **options):
        payload = {'model': model, 'messages': messages, 'stream': True}
        payload.update({k:v for k,v in options.items() if v is not None})
        self._begin_request()
        r = requests.post(f'{self.base_url}/chat/completions', headers=self.headers, json=payload, stream=True, timeout=(10, 45))
        self._set_active(r)
        try:
            # A cancellation can happen while requests.post() waits for the
            # first response headers. Preserve it when the response arrives.
            if self._is_cancelled():
                return
            self._raise_detailed(r, 'OpenRouter aanvraag mislukt')
            # OpenRouter streams Server-Sent Events as UTF-8. Requests may
            # otherwise decode text/event-stream as Latin-1 when the response
            # omits an explicit charset, producing mojibake such as scÃ¨ne.
            completed = False
            for raw in r.iter_lines(decode_unicode=False):
                if self._is_cancelled():
                    break
                if not raw:
                    continue
                if isinstance(raw, bytes):
                    line = raw.decode('utf-8', errors='replace').strip()
                else:
                    # Keep compatibility with mocked/test responses that yield
                    # text directly; real requests responses yield bytes here.
                    line = str(raw).strip()
                if line.startswith('data:'):
                    line = line[5:].strip()
                if line == '[DONE]':
                    completed = True
                    break
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                if not isinstance(data, dict):
                    continue
                error = data.get('error')
                if error:
                    if isinstance(error, dict):
                        detail = error.get('message') or error.get('code') or str(error)
                    else:
                        detail = error
                    raise RuntimeError(f'OpenRouter stream mislukt: {detail}')
                actual_model = data.get('model') if isinstance(data, dict) else None
                if isinstance(actual_model, str) and actual_model.strip():
                    yield StreamChunk(model=actual_model.strip())
                choices = data.get('choices') or []
                if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                    continue
                if choices[0].get('finish_reason'):
                    completed = True
                delta = choices[0].get('delta') or {}
                if not isinstance(delta, dict):
                    continue
                reasoning = delta.get('reasoning') or delta.get('reasoning_content') or ''
                content = delta.get('content') or ''
                if reasoning:
                    yield StreamChunk(thinking=reasoning)
                if content:
                    yield StreamChunk(content=content)
            if not self._is_cancelled() and not completed:
                raise RuntimeError('OpenRouter stream onderbroken: het antwoord is mogelijk onvolledig ontvangen.')
        finally:
            try:
                r.close()
            except Exception:
                pass
            self._clear_active(r)
