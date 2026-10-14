"""Crash recovery and fail-closed lab handoff regressions."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from quietwriter.side_by_side_update import swap_test_install, recover_test_update, _paths
from quietwriter.windows_portable_updater import PortableUpdateError
import runpy
fixture = runpy.run_path(str(Path(__file__).with_name("test_update_dev16.py")))["fixture"]

SCRIPT = Path(__file__).resolve().parents[2] / 'tools/test_signed_update_handoff.py'

def test_post_swap_crash_recovered_in_new_process(tmp_path):
    root, archive, manifest, sig, pub, key = fixture(tmp_path)
    digest = __import__('hashlib').sha256(archive.read_bytes()).hexdigest()
    code = ("import os,sys;from pathlib import Path;"
            "from quietwriter.side_by_side_update import swap_test_install;"
            "swap_test_install(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3],retain_journal=True);"
            "os._exit(17)")
    cmd = [sys.executable, '-c', code, str(root), str(archive), digest]
    result = subprocess.run(cmd, cwd=str(SCRIPT.parents[1]), capture_output=True, timeout=20)
    assert result.returncode == 17, result.stderr
    assert (root/'version.txt').read_text().strip() == '1.5.1'
    (tmp_path/'empty').write_bytes(b'')
    proc = subprocess.run([sys.executable,str(SCRIPT),'--install',str(root),'--archive',str(archive),
        '--manifest',str(tmp_path/'empty'),'--signature',str(tmp_path/'empty'),
        '--test-public-key',str(tmp_path/'empty'),'--recover-only'],
        capture_output=True,text=True,timeout=20)
    assert proc.returncode == 0, proc.stderr
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert not _paths(root)[2].exists()

def test_corrupt_journal_fail_closed(tmp_path):
    root, archive, *_ = fixture(tmp_path)
    new, old, journal = _paths(root)
    journal.write_text('{broken',encoding='utf-8')
    with pytest.raises(PortableUpdateError, match='Unreadable update journal'):
        recover_test_update(root)
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert journal.exists()

def test_unknown_journal_fail_closed(tmp_path):
    root, archive, *_ = fixture(tmp_path)
    new, old, journal = _paths(root)
    journal.write_text(json.dumps({'schema':99}),encoding='utf-8')
    with pytest.raises(PortableUpdateError, match='Unknown update journal'):
        recover_test_update(root)
    assert journal.exists()

def test_no_pending_recovery_is_idempotent(tmp_path):
    root, archive, *_ = fixture(tmp_path)
    assert recover_test_update(root) is False
    assert recover_test_update(root) is False
    assert (root/'version.txt').read_text().strip() == '1.5.0'
