"""Standalone, deliberately test-only portable updater for disposable fixtures.

No production entry point imports this module. A specially marked fixture and
its explicitly listed application files are the only supported targets.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

MARKER = '.quietwriter-mock-install.json'
APP_FILES = ('QuietWriter.exe', 'LEESMIJ.txt', 'version.txt')


class MockUpdateError(ValueError):
    pass


def _fixture(path: Path) -> Path:
    path = Path(path).resolve(strict=True)
    if path.is_symlink() or not path.is_dir():
        raise MockUpdateError('Not an ordinary fixture directory')
    marker = path / MARKER
    if marker.is_symlink() or not marker.is_file():
        raise MockUpdateError('Test installation marker missing')
    try:
        obj = json.loads(marker.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise MockUpdateError('Invalid fixture marker') from exc
    if obj != {'kind': 'quietwriter-disposable-updater-test', 'schema': 1}:
        raise MockUpdateError('Not a disposable update fixture')
    if any((path / name).is_symlink() for name in APP_FILES):
        raise MockUpdateError('Symlink targets are not supported')
    return path


def create_fixture(parent: Path, name='mock-install') -> Path:
    """Create fixture with an unambiguous opt-in marker, not a real EXE."""
    parent = Path(parent).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / name
    target.mkdir(exist_ok=False)
    (target / MARKER).write_text(json.dumps({'kind': 'quietwriter-disposable-updater-test', 'schema': 1}), encoding='utf-8')
    (target / 'QuietWriter.exe').write_bytes(b'MOCK-EXECUTABLE-NOT-RUNNABLE\n')
    (target / 'version.txt').write_text('1.5.0\n', encoding='utf-8')
    (target / 'LEESMIJ.txt').write_text('Disposable test installation\n', encoding='utf-8')
    return target


def create_mock_update(archive: Path, version='1.5.1') -> Path:
    """Zip only fake program files: no executable Python/source payload."""
    archive = Path(archive)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('QuietWriter.exe', b'MOCK-EXECUTABLE-NOT-RUNNABLE\n' + version.encode())
        z.writestr('version.txt', version + '\n')
        z.writestr('LEESMIJ.txt', 'Mock version ' + version + '\n')
    return archive


def apply_mock_update(install: Path, archive: Path, *, expected_sha256: str, fail_after: int | None = None) -> None:
    """Transactional mock swap with rollback on faults, scoped to APP_FILES.

    Only a local fixture is supported. Deliberately does not install real app ZIPs.
    """
    root = _fixture(install)
    archive = Path(archive).resolve(strict=True)
    if not archive.is_file() or archive.is_symlink():
        raise MockUpdateError('Invalid mock archive')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise MockUpdateError('Mock archive checksum mismatch')
    try:
        with zipfile.ZipFile(archive) as z:
            infos = z.infolist()
            if len(infos) != len(APP_FILES) or set(i.filename for i in infos) != set(APP_FILES):
                raise MockUpdateError('Unexpected mock archive contents')
            if any(i.is_dir() or i.file_size > 1024 * 1024 for i in infos):
                raise MockUpdateError('Invalid fixture asset')
            payload = {name: z.read(name) for name in APP_FILES}
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise MockUpdateError('Invalid mock archive') from exc
    if not payload['QuietWriter.exe'].startswith(b'MOCK-EXECUTABLE-NOT-RUNNABLE\n'):
        raise MockUpdateError('Real executable updates are prohibited in test updater')
    # Stage outside of live targets, on the same volume for atomic per-file swap.
    with tempfile.TemporaryDirectory(prefix='.mock-update-', dir=root) as stage:
        staged = Path(stage)
        backup = staged / 'backup'
        backup.mkdir()
        for name in APP_FILES:
            if (root / name).is_symlink():
                raise MockUpdateError('Symlink discovered in target')
            if (root / name).exists():
                shutil.copy2(root / name, backup / name)
            (staged / name).write_bytes(payload[name])
        applied = []
        try:
            for index, name in enumerate(APP_FILES):
                if fail_after is not None and index >= fail_after:
                    raise OSError('Injected mock replacement failure')
                os.replace(staged / name, root / name)
                applied.append(name)
        except OSError as exc:
            failures = []
            for name in reversed(applied):
                try:
                    previous = backup / name
                    if previous.exists():
                        os.replace(previous, root / name)
                    else:
                        (root / name).unlink(missing_ok=True)
                except OSError as rollback_exc:
                    failures.append(str(rollback_exc))
            if failures:
                # Never delete the only remaining backup copy on rollback failure.
                rescue = root.parent / (root.name + '-mock-rescue')
                rescue.mkdir(exist_ok=True)
                for name in APP_FILES:
                    old = backup / name
                    if old.exists():
                        shutil.copy2(old, rescue / name)
                raise MockUpdateError('Rollback incomplete; mock rescue saved') from exc
            raise MockUpdateError('Mock replacement failed; old files restored') from exc
