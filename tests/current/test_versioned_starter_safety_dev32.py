"""Regression checks for Claude dev.31 issues A1/A4/A8/A10."""
import pytest
from quietwriter.versioned_install import (initialize, activate_staged, rollback,
                                              read_active, VersionedInstallError)
from .test_versioned_install_dev31 import build


def test_extra_file_must_not_stop_startup(tmp_path):
    app = build(tmp_path, '1.5.0')
    initialize(tmp_path, 'app-1.5.0')
    (app / 'desktop.ini').write_text('Windows metadata')
    (app / 'Boeken').mkdir()
    (app / 'Boeken' / 'book.json').write_text('{}')
    assert read_active(tmp_path) == app


def test_downgrade_and_double_rollback_blocked(tmp_path):
    build(tmp_path, '1.5.0')
    build(tmp_path, '1.5.1')
    initialize(tmp_path, 'app-1.5.0')
    activate_staged(tmp_path, 'app-1.5.1')
    rollback(tmp_path)
    with pytest.raises(VersionedInstallError):
        rollback(tmp_path)
    with pytest.raises(VersionedInstallError):
        activate_staged(tmp_path, 'app-1.5.0')


def test_one_corrupt_pointer_survives(tmp_path):
    app = build(tmp_path, '1.5.0')
    initialize(tmp_path, 'app-1.5.0')
    (tmp_path / 'current.b.json').write_bytes(b'')
    assert read_active(tmp_path) == app


def test_tampered_executable_blocks_launch(tmp_path):
    app = build(tmp_path, '1.5.0')
    initialize(tmp_path, 'app-1.5.0')
    (app / 'QuietWriter.exe').write_bytes(b'OTHER')
    with pytest.raises(VersionedInstallError):
        read_active(tmp_path)
