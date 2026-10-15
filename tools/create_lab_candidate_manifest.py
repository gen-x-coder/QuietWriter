"""Create an UNSIGNED disposable-lab inventory from a complete source build.

Store output OUTSIDE the candidate install tree. Not for production releases.
"""
import argparse
import hashlib
import json
from pathlib import Path


def create(source: Path, output: Path):
    source = source.resolve(strict=True)
    output = output.resolve()
    if not source.is_dir() or source in output.parents:
        raise ValueError('Manifest must be outside the source build')
    files = {}
    for file in sorted(source.rglob('*')):
        if file.is_symlink() or (hasattr(file, 'is_junction') and file.is_junction()):
            raise ValueError('Links are not permitted')
        if file.is_file():
            name = file.relative_to(source).as_posix()
            files[name] = {'size': file.stat().st_size, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
    if not files or 'QuietWriter.exe' not in files:
        raise ValueError('Expected a complete lab candidate with QuietWriter.exe')
    output.write_text(json.dumps({'schema': 1, 'files': files}, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return len(files)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('complete_candidate', type=Path)
    p.add_argument('manifest_outside_candidate', type=Path)
    args = p.parse_args()
    print('LAB manifest:', create(args.complete_candidate, args.manifest_outside_candidate), 'files (UNSIGNED)')
