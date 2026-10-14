"""Safe EXE health probe contract; all subprocesses here are mocked."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from quietwriter.update_health import HealthCheckError, probe_executable, run_health_check

TOKEN = 'a' * 64

def test_health_ack_only_after_success(tmp_path):
    marker=tmp_path/'ok'
    assert run_health_check(TOKEN,marker,lambda: 0)==0
    assert marker.read_text() == TOKEN


def test_health_failure_does_not_create_marker(tmp_path):
    marker=tmp_path/'ok'
    assert run_health_check(TOKEN,marker,lambda: 7)==7
    assert not marker.exists()


def test_health_refuses_overwriting_existing_data(tmp_path):
    marker=tmp_path/'notes'
    marker.write_text('do not touch')
    with pytest.raises(HealthCheckError):
        run_health_check(TOKEN,marker,lambda: 0)
    assert marker.read_text()=='do not touch'


def test_health_refuses_bad_token(tmp_path):
    with pytest.raises(HealthCheckError):
        run_health_check('bad',tmp_path/'ok',lambda: 0)


def test_probe_requires_acknowledgement(tmp_path):
    exe=tmp_path/'QuietWriter.exe'; exe.write_bytes(b'mock')
    with pytest.raises(HealthCheckError):
        probe_executable(exe,tmp_path,runner=lambda *a,**k:SimpleNamespace(returncode=0))


def test_probe_rejects_nonzero_exit(tmp_path):
    exe=tmp_path/'QuietWriter.exe'; exe.write_bytes(b'mock')
    with pytest.raises(HealthCheckError):
        probe_executable(exe,tmp_path,runner=lambda *a,**k:SimpleNamespace(returncode=1))


def test_probe_accepts_matching_ack(tmp_path):
    exe=tmp_path/'QuietWriter.exe'; exe.write_bytes(b'mock')
    def runner(args, **kwargs):
        Path(args[-1]).write_text(args[-2],encoding='ascii')
        return SimpleNamespace(returncode=0)
    probe_executable(exe,tmp_path,runner=runner)
    assert list(tmp_path.glob('health-*'))==[]


def test_probe_rejects_wrong_ack(tmp_path):
    exe=tmp_path/'QuietWriter.exe'; exe.write_bytes(b'mock')
    def runner(args, **kwargs):
        Path(args[-1]).write_text('wrong',encoding='ascii')
        return SimpleNamespace(returncode=0)
    with pytest.raises(HealthCheckError):
        probe_executable(exe,tmp_path,runner=runner)
    assert list(tmp_path.glob('health-*'))==[]


def test_probe_rejects_other_executable(tmp_path):
    exe=tmp_path/'Other.exe'; exe.write_bytes(b'mock')
    with pytest.raises(HealthCheckError):
        probe_executable(exe,tmp_path)
