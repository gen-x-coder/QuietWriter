"""OS-lock and crash-recovery regressions for disposable install directories."""
import os
from pathlib import Path
import subprocess
import sys
import pytest
from quietwriter.side_by_side_update import swap_test_install, recover_test_update, _update_lock, _paths
from quietwriter.windows_portable_updater import make_test_install, make_test_archive, PortableUpdateError


def fixture(tmp_path):
    root = make_test_install(tmp_path)
    archive, digest = make_test_archive(tmp_path / 'package.zip')
    return root, archive, digest


def test_lock_exclusive_between_processes(tmp_path):
    root, archive, digest = fixture(tmp_path)
    with _update_lock(root):
        code = 'import sys; from quietwriter.side_by_side_update import recover_test_update; recover_test_update(sys.argv[1])'
        child = subprocess.run([sys.executable, '-c', code, str(root)], capture_output=True, text=True, cwd=Path(__file__).resolve().parents[2])
        assert child.returncode != 0
        assert 'already in progress' in child.stderr
    assert not recover_test_update(root)


def test_lock_released_after_process_crash(tmp_path):
    root, archive, digest = fixture(tmp_path)
    code = 'import os,sys; from quietwriter.side_by_side_update import _update_lock; from pathlib import Path;\nwith _update_lock(Path(sys.argv[1])): os._exit(17)'
    code = code.replace('\\n','\n')
    result = subprocess.run([sys.executable, '-c', code, str(root)], cwd=Path(__file__).resolve().parents[2])
    assert result.returncode == 17
    assert not recover_test_update(root)
    swap_test_install(root, archive, digest)
    assert (root/'version.txt').read_text().strip() == '1.5.1'


def test_recovery_after_real_crash_during_first_swap(tmp_path):
    root, archive, digest = fixture(tmp_path)
    script = '''import os,sys
from pathlib import Path
from quietwriter import side_by_side_update as s
root=Path(sys.argv[1]); old=s._paths(root)[1]
original=s.os.replace
def broken(a,b):
    original(a,b)
    if Path(a)==root and Path(b)==old: os._exit(19)
s.os.replace=broken
s.swap_test_install(root,Path(sys.argv[2]),sys.argv[3])
'''
    result = subprocess.run([sys.executable, '-c', script, str(root), str(archive), digest], cwd=Path(__file__).resolve().parents[2])
    assert result.returncode == 19
    assert not root.exists()
    assert recover_test_update(root)
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    swap_test_install(root,archive,digest)
    assert (root/'version.txt').read_text().strip() == '1.5.1'


def test_ambiguous_both_installations_preserved(tmp_path):
    root, archive, digest = fixture(tmp_path)
    with pytest.raises(PortableUpdateError):
        swap_test_install(root,archive,digest,fault='after_new_rename')
    assert root.exists()
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert not _paths(root)[2].exists()
