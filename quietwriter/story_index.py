from __future__ import annotations
import re
import sqlite3
from pathlib import Path

FIELDS = {'title', 'description', 'synopsis', 'tags'}


def parse_story(path: Path) -> dict:
    text = path.read_text(encoding='utf-8', errors='replace')
    meta = {'title': path.stem, 'description': '', 'synopsis': '', 'tags': ''}
    body_start = 0
    lines = text.splitlines()

    # Ondersteunt zowel eenvoudige key: value headers als YAML front matter.
    in_yaml = bool(lines and lines[0].strip() == '---')
    start = 1 if in_yaml else 0
    for i in range(start, min(len(lines), 80)):
        line = lines[i]
        if in_yaml and line.strip() == '---':
            body_start = i + 1
            break
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if not m:
            if not in_yaml and i > 0 and line.strip():
                body_start = i
                break
            continue
        key, value = m.group(1).lower(), m.group(2).strip()
        if key in FIELDS:
            meta[key] = value
        body_start = i + 1
    body = '\n'.join(lines[body_start:]).strip()
    meta['body'] = body
    meta['path'] = str(path)
    return meta


class StoryIndex:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS stories(
            path TEXT PRIMARY KEY, title TEXT, description TEXT, synopsis TEXT, tags TEXT,
            body TEXT, mtime REAL
        )''')
        self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS stories_fts USING fts5(path UNINDEXED, title, description, synopsis, tags, body)")
        self.conn.commit()

    def rebuild(self, stories_dir: Path):
        self.conn.execute('DELETE FROM stories')
        self.conn.execute('DELETE FROM stories_fts')
        for path in sorted(Path(stories_dir).rglob('*.md')):
            d = parse_story(path)
            self.conn.execute('INSERT OR REPLACE INTO stories VALUES(?,?,?,?,?,?,?)',
                              (d['path'], d['title'], d['description'], d['synopsis'], d['tags'], d['body'], path.stat().st_mtime))
            self.conn.execute('INSERT INTO stories_fts(path,title,description,synopsis,tags,body) VALUES(?,?,?,?,?,?)',
                              (d['path'], d['title'], d['description'], d['synopsis'], d['tags'], d['body']))
        self.conn.commit()

    def search(self, query: str, limit=8) -> list[dict]:
        if not query.strip():
            return []
        try:
            rows = self.conn.execute('''SELECT s.path,s.title,s.description,s.synopsis,s.tags,
                snippet(stories_fts, 5, '[', ']', ' … ', 18), bm25(stories_fts)
                FROM stories_fts JOIN stories s ON s.path=stories_fts.path
                WHERE stories_fts MATCH ? ORDER BY bm25(stories_fts) LIMIT ?''', (query, limit)).fetchall()
        except sqlite3.OperationalError:
            q = f"%{query}%"
            rows = self.conn.execute('''SELECT path,title,description,synopsis,tags,substr(body,1,240),0
                FROM stories WHERE title LIKE ? OR description LIKE ? OR synopsis LIKE ? OR tags LIKE ? OR body LIKE ? LIMIT ?''',
                                     (q, q, q, q, q, limit)).fetchall()
        return [dict(path=r[0], title=r[1], description=r[2], synopsis=r[3], tags=r[4], snippet=r[5], score=r[6]) for r in rows]

    def compact_catalog(self, limit=500) -> str:
        rows = self.conn.execute('SELECT title,tags,synopsis,path FROM stories ORDER BY title LIMIT ?', (limit,)).fetchall()
        out = []
        for i, (title, tags, synopsis, path) in enumerate(rows, 1):
            out.append(f'{i}. {title}\nTags: {tags}\nSynopsis: {synopsis}\nBestand: {path}')
        return '\n\n'.join(out)
