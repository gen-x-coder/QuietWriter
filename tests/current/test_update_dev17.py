"""Independent fixture updater worker, authentication and health failure."""
from pathlib import Path
import subprocess
import sys
import runpy
fixture=runpy.run_path(str(Path(__file__).with_name("test_update_dev16.py")))["fixture"]

SCRIPT=Path(__file__).resolve().parents[2]/'tools/test_signed_update_handoff.py'


def invoke(tmp_path, fail=False, invalid=False):
    root, archive, manifest, sig, pub, key=fixture(tmp_path)
    for name,data in (('manifest',manifest),('sig',bytes(64) if invalid else sig),('pub',pub)):
        (tmp_path/name).write_bytes(data)
    args=[sys.executable,str(SCRIPT),'--install',str(root),'--archive',str(archive),
          '--manifest',str(tmp_path/'manifest'),'--signature',str(tmp_path/'sig'),
          '--test-public-key',str(tmp_path/'pub')]
    if fail:args.append('--health-fail')
    result=subprocess.run(args,text=True,capture_output=True,timeout=30)
    return root,result


def test_independent_worker_accepted_signed_archive(tmp_path):
    root,result=invoke(tmp_path)
    assert result.returncode==0,result.stderr
    assert (root/'version.txt').read_text().strip()=='1.5.1'
    assert (root.parent/('.'+root.name+'.qw-previous')/'version.txt').read_text().strip()=='1.5.0'


def test_independent_worker_health_failure_rolls_back(tmp_path):
    root,result=invoke(tmp_path,fail=True)
    assert result.returncode!=0
    assert (root/'version.txt').read_text().strip()=='1.5.0'
    assert not (root.parent/('.'+root.name+'.qw-update-journal.json')).exists()


def test_independent_worker_rejects_forged_signature_before_swap(tmp_path):
    root,result=invoke(tmp_path,invalid=True)
    assert result.returncode!=0
    assert (root/'version.txt').read_text().strip()=='1.5.0'
    assert not (root.parent/('.'+root.name+'.qw-previous')).exists()
