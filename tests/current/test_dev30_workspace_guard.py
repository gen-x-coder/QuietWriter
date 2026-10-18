"""Safe working directories must survive installation updates."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from quietwriter.workspace_path import require_external_user_directory, UnsafeWorkspacePath, portable_install_root


def test_workspace_outside_install_is_valid(tmp_path):
    install = tmp_path / 'app'
    books = tmp_path / 'books'
    assert require_external_user_directory(books, install_root=install) == books


def test_workspace_inside_install_refused(tmp_path):
    install = tmp_path / 'app'
    for dest in (install, install / 'books', install / 'backups' / '2026'):
        with pytest.raises(UnsafeWorkspacePath):
            require_external_user_directory(dest, install_root=install)


def test_symlink_alias_of_install_refused(tmp_path):
    install = tmp_path / 'app'
    install.mkdir()
    alias = tmp_path / 'shortcut'
    try:
        alias.symlink_to(install, target_is_directory=True)
    except OSError:
        pytest.skip('Directory symlinks unavailable')
    with pytest.raises(UnsafeWorkspacePath):
        require_external_user_directory(alias / 'books', install_root=install)


def test_only_frozen_app_uses_executable_directory(tmp_path):
    from quietwriter import workspace_path
    with patch.object(workspace_path.sys, 'frozen', False, create=True):
        assert portable_install_root() is None
    with patch.object(workspace_path.sys, 'frozen', True, create=True), patch.object(workspace_path.sys, 'executable', str(tmp_path / 'QuietWriter.exe')):
        assert portable_install_root() == tmp_path


def test_velopack_layout_protects_the_whole_app_folder(tmp_path):
    from quietwriter import workspace_path
    current = tmp_path / 'current'
    current.mkdir()
    (tmp_path / 'Update.exe').write_bytes(b'')
    with patch.object(workspace_path.sys, 'frozen', True, create=True), patch.object(workspace_path.sys, 'executable', str(current / 'QuietWriter.exe')):
        assert portable_install_root() == tmp_path
    with pytest.raises(UnsafeWorkspacePath):
        require_external_user_directory(tmp_path / 'Boeken', install_root=tmp_path)


def test_missing_existing_workspace_is_checked_before_library_creation():
    source = (Path(__file__).resolve().parents[2] / 'quietwriter/ui/workspace_recovery.py').read_text(encoding='utf-8')
    assert "settings.value('first_run_done', False, bool) and not candidate.is_dir()" in source
    assert source.index("not candidate.is_dir()") < source.index('library = Library(candidate)')
