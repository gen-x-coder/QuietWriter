"""Single-command acceptance of the NONPRODUCTION QuietWriter Windows updater.

Builds a fresh onedir EXE outside OneDrive and exercises handoff, rollback and
real executable health exclusively in disposable test installations.
Does not install anything, access GitHub, or write to the original builds.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
UPDATER_ENTRY = ROOT / 'tools' / 'quietwriter_updater_lab.py'
E2E = ROOT / 'tools' / 'test_end_to_end_handoff_dev28.py'
HANDOFF = ROOT / 'tools' / 'test_windows_handoff_dev28.py'
FROZEN = ROOT / 'tools' / 'test_frozen_updater_lab.py'


def validate_build(path: Path) -> Path:
    root = path.resolve(strict=True)
    if not root.is_dir() or not (root / 'QuietWriter.exe').is_file() or not (root / '_internal').is_dir():
        raise ValueError(f'Not a complete Windows portable build: {root}')
    return root


def choose_sources(current: Path | None, candidate: Path | None) -> tuple[Path, Path]:
    if (current is None) != (candidate is None):
        raise ValueError('Supply both --current and --candidate, or neither')
    if current is None:
        # The *same* source is copied to two different disposable paths below.
        # This checks transaction mechanics, not a cross-version migration.
        from quietwriter import __version__
        current = candidate = ROOT / 'release' / f'QuietWriter-{__version__}'
    return validate_build(current), validate_build(candidate)


def run(*args: str, cwd: Path = ROOT) -> None:
    print('RUN:', ' '.join(args), flush=True)
    subprocess.run(args, cwd=str(cwd), check=True)


def acceptance(current: Path, candidate: Path, *, keep_build: bool = False) -> None:
    if os.name != 'nt':
        raise RuntimeError('Windows-only acceptance; no builds or installs were modified')
    with tempfile.TemporaryDirectory(prefix='qw-updater-accept-dev28-') as td:
        base = Path(td)
        # Both the PyInstaller work tree and distribution are disposable and outside
        # the source project, avoiding OneDrive locks and stale build artifacts.
        frozen = base / 'dist' / 'QuietWriterUpdaterLab' / 'QuietWriterUpdaterLab.exe'
        run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--console',
            '--name', 'QuietWriterUpdaterLab', '--paths', str(ROOT),
            '--distpath', str(base / 'dist'), '--workpath', str(base / 'work'),
            '--specpath', str(base / 'spec'), str(UPDATER_ENTRY))
        if not frozen.is_file():
            raise RuntimeError('Freshly built updater executable missing; refusing stale EXE')
        run(str(frozen), '--help')
        # In all cases the externally built updater is not in the install root.
        run(sys.executable, str(HANDOFF), '--updater', str(frozen))
        run(sys.executable, str(FROZEN), str(frozen))
        # The integrated test rejects identical source paths, intentionally.
        # Create separate read-only *test inputs*, then it copies again into fixtures.
        old = base / 'input-old'
        new = base / 'input-new'
        print('COPY: source builds to isolated inputs (originals unchanged)', flush=True)
        shutil.copytree(current, old)
        shutil.copytree(candidate, new)
        run(sys.executable, str(E2E), '--current', str(old), '--candidate', str(new),
            '--updater', str(frozen))
        print('PASS: complete independent Windows updater lab acceptance', flush=True)
        if keep_build:
            # Never overwrite an existing previous accepted build.
            dest = ROOT / 'release' / 'updater-lab-accepted-dev28'
            if dest.exists():
                raise RuntimeError(f'Refusing to overwrite existing accepted build: {dest}')
            shutil.copytree(frozen.parent, dest)
            print('Saved tested updater lab:', dest)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--current', type=Path)
    p.add_argument('--candidate', type=Path)
    p.add_argument('--keep-build', action='store_true', help='retain accepted updater in release/ (never overwrite)')
    a = p.parse_args(argv)
    try:
        old, new = choose_sources(a.current, a.candidate)
        acceptance(old, new, keep_build=a.keep_build)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print('FAIL:', str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
