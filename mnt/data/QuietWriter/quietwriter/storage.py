from __future__ import annotations
import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def slugify(value: str) -> str:
    value = re.sub(r'[^\w\s-]', '', value.strip(), flags=re.UNICODE)
    value = re.sub(r'[-\s]+', '-', value).strip('-').lower()
    return value or 'boek'


@dataclass
class Chapter:
    id: str
    title: str
    file: str


@dataclass
class Section:
    id: str
    title: str
    chapters: list[Chapter] = field(default_factory=list)


@dataclass
class Book:
    id: str
    title: str
    path: Path
    sections: list[Section] = field(default_factory=list)

    @property
    def manifest_path(self) -> Path:
        return self.path / 'book.json'


class Library:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.books_dir = self.root / 'books'
        self.stories_dir = self.root / 'stories'
        self.archive_dir = self.root / 'archive'
        self.persona_dir = self.root / 'persona'
        self.dict_dir = self.root / 'dictionaries'
        self.cache_dir = self.root / '.cache'
        for d in [self.books_dir, self.stories_dir, self.archive_dir, self.persona_dir, self.dict_dir, self.cache_dir]:
            d.mkdir(parents=True, exist_ok=True)
        persona = self.persona_dir / 'schrijver.md'
        if not persona.exists():
            persona.write_text('# Schrijversprofiel\n\n## Algemene stijl\n\nBeschrijf hier jouw schrijfstijl.\n', encoding='utf-8')

    def list_books(self) -> list[Book]:
        books = []
        for manifest in self.books_dir.glob('*/book.json'):
            try:
                books.append(self.load_book(manifest.parent))
            except Exception:
                continue
        return sorted(books, key=lambda b: b.manifest_path.stat().st_mtime if b.manifest_path.exists() else 0, reverse=True)

    def create_book(self, title: str) -> Book:
        book_id = str(uuid.uuid4())
        folder = self.books_dir / f'{slugify(title)}-{book_id[:8]}'
        (folder / 'chapters').mkdir(parents=True, exist_ok=True)
        book = Book(id=book_id, title=title.strip() or 'Naamloos boek', path=folder)
        # Start met één hoofdstuk zonder verplichte sectie.
        section = Section(id='root', title='Manuscript')
        chapter = self.add_chapter(book, section, 'Hoofdstuk 1', persist=False)
        section.chapters.append(chapter)
        book.sections.append(section)
        self.save_manifest(book)
        return book

    def load_book(self, folder: Path) -> Book:
        data = json.loads((Path(folder) / 'book.json').read_text(encoding='utf-8'))
        sections = []
        for s in data.get('sections', []):
            chapters = [Chapter(id=c['id'], title=c['title'], file=c['file']) for c in s.get('chapters', [])]
            sections.append(Section(id=s['id'], title=s['title'], chapters=chapters))
        return Book(id=data['id'], title=data['title'], path=Path(folder), sections=sections)

    def save_manifest(self, book: Book):
        data = {
            'format': 1,
            'id': book.id,
            'title': book.title,
            'sections': [
                {'id': s.id, 'title': s.title, 'chapters': [vars(c) for c in s.chapters]}
                for s in book.sections
            ],
        }
        tmp = book.manifest_path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, book.manifest_path)

    def add_section(self, book: Book, title: str) -> Section:
        s = Section(id=str(uuid.uuid4()), title=title.strip() or 'Nieuwe sectie')
        book.sections.append(s)
        self.save_manifest(book)
        return s

    def add_chapter(self, book: Book, section: Section, title: str, persist=True) -> Chapter:
        cid = str(uuid.uuid4())
        rel = f'chapters/{cid}.md'
        chapter = Chapter(id=cid, title=title.strip() or 'Nieuw hoofdstuk', file=rel)
        (book.path / rel).write_text('', encoding='utf-8')
        if persist:
            section.chapters.append(chapter)
            self.save_manifest(book)
        return chapter

    def read_chapter(self, book: Book, chapter: Chapter) -> str:
        p = book.path / chapter.file
        return p.read_text(encoding='utf-8') if p.exists() else ''

    def save_chapter(self, book: Book, chapter: Chapter, text: str):
        self.ensure_daily_archive(book)
        p = book.path / chapter.file
        tmp = p.with_suffix('.md.tmp')
        tmp.write_text(text, encoding='utf-8')
        os.replace(tmp, p)

    def ensure_daily_archive(self, book: Book):
        files = [p for p in book.path.rglob('*') if p.is_file()]
        if not files:
            return
        newest = max(p.stat().st_mtime for p in files)
        source_day = datetime.fromtimestamp(newest).date()
        today = datetime.now().date()
        if source_day >= today:
            return
        target = self.archive_dir / book.id / source_day.isoformat()
        if target.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(book.path, target)

    def persona_path(self) -> Path:
        return self.persona_dir / 'schrijver.md'

    def read_persona(self) -> str:
        return self.persona_path().read_text(encoding='utf-8')

    def save_persona(self, text: str):
        self.persona_path().write_text(text, encoding='utf-8')
