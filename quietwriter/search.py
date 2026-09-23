from __future__ import annotations
import sqlite3

from .media.markup import text_for_search
from pathlib import Path


class BookSearchIndex:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute('CREATE VIRTUAL TABLE IF NOT EXISTS chapters USING fts5(book_id UNINDEXED, chapter_id UNINDEXED, title, body)')
        self.conn.commit()

    def rebuild_book(self, book):
        self.conn.execute('DELETE FROM chapters WHERE book_id=?', (book.id,))
        for section in book.sections:
            for chapter in section.chapters:
                p = book.path / chapter.file
                body = text_for_search(p.read_text(encoding='utf-8', errors='replace')) if p.exists() else ''
                self.conn.execute('INSERT INTO chapters(book_id,chapter_id,title,body) VALUES(?,?,?,?)', (book.id, chapter.id, chapter.title, body))
        self.conn.commit()

    def search(self, book_id: str, query: str, limit=50):
        if not query.strip():
            return []
        try:
            return self.conn.execute('''SELECT chapter_id,title,snippet(chapters,3,'[',']',' … ',16)
                FROM chapters WHERE book_id=? AND chapters MATCH ? LIMIT ?''', (book_id, query, limit)).fetchall()
        except sqlite3.OperationalError:
            q = f'%{query}%'
            return self.conn.execute('SELECT chapter_id,title,substr(body,1,180) FROM chapters WHERE book_id=? AND (title LIKE ? OR body LIKE ?) LIMIT ?', (book_id, q, q, limit)).fetchall()
