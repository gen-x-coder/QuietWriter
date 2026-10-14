"""Independent-process locking and recoverable staging; rehearsal only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from quietwriter.update_real_transaction_lab import (
    _paths, _hash_tree, _write_journal, recover_worker, swap_worker,
    MARKER, RehearsalError,
)
from quietwriter.windows_portable_updater import PortableUpdateError


def fixture(work):
    work.mkdir()
    (work / MARKER).write_text('NONPRODUCTION-TEST-FIXTURE\n', encoding='ascii')
    current, next_, _ = _paths(work)
    current.mkdir()
    next_.mkdir()
    (current / 'QuietWriter.exe').write_bytes(b'old')
    (next_ / 'QuietWriter.exe').write_bytes(b'new')
    return current, next_


def test_recover_staged_keeps_verified_candidate(tmp_path):
    work = tmp_path / 'lab'
    old, new = fixture(work)
    before = _hash_tree(old)
    next_hash = _hash_tree(new)
    _write_journal(work, {'schema':1, 'phase':'staged','old_hash':before,'new_hash':next_hash})
    recover_worker(work)
    assert _hash_tree(old) == before
    assert any((d/'QuietWriter.exe').read_bytes() == b'new' for d in work.glob('QuietWriter.recovered-candidate-*'))
    assert not (work / 'QuietWriter.next').exists()
    assert not (work / '.qw-real-rehearsal-journal.json').exists()


def test_recover_rejects_modified_candidate(tmp_path):
    work = tmp_path / 'lab'
    old, new = fixture(work)
    _write_journal(work, {'schema':1, 'phase':'staged', 'old_hash':_hash_tree(old),'new_hash':_hash_tree(new)})
    (new/'QuietWriter.exe').write_bytes(b'corrupt')
    with pytest.raises(RehearsalError, match='Untrusted staged'):
        recover_worker(work)
    assert (old/'QuietWriter.exe').read_bytes() == b'old'
    assert new.exists()


def test_os_lock_blocks_worker_from_another_process(tmp_path):
    work = tmp_path/'lab'
    fixture(work)
    code = '''import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from quietwriter.side_by_side_update import _update_lock
with _update_lock(Path(sys.argv[2]) / 'QuietWriter'):
    print('LOCKED', flush=True)
    time.sleep(10)
'''
    project = Path(__file__).resolve().parents[2]
    proc = subprocess.Popen([sys.executable, '-I', '-c', code, str(project), str(work)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline().strip() == 'LOCKED'
        with pytest.raises(PortableUpdateError, match='already in progress'):
            recover_worker(work)
    finally:
        proc.kill()
        proc.wait(timeout=5)
    # The lock must be released by the OS after a hard process termination.
    # No journal means recovery reports a missing journal, not a stale lock.
    # Windows can briefly report the byte-range lock as busy even after the
    # owner exits. Only the POST-termination assertion retries; contention while
    # the process is running must remain immediately rejected.
    deadline = time.monotonic() + 3.0
    while True:
        try:
            with pytest.raises(RehearsalError, match='journal'):
                recover_worker(work)
            break
        except PortableUpdateError as exc:
            if 'already in progress' not in str(exc) or time.monotonic() >= deadline:
                raise
            time.sleep(0.05)


def test_rehearsal_workspace_fails_closed(tmp_path):
    with pytest.raises((RehearsalError, FileNotFoundError)):
        recover_worker(tmp_path / 'not-a-lab')
