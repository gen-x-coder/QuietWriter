from __future__ import annotations
import json
import os
import re
import shutil
import uuid
import time
import tempfile
import copy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def _safe_atomic_write_text(path: Path, text: str, encoding: str = 'utf-8', replace_retries: int = 8):
    """Write text robustly on Windows/Dropbox.

    First writes to a unique sibling temp file and retries os.replace for transient
    sharing violations. If Windows keeps denying rename/delete access to the
    destination (common with sync/indexing software), it falls back to a direct
    overwrite with fsync. The temp file is always cleaned up.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, 'w', encoding=encoding, newline='') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        delay = 0.04
        last_exc = None
        for _ in range(max(1, replace_retries)):
            try:
                os.replace(tmp, path)
                return
            except PermissionError as exc:
                last_exc = exc
                time.sleep(delay)
                delay = min(delay * 1.8, 0.45)
        # Some sync tools temporarily disallow replacing/removing the destination
        # while still permitting an ordinary overwrite. Keep this as a controlled
        # fallback after the atomic path has been exhausted.
        for _ in range(5):
            try:
                with path.open('w', encoding=encoding, newline='') as f:
                    f.write(text)
                    f.flush()
                    os.fsync(f.fileno())
                return
            except PermissionError as exc:
                last_exc = exc
                time.sleep(delay)
                delay = min(delay * 1.6, 0.55)
        raise last_exc or PermissionError(f'Kan {path} niet opslaan.')
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


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
        self.trash_dir = self.root / 'trash'
        self.persona_dir = self.root / 'persona'
        self.dict_dir = self.root / 'dictionaries'
        self.cache_dir = self.root / '.cache'
        for d in [self.books_dir, self.stories_dir, self.covers_dir, self.archive_dir, self.trash_dir,
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
        return books

    def book_activity(self, book: Book) -> float:
        try:
            last_used = float(book.metadata.get('last_used', 0) or 0)
        except Exception:
            last_used = 0.0
        mtimes = [last_used]
        if book.manifest_path.exists():
            mtimes.append(book.manifest_path.stat().st_mtime)
        for section in book.sections:
            for chapter in section.chapters:
                p = book.path / chapter.file
                if p.exists():
                    mtimes.append(p.stat().st_mtime)
        return max(mtimes or [0.0])

    def touch_book(self, book: Book):
        book.metadata['last_used'] = datetime.now().timestamp()
        self.save_manifest(book)

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
                'last_used': datetime.now().timestamp(),
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
        metadata.setdefault('last_used', 0)
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
        _safe_atomic_write_text(book.manifest_path, json.dumps(data, ensure_ascii=False, indent=2))

    def add_section(self, book: Book, title: str, after_section_id: str | None = None) -> Section:
        s = Section(id=str(uuid.uuid4()), title=title.strip() or 'Nieuwe sectie')
        if after_section_id:
            idx = next((i for i, sec in enumerate(book.sections) if sec.id == after_section_id), len(book.sections)-1)
            book.sections.insert(idx + 1, s)
        else:
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

    def find_chapter(self, book: Book, chapter_id: str):
        for section in book.sections:
            for index, chapter in enumerate(section.chapters):
                if chapter.id == chapter_id:
                    return section, index, chapter
        return None, -1, None

    def rename_chapter(self, book: Book, chapter_id: str, title: str) -> Chapter | None:
        section, index, chapter = self.find_chapter(book, chapter_id)
        if chapter is None:
            return None
        chapter.title = title.strip() or 'Nieuw hoofdstuk'
        self.save_manifest(book)
        return chapter

    def duplicate_chapter(self, book: Book, chapter_id: str) -> Chapter | None:
        section, index, source = self.find_chapter(book, chapter_id)
        if source is None or section is None:
            return None
        new_id = str(uuid.uuid4())
        rel = f'chapters/{new_id}.md'
        title = f'{source.title} (kopie)'
        target = Chapter(id=new_id, title=title, file=rel)
        source_path = book.path / source.file
        target_path = book.path / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_path.read_text(encoding='utf-8') if source_path.exists() else '', encoding='utf-8')
        section.chapters.insert(index + 1, target)
        self.save_manifest(book)
        return target

    def delete_chapter(self, book: Book, chapter_id: str) -> bool:
        """Remove a chapter from the manuscript while preserving its file in trash."""
        total = sum(len(section.chapters) for section in book.sections)
        if total <= 1:
            return False
        section, index, chapter = self.find_chapter(book, chapter_id)
        if chapter is None or section is None:
            return False
        source = book.path / chapter.file
        if source.exists():
            target_root = self.trash_dir / 'chapters' / book.id
            target_root.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            safe_name = f'{stamp}__{chapter.id}__{slugify(chapter.title)}.md'
            shutil.move(str(source), str(target_root / safe_name))
        del section.chapters[index]
        self.save_manifest(book)
        return True

    def rename_section(self, book: Book, section_id: str, title: str) -> Section | None:
        section = next((s for s in book.sections if s.id == section_id), None)
        if section is None:
            return None
        section.title = title.strip() or 'Nieuwe sectie'
        self.save_manifest(book)
        return section

    def save_chapter(self, book: Book, chapter: Chapter, text: str):
        self.ensure_daily_archive(book)
        p = book.path / chapter.file
        _safe_atomic_write_text(p, text)
        self.touch_book(book)

    def ensure_daily_archive(self, book: Book):
        files = [book.path / c.file for sec in book.sections for c in sec.chapters if (book.path / c.file).exists()]
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
        self._register_version(book, target.name, target, kind='daily', created_at=datetime.fromtimestamp(newest).isoformat(timespec='seconds'))

    def _history_root(self, book: Book) -> Path:
        root = self.archive_dir / book.id
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _history_index_path(self, book: Book) -> Path:
        return self._history_root(book) / 'history.json'

    def _load_history_index(self, book: Book) -> dict:
        path = self._history_index_path(book)
        if not path.exists():
            return {'versions': {}}
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                return {'versions': {}}
            data.setdefault('versions', {})
            return data
        except Exception:
            return {'versions': {}}

    def _save_history_index(self, book: Book, data: dict):
        _safe_atomic_write_text(self._history_index_path(book), json.dumps(data, ensure_ascii=False, indent=2))

    def _register_version(self, book: Book, version_id: str, path: Path, kind: str, created_at: str | None = None):
        data = self._load_history_index(book)
        row = dict(data['versions'].get(version_id) or {})
        row.setdefault('starred', False)
        row['kind'] = kind
        row['created_at'] = created_at or datetime.now().isoformat(timespec='seconds')
        row['folder'] = Path(path).name
        data['versions'][version_id] = row
        self._save_history_index(book, data)

    def create_version(self, book: Book, kind: str = 'manual') -> dict:
        """Create a complete immutable manuscript snapshot."""
        root = self._history_root(book)
        now = datetime.now()
        version_id = now.strftime('%Y-%m-%dT%H-%M-%S-%f')
        target = root / version_id
        counter = 2
        while target.exists():
            target = root / f'{version_id}-{counter}'
            counter += 1
        shutil.copytree(book.path, target)
        self._register_version(book, target.name, target, kind=kind, created_at=now.isoformat(timespec='seconds'))
        return next(v for v in self.list_versions(book) if v['id'] == target.name)

    def list_versions(self, book: Book) -> list[dict]:
        root = self._history_root(book)
        index = self._load_history_index(book)
        rows = []
        for folder in root.iterdir():
            if not folder.is_dir() or not (folder / 'book.json').exists():
                continue
            version_id = folder.name
            meta = dict(index.get('versions', {}).get(version_id) or {})
            if not meta:
                # Backward compatibility with 0.6.x day folders.
                try:
                    newest = max([p.stat().st_mtime for p in folder.rglob('*') if p.is_file()] or [folder.stat().st_mtime])
                except OSError:
                    newest = folder.stat().st_mtime
                created_at = datetime.fromtimestamp(newest).isoformat(timespec='seconds')
                kind = 'daily' if re.fullmatch(r'\d{4}-\d{2}-\d{2}', version_id) else 'manual'
                meta = {'created_at': created_at, 'kind': kind, 'starred': False, 'folder': folder.name}
            try:
                snap = self.load_book(folder)
                words = sum(len(self.read_chapter(snap, c).split()) for sec in snap.sections for c in sec.chapters)
                chapter_count = sum(len(sec.chapters) for sec in snap.sections)
                title = snap.title
            except Exception:
                words = 0; chapter_count = 0; title = book.title
            rows.append({
                'id': version_id, 'path': folder, 'created_at': meta.get('created_at') or datetime.fromtimestamp(folder.stat().st_mtime).isoformat(timespec='seconds'),
                'kind': meta.get('kind', 'manual'), 'starred': bool(meta.get('starred', False)),
                'title': title, 'words': words, 'chapters': chapter_count,
            })
        rows.sort(key=lambda r: r['created_at'], reverse=True)
        return rows

    def set_version_starred(self, book: Book, version_id: str, starred: bool):
        data = self._load_history_index(book)
        row = dict(data['versions'].get(version_id) or {})
        row['starred'] = bool(starred)
        if 'created_at' not in row:
            version = next((x for x in self.list_versions(book) if x['id'] == version_id), None)
            if version:
                row['created_at'] = version['created_at']; row['kind'] = version['kind']; row['folder'] = version_id
        data['versions'][version_id] = row
        self._save_history_index(book, data)

    def load_version(self, book: Book, version_id: str) -> Book:
        folder = self._history_root(book) / version_id
        if not folder.is_dir() or not (folder / 'book.json').exists():
            raise FileNotFoundError(f'Versie {version_id} bestaat niet meer.')
        return self.load_book(folder)

    def _apply_snapshot_to_live(self, live_book: Book, snapshot: Book) -> Book:
        wanted = set()
        for sec in snapshot.sections:
            for ch in sec.chapters:
                source = snapshot.path / ch.file
                target = live_book.path / ch.file
                wanted.add(target.resolve())
                _safe_atomic_write_text(target, source.read_text(encoding='utf-8') if source.exists() else '')

        restored = Book(
            id=snapshot.id, title=snapshot.title, path=live_book.path,
            sections=copy.deepcopy(snapshot.sections), metadata=copy.deepcopy(snapshot.metadata),
        )
        restored.metadata['last_used'] = datetime.now().timestamp()
        self.save_manifest(restored)

        # Remove unreferenced chapter files only after all desired files and the
        # manifest have been written successfully. A locked orphan is harmless.
        chapters_dir = live_book.path / 'chapters'
        if chapters_dir.exists():
            for existing in chapters_dir.glob('*.md'):
                if existing.resolve() not in wanted:
                    try:
                        existing.unlink()
                    except PermissionError:
                        pass
        return self.load_book(live_book.path)

    def restore_version(self, book: Book, version_id: str) -> Book:
        """Restore a snapshot with an automatic rollback checkpoint."""
        snapshot = self.load_version(book, version_id)
        safety = self.create_version(book, kind='pre_restore')
        safety_snapshot = self.load_version(book, safety['id'])
        try:
            return self._apply_snapshot_to_live(book, snapshot)
        except Exception:
            # Best effort rollback to the byte-for-byte manuscript snapshot taken
            # just before restore. If Dropbox caused a transient lock the same
            # robust write path is used for the rollback as well.
            try:
                self._apply_snapshot_to_live(book, safety_snapshot)
            except Exception:
                pass
            raise

    def delete_book(self, book: Book):
        """Verplaats een boek naar de prullenbak."""
        if not book.path.exists():
            return
        target_root = self.trash_dir / 'books'
        target_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        target = target_root / f'{stamp}__{book.path.name}'
        counter = 2
        while target.exists():
            target = target_root / f'{stamp}-{counter}__{book.path.name}'
            counter += 1
        shutil.move(str(book.path), str(target))

    def list_trashed_books(self) -> list[dict]:
        root = self.trash_dir / 'books'
        root.mkdir(parents=True, exist_ok=True)
        rows = []
        for folder in root.iterdir():
            if not folder.is_dir() or not (folder / 'book.json').exists():
                continue
            try:
                book = self.load_book(folder)
                rows.append({'path': folder, 'title': book.title, 'deleted': folder.stat().st_mtime, 'book': book})
            except Exception:
                continue
        return sorted(rows, key=lambda r: r['deleted'], reverse=True)

    def restore_trashed_book(self, trash_path: Path) -> Book:
        trash_path = Path(trash_path)
        book = self.load_book(trash_path)
        base = trash_path.name.split('__', 1)[-1]
        target = self.books_dir / base
        counter = 2
        while target.exists():
            target = self.books_dir / f'{base}-{counter}'
            counter += 1
        shutil.move(str(trash_path), str(target))
        return self.load_book(target)

    def permanently_delete_trashed_book(self, trash_path: Path):
        trash_path = Path(trash_path)
        if trash_path.exists() and self.trash_dir in trash_path.parents:
            shutil.rmtree(trash_path)

    def empty_trash(self):
        root = self.trash_dir / 'books'
        if root.exists():
            for p in list(root.iterdir()):
                if p.is_dir():
                    shutil.rmtree(p)

    def remove_cover(self, book: Book):
        stored = (book.metadata.get('cover_file') or '').strip()
        candidates = []
        if stored:
            candidates.append(self.covers_dir / stored)
        for ext in self.COVER_EXTENSIONS:
            candidates.append(self.covers_dir / f'{book.slug}{ext}')
        for p in candidates:
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        book.metadata['cover_file'] = ''
        self.save_manifest(book)

    def import_markdown_book(self, source: Path) -> Book:
        from .story_index import parse_story
        source = Path(source)
        data = parse_story(source)
        title = (data.get('title') or source.stem).strip() or source.stem
        book = self.create_book(title)
        # Verwijder het automatisch gemaakte hoofdstuk en vervang het door de hoofdstukken uit het bestand.
        for sec in book.sections:
            for ch in sec.chapters:
                p = book.path / ch.file
                if p.exists():
                    p.unlink()
        book.sections = [Section(id='root', title='Manuscript')]
        md = book.metadata
        for key in ('slug', 'description', 'meta', 'intro', 'tags', 'author', 'image', 'cover', 'featured_image', 'date', 'published'):
            if data.get(key) not in (None, ''):
                md[key] = data.get(key)
        md['slug'] = slugify(md.get('slug') or title)
        md['source_file'] = str(source)
        md['last_used'] = datetime.now().timestamp()
        if data.get('extra'):
            md['extra'] = data['extra']
        section = book.sections[0]
        chapters = data.get('chapters') or [{'title': title, 'text': data.get('body', '')}]
        for item in chapters:
            ch = self.add_chapter(book, section, item.get('title') or 'Hoofdstuk', persist=False)
            section.chapters.append(ch)
            (book.path / ch.file).write_text(item.get('text', ''), encoding='utf-8')
        self.save_manifest(book)
        return book

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
        _safe_atomic_write_text(self.persona_path(), text)
