"""Side-effect-isolated health check for a newly built QuietWriter executable.

This does not install updates. It reuses the existing smoke-test's temporary
profile and publishes an acknowledgement only after a successful start/exit.
"""
from __future__ import annotations

import os
from pathlib import Path
import secrets
import subprocess
from typing import Callable


class HealthCheckError(RuntimeError):
    pass


def run_health_check(token: str, result: Path, startup: Callable[[], int]) -> int:
    """Run an isolated startup; atomically acknowledge only a healthy return.

    The caller must provide a freshly generated token and private result path;
    this is not a general-purpose file writing CLI.
    """
    if len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
        raise HealthCheckError('Invalid health token')
    result = Path(result)
    if result.is_symlink() or result.exists() or not result.parent.is_dir():
        raise HealthCheckError('Unsafe health acknowledgement path')
    status = startup()
    if status != 0:
        return status or 1
    with result.open('x', encoding='ascii') as f:
        f.write(token)
        f.flush()
        os.fsync(f.fileno())
    return 0


def probe_executable(executable: Path, directory: Path, *, timeout: float = 45,
                     runner=subprocess.run) -> None:
    """Probe an executable without replacing or modifying any installation.

    The target receives a unique marker located in a private temporary folder.
    The controlling updater checks both exit status and the acknowledgement.
    """
    executable = Path(executable).resolve(strict=True)
    if not executable.is_file() or executable.name.lower() != 'quietwriter.exe':
        raise HealthCheckError('Not a QuietWriter executable')
    directory = Path(directory).resolve(strict=True)
    token = secrets.token_hex(32)
    acknowledgement = directory / ('health-' + secrets.token_hex(12) + '.ok')
    try:
        p = runner([str(executable), '--update-health-check', token, str(acknowledgement)],
                   cwd=str(directory), timeout=timeout, capture_output=True)
        if p.returncode != 0 or not acknowledgement.is_file() or acknowledgement.read_text(encoding='ascii') != token:
            raise HealthCheckError('Updated application health check failed')
    except (subprocess.SubprocessError, OSError, UnicodeError) as exc:
        raise HealthCheckError('Updated application health check failed') from exc
    finally:
        acknowledgement.unlink(missing_ok=True)
