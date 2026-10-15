"""Windows-portable updater transaction engine (dev.8, isolated integration harness).

This is NOT yet wired to the live application. The entry point requires a
separate test-install marker until official signing, handoff and review land.
Only explicitly listed program files are replaced; user folders are excluded.
"""
from __future__ import annotations

import hashlib
import json
import re
import os
from pathlib import Path
import shutil
import tempfile
import time
import zipfile

TEST_MARKER = '.quietwriter-updater-integration-test.json'
TEST_ID = {'kind': 'quietwriter-windows-portable-updater-test', 'schema': 1}
MAX_FILES = 2000
MAX_UNPACKED = 900 * 1024 * 1024
WINDOWS_DEVICES = frozenset({'CON', 'PRN', 'AUX', 'NUL', *('COM' + str(i) for i in range(1, 10)), *('LPT' + str(i) for i in range(1, 10))})
PROTECTED = frozenset({'books', 'library', 'data', 'archive', 'history', 'planning', '.quietwriter',
                       'settings', 'dictionaries', 'user_dictionaries', 'backups'})


class PortableUpdateError(RuntimeError):
    pass


def _test_root(path: Path) -> Path:
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_dir():
        raise PortableUpdateError('Invalid update test directory')
    marker = path / TEST_MARKER
    if marker.is_symlink() or not marker.is_file():
        raise PortableUpdateError('Production installs are not enabled in dev.8')
    try:
        if json.loads(marker.read_text(encoding='utf-8')) != TEST_ID:
            raise ValueError('Invalid marker')
    except (OSError, ValueError) as exc:
        raise PortableUpdateError('Invalid test-install marker') from exc
    return path.resolve(strict=True)


def _validate_name(name: str) -> None:
    """Reject paths that could alias, escape or behave unusually on Windows."""
    if not name or name.startswith('/') or '\\' in name or ':' in name:
        raise PortableUpdateError('Unsafe archive path')
    parts = name.split('/')
    if any(not item or item in ('.', '..') or item.endswith(('.', ' ')) for item in parts):
        raise PortableUpdateError('Unsafe archive path')
    for item in parts:
        if any(ord(ch) < 32 or ch in '<>"|?*' for ch in item):
            raise PortableUpdateError('Unsafe archive path')
        if item.split('.')[0].upper() in WINDOWS_DEVICES:
            raise PortableUpdateError('Unsafe Windows device name')
    if parts[0].casefold() in PROTECTED or name.casefold() == TEST_MARKER.casefold():
        raise PortableUpdateError('Attempt to replace protected user data')


