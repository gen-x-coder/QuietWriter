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

from .revisions import BookRevision, ExternalModificationError, FileRevision, capture_book_revision, file_revision
from .persona_profile import default_persona_markdown
from .book_profile import default_book_profile_markdown
from .book_memory import default_book_memory_markdown
from .i18n import tr
from .manuscript_profile import (
    MANUSCRIPT_SYNTAX_KEY, AmbiguousManuscriptSyntaxError, ManuscriptSyntaxMigration, current_manifest_value,
    migrate_legacy_source_to_current, migration_source_state, profile_from_manifest,
)


class BookBlockedError(RuntimeError):
    """A detached/incompatible book is deliberately closed for writes."""




_UNSET_REVISION = object()


class PersonaExternalModificationError(RuntimeError):
    """Raised before overwriting the global writer persona after an external change."""

    def __init__(self, path: Path, expected: FileRevision | None, current: FileRevision | None):
        self.path = Path(path)
        self.expected = expected
        self.current = current
        super().__init__(f'Schrijverspersona is buiten QuietWriter gewijzigd: {self.path.name}')


class CorruptSourceError(RuntimeError):
    """Refuse normal writes over an existing text file that is not valid UTF-8."""
    def __init__(self, path: Path):
        self.path = Path(path)
        super().__init__(f'{self.path} is beschadigd en kan niet veilig worden overschreven; herstel het eerst via Integriteit.')


def _guard_existing_utf8(path: Path):
    """Fail closed before a normal text save can destroy corrupt source bytes."""
    path = Path(path)
    if not path.exists():
        return
    try:
        path.read_bytes().decode('utf-8')
    except UnicodeDecodeError as exc:
        raise CorruptSourceError(path) from exc


def _guard_existing_json(path: Path):
    """Fail closed before replacing an existing JSON source that no longer parses."""
    path = Path(path)
    if not path.exists():
        return
    _guard_existing_utf8(path)
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError as exc:
        raise CorruptSourceError(path) from exc
    if not isinstance(value, dict):
        raise CorruptSourceError(path)


class StorageWriteError(OSError):
    def __init__(self, path: Path, cause: OSError):
        self.path = Path(path); self.cause = cause
        super().__init__(f'Kan {self.path} niet veilig opslaan: {cause}')


def _safe_atomic_write_text(path: Path, text: str, encoding: str = 'utf-8', replace_retries: int = 8):
    """Atomically write text; transient sharing violations are retried."""
    path = Path(path); tmp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent)); tmp=Path(tmp_name)
        with os.fdopen(fd, 'w', encoding=encoding, newline='') as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        delay=0.04; last_exc=None
        for _ in range(max(1, replace_retries)):
            try: os.replace(tmp, path); return
            except PermissionError as exc:
                last_exc=exc; time.sleep(delay); delay=min(delay*1.8,0.45)
        raise last_exc or PermissionError(f'Kan {path} niet atomair opslaan.')
    except StorageWriteError: raise
    except OSError as exc: raise StorageWriteError(path, exc) from exc
    finally:
        try:
            if tmp is not None and tmp.exists(): tmp.unlink()
        except OSError: pass


