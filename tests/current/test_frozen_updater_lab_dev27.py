"""Regression test the frozen acceptance runner with the Python lab entrypoint."""
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'tools' / 'test_frozen_updater_lab.py'


def test_missing_updater_executable_is_refused(tmp_path):
    result = subprocess.run([sys.executable, str(TOOL), str(tmp_path / 'missing.exe')],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'not found' in result.stderr


def test_acceptance_fixture_must_not_reference_real_builds():
    source = TOOL.read_text(encoding='utf-8')
    assert 'TemporaryDirectory' in source
    assert 'FAKE-' in source
    assert 'QuietWriter-1.4.0' not in source
    assert 'shutil.copytree' not in source


@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX test uses executable shim; Windows tests actual frozen EXE manually')
def test_full_standalone_acceptance_with_python_shim(tmp_path):
    shim = tmp_path / 'updater-shim'
    shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{ROOT / "tools" / "quietwriter_updater_lab.py"}" "$@"\n')
    shim.chmod(0o755)
    result = subprocess.run([sys.executable, str(TOOL), str(shim)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS: frozen standalone updater lab' in result.stdout
