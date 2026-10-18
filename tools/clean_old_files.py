"""Oude bestanden opruimen na het uitpakken van een nieuwe QuietWriter-zip.

Uitpakken over een bestaande map verwijdert niets: bestanden die in een nieuwe
versie zijn weggehaald, blijven staan (en oude tests falen dan). Dit script
vergelijkt de map met ``SOURCE_MANIFEST.txt`` uit de zip (of met ``git
ls-files`` als er een git-werkkopie is) en verplaatst wat er niet op staat naar
``_oude_bestanden/<datum-tijd>/``. Er wordt niets weggegooid.

Gebruik (in de projectmap):

    python tools/clean_old_files.py          # laat zien wat oud is en vraagt het
    python tools/clean_old_files.py --ja     # zonder vragen verplaatsen
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'SOURCE_MANIFEST.txt'
# Alleen in deze mappen wordt gezocht; al het andere (venv, builds, caches) blijft.
CHECKED_DIRS = ('quietwriter', 'tests', 'tools', 'packaging', 'resources', 'branding', 'documents')
SKIPPED_PARTS = {'__pycache__', '.pytest_cache', 'archive'}   # documents/archive is privé en staat niet in de zip
SKIPPED_SUFFIXES = {'.pyc', '.pyo'}


def known_files(root: Path = ROOT) -> set[str] | None:
    manifest = root / MANIFEST
    if manifest.is_file():
        return {line.strip() for line in manifest.read_text(encoding='utf-8').splitlines() if line.strip()}
    try:
        result = subprocess.run(['git', 'ls-files'], cwd=root, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    files = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return files or None


def old_files(root: Path = ROOT, known: set[str] | None = None) -> list[Path]:
    known = known_files(root) if known is None else known
    if not known:
        return []
    found = []
    for folder in CHECKED_DIRS:
        base = root / folder
        if not base.is_dir():
            continue
        for path in base.rglob('*'):
            if not path.is_file() or path.suffix in SKIPPED_SUFFIXES:
                continue
            relative = path.relative_to(root)
            if SKIPPED_PARTS & set(relative.parts):
                continue
            if relative.as_posix() not in known:
                found.append(path)
    return sorted(found)


def move_aside(paths: list[Path], root: Path = ROOT) -> Path:
    target = root / '_oude_bestanden' / datetime.now().strftime('%Y-%m-%d_%H%M%S')
    for path in paths:
        destination = target / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
    return target


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    known = known_files()
    if not known:
        print(f'Geen {MANIFEST} en geen git-werkkopie gevonden; er is niets om mee te vergelijken.')
        return 1
    paths = old_files(known=known)
    if not paths:
        print('Geen oude bestanden gevonden.')
        return 0
    print(f'{len(paths)} bestand(en) horen niet meer bij deze versie:')
    for path in paths:
        print('  ' + path.relative_to(ROOT).as_posix())
    if '--ja' not in argv:
        answer = input('Verplaatsen naar _oude_bestanden? (j/n) ').strip().lower()
        if answer not in ('j', 'ja', 'y', 'yes'):
            print('Niets verplaatst.')
            return 0
    target = move_aside(paths)
    print(f'Verplaatst naar {target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
