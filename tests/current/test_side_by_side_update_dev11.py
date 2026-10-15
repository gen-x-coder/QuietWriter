import hashlib
from pathlib import Path
import pytest
from quietwriter.windows_portable_updater import make_test_install, make_test_archive, PortableUpdateError
from quietwriter.side_by_side_update import swap_test_install, recover_test_update, _paths


def setup(tmp_path):
    root = make_test_install(tmp_path)
    (root/'books').mkdir()
    (root/'books'/'my_book.txt').write_text('do not lose')
    (root/'_internal').mkdir()
    (root/'_internal'/'obsolete.dll').write_bytes(b'old')
    arc, digest = make_test_archive(tmp_path/'update.zip')
    return root,arc,digest

def test_success_removes_obsolete_keeps_user_and_backup(tmp_path):
    root,arc,digest=setup(tmp_path)
    swap_test_install(root,arc,digest)
    assert (root/'version.txt').read_text().strip() == '1.5.1'
    assert not (root/'_internal'/'obsolete.dll').exists()
    assert (root/'books'/'my_book.txt').read_text() == 'do not lose'
    assert _paths(root)[1].exists()

def test_interrupted_swap_restores_old(tmp_path):
    root,arc,digest=setup(tmp_path)
    with pytest.raises(PortableUpdateError):swap_test_install(root,arc,digest,fault='after_old_rename')
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert (root/'books'/'my_book.txt').read_text() == 'do not lose'

def test_interrupted_after_new_rename_preserves_rescue(tmp_path):
    root,arc,digest=setup(tmp_path)
    with pytest.raises(PortableUpdateError):swap_test_install(root,arc,digest,fault='after_new_rename')
    assert (root/'version.txt').read_text().strip() == '1.5.0'

def test_untrusted_real_executable_rejected(tmp_path):
    import zipfile
    root,arc,digest=setup(tmp_path)
    with zipfile.ZipFile(arc,'w') as z: z.writestr('QuietWriter.exe',b'MZ real exe')
    digest=hashlib.sha256(arc.read_bytes()).hexdigest()
    with pytest.raises(PortableUpdateError,match='NONEXECUTABLE'):
        swap_test_install(root,arc,digest)
    assert (root/'version.txt').read_text().strip() == '1.5.0'

def test_bad_hash_rejected(tmp_path):
    root,arc,digest=setup(tmp_path)
    with pytest.raises(PortableUpdateError,match='integrity'):
        swap_test_install(root,arc,'0'*64)
    assert (root/'version.txt').read_text().strip() == '1.5.0'

def test_process_death_after_first_rename_recovers_on_next_run(tmp_path):
    import subprocess, sys
    root, arc, digest = setup(tmp_path)
    script = '''import sys, os
from pathlib import Path
from quietwriter import side_by_side_update as s
real=s.os.replace
root=Path(sys.argv[1])
old=s._paths(root)[1]
def intercept(a,b):
    real(a,b)
    if Path(a)==root and Path(b)==old:
        os._exit(9)
s.os.replace=intercept
s.swap_test_install(root,Path(sys.argv[2]),sys.argv[3])
'''
    done=subprocess.run([sys.executable,'-c',script,str(root),str(arc),digest], cwd=Path(__file__).resolve().parents[2])
    assert done.returncode == 9
    assert not root.exists()
    assert recover_test_update(root)
    assert (root/'version.txt').read_text().strip() == '1.5.0'
    assert (root/'books'/'my_book.txt').read_text() == 'do not lose'
