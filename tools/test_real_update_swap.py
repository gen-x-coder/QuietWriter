"""Exercise a genuine Windows onedir build inside an isolated temporary clone.

python tools/test_real_update_swap.py --current PATH --candidate PATH
python tools/test_real_update_swap.py --current PATH --candidate PATH --fault
Never edits either supplied input directory or the user's installed QuietWriter.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_real_exe_lab import rehearse_real_update, RehearsalError


def main(argv=None):
    parser = argparse.ArgumentParser(description='ISOLATED real EXE swap rehearsal (input builds never changed)')
    parser.add_argument('--current', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--fault', action='store_true', help='Inject health failure to test rollback')
    args = parser.parse_args(argv)
    try:
        rehearse_real_update(args.current, args.candidate, fail_health=args.fault)
    except (RehearsalError, OSError) as exc:
        if args.fault and isinstance(exc, RehearsalError) and 'temporary original restored' in str(exc):
            print('PASS: simulated health failure rolled back; original folders untouched')
            return 0
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    if args.fault:
        print('FAIL: expected a health failure, but it did not occur', file=sys.stderr)
        return 1
    print('PASS: real EXE health check after isolated directory swap; original folders untouched')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
