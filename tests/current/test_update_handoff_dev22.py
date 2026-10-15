"""Test the isolated EXE process handoff without modifying any installation."""
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from quietwriter.update_handoff_probe import rehearse_handoff, main
from quietwriter.update_health import HealthCheckError
from quietwriter.windows_portable_updater import PortableUpdateError


def test_health_is_run_after_wait(monkeypatch, tmp_path):
    events=[]
    monkeypatch.setattr('quietwriter.update_handoff_probe.wait_for_exit', lambda pid,t: events.append(('wait',pid)))
    monkeypatch.setattr('quietwriter.update_handoff_probe.probe_executable', lambda exe,directory,timeout: events.append(('health',str(exe))))
    rehearse_handoff(tmp_path/'QuietWriter.exe',source_pid=987,health_directory=tmp_path)
    assert events == [('wait',987),('health',str(tmp_path/'QuietWriter.exe'))]


def test_failed_wait_never_probes(monkeypatch,tmp_path):
    monkeypatch.setattr('quietwriter.update_handoff_probe.wait_for_exit',lambda pid,t: (_ for _ in ()).throw(PortableUpdateError('not closed')))
    monkeypatch.setattr('quietwriter.update_handoff_probe.probe_executable',lambda *a,**k: pytest.fail('should not probe'))
    with pytest.raises(PortableUpdateError):
        rehearse_handoff(tmp_path/'QuietWriter.exe',source_pid=555,health_directory=tmp_path)


def test_failed_health_is_reported_without_write(monkeypatch,tmp_path):
    monkeypatch.setattr('quietwriter.update_handoff_probe.probe_executable',lambda *a,**k: (_ for _ in ()).throw(HealthCheckError('bad')))
    assert main(['--executable',str(tmp_path/'QuietWriter.exe'),'--health-directory',str(tmp_path)]) == 1


def test_negative_timeout_rejected(tmp_path):
    with pytest.raises(SystemExit) as err:
        main(['--executable',str(tmp_path/'QuietWriter.exe'),'--health-directory',str(tmp_path),'--wait-timeout','0'])
    assert err.value.code == 2


def test_script_runs_independent_process(tmp_path):
    script=Path(__file__).resolve().parents[2]/'tools/test_external_exe_handoff.py'
    exe=tmp_path/'QuietWriter.exe';exe.write_bytes(b'not executable')
    proc=subprocess.run([sys.executable,str(script),str(exe)],capture_output=True,text=True,timeout=30)
    assert proc.returncode == 1
    assert 'FAIL: independent EXE handoff probe' in proc.stderr
    assert exe.read_bytes() == b'not executable'
