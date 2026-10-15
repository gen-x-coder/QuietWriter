"""Separate-process update handoff for disposable test installations only.

Production activation is deliberately unavailable. Never accepts arbitrary
command lines or real QuietWriter binaries for relaunch.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from quietwriter.windows_portable_updater import (
    PortableUpdateError, _test_root, update_test_install,
)

LOCK = '.quietwriter-test-update.lock'


def wait_for_exit(pid: int, timeout: float = 15.0) -> None:
    if not isinstance(pid, int) or pid <= 0 or pid == os.getpid():
        raise PortableUpdateError('Invalid source process')
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
        kernel.WaitForSingleObject.restype = ctypes.c_ulong
        kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
        SYNCHRONIZE = 0x00100000
        handle = kernel.OpenProcess(SYNCHRONIZE, 0, pid)
        if not handle:
            raise PortableUpdateError('Cannot verify originating application process')
        try:
            result = kernel.WaitForSingleObject(handle, max(0, int(timeout * 1000)))
            if result != 0:  # WAIT_OBJECT_0; timeout and errors must fail closed
                raise PortableUpdateError('Application did not close safely')
        finally:
            kernel.CloseHandle(handle)
    else:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            except PermissionError as exc:
                raise PortableUpdateError('Cannot verify originating application process') from exc
            time.sleep(.04)
        raise PortableUpdateError('Application did not close safely')


def run_handoff(install: Path, archive: Path, digest: str, *, source_pid: int | None = None,
                timeout: float = 15.0, fail_after: int | None = None,
                restart_marker: Path | None = None) -> None:
    root = _test_root(install)
    # Only marker inside the disposable installation may be written by restart simulator.
    if restart_marker is not None:
        marker = Path(restart_marker).absolute()
        if marker.parent.resolve() != root or marker.name != 'test-restarted.flag':
            raise PortableUpdateError('Unsafe restart marker')
    lock = root.parent / ('.' + root.name + LOCK)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PortableUpdateError('An update is already in progress') from exc
    try:
        with os.fdopen(fd, 'w', encoding='ascii') as stream:
            stream.write(str(os.getpid()))
        if source_pid is not None:
            wait_for_exit(source_pid, timeout)
        update_test_install(root, archive, expected_sha256=digest, fail_after=fail_after)
        # Restart in the fixture only. This never runs QuietWriter.exe.
        if restart_marker is not None:
            code = 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("restarted", encoding="utf-8")'
            subprocess.run([sys.executable, '-c', code, str(restart_marker)],
                           check=True, timeout=10)
    finally:
        lock.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Disposable update integration process (no production access)')
    parser.add_argument('--install', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--wait-pid', type=int)
    parser.add_argument('--timeout', type=float, default=15.)
    parser.add_argument('--fail-after', type=int)
    parser.add_argument('--simulate-restart', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = _test_root(args.install)
        run_handoff(root, args.archive, args.sha256, source_pid=args.wait_pid,
                    timeout=args.timeout, fail_after=args.fail_after,
                    restart_marker=root / 'test-restarted.flag' if args.simulate_restart else None)
    except (PortableUpdateError, OSError, subprocess.SubprocessError) as exc:
        print(f'Updater error: {exc}', file=sys.stderr)
        return 1
    print('PASS: disposable update process complete')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
