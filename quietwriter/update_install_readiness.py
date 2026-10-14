"""Read-only portable-installation inventory audit. Never installs or alters files.

The inventory alone is not a trust anchor: callers must authenticate its origin
(or use this strictly as a local diagnostic) before accepting a production update.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat

class InstallReadinessError(ValueError):
    pass


def _regular_file(p: Path) -> bool:
    try:
        return stat.S_ISREG(p.lstat().st_mode) and not p.is_symlink()
    except OSError:
        return False


def audit_portable_install(root: Path) -> dict:
    """Fail closed on unknown entries, changed bytes, links, and malformed inventory.

    This does not modify the installation, profile, or any user workspace.
    """
    from .update_release_preflight import _relative
    root = Path(root).absolute()
    if not root.is_dir() or root.is_symlink() or (hasattr(root, 'is_junction') and root.is_junction()):
        raise InstallReadinessError('Invalid or linked portable installation root')
    manifest = root / 'qw-release-files.json'
    if not _regular_file(manifest) or not _regular_file(root / 'QuietWriter.exe'):
        raise InstallReadinessError('Portable installation has no valid executable or inventory')
    try:
        if manifest.stat().st_size > 4*1024*1024:
            raise InstallReadinessError('Oversized installation inventory')
        spec = json.loads(manifest.read_text(encoding='utf-8'))
        if (not isinstance(spec, dict) or set(spec) != {'schema', 'files'} or
                type(spec['schema']) is not int or spec['schema'] != 1 or not isinstance(spec['files'], dict)):
            raise InstallReadinessError('Invalid installation inventory')
        entries = spec['files']
        if not entries or len(entries) > 20000 or 'QuietWriter.exe' not in entries:
            raise InstallReadinessError('Incomplete installation inventory')
        canonical = set()
        for name, record in entries.items():
            if not isinstance(name, str) or _relative(name) != name or name == 'qw-release-files.json':
                raise InstallReadinessError('Unsafe inventory path')
            if name.casefold() in canonical:
                raise InstallReadinessError('Duplicate Windows inventory path')
            canonical.add(name.casefold())
            if (not isinstance(record, dict) or set(record) != {'size','sha256'} or
                type(record['size']) is not int or record['size'] < 0 or
                not isinstance(record['sha256'], str) or len(record['sha256']) != 64 or
                any(c not in '0123456789abcdef' for c in record['sha256'])):
                raise InstallReadinessError('Invalid installation inventory record')
        found = set()
        # Walk WITHOUT following directory symlinks or NTFS junctions.
        pending = [root]
        while pending:
            folder = pending.pop()
            for path in folder.iterdir():
                if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                    raise InstallReadinessError('Linked path in portable installation')
                if path.is_dir():
                    pending.append(path)
                    continue
                if not _regular_file(path):
                    raise InstallReadinessError('Nonregular file in portable installation')
                name = path.relative_to(root).as_posix()
                if name == 'qw-release-files.json':
                    continue
                if name not in entries:
                    raise InstallReadinessError('Unknown or user-owned file in portable installation')
                found.add(name)
                record = entries[name]
                if path.stat().st_size != record['size']:
                    raise InstallReadinessError('Installed file size differs from inventory')
                digest = hashlib.sha256()
                with path.open('rb') as source:
                    for part in iter(lambda: source.read(256*1024), b''):
                        digest.update(part)
                if digest.hexdigest() != record['sha256']:
                    raise InstallReadinessError('Installed file digest differs from inventory')
        if found != set(entries):
            raise InstallReadinessError('Installation inventory references missing files')
        return {'status':'READ_ONLY_AUDIT_OK', 'verified_files':len(found)}
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InstallReadinessError('Cannot audit installation inventory') from exc
