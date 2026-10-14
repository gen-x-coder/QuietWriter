"""Offline packaging step for a verifiable QuietWriter Windows portable ZIP.

Creates a file-list-inventory inside ZIP; never signs anything and never
publishes to GitHub. Signing remains a separate OFFLINE release operation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import stat
import zipfile

# Supports direct isolated invocation: python -I tools/prepare_verifiable_release.py
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_release_preflight import _relative, verify_release_zip, ReleasePreflightError


def package(source: Path, destination: Path) -> Path:
    source = source.resolve(strict=True)
    destination = destination.absolute()
    if not source.is_dir() or not (source / 'QuietWriter.exe').is_file():
        raise ReleasePreflightError('Expected a built Windows portable application folder')
    if destination.exists():
        raise ReleasePreflightError('Refusing to overwrite existing release')
    if source == destination.parent or source in destination.parents:
        raise ReleasePreflightError('Cannot write an archive into its source tree')
    files = {}
    seen = set()
    for path in sorted(source.rglob('*')):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ReleasePreflightError('Build contains a linked path')
        if not path.is_file():
            continue
        name = _relative(path.relative_to(source).as_posix())
        if name == 'qw-release-files.json' or name == '_internal/qw-release-files.json':
            raise ReleasePreflightError('Release input already contains inventory')
        if name.casefold() in seen:
            raise ReleasePreflightError('Duplicate Windows file name')
        seen.add(name.casefold())
        hashcode = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(256 * 1024), b''):
                hashcode.update(block)
        files[name] = {'size': path.stat().st_size, 'sha256': hashcode.hexdigest()}
    if not files:
        raise ReleasePreflightError('Empty source directory')
    inventory = json.dumps({'schema': 1, 'files': files}, sort_keys=True, separators=(',', ':')).encode('utf-8')
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name in files:
                archive.write(source / name, arcname=name)
            archive.writestr('qw-release-files.json', inventory)
        digest = hashlib.sha256()
        with destination.open('rb') as stream:
            for block in iter(lambda: stream.read(256 * 1024), b''):
                digest.update(block)
        verify_release_zip(destination, expected_size=destination.stat().st_size, expected_sha256=digest.hexdigest())
        print(f'PASS: verifiable portable release {destination}; files={len(files)}; sha256={digest.hexdigest()}')
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description='Offline only; no signing or publishing')
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.source, args.output)


if __name__ == '__main__':
    main()
