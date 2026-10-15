"""Isolated rehearsal with genuine portable executables; NEVER modifies input folders.

Not a production updater. Copies two explicitly supplied onedir builds to a
private temporary directory, swaps only those copies, probes the candidate,
and restores the old copy on failure. No real install is ever an update target.
"""
from __future__ import annotations
from pathlib import Path
import shutil
import tempfile
from .update_health import probe_executable, HealthCheckError


class RehearsalError(RuntimeError):
    pass


def _source(path: Path) -> Path:
    path = Path(path).resolve(strict=True)
    if not path.is_dir() or not (path / 'QuietWriter.exe').is_file():
        raise RehearsalError('Expected a complete portable folder with QuietWriter.exe')
    for entry in path.rglob('*'):
        if entry.is_symlink() or (hasattr(entry, 'is_junction') and entry.is_junction()):
            raise RehearsalError('Portable source contains a link or junction')
    return path


def rehearse_real_update(current: Path, candidate: Path, *, probe=probe_executable,
                         fail_health: bool = False) -> dict:
    """Test a full directory swap using temporary *copies* of real onedir builds.

    A failed health probe restores the old temporary copy and raises; the caller's
    original sources remain untouched. `fail_health` is a deliberate fault-injection.
    """
    current = _source(current)
    candidate = _source(candidate)
    if current == candidate:
        raise RehearsalError('Current and candidate builds must be distinct')
    with tempfile.TemporaryDirectory(prefix='qw-real-update-rehearsal-') as temporary:
        workspace = Path(temporary)
        active = workspace / 'QuietWriter'
        staged = workspace / 'QuietWriter.new'
        previous = workspace / 'QuietWriter.previous'
        shutil.copytree(current, active, symlinks=False)
        shutil.copytree(candidate, staged, symlinks=False)
        if not (active / 'QuietWriter.exe').is_file() or not (staged / 'QuietWriter.exe').is_file():
            raise RehearsalError('Copied build is incomplete')
        active.rename(previous)
        try:
            staged.rename(active)
            if fail_health:
                raise HealthCheckError('Injected health failure')
            probe(active / 'QuietWriter.exe', workspace)
        except Exception as error:
            # This rehearsal deliberately runs inside an isolated private temp dir.
            # Preserve old copy until restored, even if the probe fails.
            if active.exists():
                active.rename(staged)
            previous.rename(active)
            if not (active / 'QuietWriter.exe').is_file():
                raise RehearsalError('Rollback did not restore original executable') from error
            raise RehearsalError('Health check failed; temporary original restored') from error
        return {'result': 'PASS', 'health': 'verified', 'originals_modified': False}
