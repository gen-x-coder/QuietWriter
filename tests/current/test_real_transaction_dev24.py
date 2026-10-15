from pathlib import Path
import pytest
from quietwriter.update_real_transaction_lab import rehearse_transaction, RehearsalError

def build(path,label):
    path.mkdir()
    (path/'QuietWriter.exe').write_bytes(label.encode())
    (path/'_internal').mkdir()
    (path/'_internal'/'payload.dll').write_text(label)
    return path

def test_external_transaction_health_and_sources(tmp_path):
    a=build(tmp_path/'old','old'); b=build(tmp_path/'candidate','new')
    def probe(exe,w):
        assert exe.read_bytes()==b'new'
        assert (exe.parent/'_internal'/'payload.dll').read_text()=='new'
        assert (w/'QuietWriter.previous'/'QuietWriter.exe').read_bytes()==b'old'
    assert rehearse_transaction(a,b,probe=probe)['result']=='PASS'
    assert (a/'QuietWriter.exe').read_bytes()==b'old'
    assert (b/'QuietWriter.exe').read_bytes()==b'new'

@pytest.mark.parametrize('fault,expected',[('health','ROLLED_BACK'),('staged','RECOVERED'),('old-renamed','RECOVERED'),('new-renamed','RECOVERED')])
def test_external_transaction_fault_and_recovery(tmp_path,fault,expected):
    a=build(tmp_path/'old','old');b=build(tmp_path/'candidate','new')
    def probe(exe,w):
        assert False, 'must not execute a health probe after a killed worker'
    assert rehearse_transaction(a,b,fault=fault,probe=probe)['result']==expected
    assert (a/'QuietWriter.exe').read_bytes()==b'old'
    assert (b/'QuietWriter.exe').read_bytes()==b'new'

def test_same_source_forbidden(tmp_path):
    a=build(tmp_path/'old','old')
    with pytest.raises(RehearsalError,match='distinct'):
        rehearse_transaction(a,a)
