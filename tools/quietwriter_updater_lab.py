"""Standalone Windows updater LAB executable entrypoint.

Only accepts a private disposable rehearsal workspace; never a live install.
Build independently with tools/build_updater_lab.cmd; intentionally NOT shipped
with QuietWriter.exe and NEVER invoked by the production application.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

# Support both Python -I and PyInstaller --onefile, without depending on cwd.
if not getattr(sys, 'frozen', False):
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from quietwriter.update_real_transaction_lab import (
    swap_worker, recover_worker, finish_worker,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='NONPRODUCTION QuietWriter updater laboratory')
    parser.add_argument('command', choices=('swap', 'verified-swap', 'recover', 'commit', 'handoff-probe', 'handoff-update'))
    parser.add_argument('workspace', type=Path, nargs='?')
    parser.add_argument('--parent-pid', type=int)
    parser.add_argument('--parent-created', type=int)
    parser.add_argument('--parent-image')
    parser.add_argument('--ready-event')
    parser.add_argument('--crash', choices=('staged', 'old-renamed', 'new-renamed'))
    parser.add_argument('--manifest', type=Path, help='independent lab file list; mandatory for verified-swap and handoff-update')
    parser.add_argument('--fault-health', action='store_true', help='LAB ONLY: force rollback after swap')
    args = parser.parse_args(argv)
    if args.command == 'handoff-probe':
        from quietwriter.update_handoff_windows_lab import wait_verified_parent
        if args.workspace is not None or None in (args.parent_pid, args.parent_created, args.parent_image, args.ready_event):
            parser.error('handoff-probe requires a parent identity and event, not a workspace')
        wait_verified_parent(args.parent_pid, args.parent_created, args.parent_image, args.ready_event)
        print('LAB HANDOFF OK: verified process exited; NO INSTALLATION CHANGED')
        return 0
    if args.command == 'handoff-update':
        from quietwriter.update_handoff_windows_lab import wait_verified_parent
        from quietwriter.update_real_transaction_lab import _workspace, _paths
        from quietwriter.update_health import probe_executable
        if (args.workspace is None or args.manifest is None or
                None in (args.parent_pid, args.parent_created, args.parent_image, args.ready_event)):
            parser.error('handoff-update requires workspace, independent manifest and verified parent identity')
        # Fail before sending READY if this is not a marked, disposable lab root.
        _workspace(args.workspace.resolve(strict=True))
        # Manifest must be outside the candidate, and its validity is checked before READY.
        from quietwriter.update_real_transaction_lab import verify_candidate_file_list
        _, candidate, _ = _paths(args.workspace)
        verify_candidate_file_list(candidate, args.manifest)
        wait_verified_parent(args.parent_pid, args.parent_created, args.parent_image, args.ready_event)
        # Parent is now genuinely terminated: program-directory renames are safe to attempt.
        swap_worker(args.workspace, independent_file_manifest=args.manifest)
        try:
            if args.fault_health:
                raise RuntimeError('Injected lab health failure')
            active, _, _ = _paths(args.workspace)
            probe_executable(active / 'QuietWriter.exe', args.workspace)
        except Exception as exc:
            recover_worker(args.workspace)
            print('LAB HANDOFF UPDATE ROLLED BACK:', str(exc), flush=True)
            return 21
        finish_worker(args.workspace)
        print('LAB HANDOFF UPDATE COMMITTED: verified real EXE health; test workspace only', flush=True)
        return 0
    if args.workspace is None:
        parser.error('workspace is required for transaction commands')
    if args.crash and args.command not in ('swap', 'verified-swap'):
        parser.error('--crash only applies to swap')
    if args.command == 'verified-swap':
        if args.manifest is None:
            parser.error('verified-swap requires an independent --manifest')
        swap_worker(args.workspace, crash=args.crash, independent_file_manifest=args.manifest)
    elif args.command == 'swap':
        swap_worker(args.workspace, crash=args.crash)
    elif args.command == 'recover':
        recover_worker(args.workspace)
    else:
        finish_worker(args.workspace)
    print('LAB WORKER OK:', args.command)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
