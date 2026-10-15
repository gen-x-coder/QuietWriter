"""End-to-end Windows handle-handoff probe; never touches installs or books."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import argparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_handoff_windows_lab import ReadyEvent, process_identity


def main() -> int:
    parser = argparse.ArgumentParser(description='Windows LAB handoff verification, no installation')
    parser.add_argument('--updater', type=Path, help='built QuietWriterUpdaterLab.exe')
    args = parser.parse_args()
    if os.name != 'nt':
        print('SKIP: Windows only')
        return 0
    with ReadyEvent.create() as event:
        created, image = process_identity(os.getpid())
        if args.updater:
            exe = args.updater.resolve(strict=True)
            cmd = [str(exe), 'handoff-probe', '--parent-pid', str(os.getpid()),
                   '--parent-created', str(created), '--parent-image', image, '--ready-event', event.name]
        else:
            cmd = [sys.executable, '-I', str(ROOT / 'tools' / 'windows_handoff_worker_dev28.py'),
                   str(os.getpid()), str(created), image, event.name, '--probe-only']
        child = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if args.updater and args.updater.resolve().parent.name != 'QuietWriterUpdaterLab':
            child.kill()
            child.communicate(timeout=5)
            raise RuntimeError('Expected onedir updater EXE in .../QuietWriterUpdaterLab/QuietWriterUpdaterLab.exe, not old onefile EXE')
        try:
            event.await_ready(10)
            # Parent cannot exit in this test process. The worker must remain
            # waiting on the exact handle until terminated for test cleanup.
            assert child.poll() is None, 'Worker exited unexpectedly after READY'
            print('PASS: Windows updater opened and verified parent HANDLE before READY; parent still running')
        finally:
            if child.poll() is None:
                child.kill()
            try:
                child.communicate(timeout=15)
            except subprocess.TimeoutExpired as exc:
                child.kill()
                raise RuntimeError('Lab updater failed to exit after terminating the probe; possible frozen child process. Use fresh onedir build.') from exc
    parent = [sys.executable, '-I', str(ROOT / 'tools' / 'handoff_parent_simulator_dev28.py')]
    if args.updater:
        parent += ['--updater', str(args.updater.resolve(strict=True))]
    good = subprocess.run(parent, capture_output=True, text=True, timeout=20)
    if good.returncode or 'PARENT READY:' not in good.stdout:
        raise RuntimeError('Full handoff parent did not exit safely: ' + good.stderr[-500:])
    bad = subprocess.run(parent + ['--wrong-creation'], capture_output=True, text=True, timeout=20)
    if bad.returncode or 'wrong parent creation time refused' not in bad.stdout:
        raise RuntimeError('Wrong-identity handoff was not rejected: ' + bad.stderr[-500:])
    print('PASS: full lab parent exits only after READY; wrong-creation identity refused')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
