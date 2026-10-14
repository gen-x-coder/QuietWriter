"""Isolated signed update handoff worker. NEVER use for production installs."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quietwriter.update_integration_lab import handoff_fixture_update
from quietwriter.windows_portable_updater import PortableUpdateError
from quietwriter.side_by_side_update import recover_test_update


def main(argv=None):
    ap = argparse.ArgumentParser(description='NONEXECUTABLE signed fixture updater only')
    for field in ('install','archive','manifest','signature','test-public-key'):
        ap.add_argument('--'+field, type=Path, required=True)
    ap.add_argument('--source-pid',type=int)
    ap.add_argument('--health-fail',action='store_true')
    ap.add_argument('--recover-only', action='store_true', help='Recover an interrupted disposable fixture')
    ns=ap.parse_args(argv)
    try:
        # Intentionally read a TEST key; this script is not shipped or called
        # from a compiled QuietWriter installation.
        if ns.recover_only:
            recovered = recover_test_update(ns.install)
            print('PASS: fixture recovery performed' if recovered else 'PASS: no pending fixture recovery')
            return 0
        ver=handoff_fixture_update(ns.install,ns.archive,
             ns.manifest.read_bytes(),ns.signature.read_bytes(),
             ns.test_public_key.read_bytes(),source_pid=ns.source_pid,
             health_should_fail=ns.health_fail)
    except (PortableUpdateError,ValueError,OSError,TimeoutError) as exc:
        print(f'Fixture updater rejected: {exc}',file=sys.stderr)
        return 1
    print(f'PASS: independently authenticated NONEXECUTABLE fixture update to {ver}')
    return 0

if __name__=='__main__': raise SystemExit(main())
