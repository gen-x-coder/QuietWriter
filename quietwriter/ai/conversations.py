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


class SavedConversationArchive:
    """Explicit, immutable, per-book archives; no automatic chat persistence."""
    def __init__(self, book):
        self.folder = Path(book.path) / '.quietwriter' / 'saved_ai_conversations'

    def list_items(self):
        if not self.folder.is_dir():
            return []
        items = []
        for path in sorted(self.folder.glob('*.json'), reverse=True):
            if path.is_symlink():
                continue
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if isinstance(data, dict) and isinstance(data.get('messages'), list):
                    items.append((path, data))
            except (OSError, ValueError):
                continue
        return items

    def save_explicit(self, messages, title, provider='', model=''):
        from uuid import uuid4
        if not messages or not any(m.get('role') == 'user' for m in messages):
            raise ValueError('No user conversation to save')
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().isoformat(timespec='seconds')
        data = {'schema': 1, 'title': str(title).strip()[:120] or 'Meelezer',
                'saved_at': stamp, 'provider': str(provider), 'model': str(model),
                'messages': json.loads(json.dumps(messages, ensure_ascii=False))}
        path = self.folder / (datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid4().hex + '.json')
        _safe_atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2))
        return path

    @staticmethod
    def export_markdown(data):
        title = str(data.get('title', 'Meelezer'))
        rows = [f'# {title}', '', f"Bewaard: {data.get('saved_at', '')}", '']
        for msg in data.get('messages', []):
            role = {'user':'Vraag', 'assistant':'Meelezer', 'notice':'Melding'}.get(msg.get('role'), 'Bericht')
            selection = (msg.get('context') or {}).get('selected_text')
            rows.extend([f'## {role}', ''])
            if selection:
                rows.extend(['**Geselecteerde passage**', '', '```text', str(selection).replace('```','` ` `'), '```', ''])
            rows.extend([str(msg.get('content','')), ''])
        return '\n'.join(rows).rstrip() + '\n'
