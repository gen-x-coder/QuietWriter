from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .markdown_io import split_frontmatter
from .revisions import FileRevision, file_revision
from .storage import CorruptSourceError, _guard_existing_utf8, _safe_atomic_write_text


FRAGMENT_SCHEMA_VERSION = 1
_FRAGMENT_ID_RE = re.compile(r'^[A-Za-z0-9-]+$')


@dataclass(frozen=True)
class Fragment:
    id: str
    created_at: str
    text: str
    source_book_id: str = ''
    source_book_title: str = ''
    source_chapter_id: str = ''
    source_chapter_title: str = ''
    source_before: str = ''
    source_after: str = ''
    title: str = ''
    note: str = ''
    tags: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = FRAGMENT_SCHEMA_VERSION
    revision: FileRevision | None = field(default=None, compare=False, repr=False)

    @property
    def display_title(self) -> str:
        if self.title.strip():
            return self.title.strip()
        first = next((line.strip() for line in self.text.splitlines() if line.strip()), '')
        # Storage should not own translated UI copy. The UI may replace this
        # empty fallback with a locale-specific label.
        return first[:80]


class FragmentFormatError(ValueError):
    """Raised when an existing fragment cannot be parsed safely."""


class FutureFragmentFormatError(FragmentFormatError):
    """Raised when a fragment uses a newer schema than this QuietWriter build."""


class FragmentExternalModificationError(RuntimeError):
    """Raised before metadata save when a loaded fragment changed on disk."""

    def __init__(
        self,
        path: Path,
        expected: FileRevision | None,
        current: FileRevision | None,
    ):
        self.path = Path(path)
        self.expected = expected
        self.current = current
        super().__init__(f'Fragment is buiten QuietWriter gewijzigd: {self.path.name}')


