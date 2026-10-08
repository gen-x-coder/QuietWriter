from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QStandardPaths


class WritingProgressStore:
    """Local, optional writing-activity history for one QuietWriter workspace.

    This is intentionally cache-like supporting data rather than manuscript data:
    it lives outside the workspace, may be missing/corrupt without affecting a book,
    and is never required to open or save a manuscript.
    """

    SCHEMA_VERSION = 1
    RETENTION_DAYS = 60

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.path = self._path_for_workspace()
        self._data = self._load()

    def _path_for_workspace(self) -> Path:
        local_root = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
        base = Path(local_root) if local_root else (Path.home() / '.quietwriter')
        try:
            workspace = str(self.workspace.resolve())
        except OSError:
            workspace = str(self.workspace.absolute())
        workspace_hash = hashlib.sha256(workspace.encode('utf-8')).hexdigest()[:20]
        return base / 'progress' / f'writing-progress-{workspace_hash}.json'

    def _load(self) -> dict:
        try:
            raw = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError, TypeError):
            return {'schema_version': self.SCHEMA_VERSION, 'books': {}}
        if not isinstance(raw, dict) or raw.get('schema_version') != self.SCHEMA_VERSION:
            return {'schema_version': self.SCHEMA_VERSION, 'books': {}}
        books = raw.get('books')
        if not isinstance(books, dict):
            books = {}
        clean = {}
        for book_id, days in books.items():
            if not isinstance(book_id, str) or not isinstance(days, dict):
                continue
            valid_days = {
                day: value for day, value in days.items()
                if isinstance(day, str) and isinstance(value, int) and value >= 0
            }
            if valid_days:
                clean[book_id] = valid_days
        return {'schema_version': self.SCHEMA_VERSION, 'books': clean}

    def today(self, book_id: str, *, on_date: date | None = None) -> int:
        day = (on_date or date.today()).isoformat()
        return int(self._data.get('books', {}).get(str(book_id), {}).get(day, 0) or 0)

    def add(self, book_id: str, words: int, *, on_date: date | None = None) -> int:
        amount = max(0, int(words or 0))
        current = self.today(book_id, on_date=on_date)
        if amount <= 0:
            return current
        day_value = on_date or date.today()
        books = self._data.setdefault('books', {})
        days = books.setdefault(str(book_id), {})
        days[day_value.isoformat()] = current + amount
        self._prune_all(day_value)
        self._save()
        return days[day_value.isoformat()]

    def _prune_all(self, today: date) -> None:
        cutoff = today - timedelta(days=self.RETENTION_DAYS - 1)
        books = self._data.setdefault('books', {})
        for book_id, days in list(books.items()):
            for key in list(days):
                try:
                    parsed = date.fromisoformat(key)
                except ValueError:
                    del days[key]
                    continue
                if parsed < cutoff:
                    del days[key]
            if not days:
                del books[book_id]

    def _save(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + '.tmp')
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(self._data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
            tmp.replace(self.path)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
