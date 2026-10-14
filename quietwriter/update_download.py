"""Fail-closed preparation for signed Windows release downloads.

No downloads are enabled in the UI until an official signing key is embedded
and official release packaging publishes matching signed manifests.
The download service never runs executable files or changes installations.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

MAX_MANIFEST_BYTES = 65536
MAX_ASSET_BYTES = 1024 * 1024 * 1024
GITHUB_ASSET_HOSTS = frozenset({
    'github.com', 'objects.githubusercontent.com',
    'release-assets.githubusercontent.com',
})


class UpdateDownloadError(ValueError):
    """Unsafe or unsuccessful update transfer."""


@dataclass(frozen=True)
class VerifiedAsset:
    version: str
    url: str
    filename: str
    size: int
    sha256: str
    expires: str | None = None
    released_at: str | None = None


def _official_https(url: str) -> bool:
    parts = urlparse(url)
    return (parts.scheme == 'https' and parts.hostname in GITHUB_ASSET_HOSTS
            and not parts.username and not parts.password and not parts.fragment)


def verify_signed_manifest(manifest: bytes, signature: bytes, public_key: bytes) -> VerifiedAsset:
    """Verify the publisher signature BEFORE reading any asset metadata.

    The key must come from trusted installed application code, not the release.
    The manifest and detached signature may be fetched from the same source
    because only the pinned key makes them trustworthy.
    """
    if not isinstance(manifest, bytes) or len(manifest) > MAX_MANIFEST_BYTES:
        raise UpdateDownloadError('Invalid manifest size')
    if len(signature) != 64 or len(public_key) != 32:
        raise UpdateDownloadError('Missing or invalid trusted signing key/signature')
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, manifest)
    except Exception as exc:
        raise UpdateDownloadError('Manifest signature could not be verified') from exc
    try:
        obj = json.loads(manifest.decode('utf-8'))
        if not isinstance(obj, dict) or ((obj.get('schema') == 1 and set(obj) != {'schema', 'version', 'url', 'filename', 'size', 'sha256'}) or (obj.get('schema') == 2 and set(obj) != {'schema', 'version', 'url', 'filename', 'size', 'sha256', 'released_at', 'expires'}) or obj.get('schema') not in (1,2)):
            raise ValueError('Unexpected manifest fields')
        version, filename, url = obj['version'], obj['filename'], obj['url']
        size, checksum = obj['size'], obj['sha256']
        if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
            raise ValueError('Only stable releases are supported')
        if filename != 'QuietWriter-windows-portable.zip':
            raise ValueError('Unexpected asset filename')
        if not isinstance(url, str) or not _official_https(url):
            raise ValueError('Untrusted download URL')
        if not url.startswith('https://github.com/gen-x-coder/QuietWriter/releases/download/'):
            raise ValueError('Not an official release download')
        if not isinstance(size, int) or isinstance(size, bool) or not (0 < size <= MAX_ASSET_BYTES):
            raise ValueError('Invalid download size')
        if not isinstance(checksum, str) or not re.fullmatch(r'[a-f0-9]{64}', checksum):
            raise ValueError('Invalid SHA-256 digest')
        if obj['schema'] == 2:
            from .update_version_policy import require_manifest_freshness
            from datetime import datetime
            require_manifest_freshness(obj['expires'])
            try:
                released = datetime.fromisoformat(obj['released_at'].replace('Z', '+00:00'))
                expiry = datetime.fromisoformat(obj['expires'].replace('Z', '+00:00'))
                if released.tzinfo is None or released > expiry:
                    raise ValueError('Invalid release period')
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError('Invalid signed release dates') from exc
            return VerifiedAsset(version, url, filename, size, checksum, obj['expires'], obj['released_at'])
        return VerifiedAsset(version, url, filename, size, checksum)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        raise UpdateDownloadError('Invalid verified manifest contents') from exc


def download_verified_asset(asset: VerifiedAsset, folder: Path, *, session=None,
                            cancelled=None, progress=None) -> Path:
    """Stream into a private partial file; publish only after verification.

    Progress is an optional callback receiving (received, total) byte counts.
    The caller owns the destination folder; no user files are overwritten.
    """
    if not isinstance(asset, VerifiedAsset) or not _official_https(asset.url):
        raise UpdateDownloadError('Untrusted asset URL')
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    client = session or requests.Session()
    temporary = None
    try:
        # Inspect each redirect before contacting the next host.
        url = asset.url
        for _ in range(6):
            if not _official_https(url):
                raise UpdateDownloadError('Download redirected to an untrusted host')
            response = client.get(url, stream=True, timeout=(10, 30), allow_redirects=False)
            if response.status_code in (301, 302, 303, 307, 308):
                from urllib.parse import urljoin
                next_url = urljoin(url, response.headers.get('Location', ''))
                response.close()
                url = next_url
                continue
            break
        else:
            raise UpdateDownloadError('Too many download redirects')
        with response:
            response.raise_for_status()
            if not _official_https(response.url):
                raise UpdateDownloadError('Download redirected to an untrusted host')
            with tempfile.NamedTemporaryFile(mode='wb', prefix='.quietwriter-update-', suffix='.partial',
                                             dir=folder, delete=False) as output:
                temporary = Path(output.name)
                digest = hashlib.sha256()
                received = 0
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if cancelled is not None and cancelled():
                        raise UpdateDownloadError('Download cancelled')
                    if not chunk:
                        continue
                    received += len(chunk)
                    if received > asset.size or received > MAX_ASSET_BYTES:
                        raise UpdateDownloadError('Download exceeds signed size')
                    digest.update(chunk)
                    output.write(chunk)
                    if progress is not None:
                        progress(received, asset.size)
                output.flush()
                os.fsync(output.fileno())
        if received != asset.size or digest.hexdigest() != asset.sha256:
            raise UpdateDownloadError('Downloaded asset failed integrity verification')
        # Unique, non-conflicting staging name. Never overwrite an existing update.
        destination = folder / f'QuietWriter-{asset.version}-{asset.sha256[:12]}.zip'
        if destination.exists():
            if destination.is_file() and destination.stat().st_size == asset.size and hashlib.sha256(destination.read_bytes()).hexdigest() == asset.sha256:
                return destination
            raise UpdateDownloadError('Verified update is already staged')
        try:
            os.link(temporary, destination)  # atomic, no overwrite
        except OSError as link_error:
            # Filesystems such as FAT32/exFAT do not support hard links.
            # Reserve an exclusive destination before atomic rename; do not
            # substitute a blind rename that could overwrite user files.
            if destination.exists():
                raise UpdateDownloadError('Verified update is already staged') from link_error
            try:
                fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise UpdateDownloadError('Verified update is already staged') from exc
            else:
                os.close(fd)
            try:
                os.replace(temporary, destination)
            except OSError:
                destination.unlink(missing_ok=True)
                raise
        if temporary is not None and temporary.exists():
            temporary.unlink()
        temporary = None
        return destination
    except (requests.RequestException, OSError) as exc:
        raise UpdateDownloadError('Update download failed') from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
