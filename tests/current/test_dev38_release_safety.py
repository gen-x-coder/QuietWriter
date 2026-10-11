from pathlib import Path
import subprocess
import sys
import pytest


def test_no_undefined_names():
    pytest.importorskip("pyflakes")
    result = subprocess.run([sys.executable, 'tools/check_undefined_names.py'], capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr


def test_release_version_agrees():
    import quietwriter
    assert quietwriter.__version__ == '1.4.0-dev.39'
    assert '1.4.0-dev.39' in Path('SNAPSHOT_INFO.txt').read_text()
    assert '1.3.1' in Path('SNAPSHOT_INFO.txt').read_text()
