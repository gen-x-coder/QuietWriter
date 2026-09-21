from __future__ import annotations
import json
import requests
from PySide6.QtCore import QThread, Signal


class OllamaClient:
    def __init__(self, base_url='http://127.0.0.1:11434'):
        self.base_url = base_url.rstrip('/')

    def models(self, timeout=2.0) -> list[str]:
        r = requests.get(f'{self.base_url}/api/tags', timeout=timeout)
        r.raise_for_status()
        return [m['name'] for m in r.json().get('models', [])]

    def is_available(self) -> bool:
        try:
            self.models(timeout=1.5)
            return True
        except Exception:
            return False


class ChatWorker(QThread):
    token = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, base_url: str, model: str, messages: list[dict]):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.messages = messages
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            payload = {'model': self.model, 'messages': self.messages, 'stream': True}
            with requests.post(f'{self.base_url}/api/chat', json=payload, stream=True, timeout=(5, 600)) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if self._stop:
                        return
                    if not line:
                        continue
                    data = json.loads(line)
                    part = data.get('message', {}).get('content', '')
                    if part:
                        self.token.emit(part)
                    if data.get('done'):
                        break
            self.finished_ok.emit()
        except Exception as e:
            self.failed.emit(str(e))
