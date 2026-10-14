"""Production-oriented, read-only release preflight. NO INSTALLATION ACTIONS.

Never trust keys, hashes or filesystem paths supplied by the downloaded asset.
Production activation requires offline release-key provisioning and independent review.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

from .update_download import UpdateDownloadError, verify_signed_manifest

# Intentionally empty. Public keys may be added only after an offline release-key
# ceremony and independent review. There is NO 'test key' fallback here.
PINNED_RELEASE_KEYS: dict[str, bytes] = {}
MAX_FILES = 20000
MAX_UNCOMPRESSED = 2 * 1024**3
MAX_FILE_BYTES = 512 * 1024**2
MAX_METADATA_BYTES = 4 * 1024**2


class ReleasePreflightError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(256 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def _relative(name: str) -> str:
    if not name or '\\' in name or '\x00' in name or name.startswith('/'):
        raise ReleasePreflightError('Unsafe release filename')
    parts = name.split('/')
    if any(part in ('', '.', '..') or part.endswith((' ', '.')) or ':' in part for part in parts):
        raise ReleasePreflightError('Unsafe release filename')
    if any(part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
        *('COM'+str(i) for i in range(1, 10)), *('LPT'+str(i) for i in range(1, 10))} for part in parts):
        raise ReleasePreflightError('Windows reserved release filename')
    return name


def verify_release_zip(zip_path: Path, *, expected_sha256: str, expected_size: int) -> dict:
    """Read-only audit: exact signed ZIP hash, archive safety, and file list.

    `qw-release-files.json` is authenticated indirectly by the trusted signed ZIP
    digest. It covers every non-directory archive entry other than itself.
    """
    zip_path = Path(zip_path)
    if not zip_path.is_file() or zip_path.is_symlink():
        raise ReleasePreflightError('Missing or linked release ZIP')
    if (type(expected_size) is not int or zip_path.stat().st_size != expected_size or
            not isinstance(expected_sha256, str) or _sha256_file(zip_path) != expected_sha256):
        raise ReleasePreflightError('Signed ZIP size or digest mismatch')
    try:
        with zipfile.ZipFile(zip_path) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > MAX_FILES:
                raise ReleasePreflightError('Invalid ZIP file count')
            by_name = {}
            folded = set()
            total = 0
            for info in entries:
                name = info.filename
                if info.is_dir():
                    _relative(name.rstrip('/'))
                    continue
                _relative(name)
                if name.casefold() in folded:
                    raise ReleasePreflightError('Duplicate Windows file name')
                folded.add(name.casefold())
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_IFMT(mode) == stat.S_IFLNK or info.flag_bits & 1:
                    raise ReleasePreflightError('Linked or encrypted ZIP entry')
                if info.file_size > MAX_FILE_BYTES:
                    raise ReleasePreflightError('Release file too large')
                total += info.file_size
                if total > MAX_UNCOMPRESSED:
                    raise ReleasePreflightError('Release exceeds expanded size cap')
                by_name[name] = info
            meta = by_name.get('qw-release-files.json')
            if meta is None or meta.file_size > MAX_METADATA_BYTES:
                raise ReleasePreflightError('Signed release has no valid file manifest')
            spec = json.loads(archive.read(meta).decode('utf-8'))
            if set(spec) != {'schema', 'files'} or spec['schema'] != 1 or not isinstance(spec['files'], dict):
                raise ReleasePreflightError('Unsupported release file manifest')
            actual = set(by_name) - {'qw-release-files.json'}
            if set(spec['files']) != actual:
                raise ReleasePreflightError('Release file manifest does not cover archive')
            if 'QuietWriter.exe' not in actual:
                raise ReleasePreflightError('Release has no application executable')
            for name, expected in spec['files'].items():
                if (not isinstance(expected, dict) or set(expected) != {'size', 'sha256'} or
                        type(expected['size']) is not int or expected['size'] < 0 or
                        not isinstance(expected['sha256'], str) or len(expected['sha256']) != 64):
                    raise ReleasePreflightError('Invalid file manifest record')
                entry = by_name[name]
                if entry.file_size != expected['size']:
                    raise ReleasePreflightError('Manifest file size mismatch')
                digest = hashlib.sha256()
                with archive.open(entry) as src:
                    for block in iter(lambda: src.read(256 * 1024), b''):
                        digest.update(block)
                if digest.hexdigest() != expected['sha256']:
                    raise ReleasePreflightError('Manifest file checksum mismatch')
            return {'verified_files': len(actual), 'uncompressed_bytes': total}
    except (zipfile.BadZipFile, OSError, UnicodeError, json.JSONDecodeError, RuntimeError) as exc:
        raise ReleasePreflightError('Cannot inspect signed release ZIP') from exc


def preflight_official_release(manifest: bytes, signature: bytes, key_id: str, downloaded: Path, *, installed_root: Path) -> dict:
    """Verify, do not execute or stage. Fail closed until pinned keys exist."""
    key = PINNED_RELEASE_KEYS.get(key_id)
    if key is None or key_id.startswith('test-'):
        raise ReleasePreflightError('No trusted production signing key for this release')
    asset = verify_signed_manifest(manifest, signature, key)
    if asset.expires is None:
        raise ReleasePreflightError('Signed schema 2 manifest required')
    root = Path(installed_root)
    if not root.is_dir() or root.is_symlink() or not (root / 'QuietWriter.exe').is_file():
        raise ReleasePreflightError('No recognized portable installation')
    # Existing user data in an installation root must not be swapped during an
    # update. Without an authenticated inventory, we cannot identify it safely.
    # Intentionally refuse rather than assuming personal books are disposable.
    # The local inventory is not an authorization source by itself. First require
    # an authenticated release identity in the production integration, then audit
    # all installed bytes before any future install transition.
    from .update_install_readiness import audit_portable_install, InstallReadinessError
    try:
        audit_portable_install(root)
    except InstallReadinessError as exc:
        raise ReleasePreflightError(str(exc)) from exc
    result = verify_release_zip(downloaded, expected_sha256=asset.sha256, expected_size=asset.size)
    return {'version': asset.version, **result, 'status': 'VERIFIED_ONLY_NO_INSTALL'}
