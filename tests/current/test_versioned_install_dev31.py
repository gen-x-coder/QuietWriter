"""Pure Python tests of pointer-switch design, not a production installer."""
import hashlib
import json
from pathlib import Path
import pytest

from quietwriter.versioned_install import (VersionedInstallError, initialize, read_active,
                                            activate_staged, rollback, read_previous)


def build(root: Path, version: str):
    target = root / ('app-' + version)
    target.mkdir()
    blob = ('exe-' + version).encode()
    (target / 'QuietWriter.exe').write_bytes(blob)
    (target / 'qw-release-files.json').write_text(json.dumps({'schema': 1, 'files': {
        'QuietWriter.exe': {'size': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}
    }}), encoding='utf-8')
    return target


def test_initialize_switch_and_rollback(tmp_path):
    old = build(tmp_path, '1.5.0')
    new = build(tmp_path, '1.5.1')
    initialize(tmp_path, 'app-1.5.0')
    assert read_active(tmp_path) == old
    with pytest.raises(VersionedInstallError):
        initialize(tmp_path, 'app-1.5.0')
    activate_staged(tmp_path, 'app-1.5.1')
    assert read_active(tmp_path) == new
    assert read_previous(tmp_path) == old
    rollback(tmp_path)
    assert read_active(tmp_path) == old
    assert new.exists()


def test_corrupt_staged_unchanged(tmp_path):
    build(tmp_path, '1.5.0')
    staged = build(tmp_path, '1.5.1')
    initialize(tmp_path, 'app-1.5.0')
    before = [(tmp_path / slot).read_bytes() for slot in ('current.a.json', 'current.b.json')]
    (staged / 'QuietWriter.exe').write_bytes(b'tampered')
    with pytest.raises(VersionedInstallError):
        activate_staged(tmp_path, 'app-1.5.1')
    assert [(tmp_path / slot).read_bytes() for slot in ('current.a.json', 'current.b.json')] == before


def test_missing_active_no_creation(tmp_path):
    build(tmp_path, '1.5.0')
    initialize(tmp_path, 'app-1.5.0')
    (tmp_path / 'app-1.5.0' / 'QuietWriter.exe').unlink()
    with pytest.raises(VersionedInstallError):
        read_active(tmp_path)
    assert not (tmp_path / 'app-1.5.0' / 'QuietWriter.exe').exists()


@pytest.mark.parametrize('name', ['../escape', 'app-1.5.0/evil', 'app-1.5.0\\evil', 'app-1.5.0.txt', 'app-01.5.0'])
def test_bad_name_rejected(tmp_path, name):
    with pytest.raises(VersionedInstallError):
        initialize(tmp_path, name)


def test_pointer_corruption_fails_closed(tmp_path):
    build(tmp_path, '1.5.0')
    initialize(tmp_path, 'app-1.5.0')
    (tmp_path / 'current.a.json').write_text('{bad')
    assert read_active(tmp_path) == tmp_path / 'app-1.5.0'
    (tmp_path / 'current.b.json').write_text('{bad')
    with pytest.raises(VersionedInstallError):
        read_active(tmp_path)


def test_symlink_folder_rejected(tmp_path):
    external = tmp_path.parent / (tmp_path.name + '-elsewhere')
    external.mkdir()
    build(external, '1.5.0')
    try:
        (tmp_path / 'app-1.5.0').symlink_to(external / 'app-1.5.0', target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('No symlink privileges')
    with pytest.raises(VersionedInstallError):
        initialize(tmp_path, 'app-1.5.0')
