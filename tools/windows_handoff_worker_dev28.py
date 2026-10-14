"""Subprocess entrypoint: lab-only Windows process identity/READY check."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_handoff_windows_lab import wait_verified_parent, HandoffError


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('pid', type=int)
    p.add_argument('created', type=int)
    p.add_argument('image')
    p.add_argument('ready_event')
    p.add_argument('--probe-only', action='store_true', required=True)
    a = p.parse_args(argv)
    try:
        wait_verified_parent(a.pid, a.created, a.image, a.ready_event, timeout=20)
    except HandoffError as exc:
        print('LAB HANDOFF ERROR:', exc, file=sys.stderr)
        return 1
    print('PASS: verified source process exited')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
