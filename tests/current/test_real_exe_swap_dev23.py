from pathlib import Path
import pytest
from quietwriter.update_real_exe_lab import rehearse_real_update, RehearsalError


def fake_build(root: Path, label: str):
    root.mkdir()
    (root / 'QuietWriter.exe').write_bytes(label.encode())
    (root / '_internal').mkdir()
    (root / '_internal' / 'module.dll').write_text(label)
    return root


def test_real_swap_with_health_probe_keeps_sources(tmp_path):
    old = fake_build(tmp_path / 'old', 'old')
    new = fake_build(tmp_path / 'new', 'new')
    def probe(executable, directory):
        assert executable.read_bytes() == b'new'
        assert (executable.parent / '_internal' / 'module.dll').read_text() == 'new'
        assert (directory / 'QuietWriter.previous' / 'QuietWriter.exe').read_bytes() == b'old'
    assert rehearse_real_update(old, new, probe=probe)['result'] == 'PASS'
    assert (old / 'QuietWriter.exe').read_bytes() == b'old'
    assert (new / 'QuietWriter.exe').read_bytes() == b'new'


def test_real_swap_health_failure_rolls_back_without_touching_source(tmp_path):
    old = fake_build(tmp_path / 'old', 'old')
    new = fake_build(tmp_path / 'new', 'new')
    def fail(executable, directory):
        raise RuntimeError('broken executable')
    with pytest.raises(RehearsalError, match='temporary original restored'):
        rehearse_real_update(old, new, probe=fail)
    assert (old / 'QuietWriter.exe').read_bytes() == b'old'
    assert (new / 'QuietWriter.exe').read_bytes() == b'new'


def test_real_swap_rejects_same_build(tmp_path):
    old = fake_build(tmp_path / 'old', 'old')
    with pytest.raises(RehearsalError, match='distinct'):
        rehearse_real_update(old, old, probe=lambda *args: None)


def test_real_swap_explicit_fault(tmp_path):
    old = fake_build(tmp_path / 'old', 'old')
    new = fake_build(tmp_path / 'new', 'new')
    with pytest.raises(RehearsalError, match='temporary original restored'):
        rehearse_real_update(old, new, probe=lambda *args: None, fail_health=True)
