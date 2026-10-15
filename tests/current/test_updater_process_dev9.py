"""Separate updater process and conservative safety tests."""
import os
from pathlib import Path
import subprocess
import sys

import pytest
from quietwriter.updater_process import run_handoff, wait_for_exit, LOCK
from quietwriter.windows_portable_updater import (PortableUpdateError, make_test_archive,
                                                   make_test_install)


def fixture(tmp_path):
    install = make_test_install(tmp_path)
    archive, digest = make_test_archive(tmp_path / 'update.zip')
    return install, archive, digest


def test_success_and_restart_fixture(tmp_path):
    root, archive, digest = fixture(tmp_path)
    marker = root / 'test-restarted.flag'
    run_handoff(root, archive, digest, restart_marker=marker)
    assert marker.read_text() == 'restarted'
    assert (root / 'version.txt').read_text().strip() == '1.5.1'


def test_failure_never_restarts(tmp_path):
    root, archive, digest = fixture(tmp_path)
    marker = root / 'test-restarted.flag'
    with pytest.raises(PortableUpdateError, match='restored'):
        run_handoff(root, archive, digest, fail_after=1, restart_marker=marker)
    assert not marker.exists()
    assert (root / 'version.txt').read_text().strip() == '1.5.0'


def test_double_update_rejected(tmp_path):
    root, archive, digest = fixture(tmp_path)
    lock = root.parent / ('.' + root.name + LOCK)
    lock.write_text('existing')
    with pytest.raises(PortableUpdateError, match='already in progress'):
        run_handoff(root, archive, digest)
    assert lock.read_text() == 'existing'


def test_untrusted_install_rejected(tmp_path):
    root, archive, digest = fixture(tmp_path)
    (root / '.quietwriter-updater-integration-test.json').unlink()
    with pytest.raises(PortableUpdateError, match='Production installs'):
        run_handoff(root, archive, digest)


def test_invalid_pid_and_timeout(tmp_path):
    with pytest.raises(PortableUpdateError, match='Invalid source'):
        wait_for_exit(os.getpid(), .1)
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(3)'])
    try:
        with pytest.raises(PortableUpdateError, match='did not close'):
            wait_for_exit(child.pid, .1)
    finally:
        child.terminate()
        child.wait(timeout=5)


def test_handoff_wait_failure_does_not_modify(tmp_path):
    root, archive, digest = fixture(tmp_path)
    with pytest.raises(PortableUpdateError):
        run_handoff(root, archive, digest, source_pid=os.getpid())
    assert (root / 'version.txt').read_text().strip() == '1.5.0'
    assert not (root.parent / ('.' + root.name + LOCK)).exists()


def test_restart_path_rejected(tmp_path):
    root, archive, digest = fixture(tmp_path)
    with pytest.raises(PortableUpdateError, match='Unsafe restart'):
        run_handoff(root, archive, digest, restart_marker=tmp_path / 'outside')