class FragmentStore:
    """Workspace-level storage for Darlings.

    One Markdown file per fragment is authoritative. No monolithic index is
    written, which keeps sync conflicts local to a single fragment.
    """

    def __init__(self, workspace_root: Path):
        self.root = Path(workspace_root)
        self.fragments_dir = self.root / 'fragments'
        self.trash_dir = self.root / 'trash' / 'fragments'
        self.last_list_errors: list[dict] = []
        self.last_trash_list_errors: list[dict] = []

    @staticmethod
    def _now_iso() -> str:
        # UTC makes lexical/chronological ordering stable across DST changes and
        # machines in different time zones.
        return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

    @staticmethod
    def _sort_datetime(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return datetime.min.replace(tzinfo=timezone.utc)

    @staticmethod
    def _validate_fragment_id(fragment_id: str) -> str:
        value = str(fragment_id or '')
        if not _FRAGMENT_ID_RE.fullmatch(value):
            raise FragmentFormatError('Ongeldig fragment-id.')
        return value

    @staticmethod
    def _normalize_tags(tags) -> tuple[str, ...]:
        seen: set[str] = set()
        result: list[str] = []
        for raw in tags or ():
            value = str(raw).strip()
            key = value.casefold()
            if value and key not in seen:
                seen.add(key)
                result.append(value)
        return tuple(result)

    @staticmethod
    def _quoted(value: str) -> str:
        # JSON string syntax is valid for the simple frontmatter decoder already
        # used by QuietWriter and safely handles quotes, colons and newlines.
        return json.dumps(str(value or ''), ensure_ascii=False)

    @classmethod
    def _render(cls, fragment: Fragment) -> str:
        tags_json = json.dumps(list(fragment.tags), ensure_ascii=False, separators=(',', ':'))
        rows = [
            f'fragment_schema_version: {fragment.schema_version}',
            f'id: {cls._quoted(fragment.id)}',
            f'created_at: {cls._quoted(fragment.created_at)}',
            f'source_book_id: {cls._quoted(fragment.source_book_id)}',
            f'source_book_title: {cls._quoted(fragment.source_book_title)}',
            f'source_chapter_id: {cls._quoted(fragment.source_chapter_id)}',
            f'source_chapter_title: {cls._quoted(fragment.source_chapter_title)}',
            f'source_before: {cls._quoted(fragment.source_before)}',
            f'source_after: {cls._quoted(fragment.source_after)}',
            f'title: {cls._quoted(fragment.title)}',
            f'note: {cls._quoted(fragment.note)}',
            f'tags_json: {tags_json}',
        ]
        return '---\n' + '\n'.join(rows) + '\n---\n\n' + fragment.text

    @staticmethod
    def _exact_body(text: str, path: Path | None = None) -> str:
        """Return the fragment body without trimming source whitespace.

        ``split_frontmatter`` deliberately normalizes/strips the body for book
        import. Darlings need byte-faithful LF text, including leading/trailing
        blank lines, so only metadata is delegated to that parser.
        """
        if not text.startswith('---\n'):
            raise FragmentFormatError(f'Fragmentmetadata ontbreekt of is ongeldig in {path or "fragment"}.')
        closing = text.find('\n---\n', 4)
        if closing < 0:
            raise FragmentFormatError(f'Fragmentmetadata ontbreekt of is ongeldig in {path or "fragment"}.')
        body_start = closing + len('\n---\n')
        # The storage format has exactly one separator newline after the closing
        # delimiter. That separator is not part of the user's fragment text.
        if body_start < len(text) and text[body_start] == '\n':
            body_start += 1
        return text[body_start:]

    @classmethod
    def _parse(
        cls,
        text: str,
        path: Path | None = None,
        *,
        revision: FileRevision | None = None,
    ) -> Fragment:
        metadata, _ = split_frontmatter(text)
        body = cls._exact_body(text, path)
        try:
            version = int(metadata.get('fragment_schema_version', '0'))
        except (TypeError, ValueError) as exc:
            raise FragmentFormatError(f'Ongeldige fragmentversie in {path or "fragment"}.') from exc
        if version < 1:
            raise FragmentFormatError(f'Fragmentmetadata ontbreekt of is ongeldig in {path or "fragment"}.')
        if version > FRAGMENT_SCHEMA_VERSION:
            raise FutureFragmentFormatError(
                f'Fragment gebruikt formaat {version}; deze QuietWriter ondersteunt maximaal {FRAGMENT_SCHEMA_VERSION}.'
            )
        fragment_id = cls._validate_fragment_id(str(metadata.get('id', '')).strip())
        created_at = str(metadata.get('created_at', '')).strip()
        if not created_at:
            raise FragmentFormatError(f'Verplichte fragmentmetadata ontbreekt in {path or "fragment"}.')
        try:
            datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError as exc:
            raise FragmentFormatError(f'Ongeldige aanmaaktijd in {path or "fragment"}.') from exc
        try:
            tags_raw = json.loads(metadata.get('tags_json', '[]') or '[]')
        except (json.JSONDecodeError, TypeError) as exc:
            raise FragmentFormatError(f'Ongeldige tags in {path or "fragment"}.') from exc
        if not isinstance(tags_raw, list) or not all(isinstance(item, str) for item in tags_raw):
            raise FragmentFormatError(f'Ongeldige tags in {path or "fragment"}.')
        return Fragment(
            id=fragment_id,
            created_at=created_at,
            text=body,
            source_book_id=str(metadata.get('source_book_id', '')),
            source_book_title=str(metadata.get('source_book_title', '')),
            source_chapter_id=str(metadata.get('source_chapter_id', '')),
            source_chapter_title=str(metadata.get('source_chapter_title', '')),
            source_before=str(metadata.get('source_before', '')),
            source_after=str(metadata.get('source_after', '')),
            title=str(metadata.get('title', '')),
            note=str(metadata.get('note', '')),
            tags=cls._normalize_tags(tags_raw),
            schema_version=version,
            revision=revision,
        )

    def path_for(self, fragment_id: str) -> Path:
        safe_id = self._validate_fragment_id(fragment_id)
        return self.fragments_dir / f'{safe_id}.md'

    def create(
        self,
        text: str,
        *,
        source_book_id: str = '',
        source_book_title: str = '',
        source_chapter_id: str = '',
        source_chapter_title: str = '',
        source_before: str = '',
        source_after: str = '',
        title: str = '',
        note: str = '',
        tags=(),
        fragment_id: str | None = None,
        created_at: str | None = None,
    ) -> Fragment:
        if not isinstance(text, str) or not text:
            raise ValueError('Een Darling kan niet leeg zijn.')
        safe_id = self._validate_fragment_id(fragment_id or str(uuid.uuid4()))
        fragment = Fragment(
            id=safe_id,
            created_at=created_at or self._now_iso(),
            text=text,
            source_book_id=str(source_book_id or ''),
            source_book_title=str(source_book_title or ''),
            source_chapter_id=str(source_chapter_id or ''),
            source_chapter_title=str(source_chapter_title or ''),
            source_before=str(source_before or ''),
            source_after=str(source_after or ''),
            title=str(title or ''),
            note=str(note or ''),
            tags=self._normalize_tags(tags),
        )
        path = self.path_for(fragment.id)
        if path.exists():
            raise FileExistsError(path)
        self.fragments_dir.mkdir(parents=True, exist_ok=True)
        _safe_atomic_write_text(path, self._render(fragment))
        # Verify what was committed is readable before returning success.
        return self.load(fragment.id)

    def load(self, fragment_id: str) -> Fragment:
        path = self.path_for(fragment_id)
        return self.load_path(path)

    def load_path(self, path: Path) -> Fragment:
        path = Path(path)
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError as exc:
            raise CorruptSourceError(path) from exc
        revision = file_revision(path)
        fragment = self._parse(text, path, revision=revision)
        if path.stem != fragment.id:
            raise FragmentFormatError(f'Fragment-id komt niet overeen met bestandsnaam: {path.name}.')
        return fragment

    def list_fragments(self) -> list[Fragment]:
        self.last_list_errors = []
        items: list[Fragment] = []
        for path in sorted(self.fragments_dir.glob('*.md')):
            try:
                items.append(self.load_path(path))
            except (CorruptSourceError, FragmentFormatError, OSError, UnicodeError) as exc:
                self.last_list_errors.append({'path': path, 'error': exc})
        return sorted(items, key=lambda item: self._sort_datetime(item.created_at), reverse=True)

    def search(self, query: str = '', *, tag: str = '') -> list[Fragment]:
        query_cf = str(query or '').strip().casefold()
        tag_cf = str(tag or '').strip().casefold()
        result = []
        for fragment in self.list_fragments():
            if tag_cf and not any(t.casefold() == tag_cf for t in fragment.tags):
                continue
            haystack = '\n'.join((
                fragment.title,
                fragment.note,
                fragment.text,
                fragment.source_book_title,
                fragment.source_chapter_title,
                ' '.join(fragment.tags),
            )).casefold()
            if query_cf and query_cf not in haystack:
                continue
            result.append(fragment)
        return result

    def update_metadata(
        self,
        fragment_id: str,
        *,
        expected_revision: FileRevision | None,
        title: str | None = None,
        note: str | None = None,
        tags=None,
    ) -> Fragment:
        current = self.load(fragment_id)
        path = self.path_for(fragment_id)
        if current.revision != expected_revision:
            raise FragmentExternalModificationError(path, expected_revision, current.revision)
        updated = Fragment(
            id=current.id,
            created_at=current.created_at,
            text=current.text,
            source_book_id=current.source_book_id,
            source_book_title=current.source_book_title,
            source_chapter_id=current.source_chapter_id,
            source_chapter_title=current.source_chapter_title,
            source_before=current.source_before,
            source_after=current.source_after,
            title=current.title if title is None else str(title),
            note=current.note if note is None else str(note),
            tags=current.tags if tags is None else self._normalize_tags(tags),
            schema_version=current.schema_version,
        )
        _guard_existing_utf8(path)
        # Guard again directly before the write so a sync change between load
        # and commit cannot be silently overwritten.
        latest = file_revision(path)
        if latest != expected_revision:
            raise FragmentExternalModificationError(path, expected_revision, latest)
        _safe_atomic_write_text(path, self._render(updated))
        return self.load(fragment_id)

    def move_to_trash(self, fragment_id: str) -> Path:
        source = self.path_for(fragment_id)
        # Parse before moving so corrupt/future-format data is never silently
        # transformed by a normal user action.
        self.load(fragment_id)
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        target = self.trash_dir / source.name
        if target.exists():
            target = self.trash_dir / f'{fragment_id}__{uuid.uuid4().hex[:8]}.md'
        shutil.move(str(source), str(target))
        return target

    def list_trashed(self) -> list[tuple[Path, Fragment]]:
        self.last_trash_list_errors = []
        result: list[tuple[Path, Fragment]] = []
        for path in sorted(self.trash_dir.glob('*.md')):
            try:
                text = path.read_text(encoding='utf-8')
                fragment = self._parse(text, path, revision=file_revision(path))
                result.append((path, fragment))
            except (CorruptSourceError, FragmentFormatError, OSError, UnicodeError) as exc:
                self.last_trash_list_errors.append({'path': path, 'error': exc})
        return sorted(result, key=lambda row: self._sort_datetime(row[1].created_at), reverse=True)

    def restore(self, trash_path: Path) -> Fragment:
        trash_path = Path(trash_path)
        root = self.trash_dir.resolve()
        resolved = trash_path.resolve()
        if not trash_path.exists() or root not in resolved.parents:
            raise ValueError('Dit bestand staat niet in de fragmentprullenbak.')
        try:
            text = trash_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as exc:
            raise CorruptSourceError(trash_path) from exc
        fragment = self._parse(text, trash_path, revision=file_revision(trash_path))
        target = self.path_for(fragment.id)
        if target.exists():
            raise FileExistsError(target)
        self.fragments_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(trash_path), str(target))
        return self.load(fragment.id)

    def permanently_delete(self, trash_path: Path) -> None:
        trash_path = Path(trash_path)
        root = self.trash_dir.resolve()
        resolved = trash_path.resolve()
        if not trash_path.exists() or root not in resolved.parents:
            raise ValueError('Dit bestand staat niet in de fragmentprullenbak.')
        trash_path.unlink()
