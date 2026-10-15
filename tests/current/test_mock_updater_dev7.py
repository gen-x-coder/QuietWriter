import hashlib
from pathlib import Path
import pytest
from quietwriter.update_test_updater import (MockUpdateError, apply_mock_update,
                                               create_fixture, create_mock_update)


def _prepare(tmp_path):
    root = create_fixture(tmp_path)
    archive = create_mock_update(tmp_path / 'new.zip')
    return root, archive, hashlib.sha256(archive.read_bytes()).hexdigest()


def test_mock_update_success(tmp_path):
    root, archive, sha = _prepare(tmp_path)
    (root / 'personal-notes.txt').write_text('do not touch')
    apply_mock_update(root, archive, expected_sha256=sha)
    assert (root / 'version.txt').read_text().strip() == '1.5.1'
    assert (root / 'personal-notes.txt').read_text() == 'do not touch'


def test_mock_update_rollback(tmp_path):
    root, archive, sha = _prepare(tmp_path)
    before = {name: (root / name).read_bytes() for name in ('QuietWriter.exe', 'version.txt', 'LEESMIJ.txt')}
    with pytest.raises(MockUpdateError, match='restored'):
        apply_mock_update(root, archive, expected_sha256=sha, fail_after=2)
    assert all((root / name).read_bytes() == old for name, old in before.items())


def test_mock_updater_rejects_real_install(tmp_path):
    root = tmp_path / 'real'
    root.mkdir()
    (root / 'QuietWriter.exe').write_bytes(b'actual program')
    archive = create_mock_update(tmp_path / 'update.zip')
    with pytest.raises(MockUpdateError, match='marker'):
        apply_mock_update(root, archive, expected_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())


def test_mock_updater_rejects_modified_package(tmp_path):
    root, archive, sha = _prepare(tmp_path)
    archive.write_bytes(b'changed')
    with pytest.raises(MockUpdateError, match='checksum'):
        apply_mock_update(root, archive, expected_sha256=sha)
    assert (root / 'version.txt').read_text().strip() == '1.5.0'


def test_mock_updater_rejects_extra_zip_entries(tmp_path):
    import zipfile
    root, archive, _ = _prepare(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        z.writestr('../evil.py', 'x')
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(MockUpdateError, match='Unexpected'):
        apply_mock_update(root, archive, expected_sha256=sha)


def test_mock_updater_rejects_symlink_targets(tmp_path):
    root, archive, sha = _prepare(tmp_path)
    (root / 'version.txt').unlink()
    try:
        (root / 'version.txt').symlink_to(tmp_path / 'outside.txt')
    except (OSError, NotImplementedError) as exc:
        if getattr(exc, "winerror", None) == 1314 or isinstance(exc, NotImplementedError):
            pytest.skip("Windows account lacks symlink creation privilege")
        raise
    with pytest.raises(MockUpdateError, match='Symlink'):
        apply_mock_update(root, archive, expected_sha256=sha)


def test_mock_updater_mid_first_file_failure(tmp_path):
    root, archive, sha = _prepare(tmp_path)
    with pytest.raises(MockUpdateError):
        apply_mock_update(root, archive, expected_sha256=sha, fail_after=0)
    assert (root / 'version.txt').read_text().strip() == '1.5.0'
