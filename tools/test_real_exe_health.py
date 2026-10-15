"""Non-destructive, manual Windows health probe for a built QuietWriter.exe.

This never updates, renames, deletes or installs application files. The
application itself runs in its existing isolated --smoke-test profile.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import tempfile

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quietwriter.update_health import HealthCheckError, probe_executable


def main(argv=None):
    ap=argparse.ArgumentParser(description='Non-destructive health test of a Windows QuietWriter.exe')
    ap.add_argument('executable', type=Path, help='Path to a built QuietWriter.exe in a disposable test installation')
    ns=ap.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix='qw-exe-health-') as folder:
            probe_executable(ns.executable, Path(folder))
    except (HealthCheckError, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    print('PASS: executable started and acknowledged isolated health check; no update installed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
