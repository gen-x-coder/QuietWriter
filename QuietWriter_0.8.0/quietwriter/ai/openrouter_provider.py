from __future__ import annotations
import json
import requests
from .providers import AIProvider, StreamChunk


class OpenRouterProvider(AIProvider):
    """OpenRouter-provider. De UI kan hem nu al gebruiken zodra een API-key is ingevuld."""
    name = 'openrouter'

    def __init__(self, api_key: str, base_url='https://openrouter.ai/api/v1'):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip('/')

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

    def is_available(self) -> bool:
        if not self.api_key: return False
        try:
            self.list_models(); return True
        except Exception:
            return False

    def list_models(self) -> list[dict]:
        if not self.api_key: return []
        r = requests.get(f'{self.base_url}/models', headers=self.headers, timeout=8)
        r.raise_for_status()
        rows = r.json().get('data', [])
        return [{'name': x.get('id',''), 'size': 0} for x in rows if x.get('id')]

    def stream_chat(self, model: str, messages: list[dict], **options):
        payload = {'model': model, 'messages': messages, 'stream': True}
        payload.update({k:v for k,v in options.items() if v is not None})
        with requests.post(f'{self.base_url}/chat/completions', headers=self.headers, json=payload, stream=True, timeout=(10, 900)) as r:
            r.raise_for_status()
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                line = raw.strip()
                if line.startswith('data:'): line = line[5:].strip()
                if line == '[DONE]': break
                try: data = json.loads(line)
                except Exception: continue
                delta = (((data.get('choices') or [{}])[0]).get('delta') or {})
                reasoning = delta.get('reasoning') or delta.get('reasoning_content') or ''
                content = delta.get('content') or ''
                if reasoning: yield StreamChunk(thinking=reasoning)
                if content: yield StreamChunk(content=content)
