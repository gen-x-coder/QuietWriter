"""Crash-recoverable directory swap for NONEXECUTABLE updater fixtures only.

No connection to the real application. Production requires authenticated manifest,
Windows interprocess lock, real process handle and health-check protocol.
"""
from __future__ import annotations
import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import zipfile
import time
from .windows_portable_updater import (PortableUpdateError, _test_root, _validate_name,
                                      TEST_MARKER, TEST_ID, MAX_FILES, MAX_UNPACKED)

PREFIX = b"NONEXECUTABLE-QW-INTEGRATION-FIXTURE\n"
JOURNAL_SUFFIX = ".qw-update-journal.json"

@contextmanager
def _update_lock(root: Path):
    """Kernel-managed, nonblocking, cross-process fixture lock.

    The lock *file* may persist after a crash; the OS lock does not.
    Uses a sibling of the install so the lock survives directory renames.
    """
    root = Path(root).absolute()
    path = root.parent / ('.' + root.name + '.qw-os-lock')
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise PortableUpdateError('Unsafe update lock path')
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    held = False
    try:
        if os.name == 'nt':
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            if os.fstat(fd).st_size == 0:
                os.write(fd, b'0')
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise PortableUpdateError('An update is already in progress') from exc
        else:
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (OSError, BlockingIOError) as exc:
                raise PortableUpdateError('An update is already in progress') from exc
        held = True
        yield
    finally:
        if held:
            if os.name == 'nt':
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

def _durable_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)

def _paths(root: Path):
    return (root.parent / ('.' + root.name + '.qw-next'),
            root.parent / ('.' + root.name + '.qw-previous'),
            root.parent / ('.' + root.name + JOURNAL_SUFFIX))

def _check_workspace(root: Path) -> None:
    for p in _paths(root):
        if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
            raise PortableUpdateError('Update workspace contains symlink or junction')

def _tree_digest(folder: Path) -> str:
    """Authenticated local transaction snapshot; symlinks are never followed."""
    h = hashlib.sha256()
    if not folder.is_dir() or folder.is_symlink():
        raise PortableUpdateError('Untrusted transaction tree')
    for f in sorted(folder.rglob('*'), key=lambda p: p.relative_to(folder).as_posix()):
        if f.is_symlink() or (hasattr(f, 'is_junction') and f.is_junction()):
            raise PortableUpdateError('Unsafe link in transaction tree')
        if f.is_file():
            name = f.relative_to(folder).as_posix().encode('utf-8')
            h.update(len(name).to_bytes(4, 'big') + name)
            h.update(f.stat().st_size.to_bytes(8, 'big'))
            with f.open('rb') as stream:
                for chunk in iter(lambda: stream.read(256 * 1024), b''):
                    h.update(chunk)
    return h.hexdigest()


def _read_journal(journal: Path, root: Path) -> dict:
    try:
        info = json.loads(journal.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError) as exc:
        raise PortableUpdateError('Unreadable update journal; manual recovery required') from exc
    if (not isinstance(info, dict) or info.get('schema') != 2 or
        info.get('kind') != 'qw-disposable-dir-swap' or
        info.get('install_path') != str(root) or
        info.get('phase') not in ('staging', 'ready', 'swapping')):
        raise PortableUpdateError('Unknown update journal; manual recovery required')
    return info


def _rescue(root: Path, folder: Path) -> Path:
    path = root.parent / ('.' + root.name + '.qw-rescue-' + str(time.time_ns()))
    os.replace(folder, path)
    return path


def _recover_locked(root: Path) -> bool:
    """Conservative recovery. Never erase an active installation to trust an unverified backup."""
    root = Path(root).absolute()
    new, old, journal = _paths(root)
    _check_workspace(root)
    if root.is_symlink() or (hasattr(root, 'is_junction') and root.is_junction()):
        raise PortableUpdateError('Unsafe installation root')
    if not journal.exists():
        return False
    info = _read_journal(journal, root)
    if info['phase'] == 'staging':
        if old.exists() or not root.is_dir() or not (root / TEST_MARKER).is_file():
            raise PortableUpdateError('Ambiguous staging transaction; manual recovery required')
        if new.exists():
            if not (new / '.qw-staging-marker').is_file():
                raise PortableUpdateError('Untrusted staging directory; manual recovery required')
            _rescue(root, new)  # never destructively delete unknown contents
        journal.unlink()
        return True
    expected = info.get('old_tree_sha256')
    if not isinstance(expected, str) or len(expected) != 64:
        raise PortableUpdateError('Missing verified recovery digest; manual recovery required')
    if old.exists():
        if _tree_digest(old) != expected:
            # Backup corrupt: never replace the active tree. If the first rename
            # left the installation name empty, restore the intact staged tree
            # (without trusting the damaged backup) before refusing recovery.
            if not root.exists() and new.is_dir() and info.get('new_tree_sha256') == _tree_digest(new):
                os.replace(new, root)
            raise PortableUpdateError('Recovery tree verification failed; manual recovery required')
        if root.exists():
            if new.exists():
                raise PortableUpdateError('Ambiguous update state; manual recovery required')
            _rescue(root, root)
        os.replace(old, root)
    else:
        if not root.is_dir() or _tree_digest(root) != expected:
            raise PortableUpdateError('Missing trusted previous installation; manual recovery required')
    if new.exists():
        _rescue(root, new)
    journal.unlink()
    return True

def recover_test_update(root: Path) -> bool:
    """Recover under the same lock used for swapping; crash-safe lock release."""
    with _update_lock(Path(root)):
        return _recover_locked(root)

