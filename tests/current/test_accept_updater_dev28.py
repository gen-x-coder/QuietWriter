"""Safety contracts for the consolidated updater acceptance runner."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('accept_updater_dev28', ROOT / 'tools/accept_updater_dev28.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_reject_partial_build(tmp_path):
    (tmp_path / 'QuietWriter.exe').write_bytes(b'FAKE')
    with pytest.raises(ValueError, match='complete Windows portable'):
        mod.validate_build(tmp_path)


def test_reject_single_custom_build(tmp_path):
    with pytest.raises(ValueError, match='both'):
        mod.choose_sources(tmp_path, None)


def test_accept_distinct_builds_without_modification(tmp_path):
    for name in ('one', 'two'):
        (tmp_path / name / '_internal').mkdir(parents=True)
        (tmp_path / name / 'QuietWriter.exe').write_bytes(b'FAKE')
    result = mod.choose_sources(tmp_path / 'one', tmp_path / 'two')
    assert result == (tmp_path / 'one', tmp_path / 'two')
    assert (tmp_path / 'one' / 'QuietWriter.exe').read_bytes() == b'FAKE'


def test_no_update_install_from_nonwindows(tmp_path):
    if mod.os.name != 'nt':
        with pytest.raises(RuntimeError, match='Windows-only'):
            mod.acceptance(tmp_path, tmp_path)


def test_requires_standalone_exe_and_manifest_checks():
    source = (ROOT / 'tools/accept_updater_dev28.py').read_text(encoding='utf-8')
    assert 'test_end_to_end_handoff_dev28.py' in source
    assert 'test_frozen_updater_lab.py' in source
    assert 'test_windows_handoff_dev28.py' in source
    assert 'TemporaryDirectory' in source
    assert '--onedir' in source
    assert 'release' in source
