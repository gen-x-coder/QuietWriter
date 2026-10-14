import hashlib
from pathlib import Path
import zipfile
import pytest
from quietwriter.windows_portable_updater import (make_test_install, make_test_archive,
                                                   update_test_install, PortableUpdateError)


def setup(tmp_path):
    root = make_test_install(tmp_path)
    archive, digest = make_test_archive(tmp_path / 'update.zip')
    return root, archive, digest


def test_transaction_success_and_user_files(tmp_path):
    root, archive, sha = setup(tmp_path)
    (root / 'personal.txt').write_text('keep')
    update_test_install(root, archive, expected_sha256=sha)
    assert (root / 'version.txt').read_text().strip() == '1.5.1'
    assert (root / 'personal.txt').read_text() == 'keep'
    assert (root / 'resources/sample.txt').read_text() == 'fixture'


def test_rollback(tmp_path):
    root, archive, sha = setup(tmp_path)
    with pytest.raises(PortableUpdateError, match='restored'):
        update_test_install(root, archive, expected_sha256=sha, fail_after=1)
    assert (root / 'QuietWriter.exe').read_bytes().endswith(b'old')
    assert (root / 'version.txt').read_text().strip() == '1.5.0'


def test_bad_hash_rejected(tmp_path):
    root, archive, sha = setup(tmp_path)
    with pytest.raises(PortableUpdateError, match='integrity'):
        update_test_install(root, archive, expected_sha256='0' * 64)


def test_unmarked_install_rejected(tmp_path):
    root, archive, sha = setup(tmp_path)
    (root / '.quietwriter-updater-integration-test.json').unlink()
    with pytest.raises(PortableUpdateError, match='Production installs'):
        update_test_install(root, archive, expected_sha256=sha)


def test_protected_data_rejected(tmp_path):
    root, archive, sha = setup(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        z.writestr('books/private.txt', 'bad')
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(PortableUpdateError, match='protected'):
        update_test_install(root, archive, expected_sha256=sha)


def test_path_traversal_rejected(tmp_path):
    root, archive, sha = setup(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        z.writestr('../outside.txt', 'bad')
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(PortableUpdateError, match='Unsafe'):
        update_test_install(root, archive, expected_sha256=sha)


def test_symlink_target_rejected(tmp_path):
    root, archive, sha = setup(tmp_path)
    (root / 'version.txt').unlink()
    try:
        (root / 'version.txt').symlink_to(tmp_path / 'outside')
    except (OSError, NotImplementedError):
        pytest.skip('Symlink creation not permitted')
    with pytest.raises(PortableUpdateError, match='Symlink'):
        update_test_install(root, archive, expected_sha256=sha)


@pytest.mark.parametrize('name', [
    'books\u002fPRIVATE.txt', '.QUIETWRITER-updater-integration-test.json',
    'resources/CON.txt', 'resources/bad.', 'resources/bad ',
    'resources/file:stream', 'resources/bad?.txt', 'resources/../escape',
])
def test_windows_unsafe_names_rejected(tmp_path, name):
    root, archive, _ = setup(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        z.writestr(name, 'bad')
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(PortableUpdateError):
        update_test_install(root, archive, expected_sha256=sha)
    assert (root / 'version.txt').read_text().strip() == '1.5.0'


def test_windows_case_collisions_rejected(tmp_path):
    root, archive, _ = setup(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        z.writestr('VERSION.TXT', 'bad')
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(PortableUpdateError, match='Colliding'):
        update_test_install(root, archive, expected_sha256=sha)
    assert (root / 'version.txt').read_text().strip() == '1.5.0'


def test_archive_file_directory_conflict_rejected(tmp_path):
    root, archive, _ = setup(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        z.writestr('resources', 'bad')
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(PortableUpdateError, match='Colliding'):
        update_test_install(root, archive, expected_sha256=sha)


def test_target_symlink_after_callback_rejected(tmp_path):
    root, archive, sha = setup(tmp_path)
    outside = tmp_path / 'outside'
    outside.write_text('safe')
    def replace_after_first_check():
        (root / 'version.txt').unlink()
        (root / 'version.txt').symlink_to(outside)
    try:
        update_test_install(root, archive, expected_sha256=sha,
                            before_swap=replace_after_first_check)
    except (OSError, NotImplementedError):
        pytest.skip('Symlink creation not permitted')
    except PortableUpdateError as exc:
        assert 'Symlink' in str(exc)
        assert outside.read_text() == 'safe'
    else:
        pytest.fail('Expected symlink rejection')