def _extract_fixture(archive: Path, destination: Path, digest: str):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
        raise PortableUpdateError('Archive integrity check failed')
    seen = set(); total=0; count=0
    try:
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                if info.is_dir(): continue
                name = info.filename
                _validate_name(name)
                canonical = name.casefold(); count+=1;total+=info.file_size
                if count > MAX_FILES or total > MAX_UNPACKED:
                    raise PortableUpdateError('Archive limits exceeded')
                if canonical in seen or any(canonical.startswith(p+'/') or p.startswith(canonical+'/') for p in seen):
                    raise PortableUpdateError('Colliding archive paths')
                seen.add(canonical)
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise PortableUpdateError('Archive symlinks forbidden')
                dest = destination.joinpath(*name.split('/'))
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, dest.open('xb') as dst:
                    shutil.copyfileobj(src,dst,256*1024)
                    dst.flush();os.fsync(dst.fileno())
    except (zipfile.BadZipFile, EOFError) as exc:
        raise PortableUpdateError('Invalid portable archive') from exc
    exe = destination/'QuietWriter.exe'
    if not exe.is_file() or not exe.read_bytes().startswith(PREFIX):
        raise PortableUpdateError('Only NONEXECUTABLE fixtures are supported')
    (destination/TEST_MARKER).write_text(json.dumps(TEST_ID),encoding='utf-8')

def _swap_locked(install: Path, archive: Path, expected_sha256: str, *, fault: str|None=None, retain_journal: bool=False) -> Path:
    """Fixture-only, write-ahead transaction; retain untrusted trees for examination."""
    root = Path(install).absolute()
    new, old, journal = _paths(root)
    _check_workspace(root)
    if journal.exists():
        _recover_locked(root)
    root = _test_root(root)
    if new.exists():
        raise PortableUpdateError('Existing staging directory; manual recovery required')
    if old.exists():
        if not (old / TEST_MARKER).is_file() or not (old / 'QuietWriter.exe').is_file():
            raise PortableUpdateError('Untrusted previous version; manual recovery required')
        # One retained previous version is allowed, but never delete it before
        # the new version is safely healthy. Rotate it out of the transaction slot.
        _rescue(root, old)
    archive = Path(archive).resolve(strict=True)
    _durable_json(journal, {'schema':2, 'kind':'qw-disposable-dir-swap',
        'install_path':str(root), 'phase':'staging'})
    try:
        new.mkdir()
        (new / '.qw-staging-marker').write_text('fixture-only', encoding='utf-8')
        _extract_fixture(archive,new,expected_sha256)
        (new / '.qw-staging-marker').unlink()
        # Strictly preserve unknown user files as well as known folders. Program
        # payload belongs to the new signed archive, not to this old tree.
        program = {'QuietWriter.exe', 'version.txt', TEST_MARKER}
        with zipfile.ZipFile(archive) as z:
            program.update(x.filename for x in z.infolist() if not x.is_dir())
        for entry in root.iterdir():
            if entry.name in program or entry.name == '_internal':
                continue
            target = new / entry.name
            if target.exists():
                raise PortableUpdateError('User data conflicts with new release')
            if entry.is_symlink() or (hasattr(entry,'is_junction') and entry.is_junction()):
                raise PortableUpdateError('Unsafe user data path')
            if entry.is_dir(): shutil.copytree(entry,target,symlinks=False)
            elif entry.is_file(): shutil.copy2(entry,target)
        old_digest = _tree_digest(root)
        new_digest = _tree_digest(new)
        _durable_json(journal, {'schema':2,'kind':'qw-disposable-dir-swap',
            'install_path':str(root),'phase':'ready',
            'old_tree_sha256':old_digest,'new_tree_sha256':new_digest})
        os.replace(root,old)
        if fault == 'after_old_rename': raise OSError('Injected crash after old rename')
        os.replace(new,root)
        if fault == 'after_new_rename': raise OSError('Injected crash after new rename')
        if not retain_journal:
            journal.unlink()
        return root
    except Exception as exc:
        if journal.exists():
            try: _recover_locked(root)
            except (PortableUpdateError, OSError): pass
        raise PortableUpdateError(f'Side-by-side update failed; recovery attempted: {exc}') from exc


def swap_test_install(install: Path, archive: Path, expected_sha256: str, *, fault: str | None = None, retain_journal: bool = False) -> Path:
    """Fixture-only map swap with OS-owned lock, including recovery."""
    with _update_lock(Path(install)):
        return _swap_locked(install, archive, expected_sha256, fault=fault, retain_journal=retain_journal)


def complete_test_update(root: Path, *, healthy: bool) -> bool:
    """Commit a verified fixture after health-check, or restore its old tree.

    This is deliberately fixture-only. No executable is launched by this method.
    The OS lock ensures crash recovery and commit cannot race.
    """
    root = Path(root).absolute()
    with _update_lock(root):
        new, old, journal = _paths(root)
        _check_workspace(root)
        if not journal.is_file() or not old.is_dir() or not root.is_dir():
            raise PortableUpdateError('No pending verified update')
        if new.exists():
            raise PortableUpdateError('Ambiguous staged update; manual recovery required')
        info = json.loads(journal.read_text(encoding='utf-8'))
        if info != _read_journal(journal, root):
            raise PortableUpdateError('Untrusted pending update journal')
        if _tree_digest(old) != info.get('old_tree_sha256'):
            raise PortableUpdateError('Recovery tree verification failed')
        if not (root / TEST_MARKER).is_file() or not (old / TEST_MARKER).is_file():
            raise PortableUpdateError('Unsafe fixture installation')
        if not healthy:
            return _recover_locked(root)
        journal.unlink()
        # Keep the complete prior version for deferred cleanup / manual rescue.
        return True
