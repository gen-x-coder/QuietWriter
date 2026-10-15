"""LAB-ONLY starter proof of concept. Not distributed or called by QuietWriter.

Eventually packaged as a separate, fixed Windows executable. Never enables
updating, interprets a pilot marker, or downloads/install files.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quietwriter.versioned_install import read_active, read_previous, VersionedInstallError


def select_executable(install_root: Path) -> Path:
    try:
        exe = read_active(install_root) / 'QuietWriter.exe'
    except VersionedInstallError as exc:
        # A damaged application is not a damaged pointer. The previous version
        # remains available as a conscious, visible emergency launch fallback.
        if 'pointer' in str(exc).lower() or 'unreadable' in str(exc).lower():
            raise
        previous = read_previous(install_root)
        if previous is None:
            raise
        exe = previous / 'QuietWriter.exe'
        print('WAARSCHUWING: nieuwste versie niet bruikbaar; vorige versie wordt gestart. Boeken zijn niet gewijzigd.', file=sys.stderr)
    if not exe.is_file():
        raise VersionedInstallError('Selected QuietWriter executable not found')
    return exe


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Experimental read-only versioned QuietWriter starter')
    parser.add_argument('--root', type=Path, required=True, help='Versioned install root')
    parser.add_argument('--check', action='store_true', help='Validate and show target; do not launch')
    options = parser.parse_args(argv)
    try:
        exe = select_executable(options.root)
    except (VersionedInstallError, OSError) as exc:
        parser.exit(2, f'Versiebeheer niet beschikbaar: {exc}\nGebruik de handmatige GitHub-installatie of herstel de installatie.\n')
    if options.check:
        print(f'PASS: starter targets verified executable: {exe}')
        return 0
    try:
        subprocess.Popen([str(exe)], cwd=str(exe.parent), shell=False, close_fds=True)
    except OSError as exc:
        parser.exit(2, f'QuietWriter kon niet worden gestart: {exc}\nGebruik de handmatige GitHub-installatie om te herstellen.\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
