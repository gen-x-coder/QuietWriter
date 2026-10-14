"""Disposable parent application simulator for Windows process-handle handoff."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_handoff_windows_lab import ReadyEvent, process_identity


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--updater', type=Path)
    p.add_argument('--wrong-creation', action='store_true')
    a = p.parse_args()
    created, image = process_identity(os.getpid())
    if a.wrong_creation:
        created += 1
    with ReadyEvent.create() as event:
        if a.updater:
            child = [str(a.updater.resolve(strict=True)), 'handoff-probe',
                     '--parent-pid', str(os.getpid()), '--parent-created', str(created),
                     '--parent-image', image, '--ready-event', event.name]
        else:
            child = [sys.executable, '-I', str(ROOT / 'tools' / 'windows_handoff_worker_dev28.py'),
                     str(os.getpid()), str(created), image, event.name, '--probe-only']
        worker = subprocess.Popen(child, cwd=str(ROOT), stdin=subprocess.DEVNULL,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if a.wrong_creation:
                try:
                    event.await_ready(2)
                except Exception:
                    print('PASS: wrong parent creation time refused before READY', flush=True)
                    return 0
                raise RuntimeError('FAIL: bad parent identity was acknowledged')
            event.await_ready(10)
            print('PARENT READY: verified worker has parent HANDLE; exiting now', flush=True)
            # This process exits and closes its own stdout; a separate supervising
            # process checks that the updater exits after observing this closure.
            return 0
        finally:
            if a.wrong_creation:
                worker.kill()
                worker.wait(timeout=5)


if __name__ == '__main__':
    raise SystemExit(main())
