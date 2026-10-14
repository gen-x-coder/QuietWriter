"""No GitHub, no production installation: independent candidate inventory regressions."""
import hashlib
import json
from pathlib import Path
import pytest
from quietwriter.update_real_transaction_lab import MARKER, swap_worker, verify_candidate_file_list
from quietwriter.update_real_exe_lab import RehearsalError


def prepared(tmp_path):
    lab = tmp_path / 'lab'
    lab.mkdir()
    (lab / MARKER).write_text('NONPRODUCTION-TEST-FIXTURE\n')
    for name, label in [('QuietWriter', 'old'), ('QuietWriter.next', 'new')]:
        folder = lab / name
        (folder / '_internal').mkdir(parents=True)
        (folder / 'QuietWriter.exe').write_text(label)
        (folder / '_internal' / 'required.dll').write_bytes(b'required module')
    new = lab / 'QuietWriter.next'
    entries = {p.relative_to(new).as_posix(): {'size': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in new.rglob('*') if p.is_file()}
    manifest = tmp_path / 'verified-from-source.json'
    manifest.write_text(json.dumps({'schema': 1, 'files': entries}))
    return lab, manifest


def test_verified_lab_swap(tmp_path):
    lab, manifest = prepared(tmp_path)
    swap_worker(lab, independent_file_manifest=manifest)
    assert (lab / 'QuietWriter' / 'QuietWriter.exe').read_text() == 'new'


def test_truncated_copy_rejected_before_rename(tmp_path):
    lab, manifest = prepared(tmp_path)
    (lab / 'QuietWriter.next' / '_internal' / 'required.dll').unlink()
    with pytest.raises(RehearsalError, match='independent file manifest'):
        swap_worker(lab, independent_file_manifest=manifest)
    assert (lab / 'QuietWriter' / 'QuietWriter.exe').read_text() == 'old'
    assert (lab / 'QuietWriter.next').is_dir()


def test_modified_bytes_rejected(tmp_path):
    lab, manifest = prepared(tmp_path)
    (lab / 'QuietWriter.next' / '_internal' / 'required.dll').write_bytes(b'bad module____')
    with pytest.raises(RehearsalError, match='independent file manifest'):
        swap_worker(lab, independent_file_manifest=manifest)
    assert (lab / 'QuietWriter' / 'QuietWriter.exe').read_text() == 'old'


def test_self_supplied_manifest_rejected(tmp_path):
    lab, manifest = prepared(tmp_path)
    inside = lab / 'QuietWriter.next' / 'self.json'
    inside.write_bytes(manifest.read_bytes())
    with pytest.raises(RehearsalError, match='own trusted file list'):
        verify_candidate_file_list(lab / 'QuietWriter.next', inside)


def test_unexpected_extra_file_rejected(tmp_path):
    lab, manifest = prepared(tmp_path)
    (lab / 'QuietWriter.next' / 'unexpected.py').write_text('unexpected')
    with pytest.raises(RehearsalError, match='independent file manifest'):
        swap_worker(lab, independent_file_manifest=manifest)
