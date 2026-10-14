"""Crash after second rename and version policy regressions."""
from pathlib import Path
import os
import subprocess
import sys
import pytest
from quietwriter.side_by_side_update import swap_test_install, recover_test_update, _paths
from quietwriter.windows_portable_updater import make_test_install, make_test_archive, PortableUpdateError
from quietwriter.update_download import VerifiedAsset, UpdateDownloadError
from quietwriter.update_version_policy import require_upgrade, require_manifest_freshness


def test_recover_after_second_rename_hard_process_death(tmp_path):
    root = make_test_install(tmp_path)
    (root/'books').mkdir()
    (root/'books'/'chapter.txt').write_text('personal')
    archive, digest = make_test_archive(tmp_path/'update.zip')
    script = 'import os,sys\nfrom pathlib import Path\nfrom quietwriter import side_by_side_update as s\nroot=Path(sys.argv[1]);new,old,_=s._paths(root); original=s.os.replace\ndef intercept(a,b):\n    original(a,b)\n    if Path(a)==new and Path(b)==root: os._exit(23)\ns.os.replace=intercept\ns.swap_test_install(root,Path(sys.argv[2]),sys.argv[3])\n'
    result = subprocess.run([sys.executable,'-c',script,str(root),str(archive),digest],cwd=Path(__file__).resolve().parents[2])
    assert result.returncode == 23
    assert (root/'version.txt').read_text().strip() == '1.5.1'
    assert _paths(root)[1].exists()
    assert recover_test_update(root)
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert (root/'books'/'chapter.txt').read_text() == 'personal'
    assert not _paths(root)[2].exists()


def test_recovery_after_injected_second_rename_fault(tmp_path):
    root = make_test_install(tmp_path)
    archive,digest = make_test_archive(tmp_path/'update.zip')
    with pytest.raises(PortableUpdateError):
        swap_test_install(root,archive,digest,fault='after_new_rename')
    assert (root/'version.txt').read_text().strip() == '1.5.0'


def asset(v):
    return VerifiedAsset(v,'https://github.com/gen-x-coder/QuietWriter/releases/download/v'+v+'/QuietWriter-windows-portable.zip','QuietWriter-windows-portable.zip',3,'0'*64)

@pytest.mark.parametrize('current,candidate,allowed', [('1.5.0','1.4.0',False),('1.5.0','1.5.0',False),('1.5.0','1.5.1',True),('1.5.0-dev.13','1.5.0',True),('1.5.0-dev.13','1.4.9',False)])
def test_upgrade_policy(current,candidate,allowed):
    if allowed: require_upgrade(asset(candidate),current)
    else:
        with pytest.raises(UpdateDownloadError): require_upgrade(asset(candidate),current)


def test_replay_rejected():
    with pytest.raises(UpdateDownloadError,match='replay'):
        require_upgrade(asset('1.5.2'),'1.5.0',highest_seen='1.5.3')


def test_signed_expiration():
    with pytest.raises(UpdateDownloadError,match='expired'):
        require_manifest_freshness('2020-01-01T00:00:00Z')
    require_manifest_freshness('2099-01-01T00:00:00Z')
