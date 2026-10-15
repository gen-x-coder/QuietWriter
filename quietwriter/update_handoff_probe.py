"""Independent, non-destructive Windows updater handoff rehearsal.

This does NOT modify install files and is intentionally unconnected to production.
A PID is used only in the disposable test protocol, not for production handoff.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
from .update_health import probe_executable, HealthCheckError
from .updater_process import wait_for_exit
from .windows_portable_updater import PortableUpdateError


def rehearse_handoff(executable: Path, *, source_pid: int | None = None,
                      wait_timeout: float = 15, health_timeout: float = 45,
                      health_directory: Path) -> None:
    """Wait for disposable parent then probe EXE; never touch the installed files."""
    if source_pid is not None:
        wait_for_exit(source_pid, wait_timeout)
    probe_executable(executable, health_directory, timeout=health_timeout)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='NON-DESTRUCTIVE Windows executable handoff rehearsal')
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--health-directory', required=True, type=Path)
    parser.add_argument('--wait-pid', type=int)
    parser.add_argument('--wait-timeout', type=float, default=15)
    parser.add_argument('--health-timeout', type=float, default=45)
    args = parser.parse_args(argv)
    if args.wait_timeout <= 0 or args.health_timeout <= 0:
        parser.error('Timeouts must be positive')
    try:
        rehearse_handoff(args.executable, source_pid=args.wait_pid,
                         wait_timeout=args.wait_timeout, health_timeout=args.health_timeout,
                         health_directory=args.health_directory)
    except (PortableUpdateError, HealthCheckError, OSError, subprocess.SubprocessError) as exc:
        print(f'FAIL: independent EXE handoff probe: {exc}', file=sys.stderr)
        return 1
    print('PASS: independent EXE handoff health probe; no program files changed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
