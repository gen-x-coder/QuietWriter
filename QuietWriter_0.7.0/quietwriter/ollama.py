from __future__ import annotations
import json
import requests
from PySide6.QtCore import QThread, Signal


class OllamaClient:
    def __init__(self, base_url='http://127.0.0.1:11434'):
        self.base_url = base_url.rstrip('/')

    def model_info(self, timeout=2.0) -> list[dict]:
        r = requests.get(f'{self.base_url}/api/tags', timeout=timeout)
        r.raise_for_status()
        return [
            {'name': m.get('name', ''), 'size': int(m.get('size', 0) or 0)}
            for m in r.json().get('models', []) if m.get('name')
        ]

    def models(self, timeout=2.0) -> list[str]:
        return [m['name'] for m in self.model_info(timeout)]

    def is_available(self) -> bool:
        try:
            self.models(timeout=1.5)
            return True
        except Exception:
            return False


class ChatWorker(QThread):
    token = Signal(str)
    thinking = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, base_url: str, model: str, messages: list[dict]):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.messages = messages
        self._stop = False
        self._in_think = False
        self._parse_buffer = ''

    def stop(self):
        self._stop = True

    @staticmethod
    def _prefix_suffix(text: str, tag: str) -> int:
        max_len = min(len(text), len(tag) - 1)
        for n in range(max_len, 0, -1):
            if tag.startswith(text[-n:]):
                return n
        return 0

    def _emit_content(self, part: str, final=False):
        self._parse_buffer += part
        while self._parse_buffer:
            if self._in_think:
                tag = '</think>'
                pos = self._parse_buffer.find(tag)
                if pos >= 0:
                    if pos:
                        self.thinking.emit(self._parse_buffer[:pos])
                    self._parse_buffer = self._parse_buffer[pos + len(tag):]
                    self._in_think = False
                    continue
                keep = 0 if final else self._prefix_suffix(self._parse_buffer, tag)
                emit = self._parse_buffer[:-keep] if keep else self._parse_buffer
                if emit:
                    self.thinking.emit(emit)
                self._parse_buffer = self._parse_buffer[-keep:] if keep else ''
                break
            else:
                tag = '<think>'
                pos = self._parse_buffer.find(tag)
                if pos >= 0:
                    if pos:
                        self.token.emit(self._parse_buffer[:pos])
                    self._parse_buffer = self._parse_buffer[pos + len(tag):]
                    self._in_think = True
                    continue
                keep = 0 if final else self._prefix_suffix(self._parse_buffer, tag)
                emit = self._parse_buffer[:-keep] if keep else self._parse_buffer
                if emit:
                    self.token.emit(emit)
                self._parse_buffer = self._parse_buffer[-keep:] if keep else ''
                break

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
                    message = data.get('message', {})
                    thought = message.get('thinking', '') or ''
                    if thought:
                        self.thinking.emit(thought)
                    part = message.get('content', '') or ''
                    if part:
                        self._emit_content(part)
                    if data.get('done'):
                        break
            self._emit_content('', final=True)
            self.finished_ok.emit()
        except Exception as e:
            self.failed.emit(str(e))
