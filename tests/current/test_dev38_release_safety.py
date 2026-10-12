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
    snapshot = Path('SNAPSHOT_INFO.txt').read_text(encoding='utf-8')
    assert quietwriter.__version__ == '1.4.0'
    assert f'Application version: {quietwriter.__version__}' in snapshot
    assert 'Previous stable public release: 1.3.1' in snapshot
