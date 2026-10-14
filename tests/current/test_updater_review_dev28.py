"""Review regressions on disposable laboratory only."""
from pathlib import Path
import hashlib
import pytest
from quietwriter.update_real_transaction_lab import MARKER, JOURNAL, _hash_tree, swap_worker, recover_worker, finish_worker
from quietwriter.update_real_exe_lab import RehearsalError

def fixture(tmp_path):
    (tmp_path / MARKER).write_text('NONPRODUCTION-TEST-FIXTURE\n')
    for name, ver in [('QuietWriter','OLD'),('QuietWriter.next','NEW')]:
        d=tmp_path/name; d.mkdir(); (d/'QuietWriter.exe').write_text(ver)
    return tmp_path

def test_two_updates(tmp_path):
    w=fixture(tmp_path);swap_worker(w);finish_worker(w)
    (w/'QuietWriter.next').mkdir();(w/'QuietWriter.next'/'QuietWriter.exe').write_text('NEW2')
    swap_worker(w);finish_worker(w)
    assert (w/'QuietWriter'/'QuietWriter.exe').read_text()=='NEW2'

def test_stale_tmp_does_not_block(tmp_path):
    w=fixture(tmp_path);(w/(JOURNAL+'.tmp')).write_text('partial')
    swap_worker(w);finish_worker(w)
    assert not (w/(JOURNAL+'.tmp')).exists()

def test_digest_is_unambiguous(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir()
    (a/'a').write_bytes(b'1'+(1).to_bytes(4,'big')+b'b2')
    (b/'a').write_bytes(b'1');(b/'b').write_bytes(b'2')
    assert _hash_tree(a)!=_hash_tree(b)

def test_expected_digest_rejects_truncated(tmp_path):
    w=fixture(tmp_path); good=_hash_tree(w/'QuietWriter.next')
    (w/'QuietWriter.next'/'QuietWriter.exe').write_text('TRUNCATED')
    with pytest.raises(RehearsalError,match='trusted candidate digest'):
        swap_worker(w, expected_candidate_sha256=good)
    assert (w/'QuietWriter'/'QuietWriter.exe').read_text()=='OLD'

def test_recover_with_existing_rescue(tmp_path):
    w=fixture(tmp_path); (w/'QuietWriter.recovered-candidate').mkdir()
    (w/'QuietWriter.recovered-candidate'/'old.txt').write_text('KEEP')
    swap_worker(w);recover_worker(w)
    assert (w/'QuietWriter'/'QuietWriter.exe').read_text()=='OLD'
    assert (w/'QuietWriter.recovered-candidate'/'old.txt').read_text()=='KEEP'
