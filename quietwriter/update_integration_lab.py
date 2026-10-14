"""End-to-end integration *lab* for signed fixtures and health-gated rollback.

No real program binaries are accepted or executed. Deliberately disconnected from
QuietWriter UI and production release pipeline.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import os
from .side_by_side_update import swap_test_install, complete_test_update, recover_test_update
from .windows_portable_updater import PortableUpdateError, _test_root
from .update_download import verify_signed_manifest
from .update_version_policy import require_upgrade


def run_fixture_update(install: Path, archive: Path, signed_manifest: bytes,
                       signature: bytes, pinned_public_key: bytes,
                       *, highest_seen: str | None = None,
                       health_should_fail: bool = False,
                       fault: str | None = None) -> str:
    """Verify, swap, run a non-executable health probe, commit or rollback."""
    root = _test_root(install)
    asset = verify_signed_manifest(signed_manifest, signature, pinned_public_key)
    if asset.expires is None:
        raise PortableUpdateError('Current signed manifest schema required')
    current = (root / 'version.txt').read_text(encoding='utf-8').strip()
    require_upgrade(asset, current, highest_seen=highest_seen)
    archive = Path(archive).resolve(strict=True)
    if archive.name != asset.filename:
        raise PortableUpdateError('Downloaded asset does not match manifest filename')
    if archive.stat().st_size != asset.size:
        raise PortableUpdateError('Downloaded asset size mismatch')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != asset.sha256:
        raise PortableUpdateError('Downloaded asset hash mismatch')
    # Swap cannot complete transaction until a separate process has probed it.
    swap_test_install(root, archive, asset.sha256, retain_journal=True, fault=fault)
    # The probe reads only the fixture version, NEVER executes QuietWriter.exe.
    code = ('from pathlib import Path; import sys; '
            'print(Path(sys.argv[1]).read_text(encoding="utf-8").strip())')
    try:
        if health_should_fail:
            raise subprocess.CalledProcessError(1, ['fixture-health'])
        proc = subprocess.run([sys.executable, '-I', '-c', code, str(root / 'version.txt')],
                              check=True, capture_output=True, text=True, timeout=10)
        if proc.stdout.strip() != asset.version:
            raise PortableUpdateError('Health check reported unexpected version')
    except (OSError, subprocess.SubprocessError, PortableUpdateError) as exc:
        complete_test_update(root, healthy=False)
        raise PortableUpdateError('Health check failed; old installation restored') from exc
    complete_test_update(root, healthy=True)
    return asset.version


def handoff_fixture_update(install: Path, archive: Path, signed_manifest: bytes,
                           signature: bytes, pinned_public_key: bytes,
                           *, highest_seen: str | None = None,
                           health_should_fail: bool = False,
                           source_pid: int | None = None,
                           source_timeout: float = 15.0) -> str:
    """Exercise authenticated update in an independent Python updater process.

    All paths and executables are fixture-only; the production app cannot invoke
    this entry point, and the TEST public key is passed only by the lab caller.
    The worker verifies the signature itself rather than trusting a caller hash.
    """
    root = _test_root(install)
    from .updater_process import wait_for_exit
    if source_pid is not None:
        wait_for_exit(source_pid, source_timeout)
    return run_fixture_update(root, archive, signed_manifest, signature,
                              pinned_public_key, highest_seen=highest_seen,
                              health_should_fail=health_should_fail)
