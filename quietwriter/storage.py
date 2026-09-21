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
    metadata: dict = field(default_factory=dict)

    @property
    def manifest_path(self) -> Path:
        return self.path / 'book.json'

    @property
    def slug(self) -> str:
        return (self.metadata.get('slug') or slugify(self.title)).strip()


class Library:
    COVER_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

    def __init__(self, root: Path):
        self.root = Path(root)
        self.books_dir = self.root / 'books'
        self.stories_dir = self.root / 'stories'
        self.covers_dir = self.root / 'boekomslagen'
        self.archive_dir = self.root / 'archive'
        self.persona_dir = self.root / 'persona'
        self.dict_dir = self.root / 'dictionaries'
        self.cache_dir = self.root / '.cache'
        for d in [self.books_dir, self.stories_dir, self.covers_dir, self.archive_dir,
                  self.persona_dir, self.dict_dir, self.cache_dir]:
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
        clean_title = title.strip() or 'Naamloos boek'
        folder = self.books_dir / f'{slugify(clean_title)}-{book_id[:8]}'
        (folder / 'chapters').mkdir(parents=True, exist_ok=True)
        book = Book(
            id=book_id,
            title=clean_title,
            path=folder,
            metadata={
                'slug': slugify(clean_title),
                'description': '',
                'meta': '',
                'intro': '',
                'tags': '',
                'author': '',
                'cover_file': '',
            },
        )
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
        metadata = dict(data.get('metadata') or {})
        metadata.setdefault('slug', slugify(data.get('title', 'boek')))
        metadata.setdefault('description', '')
        metadata.setdefault('meta', '')
        metadata.setdefault('intro', '')
        metadata.setdefault('tags', '')
        metadata.setdefault('author', '')
        metadata.setdefault('cover_file', '')
        return Book(id=data['id'], title=data['title'], path=Path(folder), sections=sections, metadata=metadata)

    def save_manifest(self, book: Book):
        book.metadata.setdefault('slug', slugify(book.title))
        data = {
            'format': 2,
            'id': book.id,
            'title': book.title,
            'metadata': book.metadata,
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

    def delete_book(self, book: Book):
        """Verwijder een boek na bevestiging in de UI."""
        if book.path.exists():
            shutil.rmtree(book.path)

    def cover_path(self, book: Book) -> Path | None:
        stored = (book.metadata.get('cover_file') or '').strip()
        if stored:
            p = self.covers_dir / stored
            if p.exists():
                return p
        slug = book.slug
        for ext in self.COVER_EXTENSIONS:
            p = self.covers_dir / f'{slug}{ext}'
            if p.exists():
                return p
        return None

    def default_cover_path(self) -> Path | None:
        for name in ('default-cover', 'standaard-omslag', 'standaard'):
            for ext in self.COVER_EXTENSIONS:
                p = self.covers_dir / f'{name}{ext}'
                if p.exists():
                    return p
        return None

    def set_cover(self, book: Book, source: Path) -> Path:
        source = Path(source)
        ext = source.suffix.lower()
        if ext not in self.COVER_EXTENSIONS:
            raise ValueError('Ondersteunde formaten: JPG, JPEG, PNG en WEBP.')
        target = self.covers_dir / f'{book.slug}{ext}'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        # Ruim een eerdere omslag met dezelfde slug maar andere extensie op.
        for other_ext in self.COVER_EXTENSIONS:
            other = self.covers_dir / f'{book.slug}{other_ext}'
            if other != target and other.exists():
                try:
                    other.unlink()
                except OSError:
                    pass
        book.metadata['cover_file'] = target.name
        self.save_manifest(book)
        return target

    def rename_cover_for_slug(self, book: Book, old_slug: str, new_slug: str):
        p = self.cover_path(book)
        if not p or old_slug == new_slug:
            return
        target = self.covers_dir / f'{new_slug}{p.suffix.lower()}'
        if target != p:
            p.replace(target)
        book.metadata['cover_file'] = target.name

    def persona_path(self) -> Path:
        return self.persona_dir / 'schrijver.md'

    def read_persona(self) -> str:
        return self.persona_path().read_text(encoding='utf-8')

    def save_persona(self, text: str):
        self.persona_path().write_text(text, encoding='utf-8')