def _read_archive(archive: Path, expected_sha256: str) -> dict[str, bytes]:
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise PortableUpdateError('Expected verified digest missing')
    digest = hashlib.sha256()
    with archive.open('rb') as stream:
        for block in iter(lambda: stream.read(256 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != expected_sha256:
        raise PortableUpdateError('Archive integrity check failed')
    files = {}
    canonical_paths = set()
    try:
        with zipfile.ZipFile(archive) as z:
            entries = z.infolist()
            if len(entries) > MAX_FILES:
                raise PortableUpdateError('Too many files')
            total = 0
            for info in entries:
                if info.is_dir():
                    continue
                _validate_name(info.filename)
                # NTFS is usually case-insensitive; deny colliding paths and
                # file/directory prefix clashes *before* writing anything.
                canonical = info.filename.casefold()
                prefixes = ['/'.join(canonical.split('/')[:i]) for i in range(1, len(canonical.split('/')))]
                if canonical in canonical_paths or any(prefix in canonical_paths for prefix in prefixes) or any(previous.startswith(canonical + '/') for previous in canonical_paths):
                    raise PortableUpdateError('Colliding archive paths')
                canonical_paths.add(canonical)
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise PortableUpdateError('Archive symlinks are forbidden')
                total += info.file_size
                if total > MAX_UNPACKED:
                    raise PortableUpdateError('Archive exceeds unpacked size limit')
                files[info.filename] = z.read(info)
    except zipfile.BadZipFile as exc:
        raise PortableUpdateError('Invalid portable archive') from exc
    if 'QuietWriter.exe' not in files:
        raise PortableUpdateError('Portable archive lacks QuietWriter.exe')
    return files


def update_test_install(install: Path, archive: Path, *, expected_sha256: str,
                        fail_after: int | None = None, before_swap=None) -> Path:
    """Replace a disposable app directory, preserving unrelated user content.

    Backup is kept on failure if rollback is incomplete, never auto-discarded.
    A success returns the target. Real live-install activation is deliberately
    blocked until the signed release flow and Windows handoff are reviewed.
    """
    root = _test_root(install)
    archive = Path(archive).resolve(strict=True)
    if not archive.is_file() or archive.is_symlink():
        raise PortableUpdateError('Invalid update archive')
    files = _read_archive(archive, expected_sha256)
    # In the test harness a non-executable EXE prevents accidental launching.
    if not files['QuietWriter.exe'].startswith(b'NONEXECUTABLE-QW-INTEGRATION-FIXTURE\n'):
        raise PortableUpdateError('Dev.8 only supports non-executable updater fixtures')
    # Protect against symlink traversal, including nested directories.
    for relative in files:
        current = root
        for component in relative.split('/'):
            current = current / component
            if current.is_symlink():
                raise PortableUpdateError('Symlink in update target')
    if before_swap is not None:
        before_swap()
    # Recheck after the caller's final pre-swap work, which may change the tree.
    _test_root(root)
    for relative in files:
        current = root
        for component in relative.split('/'):
            current = current / component
            if current.is_symlink():
                raise PortableUpdateError('Symlink in update target')
    # Persist backup OUTSIDE staging; failed rollbacks never lose their safety copy.
    transaction = Path(tempfile.mkdtemp(prefix='.qw-txn-', dir=root.parent))
    staging, backup = transaction / 'staged', transaction / 'old'
    staging.mkdir()
    backup.mkdir()
    replaced = []
    existed = set()
    try:
        for relative, body in files.items():
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
            old = root / relative
            if old.exists():
                if not old.is_file():
                    raise PortableUpdateError('Update destination is not a regular file')
                existed.add(relative)
                saved = backup / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old, saved)
        for index, relative in enumerate(files):
            if fail_after is not None and index >= fail_after:
                raise OSError('Injected replacement failure')
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / relative, destination)
            replaced.append(relative)
    except Exception as exc:
        rollback_errors = []
        for relative in reversed(replaced):
            try:
                if relative in existed:
                    os.replace(backup / relative, root / relative)
                else:
                    (root / relative).unlink(missing_ok=True)
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        if rollback_errors:
            # Keep backup and original staged data for recovery, never clean it.
            raise PortableUpdateError(f'Rollback incomplete; recovery files retained: {transaction}') from exc
        shutil.rmtree(transaction, ignore_errors=True)
        raise PortableUpdateError('Update failed; prior program files restored') from exc
    shutil.rmtree(transaction)
    return root


def make_test_install(parent: Path) -> Path:
    root = Path(parent) / 'portable'
    root.mkdir(parents=True, exist_ok=False)
    (root / TEST_MARKER).write_text(json.dumps(TEST_ID), encoding='utf-8')
    (root / 'QuietWriter.exe').write_bytes(b'NONEXECUTABLE-QW-INTEGRATION-FIXTURE\nold')
    (root / 'version.txt').write_text('1.5.0\n', encoding='utf-8')
    return root


def make_test_archive(path: Path, version='1.5.1') -> tuple[Path, str]:
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('QuietWriter.exe', b'NONEXECUTABLE-QW-INTEGRATION-FIXTURE\n' + version.encode())
        z.writestr('version.txt', version + '\n')
        z.writestr('resources/sample.txt', 'fixture')
    return path, hashlib.sha256(path.read_bytes()).hexdigest()
