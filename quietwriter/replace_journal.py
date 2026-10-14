"""Crash-recovery ledger for multi-chapter replacements (local archive only).

Never overwrite an externally changed chapter during recovery.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def journal_write(path: Path, payload: dict, writer):
    writer(path, (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8'))


def recover_transaction(folder: Path, book_folder: Path, writer) -> tuple[str, ...]:
    """Return pending filenames. Restore only files identical to our committed bytes.

    A journal can be missing/invalid: fail closed, preserve all evidence.
    """
    journal = folder / 'transaction.json'
    if not journal.is_file():
        return ()
    state = json.loads(journal.read_text(encoding='utf-8'))
    if state.get('schema') != 1 or state.get('book') != folder.parent.name:
        raise RuntimeError('Onbekend vervangjournaal; automatisch herstel gestopt.')
    if state.get('status') in {'committed', 'recovered'}:
        return ()
    if state.get('status') != 'pending':
        raise RuntimeError('Ongeldige vervangstatus; automatisch herstel gestopt.')
    conflicts = []
    for item in state['files']:
        name = item['name']
        from pathlib import PurePosixPath
        rel = PurePosixPath(name) if isinstance(name, str) else PurePosixPath('..')
        if rel.is_absolute() or not rel.parts or any(part in ('', '.', '..') for part in rel.parts) or rel.parts[0] != 'chapters':
            raise RuntimeError('Ongeldig herstelpad.')
        path = book_folder.joinpath(*rel.parts)
        backup_name = item['backup']
        if not isinstance(backup_name, str) or not backup_name.endswith('.original') or Path(backup_name).name != backup_name:
            raise RuntimeError('Ongeldig pad naar herstelkopie.')
        backup = folder / backup_name
        old = backup.read_bytes()
        if digest(old) != item['old_sha256']:
            raise RuntimeError('Herstelkopie is gewijzigd; herstel gestopt.')
        try:
            present = path.read_bytes()
        except FileNotFoundError:
            conflicts.append(name)
            continue
        if digest(present) == item['new_sha256']:
            writer(path, old)
        elif digest(present) != item['old_sha256']:
            conflicts.append(name)
    if not conflicts:
        state['status'] = 'recovered'
        journal_write(journal, state, writer)
    return tuple(conflicts)

from contextlib import contextmanager


@contextmanager
def replace_lock(book_archive: Path):
    """Nonblocking advisory lock across processes; never in the synced book folder."""
    book_archive.mkdir(parents=True, exist_ok=True)
    path = book_archive / '.replace.lock'
    with path.open('a+b') as handle:
        try:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                if not handle.read(1):
                    handle.write(b'0')
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            raise RuntimeError('Een andere vervangactie of herstelcontrole is nog bezig.') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
