from __future__ import annotations
import json
import re
import sqlite3
from pathlib import Path

CORE_FIELDS = {'title', 'description', 'synopsis', 'tags', 'date', 'slug', 'meta', 'intro', 'author', 'published'}


def _split_tags(value: str) -> list[str]:
    return [part.strip() for part in value.split(',') if part.strip()]


def split_chapters(body: str, fallback_title: str) -> list[dict]:
    """Splits een oud verhaal op top-level Markdownkoppen (# Titel).

    Alleen één # telt als hoofdstuk. ## en lager blijven onderdeel van het hoofdstuk.
    Tekst vóór de eerste hoofdstukkop blijft als 'Inleiding' beschikbaar.
    """
    lines = body.splitlines()
    headings = []
    for i, line in enumerate(lines):
        m = re.match(r'^#\s+(.+?)\s*$', line)
        if m:
            headings.append((i, m.group(1).strip()))
    if not headings:
        return [{'title': fallback_title, 'text': body.strip()}]

    chapters = []
    first_line = headings[0][0]
    preface = '\n'.join(lines[:first_line]).strip()
    if preface:
        chapters.append({'title': 'Inleiding', 'text': preface})

    for idx, (line_no, title) in enumerate(headings):
        end = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
        chapter_text = '\n'.join(lines[line_no + 1:end]).strip()
        chapters.append({'title': title, 'text': chapter_text})
    return chapters


def parse_story(path: Path) -> dict:
    text = path.read_text(encoding='utf-8', errors='replace')
    meta = {'title': path.stem, 'description': '', 'synopsis': '', 'tags': ''}
    extra = {}
    body_start = 0
    lines = text.splitlines()

    in_yaml = bool(lines and lines[0].strip() == '---')
    start = 1 if in_yaml else 0
    for i in range(start, min(len(lines), 120)):
        line = lines[i]
        if line.strip() == '---':
            body_start = i + 1
            break
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if not m:
            if not in_yaml and i > 0 and line.strip():
                body_start = i
                break
            continue
        key, value = m.group(1).lower(), m.group(2).strip()
        if key in CORE_FIELDS:
            if key in meta:
                meta[key] = value
            else:
                extra[key] = value
        else:
            extra[key] = value
        body_start = i + 1

    if not meta.get('synopsis'):
        meta['synopsis'] = extra.get('intro') or extra.get('meta') or ''
    body = '\n'.join(lines[body_start:]).strip()
    chapters = split_chapters(body, meta['title'])
    meta['body'] = body
    meta['path'] = str(path)
    meta['tags_list'] = _split_tags(meta.get('tags', ''))
    meta['extra'] = extra
    meta['chapters'] = chapters
    return meta


class StoryIndex:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS stories(
            path TEXT PRIMARY KEY, title TEXT, description TEXT, synopsis TEXT, tags TEXT,
            body TEXT, metadata TEXT, mtime REAL
        )''')
        columns = {row[1] for row in self.conn.execute('PRAGMA table_info(stories)')}
        if 'metadata' not in columns:
            self.conn.execute("ALTER TABLE stories ADD COLUMN metadata TEXT DEFAULT '{}' ")
        self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS stories_fts USING fts5(path UNINDEXED, title, description, synopsis, tags, body)")
        self.conn.commit()

    def rebuild(self, stories_dir: Path):
        self.conn.execute('DELETE FROM stories')
        self.conn.execute('DELETE FROM stories_fts')
        for path in sorted(Path(stories_dir).rglob('*.md')):
            d = parse_story(path)
            metadata = {k: v for k, v in d.items() if k not in {'body', 'chapters', 'path', 'tags_list', 'title', 'description', 'synopsis', 'tags'}}
            self.conn.execute('''INSERT OR REPLACE INTO stories(path,title,description,synopsis,tags,body,metadata,mtime)
                                 VALUES(?,?,?,?,?,?,?,?)''',
                              (d['path'], d['title'], d['description'], d['synopsis'], d['tags'], d['body'],
                               json.dumps(metadata, ensure_ascii=False), path.stat().st_mtime))
            self.conn.execute('INSERT INTO stories_fts(path,title,description,synopsis,tags,body) VALUES(?,?,?,?,?,?)',
                              (d['path'], d['title'], d['description'], d['synopsis'], d['tags'], d['body']))
        self.conn.commit()

    def list_all(self) -> list[dict]:
        rows = self.conn.execute('SELECT path,title,description,synopsis,tags,mtime FROM stories ORDER BY title COLLATE NOCASE').fetchall()
        return [dict(path=r[0], title=r[1], description=r[2], synopsis=r[3], tags=r[4], mtime=r[5]) for r in rows]

    def get(self, path: str | Path) -> dict:
        return parse_story(Path(path))

    def search(self, query: str, limit=8) -> list[dict]:
        if not query.strip():
            return self.list_all()[:limit]
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
