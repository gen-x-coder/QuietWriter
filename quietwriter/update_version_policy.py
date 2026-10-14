"""Version acceptance policy for verified, stable release manifests.

The signing verifier checks authenticity; this module checks freshness. Production
is NOT wired up until trusted key publication and separate updater review.
"""
from __future__ import annotations
from datetime import datetime, timezone
import re
from .update_download import UpdateDownloadError, VerifiedAsset


def _parse(version: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-(?:dev|rc)\.?\d+)?", version)
    if not match:
        raise UpdateDownloadError('Unsupported release version')
    return tuple(int(match.group(i)) for i in range(1, 4))


def require_upgrade(asset: VerifiedAsset, current: str, *, highest_seen: str | None = None) -> None:
    """Fail closed for downgrades/replays; dev-builds may update to their next stable line.

    Untrusted 'highest_seen' must be persisted only after authenticating the
    corresponding manifest; caller must not derive it from network metadata.
    """
    candidate = _parse(asset.version)
    active = _parse(current)
    if candidate < active or (candidate == active and '-dev' not in current and '-rc' not in current):
        raise UpdateDownloadError('Update is not newer than the installed release')
    if highest_seen is not None and candidate < _parse(highest_seen):
        raise UpdateDownloadError('Older signed release refused (replay protection)')


def require_manifest_freshness(expires: str, *, now: datetime | None = None) -> None:
    """Check a signed expiry timestamp; schema integration is a later step."""
    try:
        expiry = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        if expiry.tzinfo is None:
            raise ValueError('timezone missing')
    except (ValueError, TypeError, AttributeError) as exc:
        raise UpdateDownloadError('Invalid signed manifest expiry') from exc
    if (now or datetime.now(timezone.utc)) > expiry:
        raise UpdateDownloadError('Signed manifest has expired')
