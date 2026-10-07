from __future__ import annotations

import sqlite3
from pathlib import Path

from .manuscript_text import text_for_search


class BookSearchIndex:
    """Disposable FTS cache for manuscript search.

    The index lives in the workspace for backward compatibility, but it is never
    authoritative data. Corruption, sync conflicts or an unwritable cache must
    therefore never block QuietWriter startup or manuscript saves.
    """

    _CREATE_SQL = (
        'CREATE VIRTUAL TABLE IF NOT EXISTS chapters USING '
        'fts5(book_id UNINDEXED, chapter_id UNINDEXED, title, body)'
    )

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None
        self._memory_only = False
        self._open_with_recovery()

    def _disk_header_looks_valid(self) -> bool:
        if not self.db_path.exists() or self.db_path.stat().st_size == 0:
            return True
        try:
            with self.db_path.open('rb') as handle:
                return handle.read(16) == b'SQLite format 3\x00'
        except OSError:
            return False

    def _connect_disk(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._disk_header_looks_valid():
            raise sqlite3.DatabaseError('invalid SQLite cache header')
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(self._CREATE_SQL)
            conn.commit()
            return conn
        except Exception:
            conn.close()
            raise

    def _discard_disk_cache(self):
        for candidate in (
            self.db_path,
            Path(str(self.db_path) + '-wal'),
            Path(str(self.db_path) + '-shm'),
        ):
            try:
                candidate.unlink(missing_ok=True)
            except OSError:
                pass

    def _open_memory(self):
        self._memory_only = True
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute(self._CREATE_SQL)
        self.conn.commit()

    def _open_with_recovery(self):
        self.close()
        self._memory_only = False
        try:
            self.conn = self._connect_disk()
            return
        except (sqlite3.Error, OSError):
            self.close()
            self._discard_disk_cache()
        try:
            self.conn = self._connect_disk()
        except (sqlite3.Error, OSError):
            self.close()
            self._open_memory()

    def close(self):
        conn = getattr(self, 'conn', None)
        if conn is not None:
            try:
                conn.close()
            except sqlite3.Error:
                pass
        self.conn = None

    def _rebuild_once(self, book):
        if self.conn is None:
            raise sqlite3.ProgrammingError('search cache is closed')
        self.conn.execute('DELETE FROM chapters WHERE book_id=?', (book.id,))
        for section in book.sections:
            for chapter in section.chapters:
                p = book.path / chapter.file
                try:
                    raw = p.read_text(encoding='utf-8', errors='replace') if p.exists() else ''
                except OSError:
                    raw = ''
                body = text_for_search(raw)
                self.conn.execute(
                    'INSERT INTO chapters(book_id,chapter_id,title,body) VALUES(?,?,?,?)',
                    (book.id, chapter.id, chapter.title, body),
                )
        self.conn.commit()

    def rebuild_book(self, book):
        try:
            self._rebuild_once(book)
            return True
        except (sqlite3.Error, OSError):
            # A cache failure after startup is equally non-authoritative. Reopen
            # from a clean database and retry once; if even that fails, leave
            # search degraded rather than propagating through an editor save.
            try:
                self._open_with_recovery()
                self._rebuild_once(book)
                return True
            except (sqlite3.Error, OSError):
                return False

    def search(self, book_id: str, query: str, limit=50):
        if not query.strip() or self.conn is None:
            return []
        try:
            return self.conn.execute(
                """SELECT chapter_id,title,snippet(chapters,3,'[',']',' … ',16)
                FROM chapters WHERE book_id=? AND chapters MATCH ? LIMIT ?""",
                (book_id, query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            try:
                q = f'%{query}%'
                return self.conn.execute(
                    'SELECT chapter_id,title,substr(body,1,180) FROM chapters '
                    'WHERE book_id=? AND (title LIKE ? OR body LIKE ?) LIMIT ?',
                    (book_id, q, q, limit),
                ).fetchall()
            except sqlite3.Error:
                return []
        except sqlite3.DatabaseError:
            self._open_with_recovery()
            return []
