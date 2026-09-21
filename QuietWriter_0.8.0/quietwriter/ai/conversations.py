from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from ..storage import _safe_atomic_write_text


class ConversationStore:
    def __init__(self, book):
        self.path = Path(book.path) / '.quietwriter' / 'ai_chat.json'

    def load(self) -> list[dict]:
        if not self.path.exists(): return []
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save(self, messages: list[dict]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _safe_atomic_write_text(self.path, json.dumps(messages[-100:], ensure_ascii=False, indent=2))

    @staticmethod
    def entry(role: str, content: str, context=None):
        return {'role': role, 'content': content, 'context': context or {}, 'time': datetime.now().isoformat(timespec='seconds')}
