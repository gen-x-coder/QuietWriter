"""Lab-only regression checks for durable phase intent and bounded rename retries."""
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from quietwriter import update_real_transaction_lab as rt


def fixture(tmp_path):
    (tmp_path / rt.MARKER).write_text('NONPRODUCTION-TEST-FIXTURE\n')
    for name, content in [('QuietWriter', 'OLD'), ('QuietWriter.next', 'NEW')]:
        folder = tmp_path / name
        folder.mkdir()
        (folder / 'QuietWriter.exe').write_text(content)
    return tmp_path


def test_journal_intents_written_before_each_rename(tmp_path):
    w = fixture(tmp_path)
    original = rt.os.replace
    phases = []
    def observed(src, dst):
        if Path(src).name in ('QuietWriter', 'QuietWriter.next'):
            phases.append(json.loads((w / rt.JOURNAL).read_text())['phase'])
        return original(src, dst)
    with patch.object(rt.os, 'replace', side_effect=observed):
        rt.swap_worker(w)
    assert phases == ['renaming-old', 'renaming-new']
    assert json.loads((w / rt.JOURNAL).read_text())['phase'] == 'new-renamed'
    rt.finish_worker(w)


@pytest.mark.parametrize('phase', ['renaming-old', 'renaming-new'])
def test_recovery_works_with_pre_rename_phase(tmp_path, phase):
    w = fixture(tmp_path)
    old_hash = rt._hash_tree(w / 'QuietWriter')
    new_hash = rt._hash_tree(w / 'QuietWriter.next')
    if phase == 'renaming-new':
        (w / 'QuietWriter').rename(w / 'QuietWriter.previous')
    rt._write_journal(w, {'schema': 1, 'phase': phase, 'old_hash': old_hash, 'new_hash': new_hash})
    rt.recover_worker(w)
    assert (w / 'QuietWriter' / 'QuietWriter.exe').read_text() == 'OLD'
    assert not (w / rt.JOURNAL).exists()


def test_retry_never_retries_nonsharing_failure(tmp_path):
    source = tmp_path / 'a'
    source.write_text('a')
    with patch.object(rt.os, 'replace', side_effect=PermissionError(13, 'denied')) as mocked:
        with pytest.raises(PermissionError):
            rt._rename_with_windows_retry(source, tmp_path / 'b', timeout=0.01)
    assert mocked.call_count == 1