def _safe_atomic_write_bytes(path: Path, data: bytes, replace_retries: int = 8):
    """Byte-exact sibling-temp write with the same lock/retry contract as text."""
    path=Path(path); tmp=None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd,tmp_name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent)); tmp=Path(tmp_name)
        with os.fdopen(fd,'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        delay=0.04; last_exc=None
        for _ in range(max(1,replace_retries)):
            try: os.replace(tmp,path); return
            except PermissionError as exc:
                last_exc=exc; time.sleep(delay); delay=min(delay*1.8,0.45)
        raise last_exc or PermissionError(f'Kan {path} niet atomair opslaan.')
    except StorageWriteError: raise
    except OSError as exc: raise StorageWriteError(path,exc) from exc
    finally:
        try:
            if tmp is not None and tmp.exists(): tmp.unlink()
        except OSError: pass


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
    format_version: int = 2
    sections: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    # Unknown top-level manifest keys are retained verbatim for forward-compatible round trips.
    extra_manifest: dict = field(default_factory=dict)

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
        self.covers_dir = self.root / 'boekomslagen'
        self.archive_dir = self.root / 'archive'
        self.trash_dir = self.root / 'trash'
        self.persona_dir = self.root / 'persona'
        self.dict_dir = self.root / 'dictionaries'
        self.cache_dir = self.root / '.cache'
        # Revisions are kept in memory only. Nothing is locked on disk, so a
        # crash can never leave a stale workspace lock behind.
        self._tracked_revisions: dict[str, BookRevision] = {}
        self._blocked_book_ids: set[str] = set()
        self.last_list_errors: list[dict] = []
        for d in [self.books_dir, self.covers_dir, self.archive_dir, self.trash_dir,
                  self.persona_dir, self.dict_dir, self.cache_dir]:
            d.mkdir(parents=True, exist_ok=True)
        self._cleanup_stale_import_staging()
        persona = self.persona_dir / 'schrijver.md'
        if not persona.exists():
            _safe_atomic_write_text(persona, default_persona_markdown())

    def _cleanup_stale_import_staging(self, *, older_than_seconds: float = 24 * 60 * 60):
        """Remove abandoned DOCX staging trees from earlier crashed sessions.

        A fresh staging directory may belong to another running QuietWriter
        process using the same workspace, so only directories older than one
        day are eligible. Cleanup is best-effort and never blocks startup.
        """
        try:
            now = time.time()
            for path in self.books_dir.glob('.import-*'):
                try:
                    if not path.is_dir():
                        continue
                    age = now - path.stat().st_mtime
                    if age >= older_than_seconds:
                        shutil.rmtree(path, ignore_errors=True)
                except OSError:
                    continue
        except OSError:
            pass

    def _chapter_files(self, book: Book) -> list[str]:
        return [chapter.file for section in book.sections for chapter in section.chapters]

    def capture_revision(self, book: Book) -> BookRevision:
        return capture_book_revision(book.path, self._chapter_files(book))

    def track_book(self, book: Book) -> BookRevision:
        revision = self.capture_revision(book)
        self._tracked_revisions[book.id] = revision
        # Explicitly reopening/retracking a book clears a detach write-block.
        self._blocked_book_ids.discard(book.id)
        return revision

    def untrack_book(self, book: Book):
        self._tracked_revisions.pop(book.id, None)
        self._blocked_book_ids.discard(book.id)

    def block_book(self, book: Book):
        """Fail closed for a detached/incompatible book until it is explicitly reopened."""
        self._blocked_book_ids.add(book.id)

    def is_book_blocked(self, book: Book) -> bool:
        """Return whether writes for this live book are deliberately blocked."""
        return book.id in self._blocked_book_ids

    def tracked_revision(self, book: Book) -> BookRevision | None:
        return self._tracked_revisions.get(book.id)

    def verify_book_unchanged(self, book: Book) -> BookRevision:
        if book.id in self._blocked_book_ids:
            raise BookBlockedError('Dit boek is losgekoppeld en geblokkeerd voor verdere schrijfacties. Open het boek opnieuw voordat je wijzigingen aanbrengt.')
        current = self.capture_revision(book)
        expected = self._tracked_revisions.get(book.id)
        if expected is not None:
            changed = expected.changed_files(current)
            if changed:
                raise ExternalModificationError(book.id, changed, expected, current)
        return current

    def refresh_book_revision(self, book: Book) -> BookRevision:
        return self.track_book(book)

    def _refresh_if_tracked(self, book: Book):
        if book.id in self._tracked_revisions:
            self.refresh_book_revision(book)

    def manifest_text(self, book: Book) -> str:
        """Return the canonical book.json representation without writing live state."""
        metadata = dict(book.metadata or {})
        metadata.setdefault('slug', slugify(book.title))
        data = copy.deepcopy(book.extra_manifest or {})
        data.update({
            'format': int(book.format_version),
            'id': book.id,
            'title': book.title,
            'metadata': metadata,
            'sections': [
                {'id': section.id, 'title': section.title, 'chapters': [vars(chapter) for chapter in section.chapters]}
                for section in book.sections
            ],
        })
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _write_manifest_unchecked(self, book: Book):
        book.metadata.setdefault('slug', slugify(book.title))
        _safe_atomic_write_text(book.manifest_path, self.manifest_text(book))

    def list_books(self) -> list[Book]:
        books = []
        self.last_list_errors = []
        for manifest in self.books_dir.glob('*/book.json'):
            if manifest.parent.name.startswith('.'):
                continue
            try:
                books.append(self.load_book(manifest.parent))
            except Exception as exc:
                title = manifest.parent.name
                try:
                    raw = json.loads(manifest.read_text(encoding='utf-8'))
                    if isinstance(raw, dict) and isinstance(raw.get('title'), str): title = raw['title']
                except Exception:
                    pass
                self.last_list_errors.append({'path': manifest.parent, 'title': title, 'error': exc})
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

    def touch_book(self, book: Book) -> Book:
        """Update only ``last_used`` on the freshest manifest from disk.

        A Book object supplied by the bookshelf can be minutes or hours older than
        ``book.json`` when a sync client updated the workspace in the meantime.
        Never write that stale in-memory structure back just to record activity.
        """
        current = self.load_book(book.path)
        self.verify_book_unchanged(current)
        current.metadata['last_used'] = datetime.now().timestamp()
        self._write_manifest_unchecked(current)
        self._refresh_if_tracked(current)
        return current

    def create_book(self, title: str) -> Book:
        book_id = str(uuid.uuid4())
        clean_title = title.strip() or 'Naamloos boek'
        folder = self.books_dir / f'{slugify(clean_title)}-{book_id[:8]}'
        (folder / 'chapters').mkdir(parents=True, exist_ok=True)
        (folder / 'assets' / 'images').mkdir(parents=True, exist_ok=True)
        (folder / 'assets' / 'cover').mkdir(parents=True, exist_ok=True)
        _safe_atomic_write_text(folder / 'assets' / 'manifest.json', json.dumps({'version': 1, 'images': {}}, ensure_ascii=False, indent=2))
        book = Book(
            id=book_id,
            title=clean_title,
            path=folder,
            extra_manifest={MANUSCRIPT_SYNTAX_KEY: current_manifest_value()},
            metadata={
                'slug': slugify(clean_title),
                'date': datetime.now().isoformat(timespec='minutes'),
                'description': '',
                'intro': '',
                'meta': '',
                'image': '',
                'image_alt': '',
                'author': '',
                'language': 'nl',
                'tags': '',
                'published': 'No',
                'synopsis': '',
                'cover_file': '',
                'last_used': datetime.now().timestamp(),
            },
        )
        section = Section(id='root', title='Manuscript')
        chapter = self.add_chapter(book, section, tr('storage.default_chapter_1', 'Hoofdstuk 1'), persist=False)
        section.chapters.append(chapter)
        book.sections.append(section)
        self.save_manifest(book)
        return book

    def load_book(self, folder: Path) -> Book:
        data = json.loads((Path(folder) / 'book.json').read_text(encoding='utf-8'))
        from .migrations import detected_book_format, validate_manifest_structure
        validate_manifest_structure(data, allow_legacy=True)
        profile_from_manifest(data)
        sections = []
        for s in data.get('sections', []):
            chapters = [Chapter(id=c['id'], title=c['title'], file=c['file']) for c in s.get('chapters', [])]
            sections.append(Section(id=s['id'], title=s['title'], chapters=chapters))
        metadata = dict(data.get('metadata') or {})
        # ``cover_file`` was introduced with book-local covers in 0.20.0.
        # Older releases subsequently wrote ``cover_file: ''`` into legacy
        # manifests via ``setdefault``/``touch_book``, so the field's mere
        # presence is not a reliable migration marker. A genuine 0.20+ book is
        # identified by its book-local media manifest; only books without that
        # marker may adopt an old global ``boekomslagen/<slug>.*`` cover.
        has_book_local_media_manifest = (Path(folder) / 'assets' / 'manifest.json').exists()
        metadata.setdefault('slug', slugify(data.get('title', 'boek')))
        metadata.setdefault('date', '')
        metadata.setdefault('description', '')
        metadata.setdefault('intro', '')
        metadata.setdefault('meta', '')
        metadata.setdefault('image', '')
        metadata.setdefault('image_alt', '')
        metadata.setdefault('author', '')
        metadata.setdefault('language', 'nl')
        metadata.setdefault('tags', '')
        metadata.setdefault('published', 'No')
        metadata.setdefault('synopsis', '')
        metadata.setdefault('cover_file', '')
        if not metadata['cover_file'] and not has_book_local_media_manifest:
            local_cover_dir = Path(folder) / 'assets' / 'cover'
            has_local_cover = any((local_cover_dir / f'cover{ext}').exists() for ext in self.COVER_EXTENSIONS)
            if not has_local_cover:
                legacy_slug = (metadata.get('slug') or slugify(data.get('title', 'boek'))).strip()
                for ext in self.COVER_EXTENSIONS:
                    candidate = self.covers_dir / f'{legacy_slug}{ext}'
                    if candidate.exists():
                        # Keep explicit ownership in memory. The next normal
                        # manifest write/touch persists this migration, so the
                        # ambiguous slug fallback is never needed again.
                        metadata['cover_file'] = candidate.name
                        break
        metadata.setdefault('last_used', 0)
        known = {'format', 'id', 'title', 'metadata', 'sections'}
        extra_manifest = {k: copy.deepcopy(v) for k, v in data.items() if k not in known}
        return Book(id=data['id'], title=data['title'], path=Path(folder), format_version=detected_book_format(data), sections=sections, metadata=metadata, extra_manifest=extra_manifest)

    def _manuscript_syntax_files(self, book: Book) -> list[Path]:
        paths: list[Path] = []
        for section in book.sections:
            for chapter in section.chapters:
                paths.append(book.path / chapter.file)
        publication_dir = book.path / 'publication' / 'texts'
        if publication_dir.is_dir():
            paths.extend(sorted(publication_dir.glob('*.md')))
        return paths

    def manuscript_syntax_migration_state(self, book: Book) -> str:
        """Return legacy/escape-era/ambiguous for an unversioned book."""
        sources: list[str] = []
        for path in self._manuscript_syntax_files(book):
            _guard_existing_utf8(path)
            sources.append(path.read_text(encoding='utf-8') if path.exists() else '')
        return migration_source_state(sources)

    def migrate_manuscript_syntax(self, book: Book, *, assume_escape_era: bool | None = None):
        """Explicitly migrate one unversioned manuscript to the current profile.

        Books edited by the escape-aware 1.2.19+ editor can already contain the
        current byte grammar despite lacking the marker. Strong fingerprints are
        therefore marker-only. Pure legacy books receive the minimal backslash
        additions needed to preserve their old visible text. Ambiguous all-even
        backslash runs require an explicit caller choice.
        """
        self.verify_book_unchanged(book)
        raw_manifest = json.loads(book.manifest_path.read_text(encoding='utf-8'))
        profile = profile_from_manifest(raw_manifest)
        if profile.is_current:
            return book, ManuscriptSyntaxMigration(0, 0, 'current'), None
        if profile.explicit:
            raise BookBlockedError(
                f'Geen veilig migratiepad beschikbaar voor manuscriptsyntax {profile.version}.'
            )

        source_by_path: dict[Path, str] = {}
        for path in self._manuscript_syntax_files(book):
            _guard_existing_utf8(path)
            source_by_path[path] = path.read_text(encoding='utf-8') if path.exists() else ''

        state = migration_source_state(tuple(source_by_path.values()))
        if state == 'ambiguous' and assume_escape_era is None:
            raise AmbiguousManuscriptSyntaxError(
                'Dit boek bevat alleen dubbelzinnige backslashreeksen; kies of de tekst al met de veilige escapes is bewerkt.'
            )
        marker_only = state == 'escape-era' or (state == 'ambiguous' and assume_escape_era is True)

        updates: dict[Path, str] = {}
        escaped_backslashes = 0
        if not marker_only:
            for path, source in source_by_path.items():
                migrated, count = migrate_legacy_source_to_current(source)
                escaped_backslashes += count
                if migrated != source:
                    updates[path] = migrated

        checkpoint = self.create_version(book, kind='pre_syntax_migration')
        checkpoint_id = checkpoint['id']
        try:
            self.verify_book_unchanged(book)
            for path, text in updates.items():
                _safe_atomic_write_text(path, text)

            migrated_book = copy.deepcopy(book)
            migrated_book.extra_manifest = copy.deepcopy(book.extra_manifest or {})
            migrated_book.extra_manifest[MANUSCRIPT_SYNTAX_KEY] = current_manifest_value()
            migrated_book.metadata = copy.deepcopy(book.metadata or {})
            migrated_book.metadata['last_used'] = datetime.now().timestamp()
            self._write_manifest_unchecked(migrated_book)
            live = self.load_book(book.path)
            self.refresh_book_revision(live)
            changed_chapters = sum(
                1 for path in updates if 'chapters' in path.parts
            )
            mode = 'escape-era' if marker_only else 'legacy'
            return live, ManuscriptSyntaxMigration(changed_chapters, escaped_backslashes, mode), checkpoint_id
        except Exception:
            try:
                snapshot = self.load_version(book, checkpoint_id)
                restored = self._apply_snapshot_to_live(book, snapshot)
                self.refresh_book_revision(restored)
            except Exception:
                pass
            raise

    def migrate_book_format(self, book: Book):
        """Explicitly migrate book.json with a complete rollback snapshot.

        Opening a book never performs a silent migration. Callers can audit first
        and invoke this operation deliberately.
        """
        from .migrations import migrate_manifest_data, migrate_manifest_file
        self.verify_book_unchanged(book)
        current_data = json.loads(book.manifest_path.read_text(encoding='utf-8'))
        _, preview = migrate_manifest_data(current_data)
        if not preview.changed:
            return book, preview, None
        checkpoint = self.create_version(book, kind='pre_migration')
        self.verify_book_unchanged(book)
        try:
            result = migrate_manifest_file(book.manifest_path)
            migrated = self.load_book(book.path)
            self.refresh_book_revision(migrated)
            return migrated, result, checkpoint['id']
        except Exception:
            # migrate_manifest_file is atomic, so a failed write leaves the live
            # manifest untouched. Keep the checkpoint as an additional recovery
            # source instead of attempting a second live write here.
            raise

    def save_manifest(self, book: Book):
        self.verify_book_unchanged(book)
        self._write_manifest_unchecked(book)
        self._refresh_if_tracked(book)

    def add_section(self, book: Book, title: str, after_section_id: str | None = None) -> Section:
        self.verify_book_unchanged(book)
        section = Section(id=str(uuid.uuid4()), title=title.strip() or 'Nieuwe sectie')
        if after_section_id:
            idx = next((i for i, sec in enumerate(book.sections) if sec.id == after_section_id), len(book.sections)-1)
            insert_at = idx + 1
        else:
            insert_at = len(book.sections)
        book.sections.insert(insert_at, section)
        try:
            self._write_manifest_unchecked(book)
        except Exception:
            # Keep the live model aligned with the unchanged manifest if the
            # manifest write fails for any reason (disk full, permissions, sync lock).
            if section in book.sections:
                book.sections.remove(section)
            raise
        self._refresh_if_tracked(book)
        return section

    def add_chapter(self, book: Book, section: Section, title: str, persist=True) -> Chapter:
        if persist:
            self.verify_book_unchanged(book)
        cid = str(uuid.uuid4())
        rel = f'chapters/{cid}.md'
        chapter = Chapter(id=cid, title=title.strip() or 'Nieuw hoofdstuk', file=rel)
        chapter_path = book.path / rel
        _safe_atomic_write_text(chapter_path, '')
        if persist:
            section.chapters.append(chapter)
            try:
                self._write_manifest_unchecked(book)
            except Exception:
                if chapter in section.chapters:
                    section.chapters.remove(chapter)
                try:
                    chapter_path.unlink(missing_ok=True)
                except OSError:
                    # An unreferenced empty UUID file is safer than mutating the
                    # manifest/model after a failed transaction. It can be cleaned later.
                    pass
                raise
            self._refresh_if_tracked(book)
        return chapter

    def read_chapter(self, book: Book, chapter: Chapter) -> str:
        path = book.path / chapter.file
        return path.read_text(encoding='utf-8') if path.exists() else ''

    def locate_chapter(self, book: Book, chapter_id: str):
        for section in book.sections:
            for index, chapter in enumerate(section.chapters):
                if chapter.id == chapter_id:
                    return section, index, chapter
        return None, -1, None

    def rename_chapter(self, book: Book, chapter_id: str, title: str) -> Chapter | None:
        self.verify_book_unchanged(book)
        section, index, chapter = self.locate_chapter(book, chapter_id)
        if chapter is None:
            return None
        old_title = chapter.title
        chapter.title = title.strip() or 'Nieuw hoofdstuk'
        try:
            self._write_manifest_unchecked(book)
        except Exception:
            chapter.title = old_title
            raise
        self._refresh_if_tracked(book)
        return chapter

    def duplicate_chapter(self, book: Book, chapter_id: str) -> Chapter | None:
        self.verify_book_unchanged(book)
        section, index, source = self.locate_chapter(book, chapter_id)
        if source is None or section is None:
            return None
        new_id = str(uuid.uuid4())
        rel = f'chapters/{new_id}.md'
        title = f'{source.title} (kopie)'
        target = Chapter(id=new_id, title=title, file=rel)
        source_path = book.path / source.file
        target_path = book.path / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Duplicating is a normal content operation, not a recovery path.
        # Never turn invalid UTF-8 into a generic decode crash or copy it blindly.
        _guard_existing_utf8(source_path)
        _safe_atomic_write_text(target_path, source_path.read_text(encoding='utf-8') if source_path.exists() else '')
        section.chapters.insert(index + 1, target)
        try:
            self._write_manifest_unchecked(book)
        except Exception:
            if target in section.chapters:
                section.chapters.remove(target)
            try:
                target_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        self._refresh_if_tracked(book)
        return target

    def adjacent_chapter_for_delete(self, book: Book, chapter_id: str) -> Chapter | None:
        ordered = [chapter for section in book.sections for chapter in section.chapters]
        index = next((i for i, chapter in enumerate(ordered) if chapter.id == chapter_id), -1)
        if index < 0 or len(ordered) <= 1:
            return None
        if index > 0:
            return ordered[index - 1]
        return ordered[index + 1] if index + 1 < len(ordered) else None

    def delete_chapter(self, book: Book, chapter_id: str) -> bool:
        self.verify_book_unchanged(book)
        total = sum(len(section.chapters) for section in book.sections)
        if total <= 1:
            return False
        section, index, chapter = self.locate_chapter(book, chapter_id)
        if chapter is None or section is None:
            return False

        source = book.path / chapter.file
        trash_copy = None
        trash_metadata = None
        if source.exists():
            # Never move the only live copy before book.json has been committed.
            # First create a recoverable trash copy plus enough metadata to put
            # the chapter back in its original book/section later.
            target_root = self.trash_dir / 'chapters' / book.id
            target_root.mkdir(parents=True, exist_ok=True)
            deleted_at = datetime.now().timestamp()
            stamp = datetime.fromtimestamp(deleted_at).strftime('%Y%m%d-%H%M%S-%f')
            safe_name = f'{stamp}__{chapter.id}__{slugify(chapter.title)}.md'
            trash_copy = target_root / safe_name
            trash_metadata = trash_copy.with_suffix('.json')
            shutil.copy2(source, trash_copy)
            metadata = {
                'format': 1,
                'deleted': deleted_at,
                'book_id': book.id,
                'book_title': book.title,
                'chapter_id': chapter.id,
                'chapter_title': chapter.title,
                'chapter_file': chapter.file,
                'section_id': section.id,
                'section_title': section.title,
                'section_index': book.sections.index(section),
                'chapter_index': index,
            }
            try:
                _safe_atomic_write_text(trash_metadata, json.dumps(metadata, ensure_ascii=False, indent=2))
            except Exception:
                try:
                    trash_copy.unlink(missing_ok=True)
                except OSError:
                    pass
                raise

        del section.chapters[index]
        try:
            self._write_manifest_unchecked(book)
        except Exception:
            section.chapters.insert(index, chapter)
            for candidate in (trash_metadata, trash_copy):
                if candidate is not None:
                    try:
                        candidate.unlink(missing_ok=True)
                    except OSError:
                        pass
            raise

        # book.json no longer references the chapter. Removing the old source is
        # now cleanup rather than the only copy operation; the metadata-backed
        # trash copy remains available for restore from the Trash page.
        if source.exists():
            try:
                source.unlink()
            except OSError:
                # A transient sync/file lock may leave an unreferenced UUID file
                # behind, but never causes content loss or a broken manifest.
                pass
        self._refresh_if_tracked(book)
        return True

    def rename_section(self, book: Book, section_id: str, title: str) -> Section | None:
        self.verify_book_unchanged(book)
        section = next((section for section in book.sections if section.id == section_id), None)
        if section is None:
            return None
        old_title = section.title
        section.title = title.strip() or 'Nieuwe sectie'
        try:
            self._write_manifest_unchecked(book)
        except Exception:
            section.title = old_title
            raise
        self._refresh_if_tracked(book)
        return section

    def save_chapter(self, book: Book, chapter: Chapter, text: str):
        # Verify the complete currently tracked book before the logical save.
        # The manuscript file is authoritative; updating ``last_used`` in the
        # manifest is bookkeeping and may fail transiently under sync/file locks.
        self.verify_book_unchanged(book)
        self.ensure_daily_archive(book)
        path = book.path / chapter.file
        _guard_existing_utf8(path)
        _safe_atomic_write_text(path, text)
        book.metadata['last_used'] = datetime.now().timestamp()
        try:
            self._write_manifest_unchecked(book)
        except OSError:
            # Text has already been committed successfully. Do not turn a
            # best-effort activity timestamp into a failed manuscript save.
            pass
        finally:
            # Once the chapter write succeeded, advance the baseline even if
            # book.json could not be touched. Otherwise the next save reports
            # our own text as an external modification.
            self._refresh_if_tracked(book)

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

    def create_version_from_state(self, book: Book, chapter_overrides: dict[str, str] | None = None, kind: str = 'conflict_local') -> dict:
        """Snapshot the in-memory book structure, optionally overriding chapter text.

        Used before discarding unsaved local editor text after an external-change
        conflict. The snapshot deliberately uses the in-memory manifest rather
        than the possibly newer live manifest on disk, so the current chapter
        remains reachable from History even if the external structure changed.
        """
        chapter_overrides = chapter_overrides or {}
        root = self._history_root(book)
        now = datetime.now()
        version_id = now.strftime('%Y-%m-%dT%H-%M-%S-%f')
        target = root / version_id
        counter = 2
        while target.exists():
            target = root / f'{version_id}-{counter}'
            counter += 1
        (target / 'chapters').mkdir(parents=True, exist_ok=True)
        snapshot = Book(
            id=book.id, title=book.title, path=target,
            format_version=book.format_version, sections=copy.deepcopy(book.sections), metadata=copy.deepcopy(book.metadata),
            extra_manifest=copy.deepcopy(book.extra_manifest),
        )
        for section in snapshot.sections:
            for chapter in section.chapters:
                relative = Path(chapter.file).as_posix()
                destination = target / chapter.file
                destination.parent.mkdir(parents=True, exist_ok=True)
                if relative in chapter_overrides:
                    text = chapter_overrides[relative]
                else:
                    source = book.path / chapter.file
                    text = source.read_text(encoding='utf-8') if source.exists() else ''
                _safe_atomic_write_text(destination, text)
        # A conflict-local snapshot must remain a complete book snapshot. Keep
        # auxiliary book-owned data alongside the in-memory manuscript state.
        for aux_name in ('planning', 'publication', 'ai', 'assets'):
            source_aux = book.path / aux_name
            target_aux = target / aux_name
            if source_aux.exists():
                shutil.copytree(source_aux, target_aux)
        self._write_manifest_unchecked(snapshot)
        self._register_version(book, target.name, target, kind=kind, created_at=now.isoformat(timespec='seconds'))
        return next(version for version in self.list_versions(book) if version['id'] == target.name)

    def create_version_with_file_overrides(self, book: Book, file_overrides: dict[str, str], kind: str = 'conflict_local') -> dict:
        """Snapshot the current on-disk book and replace selected files in the snapshot.

        This is used by optional book-planning surfaces when a local unsaved
        planning value would otherwise be discarded after an external-change
        conflict. It never writes the live book.
        """
        root = self._history_root(book)
        now = datetime.now()
        version_id = now.strftime('%Y-%m-%dT%H-%M-%S-%f')
        target = root / version_id
        counter = 2
        while target.exists():
            target = root / f'{version_id}-{counter}'
            counter += 1
        shutil.copytree(book.path, target)
        for relative, text in (file_overrides or {}).items():
            destination = target / Path(relative)
            _safe_atomic_write_text(destination, text)
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
                from .manuscript_text import count_words
                words = sum(count_words(self.read_chapter(snap, c)) for sec in snap.sections for c in sec.chapters)
                chapter_count = sum(len(sec.chapters) for sec in snap.sections)
                title = snap.title
            except Exception:
                words = 0; chapter_count = 0; title = book.title
            rows.append({
                'id': version_id, 'path': folder, 'created_at': meta.get('created_at') or datetime.fromtimestamp(folder.stat().st_mtime).isoformat(timespec='seconds'),
                'kind': meta.get('kind', 'manual'), 'starred': bool(meta.get('starred', False)),
                'title': title, 'words': words, 'chapters': chapter_count,
            })
        rows.sort(key=lambda r: (r['created_at'], r['id']), reverse=True)
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

    def _sync_snapshot_auxiliary_dir(self, live_book: Book, snapshot: Book, name: str, *, remove_extras: bool = True):
        """Restore optional book-owned data such as planning/publication files.

        History snapshots are complete copies of the book folder. Restoring only
        chapters and book.json would leave planning/publication state from the
        newer book behind, so sync these small text/json trees as part of the same
        restore operation. Writes use the same robust path as the manuscript.
        """
        source_root = snapshot.path / name
        target_root = live_book.path / name
        # Historical snapshots created before this auxiliary data type existed
        # must not erase newer planning/publication data when restored. Absence
        # therefore means "snapshot has no opinion about this tree".
        if not source_root.exists():
            return
        wanted: set[Path] = set()
        for source in source_root.rglob('*'):
            if not source.is_file():
                continue
            relative = source.relative_to(source_root)
            target = target_root / relative
            wanted.add(target.resolve())
            if source.suffix.lower() in {'.json', '.md', '.txt'}:
                _safe_atomic_write_text(target, source.read_text(encoding='utf-8'))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        if remove_extras and target_root.exists():
            for existing in sorted((p for p in target_root.rglob('*') if p.is_file()), reverse=True):
                if existing.resolve() not in wanted:
                    try:
                        existing.unlink()
                    except PermissionError:
                        pass
            for folder in sorted((p for p in target_root.rglob('*') if p.is_dir()), key=lambda x: len(x.parts), reverse=True):
                try:
                    folder.rmdir()
                except OSError:
                    pass

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
            format_version=snapshot.format_version, sections=copy.deepcopy(snapshot.sections), metadata=copy.deepcopy(snapshot.metadata),
            extra_manifest=copy.deepcopy(snapshot.extra_manifest),
        )
        restored.metadata['last_used'] = datetime.now().timestamp()
        self._write_manifest_unchecked(restored)
        self._sync_snapshot_auxiliary_dir(live_book, snapshot, 'planning')
        self._sync_snapshot_auxiliary_dir(live_book, snapshot, 'publication')
        self._sync_snapshot_auxiliary_dir(live_book, snapshot, 'ai')
        # Media binaries are immutable. Restore the snapshot's manifest/cover and
        # referenced files, but never delete newer UUID assets automatically.
        self._sync_snapshot_auxiliary_dir(live_book, snapshot, 'assets', remove_extras=False)

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

    def _guard_future_planning_before_restore(self, book: Book):
        """Never roll a live newer Planning schema back through History."""
        # Local import avoids a module cycle: planning_validation depends on
        # CorruptSourceError from this module. Corrupt/invalid v1 data may still
        # be intentionally restored; only a *newer valid format marker* blocks
        # the whole restore.
        from .planning_validation import FuturePlanningFormatError, validate_planning_payload

        planning_root = book.path / 'planning'
        for kind, filename in (('scenes', 'outline.json'), ('characters', 'characters.json')):
            path = planning_root / filename
            if not path.exists():
                continue
            try:
                value = json.loads(path.read_text(encoding='utf-8-sig'))
                validate_planning_payload(kind, value, path)
            except FuturePlanningFormatError:
                raise
            except Exception:
                # History remains a valid explicit repair path for genuinely
                # corrupt/old-format Planning; those cases are not newer data.
                continue

    def restore_version(self, book: Book, version_id: str) -> Book:
        """Restore a snapshot with an automatic rollback checkpoint."""
        self._guard_future_planning_before_restore(book)
        self.verify_book_unchanged(book)
        snapshot = self.load_version(book, version_id)
        safety = self.create_version(book, kind='pre_restore')
        safety_snapshot = self.load_version(book, safety['id'])
        try:
            restored = self._apply_snapshot_to_live(book, snapshot)
            self._refresh_if_tracked(restored)
            return restored
        except Exception:
            # Best effort rollback to the byte-for-byte manuscript snapshot taken
            # just before restore. If Dropbox caused a transient lock the same
            # robust write path is used for the rollback as well.
            try:
                self._apply_snapshot_to_live(book, safety_snapshot)
            except Exception:
                pass
            raise

    def _chapter_trash_entry(self, chapter_path: Path) -> dict:
        chapter_path = Path(chapter_path)
        metadata_path = chapter_path.with_suffix('.json')
        data = {}
        if metadata_path.exists():
            try:
                loaded = json.loads(metadata_path.read_text(encoding='utf-8'))
                if isinstance(loaded, dict):
                    data = loaded
            except Exception:
                data = {}

        parts = chapter_path.stem.split('__', 2)
        fallback_id = parts[1] if len(parts) >= 2 else ''
        fallback_slug = parts[2] if len(parts) >= 3 else 'herstel-hoofdstuk'
        book_id = str(data.get('book_id') or chapter_path.parent.name)
        title = str(data.get('chapter_title') or fallback_slug.replace('-', ' ').strip().capitalize() or 'Hersteld hoofdstuk')
        try:
            deleted = float(data.get('deleted') or chapter_path.stat().st_mtime)
        except (TypeError, ValueError, OSError):
            deleted = 0.0
        return {
            'kind': 'chapter',
            'path': chapter_path,
            'metadata_path': metadata_path,
            'deleted': deleted,
            'book_id': book_id,
            'book_title': str(data.get('book_title') or ''),
            'chapter_id': str(data.get('chapter_id') or fallback_id or uuid.uuid4()),
            'title': title,
            'chapter_file': str(data.get('chapter_file') or ''),
            'section_id': str(data.get('section_id') or ''),
            'section_title': str(data.get('section_title') or ''),
            'section_index': data.get('section_index'),
            'chapter_index': data.get('chapter_index'),
        }

    def list_trashed_chapters(self) -> list[dict]:
        root = self.trash_dir / 'chapters'
        root.mkdir(parents=True, exist_ok=True)
        rows = []
        live_titles = {book.id: book.title for book in self.list_books()}
        trashed_titles = {}
        for row in self.list_trashed_books():
            try:
                trashed_titles[row['book'].id] = row['title']
            except Exception:
                pass
        for chapter_path in root.glob('*/*.md'):
            if not chapter_path.is_file():
                continue
            row = self._chapter_trash_entry(chapter_path)
            if not row['book_title']:
                row['book_title'] = live_titles.get(row['book_id']) or trashed_titles.get(row['book_id']) or row['book_id']
            row['book_available'] = row['book_id'] in live_titles
            rows.append(row)
        return sorted(rows, key=lambda r: r['deleted'], reverse=True)

    def _live_book_by_id(self, book_id: str) -> Book | None:
        return next((book for book in self.list_books() if book.id == book_id), None)

    def restore_trashed_chapter(self, trash_path: Path, book: Book | None = None) -> Chapter:
        trash_path = Path(trash_path)
        chapter_root = (self.trash_dir / 'chapters').resolve()
        if not trash_path.exists() or chapter_root not in trash_path.resolve().parents:
            raise FileNotFoundError('Het verwijderde hoofdstuk bestaat niet meer.')
        entry = self._chapter_trash_entry(trash_path)
        if book is not None and book.id != entry['book_id']:
            raise ValueError('Dit verwijderde hoofdstuk hoort bij een ander boek.')
        book = book or self._live_book_by_id(entry['book_id'])
        if book is None:
            raise RuntimeError('Herstel eerst het bijbehorende boek; daarna kan dit hoofdstuk worden teruggezet.')
        self.verify_book_unchanged(book)

        chapter_id = entry['chapter_id'] or str(uuid.uuid4())
        used_ids = {chapter.id for section in book.sections for chapter in section.chapters}
        target_file = book.path / f'chapters/{chapter_id}.md'
        if chapter_id in used_ids or target_file.exists():
            chapter_id = str(uuid.uuid4())
            target_file = book.path / f'chapters/{chapter_id}.md'
        chapter = Chapter(id=chapter_id, title=entry['title'] or 'Hersteld hoofdstuk', file=f'chapters/{chapter_id}.md')

        section = next((sec for sec in book.sections if sec.id == entry['section_id']), None)
        created_section = None
        if section is None and entry['section_id']:
            created_section = Section(id=entry['section_id'], title=entry['section_title'] or 'Herstelde sectie')
            try:
                section_index = int(entry['section_index'])
            except (TypeError, ValueError):
                section_index = len(book.sections)
            book.sections.insert(max(0, min(section_index, len(book.sections))), created_section)
            section = created_section
        elif section is None:
            if book.sections:
                section = book.sections[0]
            else:
                created_section = Section(id='root', title='Manuscript')
                book.sections.append(created_section)
                section = created_section

        try:
            chapter_index = int(entry['chapter_index'])
        except (TypeError, ValueError):
            chapter_index = len(section.chapters)
        chapter_index = max(0, min(chapter_index, len(section.chapters)))
        content = trash_path.read_text(encoding='utf-8')
        _safe_atomic_write_text(target_file, content)
        section.chapters.insert(chapter_index, chapter)
        try:
            self._write_manifest_unchecked(book)
        except Exception:
            if chapter in section.chapters:
                section.chapters.remove(chapter)
            if created_section is not None and not created_section.chapters and created_section in book.sections:
                book.sections.remove(created_section)
            try:
                target_file.unlink(missing_ok=True)
            except OSError:
                pass
            raise

        self._refresh_if_tracked(book)
        self.permanently_delete_trashed_chapter(trash_path)
        return chapter

    def permanently_delete_trashed_chapter(self, trash_path: Path):
        trash_path = Path(trash_path)
        chapter_root = (self.trash_dir / 'chapters').resolve()
        resolved = trash_path.resolve()
        if chapter_root not in resolved.parents:
            return
        metadata_path = trash_path.with_suffix('.json')
        for candidate in (trash_path, metadata_path):
            if candidate.exists():
                candidate.unlink()
        parent = trash_path.parent
        try:
            parent.rmdir()
        except OSError:
            pass

    def _purge_chapter_trash_for_book(self, book_id: str):
        if not book_id:
            return
        folder = self.trash_dir / 'chapters' / book_id
        if folder.exists():
            shutil.rmtree(folder)

    def delete_book(self, book: Book):
        """Verplaats een boek naar de prullenbak."""
        self.verify_book_unchanged(book)
        if not book.path.exists():
            self.untrack_book(book)
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
        # Keep optimistic-concurrency protection active until the destructive
        # move has actually succeeded. A Windows/Dropbox sharing violation must
        # never leave an open live book silently untracked.
        self.untrack_book(book)

    def list_trashed_books(self) -> list[dict]:
        root = self.trash_dir / 'books'
        root.mkdir(parents=True, exist_ok=True)
        rows = []
        for folder in root.iterdir():
            if not folder.is_dir() or not (folder / 'book.json').exists():
                continue
            try:
                book = self.load_book(folder)
                rows.append({'kind': 'book', 'path': folder, 'title': book.title, 'deleted': folder.stat().st_mtime, 'book': book, 'book_id': book.id})
            except Exception:
                continue
        return sorted(rows, key=lambda r: r['deleted'], reverse=True)

    def restore_trashed_book(self, trash_path: Path) -> Book:
        trash_path = Path(trash_path)
        trashed_book = self.load_book(trash_path)
        for existing in self.list_books():
            if existing.id == trashed_book.id:
                raise RuntimeError(tr(
                    'storage.restore_duplicate_identity',
                    'Een boek met dezelfde identiteit staat al op de boekenplank. Verwijder dat boek eerst of laat dit boek in de prullenbak.',
                ))
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
        book_id = ''
        try:
            data = json.loads((trash_path / 'book.json').read_text(encoding='utf-8'))
            book_id = str(data.get('id') or '') if isinstance(data, dict) else ''
        except Exception:
            pass
        if trash_path.exists() and self.trash_dir in trash_path.parents:
            shutil.rmtree(trash_path)
            self._purge_chapter_trash_for_book(book_id)

    def empty_trash(self):
        errors = []
        for root in (self.trash_dir / 'books', self.trash_dir / 'chapters'):
            if not root.exists():
                continue
            for p in list(root.iterdir()):
                try:
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
                except OSError as exc:
                    errors.append(f'{p.name}: {exc}')
        if errors:
            raise OSError('Niet alle onderdelen van de prullenbak konden worden verwijderd:\n' + '\n'.join(errors))

    def remove_cover(self, book: Book):
        self.verify_book_unchanged(book)
        stored = (book.metadata.get('cover_file') or '').strip()
        candidates: list[Path] = []
        if stored:
            stored_path = Path(stored)
            candidates.append((book.path / stored_path) if len(stored_path.parts) > 1 else (self.covers_dir / stored_path))
        # Local 0.20+ covers belong unambiguously to this book. Never delete a
        # global cover merely because its filename happens to match this book's
        # slug; same-title books may coexist.
        local_cover = book.path / 'assets' / 'cover'
        for ext in self.COVER_EXTENSIONS:
            candidates.append(local_cover / f'cover{ext}')
        for candidate in dict.fromkeys(candidates):
            if candidate.exists():
                try:
                    candidate.unlink()
                except OSError:
                    pass
        book.metadata['cover_file'] = ''
        self._write_manifest_unchecked(book)
        self._refresh_if_tracked(book)

    def import_markdown_book(self, source: Path) -> Book:
        """Import external Markdown through the neutral import model.

        Markdown is an interchange format here, not QuietWriter's canonical
        manuscript parser. The complete book is staged and only published after
        every chapter has been serialized successfully.
        """
        from .markdown_io import read_markdown_import_document

        source = Path(source)
        imported = read_markdown_import_document(source)
        book, _warnings = self._import_neutral_document(imported, source)
        return book


    def _new_staged_import_book(self, title: str) -> tuple[Book, Path]:
        """Create an unpublished book tree beside the live books directory.

        The staging folder deliberately lives under ``books/`` so the final
        directory rename stays on the same filesystem. Hidden staging folders
        are ignored by :meth:`list_books` and are removed on every handled
        failure before an import can become visible to the user.
        """
        book_id = str(uuid.uuid4())
        clean_title = title.strip() or 'Naamloos boek'
        final_path = self.books_dir / f'{slugify(clean_title)}-{book_id[:8]}'
        stage_path = self.books_dir / f'.import-{book_id}'
        (stage_path / 'chapters').mkdir(parents=True, exist_ok=False)
        (stage_path / 'assets' / 'images').mkdir(parents=True, exist_ok=True)
        (stage_path / 'assets' / 'cover').mkdir(parents=True, exist_ok=True)
        _safe_atomic_write_text(
            stage_path / 'assets' / 'manifest.json',
            json.dumps({'version': 1, 'images': {}}, ensure_ascii=False, indent=2),
        )
        book = Book(
            id=book_id,
            title=clean_title,
            path=stage_path,
            extra_manifest={MANUSCRIPT_SYNTAX_KEY: current_manifest_value()},
            metadata={
                'slug': slugify(clean_title),
                'date': datetime.now().isoformat(timespec='minutes'),
                'description': '',
                'intro': '',
                'meta': '',
                'image': '',
                'image_alt': '',
                'author': '',
                'language': 'nl',
                'tags': '',
                'published': 'No',
                'synopsis': '',
                'cover_file': '',
                'last_used': datetime.now().timestamp(),
            },
        )
        return book, final_path

    def _publish_staged_import(self, book: Book, final_path: Path) -> Book:
        """Atomically make a complete staged book visible in the library."""
        final_path = Path(final_path)
        if final_path.exists():
            raise FileExistsError(f'Doelmap voor import bestaat al: {final_path}')
        # Validate the complete staged manifest before it can become visible.
        staged = self.load_book(book.path)
        missing = [
            chapter.file
            for section in staged.sections
            for chapter in section.chapters
            if not (staged.path / chapter.file).is_file()
        ]
        if missing:
            raise StorageWriteError(book.path, OSError(f'Ontbrekende hoofdstukbestanden: {", ".join(missing)}'))
        os.replace(book.path, final_path)
        book.path = final_path
        return book

    def _import_neutral_document(self, imported, source: Path):
        """Stage and atomically publish one neutral ImportDocument."""
        from .import_document import serialize_import_chapter
        from .media.store import MediaStore

        source = Path(source)
        title = (imported.title or source.stem).strip() or source.stem
        book, final_path = self._new_staged_import_book(title)
        stage_path = book.path
        try:
            metadata = dict(getattr(imported, 'metadata', {}) or {})
            known = {
                'slug', 'date', 'description', 'intro', 'meta', 'image',
                'image_alt', 'author', 'language', 'tags', 'published',
                'synopsis', 'cover', 'featured_image',
            }
            for key in known:
                value = metadata.get(key)
                if value not in (None, ''):
                    book.metadata[key] = value
            if imported.author:
                book.metadata['author'] = imported.author
            if imported.language:
                book.metadata['language'] = imported.language
            extra = {k: v for k, v in metadata.items() if k not in known and k != 'title'}
            if extra:
                book.metadata['extra'] = extra
            book.metadata['slug'] = slugify(book.metadata.get('slug') or title)
            book.metadata['source_file'] = str(source)
            book.metadata['last_used'] = datetime.now().timestamp()

            media_store = MediaStore(self)
            imported_assets = {}
            for asset in imported.assets:
                imported_assets[asset.key] = media_store.import_image_bytes(
                    book, asset.data, asset.filename, verify_revision=False
                )

            sections = imported.sections or ()
            for idx, imported_section in enumerate(sections):
                section_title = imported_section.title
                sec_id = 'root' if len(sections) == 1 and not section_title else str(uuid.uuid4())
                sec = Section(
                    id=sec_id,
                    title=section_title or ('Manuscript' if sec_id == 'root' else f'Sectie {idx+1}'),
                )
                book.sections.append(sec)
                for imported_chapter in imported_section.chapters:
                    cid = str(uuid.uuid4())
                    chapter = Chapter(
                        id=cid,
                        title=(imported_chapter.title or tr('storage.default_chapter', 'Hoofdstuk')).strip()
                              or tr('storage.default_chapter', 'Hoofdstuk'),
                        file=f'chapters/{cid}.md',
                    )
                    sec.chapters.append(chapter)
                    image_refs = {
                        key: media_store.reference_for_chapter(chapter, media_asset)
                        for key, media_asset in imported_assets.items()
                    }
                    chapter_source = serialize_import_chapter(imported_chapter, image_refs=image_refs)
                    _safe_atomic_write_text(book.path / chapter.file, chapter_source)

            if not any(sec.chapters for sec in book.sections):
                if not book.sections:
                    book.sections = [Section(id='root', title='Manuscript')]
                cid = str(uuid.uuid4())
                chapter = Chapter(id=cid, title=title, file=f'chapters/{cid}.md')
                book.sections[0].chapters.append(chapter)
                _safe_atomic_write_text(book.path / chapter.file, '')

            self._write_manifest_unchecked(book)
            published = self._publish_staged_import(book, final_path)
            return published, tuple(imported.warnings or ())
        except Exception:
            if stage_path.exists():
                shutil.rmtree(stage_path, ignore_errors=True)
            raise


    def import_docx_book(self, source: Path):
        """Import DOCX transactionally through the neutral import model."""
        from .docx_io import read_docx_import_document

        source = Path(source)
        imported = read_docx_import_document(source)
        return self._import_neutral_document(imported, source)

    def export_markdown_book(self, book: Book, destination: Path, image_ref: str = '', include_frontmatter: bool = True,
                             include_section_markers: bool = True) -> Path:
        from .markdown_io import export_book_markdown
        return export_book_markdown(self, book, destination, image_ref=image_ref,
                                    include_frontmatter=include_frontmatter, include_section_markers=include_section_markers)

    def cover_path(self, book: Book) -> Path | None:
        stored = (book.metadata.get('cover_file') or '').strip()
        if stored:
            stored_path = Path(stored)
            candidate = (book.path / stored_path) if len(stored_path.parts) > 1 else (self.covers_dir / stored_path)
            if candidate.exists():
                return candidate
        # 0.20+: book-local cover. Legacy global ownership is resolved once in
        # ``load_book`` only for manifests that predate ``cover_file``. There is
        # deliberately no slug-based fallback here: a new same-title book must
        # never adopt another book's global cover by coincidence.
        for ext in self.COVER_EXTENSIONS:
            candidate = book.path / 'assets' / 'cover' / f'cover{ext}'
            if candidate.exists():
                return candidate
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
        self.verify_book_unchanged(book)
        cover_dir = book.path / 'assets' / 'cover'
        cover_dir.mkdir(parents=True, exist_ok=True)
        target = cover_dir / f'cover{ext}'
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        for other_ext in self.COVER_EXTENSIONS:
            other = cover_dir / f'cover{other_ext}'
            if other != target and other.exists():
                try:
                    other.unlink()
                except OSError:
                    pass
        book.metadata['cover_file'] = target.relative_to(book.path).as_posix()
        self._write_manifest_unchecked(book)
        self._refresh_if_tracked(book)
        return target

    def rename_cover_for_slug(self, book: Book, old_slug: str, new_slug: str):
        # Kept as a compatibility hook for older callers. Covers are no longer
        # physically renamed with the book slug: 0.20+ covers are book-local,
        # while a legacy global cover now has explicit ``cover_file`` ownership.
        # Keeping that legacy filename stable also avoids collisions when two
        # books use the same slug.
        return

    def save_book_details(self, live_book: Book, candidate: Book, pending_cover=None):
        """Commit metadata/cover edits without mutating ``live_book`` first.

        Cover files are staged before the manifest write and restored if the
        guarded manifest commit fails. Only the caller adopts ``candidate`` into
        the shared live object after this method returns successfully.
        """
        self.verify_book_unchanged(live_book)

        local_dir = live_book.path / 'assets' / 'cover'
        managed: set[Path] = {local_dir / f'cover{ext}' for ext in self.COVER_EXTENSIONS}
        stored = (live_book.metadata.get('cover_file') or '').strip()
        if stored:
            stored_path = Path(stored)
            managed.add((live_book.path / stored_path) if len(stored_path.parts) > 1 else (self.covers_dir / stored_path))

        source = Path(pending_cover) if isinstance(pending_cover, Path) else None
        if source is not None:
            ext = source.suffix.lower()
            if ext not in self.COVER_EXTENSIONS:
                raise ValueError('Ondersteunde formaten: JPG, JPEG, PNG en WEBP.')
            managed.add(local_dir / f'cover{ext}')

        with tempfile.TemporaryDirectory(prefix='quietwriter-cover-') as td:
            backup_root = Path(td)
            backups: dict[Path, Path] = {}
            for index, path in enumerate(sorted(managed, key=lambda item: str(item))):
                if path.exists():
                    backup = backup_root / f'{index}{path.suffix.lower()}'
                    shutil.copy2(path, backup)
                    backups[path] = backup

            def rollback_cover_files():
                for path in managed:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
                for path, backup in backups.items():
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, path)
                    except OSError:
                        pass

            try:
                if pending_cover == '__REMOVE__':
                    for path in managed:
                        path.unlink(missing_ok=True)
                    candidate.metadata['cover_file'] = ''
                elif source is not None:
                    local_dir.mkdir(parents=True, exist_ok=True)
                    target = local_dir / f'cover{source.suffix.lower()}'
                    if source.resolve() != target.resolve():
                        shutil.copy2(source, target)
                    for ext in self.COVER_EXTENSIONS:
                        other = local_dir / f'cover{ext}'
                        if other != target:
                            other.unlink(missing_ok=True)
                    candidate.metadata['cover_file'] = target.relative_to(candidate.path).as_posix()

                # Verify again immediately before the authoritative manifest
                # write so an external edit that arrived while staging the cover
                # is still surfaced as a normal conflict.
                self.save_manifest(candidate)
            except Exception:
                rollback_cover_files()
                raise


    def book_profile_path(self, book: Book) -> Path:
        return Path(book.path) / 'ai' / 'boekprofiel.md'

    def read_book_profile(self, book: Book) -> str:
        path = self.book_profile_path(book)
        if not path.exists():
            return default_book_profile_markdown()
        return path.read_text(encoding='utf-8')

    def save_book_profile(self, book: Book, text: str):
        self.verify_book_unchanged(book)
        _guard_existing_utf8(self.book_profile_path(book))
        _safe_atomic_write_text(self.book_profile_path(book), text)
        self._refresh_if_tracked(book)

    def book_memory_path(self, book: Book) -> Path:
        return Path(book.path) / 'ai' / 'memory.md'

    def read_book_memory(self, book: Book) -> str:
        path = self.book_memory_path(book)
        if not path.exists():
            return default_book_memory_markdown()
        return path.read_text(encoding='utf-8')

    def save_book_memory(self, book: Book, text: str):
        self.verify_book_unchanged(book)
        _guard_existing_utf8(self.book_memory_path(book))
        _safe_atomic_write_text(self.book_memory_path(book), text)
        self._refresh_if_tracked(book)

    def persona_path(self) -> Path:
        return self.persona_dir / 'schrijver.md'

    def capture_persona_revision(self) -> FileRevision | None:
        return file_revision(self.persona_path())

    def read_persona(self) -> str:
        path = self.persona_path()
        if not path.exists():
            return default_persona_markdown()
        return path.read_text(encoding='utf-8')

    def create_persona_recovery(self, text: str, *, kind: str = 'conflict_local') -> Path:
        """Store a global persona recovery copy outside the live persona file."""
        root = self.archive_dir / 'persona'
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')
        target = root / f'{stamp}__{kind}.md'
        counter = 2
        while target.exists():
            target = root / f'{stamp}-{counter}__{kind}.md'
            counter += 1
        _safe_atomic_write_text(target, text)
        return target

    def save_persona(
        self,
        text: str,
        *,
        expected_revision: FileRevision | None | object = _UNSET_REVISION,
    ):
        path = self.persona_path()
        _guard_existing_utf8(path)
        current = file_revision(path)
        if expected_revision is not _UNSET_REVISION and current != expected_revision:
            raise PersonaExternalModificationError(path, expected_revision, current)
        _safe_atomic_write_text(path, text)
        return file_revision(path)
