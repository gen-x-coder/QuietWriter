from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FileRevision:
    """Content identity for one manuscript file.

    mtime is intentionally not part of equality. Sync/restore tools may preserve
    timestamps while replacing content, or change timestamps without changing
    content. Size + SHA-256 are the revision identity; mtime is diagnostic only.
    """

    size: int
    sha256: str
    mtime_ns: int | None = field(default=None, compare=False)


@dataclass(frozen=True)
class BookRevision:
    files: dict[str, FileRevision | None]

    def changed_files(self, other: "BookRevision") -> list[str]:
        keys = set(self.files) | set(other.files)
        return sorted(
            key for key in keys
            if (key not in self.files) or (key not in other.files) or self.files[key] != other.files[key]
        )


class RevisionVerificationError(OSError):
    """The current revision could not be verified reliably."""

    def __init__(self, path: Path, cause: BaseException):
        super().__init__(f'Kan de actuele versie van {path} niet betrouwbaar controleren: {cause}')
        self.path = Path(path)
        self.__cause__ = cause


class ExternalModificationError(RuntimeError):
    """Raised before a write when the tracked book changed on disk."""

    def __init__(self, book_id: str, changed_files: list[str], expected: BookRevision, current: BookRevision):
        self.book_id = book_id
        self.changed_files = tuple(changed_files)
        self.expected = expected
        self.current = current
        names = ', '.join(changed_files[:4]) or 'onbekend bestand'
        if len(changed_files) > 4:
            names += f' (+{len(changed_files) - 4})'
        super().__init__(f'Boek is buiten QuietWriter gewijzigd: {names}')


def _sha256_file(path: Path, retries: int = 4) -> FileRevision:
    delay = 0.04
    last_exc: BaseException | None = None
    for _ in range(max(1, retries)):
        try:
            stat = path.stat()
            digest = hashlib.sha256()
            with path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                    digest.update(chunk)
            # Stat once more so a file replaced while hashing is not silently
            # accepted as one coherent revision.
            after = path.stat()
            if stat.st_size != after.st_size or stat.st_mtime_ns != after.st_mtime_ns:
                raise OSError('Bestand veranderde tijdens revision-controle.')
            return FileRevision(size=after.st_size, sha256=digest.hexdigest(), mtime_ns=after.st_mtime_ns)
        except FileNotFoundError:
            raise
        except (PermissionError, OSError) as exc:
            last_exc = exc
            time.sleep(delay)
            delay = min(delay * 1.8, 0.35)
    raise RevisionVerificationError(path, last_exc or OSError('Onbekende leesfout'))


def file_revision(path: Path) -> FileRevision | None:
    path = Path(path)
    try:
        return _sha256_file(path)
    except FileNotFoundError:
        return None


def book_file_names(book_path: Path, chapter_files: Iterable[str]) -> set[str]:
    """Return all manuscript files relevant to one book revision.

    Besides files referenced by the in-memory manifest, include existing chapter
    files. This also detects externally added/removed chapter files that the
    current in-memory manifest does not know about yet.
    """

    names = {'book.json'}
    names.update(str(Path(name).as_posix()) for name in chapter_files)
    chapters_dir = Path(book_path) / 'chapters'
    if chapters_dir.exists():
        for path in chapters_dir.rglob('*.md'):
            try:
                names.add(path.relative_to(book_path).as_posix())
            except ValueError:
                pass
    return names


def capture_book_revision(book_path: Path, chapter_files: Iterable[str]) -> BookRevision:
    book_path = Path(book_path)
    revisions: dict[str, FileRevision | None] = {}
    for relative in sorted(book_file_names(book_path, chapter_files)):
        revisions[relative] = file_revision(book_path / relative)
    return BookRevision(revisions)
