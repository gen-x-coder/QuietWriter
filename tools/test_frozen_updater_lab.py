"""Windows acceptance test of the actually built, standalone updater LAB executable.

Uses only disposable synthetic directories; never receives a user's install path.
No GitHub access, downloaded release, or real QuietWriter installation is needed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_real_transaction_lab import MARKER, JOURNAL, _hash_tree


def _run(exe: Path, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(exe), *(str(x) for x in args)], capture_output=True, text=True, timeout=60)


def _fixture(work: Path) -> tuple[str, str]:
    (work / MARKER).write_text('NONPRODUCTION-TEST-FIXTURE\n', encoding='ascii')
    for directory, label in [('QuietWriter', 'OLD'), ('QuietWriter.next', 'NEW')]:
        folder = work / directory
        folder.mkdir()
        (folder / 'QuietWriter.exe').write_bytes(f'FAKE-{label}-EXE'.encode())
        (folder / 'data.bin').write_bytes((label * 100).encode())
    return _hash_tree(work / 'QuietWriter'), _hash_tree(work / 'QuietWriter.next')


def exercise(exe: Path) -> None:
    if not exe.is_file():
        raise ValueError(f'Updater lab executable not found: {exe}')
    # Exercise the frozen entrypoint before putting even fake files within scope.
    with tempfile.TemporaryDirectory(prefix='qw-frozen-lab-') as td:
        base = Path(td)
        unmarked = base / 'unmarked'
        unmarked.mkdir()
        (unmarked / 'QuietWriter.exe').write_bytes(b'LEAVE-ME-ALONE')
        rejected = _run(exe, 'swap', unmarked)
        if rejected.returncode == 0 or (unmarked / 'QuietWriter.exe').read_bytes() != b'LEAVE-ME-ALONE':
            raise AssertionError('Frozen updater accepted an unmarked directory or modified files')

        for scenario in ('success', 'old-renamed', 'new-renamed'):
            work = base / scenario
            work.mkdir()
            old_hash, new_hash = _fixture(work)
            cmd = ('swap', work) if scenario == 'success' else ('swap', work, '--crash', scenario)
            result = _run(exe, *cmd)
            if scenario == 'success':
                if result.returncode != 0 or _hash_tree(work / 'QuietWriter') != new_hash:
                    raise AssertionError('Standalone swap did not install fake candidate: ' + result.stderr[-400:])
                result = _run(exe, 'commit', work)
                if result.returncode != 0 or (work / JOURNAL).exists():
                    raise AssertionError('Standalone commit did not complete: ' + result.stderr[-400:])
            else:
                if result.returncode != 9:
                    raise AssertionError(f'Crash point {scenario} expected exit code 9, got {result.returncode}')
                result = _run(exe, 'recover', work)
                if result.returncode != 0 or _hash_tree(work / 'QuietWriter') != old_hash:
                    raise AssertionError('Standalone recovery failed: ' + result.stderr[-400:])
                if (work / JOURNAL).exists():
                    raise AssertionError('Recovery left a journal')
    print('PASS: frozen standalone updater lab; unmarked rejection, swap, commit and two crash recoveries; temp files removed')


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Acceptance test for frozen, nonproduction updater lab EXE')
    p.add_argument('exe', nargs='?', type=Path, default=ROOT / 'release/updater-lab-onedir/QuietWriterUpdaterLab/QuietWriterUpdaterLab.exe')
    a = p.parse_args(argv)
    try:
        exercise(a.exe.resolve())
    except (ValueError, AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        print('FAIL:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
