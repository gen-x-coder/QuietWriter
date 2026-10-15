"""Nonproduction standalone updater executable entrypoint contract."""
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'tools' / 'quietwriter_updater_lab.py'


def run(*args):
    return subprocess.run([sys.executable, '-I', str(TOOL), *map(str, args)],
                          cwd=ROOT.parent, capture_output=True, text=True, timeout=15)


def test_standalone_lab_rejects_unmarked_workspace(tmp_path):
    result = run('swap', tmp_path)
    assert result.returncode != 0
    assert 'disposable rehearsal workspace' in result.stderr


@pytest.mark.parametrize('command', ['swap', 'recover', 'commit'])
def test_standalone_lab_rejects_live_install(tmp_path, command):
    live = tmp_path / 'QuietWriter'
    live.mkdir()
    (live / 'QuietWriter.exe').write_bytes(b'UNCHANGED')
    result = run(command, live)
    assert result.returncode != 0
    assert (live / 'QuietWriter.exe').read_bytes() == b'UNCHANGED'


def test_standalone_rejects_invalid_crash_command(tmp_path):
    result = run('recover', tmp_path, '--crash', 'staged')
    assert result.returncode != 0
    assert '--crash only applies to swap' in result.stderr


def test_build_script_does_not_modify_production_build():
    script = (ROOT / 'tools' / 'build_updater_lab.cmd').read_text(encoding='utf-8')
    assert 'QuietWriterUpdaterLab' in script
    assert 'updater-lab' in script
    assert 'build_exe.cmd' not in script
    assert 'quietwriter_updater_lab.py' in script
