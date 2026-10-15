"""Disposable REAL EXE rehearsal: journaled directory swap in a worker process.

This is a test harness, NOT a production updater. It will only operate inside
an internally-created TemporaryDirectory with a private marker. Supplied build
folders are read-only inputs, and the normal QuietWriter app never imports it.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from .side_by_side_update import _update_lock, _tree_digest
from .update_health import probe_executable
from .update_real_exe_lab import _source, RehearsalError

MARKER = '.qw-real-rehearsal-marker'
JOURNAL = '.qw-real-rehearsal-journal.json'


def _hash_tree(root: Path) -> str:
    """Use the single unambiguous tree-digest primitive shared with fixture engine."""
    try:
        return _tree_digest(root)
    except Exception as exc:
        raise RehearsalError('Missing or unsafe rehearsal tree') from exc


def _write_journal(work: Path, data: dict) -> None:
    p = work / JOURNAL
    tmp = work / (JOURNAL + '.' + os.urandom(8).hex() + '.tmp')
    with tmp.open('x', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp, p)
    finally:
        tmp.unlink(missing_ok=True)


def _rename_with_windows_retry(source: Path, destination: Path, *, timeout: float = 3.0) -> None:
    """Retry transient Windows sharing failures, never changing the safety checks.

    For lab use only. POSIX and non-sharing failures fail immediately.
    """
    deadline = time.monotonic() + timeout
    delay = 0.05
    while True:
        try:
            os.replace(source, destination)
            return
        except PermissionError as exc:
            winerror = getattr(exc, 'winerror', None)
            if os.name != 'nt' or winerror not in (5, 32, 33) or time.monotonic() >= deadline:
                raise
            time.sleep(min(delay, max(0.0, deadline - time.monotonic())))
            delay = min(delay * 2, 0.5)


def _phase(work: Path, current: dict, phase: str) -> None:
    """Record intent before a directory rename; recovery verifies actual trees."""
    _write_journal(work, {**current, 'phase': phase})


def _workspace(work: Path) -> None:
    if not work.is_dir() or work.is_symlink() or not (work / MARKER).is_file():
        raise RehearsalError('Not a private disposable rehearsal workspace')
    if (work / MARKER).read_text(encoding='ascii') != 'NONPRODUCTION-TEST-FIXTURE\n':
        raise RehearsalError('Invalid private rehearsal marker')


def _journal(work: Path) -> dict:
    try:
        d = json.loads((work / JOURNAL).read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        raise RehearsalError('Missing or damaged rehearsal journal') from exc
    if d.get('schema') != 1 or d.get('phase') not in ('staged', 'renaming-old', 'old-renamed', 'renaming-new', 'new-renamed') or not isinstance(d.get('old_hash'), str) or not isinstance(d.get('new_hash'), str):
        raise RehearsalError('Invalid rehearsal journal')
    return d


def _paths(work: Path):
    return work / 'QuietWriter', work / 'QuietWriter.next', work / 'QuietWriter.previous'


def _serialized_worker(fn):
    """A crash-released OS lock shared by swap, recovery and commit.

    Test workspaces only. The lock lives next to the active directory and
    survives directory renames; its kernel ownership does not survive a crash.
    """
    from functools import wraps
    @wraps(fn)
    def wrapper(work: Path, *args, **kwargs):
        work = Path(work).resolve(strict=True)
        _workspace(work)
        with _update_lock(work / 'QuietWriter'):
            return fn(work, *args, **kwargs)
    return wrapper


def verify_candidate_file_list(candidate: Path, manifest: Path) -> str:
    """Verify a disposable candidate against an independently supplied lab file list.

    The manifest MUST be created from a known-complete source *before* copying
    into QuietWriter.next. This is not a signature or a production trust root.
    """
    manifest = Path(manifest).resolve(strict=True)
    candidate = Path(candidate).resolve(strict=True)
    if manifest == candidate or candidate in manifest.parents:
        raise RehearsalError('Candidate cannot supply its own trusted file list')
    try:
        specification = json.loads(manifest.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError) as exc:
        raise RehearsalError('Invalid independent lab file manifest') from exc
    if not isinstance(specification, dict) or specification.get('schema') != 1 or not isinstance(specification.get('files'), dict):
        raise RehearsalError('Invalid independent lab file manifest')
    expected = specification['files']
    if not expected or len(expected) > 20000:
        raise RehearsalError('Invalid lab file count')
    observed = {}
    for file in candidate.rglob('*'):
        if file.is_symlink() or (hasattr(file, 'is_junction') and file.is_junction()):
            raise RehearsalError('Unsafe link in candidate')
        if file.is_file():
            name = file.relative_to(candidate).as_posix()
            observed[name] = file
    if set(observed) != set(expected):
        raise RehearsalError('Staged build does not match independent file manifest')
    for name, details in expected.items():
        if (not isinstance(name, str) or name.startswith('/') or '\\' in name or
            any(part in ('', '.', '..') for part in name.split('/')) or
            not isinstance(details, dict) or
            not isinstance(details.get('size'), int) or details['size'] < 0 or
            not isinstance(details.get('sha256'), str) or len(details['sha256']) != 64):
            raise RehearsalError('Invalid independent lab file manifest')
        file = observed[name]
        if file.stat().st_size != details['size']:
            raise RehearsalError('Staged build does not match independent file manifest')
        checksum = hashlib.sha256()
        with file.open('rb') as stream:
            for block in iter(lambda: stream.read(256 * 1024), b''):
                checksum.update(block)
        if checksum.hexdigest() != details['sha256']:
            raise RehearsalError('Staged build does not match independent file manifest')
    return _hash_tree(candidate)


@_serialized_worker
def swap_worker(work: Path, *, crash: str | None = None, expected_candidate_sha256: str | None = None,
                independent_file_manifest: Path | None = None) -> None:
    """Executed in a separate Python process and only on marked test copies."""
    work = Path(work).resolve(strict=True)
    _workspace(work)
    a, n, o = _paths(work)
    if not a.is_dir() or not n.is_dir() or (work / JOURNAL).exists():
        raise RehearsalError('Unclean rehearsal workspace')
    # Old retained builds cannot be overwritten in place. Rotate safely, without deleting.
    if o.exists():
        if not o.is_dir() or o.is_symlink():
            raise RehearsalError('Untrusted retained previous build')
        os.replace(o, work / ('QuietWriter.previous-retained-' + os.urandom(8).hex()))
    # Prevent a stale, failed write-ahead journal from blocking subsequent updates.
    # This is safe only while no committed journal exists and under the OS lock.
    for stale in work.glob(JOURNAL + '.*.tmp'):
        if stale.is_symlink() or not stale.is_file():
            raise RehearsalError('Unsafe leftover journal')
        stale.unlink()
    legacy_tmp = work / (JOURNAL + '.tmp')
    if legacy_tmp.exists():
        if legacy_tmp.is_symlink() or not legacy_tmp.is_file():
            raise RehearsalError('Unsafe leftover legacy journal')
        legacy_tmp.unlink()
    old_hash = _hash_tree(a)
    new_hash = (verify_candidate_file_list(n, independent_file_manifest)
                if independent_file_manifest is not None else _hash_tree(n))
    if expected_candidate_sha256 is not None:
        if len(expected_candidate_sha256) != 64 or expected_candidate_sha256.lower() != new_hash:
            raise RehearsalError('Staged build does not match trusted candidate digest')
    # Without a signed release manifest the laboratory cannot know that a staged
    # build is complete. Keep this entrypoint LAB ONLY, never production.
    journal_data = {'schema': 1, 'old_hash': old_hash, 'new_hash': new_hash}
    _phase(work, journal_data, 'staged')
    if crash == 'staged':
        os._exit(9)
    _phase(work, journal_data, 'renaming-old')
    _rename_with_windows_retry(a, o)
    _phase(work, journal_data, 'old-renamed')
    if crash == 'old-renamed':
        os._exit(9)
    _phase(work, journal_data, 'renaming-new')
    _rename_with_windows_retry(n, a)
    _phase(work, journal_data, 'new-renamed')
    if crash == 'new-renamed':
        os._exit(9)
    if _hash_tree(a) != new_hash:
        raise RehearsalError('Updated directory verification failed')


@_serialized_worker
def recover_worker(work: Path) -> None:
    """Verify BOTH trees; never delete an unverified active installation."""
    work = Path(work).resolve(strict=True)
    _workspace(work)
    d = _journal(work)
    a, n, o = _paths(work)
    if o.exists():
        if _hash_tree(o) != d['old_hash']:
            raise RehearsalError('Corrupt previous version; manual recovery required')
        if a.exists():
            if _hash_tree(a) != d['new_hash']:
                raise RehearsalError('Untrusted active tree; manual recovery required')
            if n.exists():
                raise RehearsalError('Ambiguous rehearsal trees')
            _rename_with_windows_retry(a, n)
        elif n.exists() and _hash_tree(n) != d['new_hash']:
            raise RehearsalError('Corrupt staged tree')
        _rename_with_windows_retry(o, a)
    elif not a.exists() or _hash_tree(a) != d['old_hash']:
        raise RehearsalError('Cannot verify original rehearsal build')
    if n.exists():
        if _hash_tree(n) != d['new_hash']:
            raise RehearsalError('Untrusted staged rehearsal tree; manual recovery required')
        # Never remove a candidate until it has been verified. Preserve it
        # outside the active slot for examination instead of deleting it.
        os.replace(n, work / ('QuietWriter.recovered-candidate-' + os.urandom(8).hex()))
    (work / JOURNAL).unlink()
    if _hash_tree(a) != d['old_hash']:
        raise RehearsalError('Recovered tree failed verification')


@_serialized_worker
def finish_worker(work: Path) -> None:
    work = Path(work).resolve(strict=True)
    _workspace(work)
    d = _journal(work)
    a, n, o = _paths(work)
    if not o.is_dir() or _hash_tree(o) != d['old_hash'] or _hash_tree(a) != d['new_hash'] or n.exists():
        raise RehearsalError('Cannot commit unverified rehearsal')
    (work / JOURNAL).unlink()


def _worker(work: Path, command: str, crash: str | None = None) -> subprocess.CompletedProcess:
    # The tool itself has its own project-root bootstrap and runs isolated (-I).
    tool = Path(__file__).resolve().parents[1] / 'tools' / 'real_update_transaction_worker.py'
    argv = [sys.executable, '-I', str(tool), command, str(work)]
    if crash:
        argv.extend(['--crash', crash])
    return subprocess.run(argv, cwd=str(work.parent), capture_output=True, text=True, timeout=50)


def rehearse_transaction(current: Path, candidate: Path, *, fault: str | None = None,
                          probe=probe_executable) -> dict:
    """Crash-proof lab rehearsal using external worker and genuine EXE health probe."""
    current, candidate = _source(current), _source(candidate)
    if current == candidate:
        raise RehearsalError('Builds must be distinct')
    with tempfile.TemporaryDirectory(prefix='qw-transaction-real-exe-') as td:
        w = Path(td)
        (w / MARKER).write_text('NONPRODUCTION-TEST-FIXTURE\n', encoding='ascii')
        a, n, o = _paths(w)
        shutil.copytree(current, a)
        shutil.copytree(candidate, n)
        original_hash = _hash_tree(a)
        p = _worker(w, 'swap', fault if fault in ('staged', 'renaming-old', 'old-renamed', 'renaming-new', 'new-renamed') else None)
        if p.returncode != 0:
            if fault not in ('staged', 'renaming-old', 'old-renamed', 'renaming-new', 'new-renamed') or p.returncode != 9:
                raise RehearsalError('External swap failed: ' + p.stderr[-500:])
            r = _worker(w, 'recover')
            if r.returncode != 0 or _hash_tree(a) != original_hash:
                raise RehearsalError('Recovery after process kill failed: ' + r.stderr[-500:])
            return {'result':'RECOVERED', 'originals_modified':False}
        try:
            if fault == 'health':
                raise RehearsalError('Injected EXE health failure')
            probe(a / 'QuietWriter.exe', w)
        except Exception as exc:
            r = _worker(w, 'recover')
            if r.returncode != 0 or _hash_tree(a) != original_hash:
                raise RehearsalError('Health failed; automatic recovery failed: ' + r.stderr[-500:]) from exc
            return {'result':'ROLLED_BACK', 'originals_modified':False}
        p = _worker(w, 'commit')
        if p.returncode != 0:
            raise RehearsalError('Commit failed: ' + p.stderr[-500:])
        return {'result':'PASS','health':'verified','originals_modified':False}
