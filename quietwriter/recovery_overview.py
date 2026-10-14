"""Read-only overview of multi-chapter replacement recovery archives.

The overview never opens manuscript contents or changes a recovery journal.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class RecoveryEntry:
    location: Path
    book_id: str
    status: str
    copies: int
    note: str = ''


def list_replacement_recoveries(archive_dir: Path, *, book_id: str | None = None) -> list[RecoveryEntry]:
    """Inspect journals, treating malformed records as requiring attention.

    A missing/corrupt journal must never cause its copies to be removed.
    """
    root = Path(archive_dir)
    if not root.is_dir() or root.is_symlink():
        return []
    found = []
    for book in sorted(root.iterdir()):
        if not book.is_dir() or book.is_symlink() or (book_id is not None and book.name != book_id):
            continue
        for folder in sorted(book.glob('replace-recovery-*')):
            if not folder.is_dir() or folder.is_symlink():
                continue
            copies = sum(1 for p in folder.iterdir() if p.is_file() and not p.is_symlink() and p.name.endswith('.original'))
            status = 'attention'
            note = 'Journaal ontbreekt of is niet leesbaar'
            try:
                path = folder / 'transaction.json'
                if path.is_symlink():
                    raise ValueError('Symlink journal')
                payload = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(payload, dict) or payload.get('schema') != 1 or payload.get('book') != book.name:
                    raise ValueError('Unexpected journal identity')
                if payload.get('status') not in {'pending', 'recovered', 'committed'}:
                    raise ValueError('Unknown journal status')
                if not isinstance(payload.get('files'), list):
                    raise ValueError('Unknown file list')
                status = payload['status']
                note = ''
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError):
                pass
            found.append(RecoveryEntry(folder, book.name, status, copies, note))
    return found


@dataclass(frozen=True)
class RecoveryComparison:
    chapter: str
    original: str
    current: str
    state: str


def compare_recovery_files(folder: Path, book_folder: Path, *, max_bytes: int = 1_000_000) -> list[RecoveryComparison]:
    """Bounded, read-only comparison; reject unsafe paths and altered backups."""
    import hashlib
    from pathlib import PurePosixPath

    folder, book_folder = Path(folder), Path(book_folder)
    if folder.is_symlink() or book_folder.is_symlink() or not folder.is_dir() or not book_folder.is_dir():
        raise ValueError('Unsafe recovery location')
    journal = folder / 'transaction.json'
    if journal.is_symlink() or journal.stat().st_size > 2_000_000:
        raise ValueError('Unsafe recovery journal')
    record = json.loads(journal.read_text(encoding='utf-8'))
    if not isinstance(record, dict) or record.get('schema') != 1 or record.get('book') != book_folder.name or not isinstance(record.get('files'), list):
        raise ValueError('Invalid recovery journal')
    if len(record['files']) > 20:
        raise ValueError('Recovery contains too many entries')
    result = []
    for item in record['files']:
        if not isinstance(item, dict):
            raise ValueError('Invalid chapter record')
        name, backup_name = item.get('name'), item.get('backup')
        if not isinstance(name, str) or not isinstance(backup_name, str):
            raise ValueError('Invalid chapter path')
        rel = PurePosixPath(name)
        if (rel.is_absolute() or len(rel.parts) != 2 or rel.parts[0] != 'chapters' or
                any(part in ('', '.', '..') or '\\' in part or ':' in part for part in rel.parts) or
                not rel.parts[1].endswith('.md')):
            raise ValueError('Unsafe chapter path')
        if Path(backup_name).name != backup_name or not backup_name.endswith('.original') or '/' in backup_name or '\\' in backup_name:
            raise ValueError('Unsafe backup path')
        backup = folder / backup_name
        chapter_dir = book_folder / 'chapters'
        current = chapter_dir / rel.parts[1]
        if backup.is_symlink() or chapter_dir.is_symlink() or current.is_symlink() or folder.parent.is_symlink():
            raise ValueError('Linked files are not compared')
        if not backup.is_file() or backup.stat().st_size > max_bytes:
            raise ValueError('Original is unavailable or too large for preview')
        old_data = backup.read_bytes()
        if hashlib.sha256(old_data).hexdigest() != item.get('old_sha256'):
            raise ValueError('Original recovery copy differs from journal')
        if current.is_file():
            if current.stat().st_size > max_bytes:
                raise ValueError('Current chapter too large for preview')
            current_data = current.read_bytes()
            current_text = current_data.decode('utf-8')
            state = 'unchanged' if current_data == old_data else 'changed'
        elif current.exists():
            raise ValueError('Current chapter is not a file')
        else:
            current_text, state = '', 'missing'
        result.append(RecoveryComparison(name, old_data.decode('utf-8'), current_text, state))
    return result
