"""Version-folder prototype: robust launch selection and LAB-ONLY switch operations.

No production update path invokes this module. It does not authenticate releases,
fetch assets, or authorize a marker to install software. Until offline Ed25519
verification and a native starter exist, never enable automatic installation.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time

from .update_install_readiness import audit_portable_install, InstallReadinessError

_PATTERN = re.compile(r'app-(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(dev|rc)\.(0|[1-9]\d*))?\Z')
_SLOTS = ('current.a.json', 'current.b.json')
_MAX_POINTER = 4096


class VersionedInstallError(ValueError):
    pass


def _root(path: Path) -> Path:
    path = Path(path).absolute()
    if not path.is_dir() or path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise VersionedInstallError('Invalid or linked installation root')
    return path


def _name(name: str) -> str:
    if not isinstance(name, str) or not _PATTERN.fullmatch(name):
        raise VersionedInstallError('Invalid version folder name')
    return name


def _version_key(name: str):
    match = _PATTERN.fullmatch(_name(name))
    a, b, c, phase, number = match.groups()
    # Stable > RC > development for the same numeric version.
    return int(a), int(b), int(c), {'dev': 0, 'rc': 1, None: 2}[phase], int(number or 0)


def _location(root: Path, name: str) -> Path:
    path = root / _name(name)
    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise VersionedInstallError('Linked application folder')
    if not path.is_dir() or path.resolve(strict=True).parent != root.resolve(strict=True):
        raise VersionedInstallError('Version folder missing or outside installation')
    return path


def _target(root: Path, name: str, *, strict: bool) -> Path:
    path = _location(root, name)
    if strict:
        try:
            audit_portable_install(path)
        except (InstallReadinessError, ValueError, OSError) as exc:
            raise VersionedInstallError('Candidate installation failed inventory audit') from exc
    else:
        quick_launch_check(path)
    return path


def quick_launch_check(app: Path) -> None:
    """Fast launch availability, tolerant of unrelated files.

    Does not establish authenticity. The updater must audit and authenticate
    the complete signed release before activation. No full tree hash at startup.
    """
    from .update_release_preflight import _relative
    app = Path(app)
    manifest = app / 'qw-release-files.json'
    try:
        if manifest.is_symlink() or manifest.stat().st_size > 4 * 1024 * 1024:
            raise VersionedInstallError('Missing or oversized inventory')
        spec = json.loads(manifest.read_text(encoding='utf-8-sig'))
        entries = spec['files']
        if spec['schema'] != 1 or not isinstance(entries, dict) or not entries or len(entries) > 20000:
            raise VersionedInstallError('Invalid inventory')
        if 'QuietWriter.exe' not in entries:
            raise VersionedInstallError('Executable missing from inventory')
        for name, record in entries.items():
            if _relative(name) != name or name == 'qw-release-files.json':
                raise VersionedInstallError('Unsafe inventory path')
            path = app / name
            if not isinstance(record, dict) or type(record.get('size')) is not int or record['size'] < 0:
                raise VersionedInstallError('Invalid inventory file size')
            for ancestor in (path, *list(path.parents)):
                if ancestor == app:
                    break
                if ancestor.is_symlink() or (hasattr(ancestor, 'is_junction') and ancestor.is_junction()):
                    raise VersionedInstallError('Linked program path')
            if not path.is_file() or not path.resolve().is_relative_to(app.resolve()):
                raise VersionedInstallError('Missing or linked program file')
            if path.stat().st_size != record['size']:
                raise VersionedInstallError('Changed program file size')
        exe = app / 'QuietWriter.exe'
        sha = hashlib.sha256(exe.read_bytes()).hexdigest()
        if sha != entries['QuietWriter.exe']['sha256']:
            raise VersionedInstallError('Executable hash mismatch')
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, AttributeError) as exc:
        raise VersionedInstallError('Application failed quick launch check') from exc


def _canonical(body: dict) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')


def _seal(body: dict) -> dict:
    return {**body, 'checksum': hashlib.sha256(_canonical(body)).hexdigest()}


def _parse_slot(path: Path) -> dict | None:
    for attempt in range(5):
        try:
            return _parse_slot_once(path)
        except FileNotFoundError:
            return None
        except OSError as exc:
            if attempt == 4:
                raise VersionedInstallError('Version pointer temporarily unreadable; refusing silent downgrade') from exc
            time.sleep(0.1)
    return None


def _parse_slot_once(path: Path) -> dict | None:
    try:
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            return None
        if path.stat().st_size > _MAX_POINTER:
            return None
        doc = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(doc, dict) or set(doc) != {'schema', 'seq', 'active', 'previous', 'checksum'}:
            return None
        if doc['schema'] != 2 or type(doc['seq']) is not int or doc['seq'] < 1:
            return None
        _name(doc['active'])
        if doc['previous'] is not None:
            _name(doc['previous'])
        if doc['active'] == doc['previous']:
            return None
        checksum = doc.pop('checksum')
        if not isinstance(checksum, str) or hashlib.sha256(_canonical(doc)).hexdigest() != checksum:
            return None
        return doc
    except (ValueError, UnicodeError, TypeError, KeyError):
        return None


def _pointer(root: Path) -> tuple[dict, int]:
    found = [(doc, index) for index, name in enumerate(_SLOTS)
             if (doc := _parse_slot(root / name)) is not None]
    if not found:
        raise VersionedInstallError('Both version pointers are unavailable; manual recovery required')
    return max(found, key=lambda pair: (pair[0]['seq'], pair[1]))


def _atomic_pointer(root: Path, body: dict, slot: int) -> None:
    fd, tmp = tempfile.mkstemp(prefix='.current-', suffix='.tmp', dir=root)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(_seal(body), stream, sort_keys=True, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, root / _SLOTS[slot])
    finally:
        Path(tmp).unlink(missing_ok=True)


@contextmanager
def _locked(root: Path):
    """Cross-process non-blocking guard for lab pointer changes (OS-level lock)."""
    handle = (root / '.versioned-update.lock').open('a+b')
    try:
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            if handle.seek(0, 2) == 0:
                handle.write(b'0')
            handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise VersionedInstallError('Another update is in progress') from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise VersionedInstallError('Another update is in progress') from exc
        yield
    finally:
        try:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


def read_active(root: Path) -> Path:
    root = _root(root)
    body, _ = _pointer(root)
    return _target(root, body['active'], strict=False)


def read_previous(root: Path) -> Path | None:
    root = _root(root)
    body, _ = _pointer(root)
    return None if body['previous'] is None else _target(root, body['previous'], strict=False)


def initialize(root: Path, installed_version: str) -> None:
    """LAB ONLY. First production install must supply a signed trusted version."""
    root = _root(root)
    with _locked(root):
        if any((root / name).exists() or (root / name).is_symlink() for name in _SLOTS):
            raise VersionedInstallError('Version pointer already exists')
        _target(root, installed_version, strict=True)
        _atomic_pointer(root, {'schema': 2, 'seq': 1, 'active': installed_version, 'previous': None}, 0)
        # Both slots initially valid: first survives corruption of the second.
        _atomic_pointer(root, {'schema': 2, 'seq': 1, 'active': installed_version, 'previous': None}, 1)


def _lab_activate(root: Path, candidate: str) -> None:
    """UNTRUSTED LAB API; never expose this path to the UI or an update service."""
    root = _root(root)
    with _locked(root):
        old, index = _pointer(root)
        if candidate == old['active'] or _version_key(candidate) <= _version_key(old['active']):
            raise VersionedInstallError('Only a newer candidate is allowed')
        _target(root, candidate, strict=True)
        _atomic_pointer(root, {'schema': 2, 'seq': old['seq'] + 1,
                               'active': candidate, 'previous': old['active']}, 1-index)


def activate_staged(root: Path, candidate: str) -> None:
    """Compatibility for existing lab tests only. NOT a production update API."""
    _lab_activate(root, candidate)


def rollback(root: Path) -> None:
    root = _root(root)
    with _locked(root):
        old, index = _pointer(root)
        if old['previous'] is None:
            raise VersionedInstallError('No previous version')
        _target(root, old['previous'], strict=False)
        _atomic_pointer(root, {'schema': 2, 'seq': old['seq'] + 1,
                               'active': old['previous'], 'previous': None}, 1-index)
