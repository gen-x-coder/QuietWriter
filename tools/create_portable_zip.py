"""Create an unambiguous, root-relative Windows portable ZIP.

Usage: python tools/create_portable_zip.py --source release/QuietWriter-1.5.0 --output release/QuietWriter-1.5.0-windows-portable.zip
Only program contents are packaged; never the container directory itself.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import zipfile
import sys

# Direct invocation (python tools/create_portable_zip.py) otherwise puts only
# tools/ on sys.path, not the project root containing quietwriter/.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def create_portable_zip(source: Path, output: Path) -> None:
    source = Path(source).resolve(strict=True)
    output = Path(output).absolute()
    if not source.is_dir() or not (source/'QuietWriter.exe').is_file():
        raise ValueError('A Windows portable installation with QuietWriter.exe is required')
    if output == source or source in output.parents:
        raise ValueError('Output must be outside the installation')
    paths = sorted(source.rglob('*'))
    from quietwriter.windows_portable_updater import _validate_name, PortableUpdateError
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in paths:
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise ValueError('Link in portable build')
            if not path.is_file():
                continue
            name = path.relative_to(source).as_posix()
            try:
                _validate_name(name)
            except PortableUpdateError as exc:
                raise ValueError(f'Unsafe portable filename: {name}') from exc
            z.write(path, arcname=name)
    with zipfile.ZipFile(output) as z:
        assert 'QuietWriter.exe' in z.namelist()
        assert all('\\' not in n for n in z.namelist())


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    create_portable_zip(a.source,a.output)
    print(f'Portable ZIP created: {a.output}')

if __name__=='__main__': main()
