import json
from pathlib import Path
from quietwriter.recovery_overview import list_replacement_recoveries


def _record(root, book, name, status='pending'):
    folder = root / book / name
    folder.mkdir(parents=True)
    (folder / '00000.original').write_bytes(b'Original manuscript text')
    (folder / 'transaction.json').write_text(json.dumps({'schema':1,'book':book,'status':status,'files': []}), encoding='utf-8')
    return folder


def test_lists_pending_and_preserves_every_byte(tmp_path):
    root = tmp_path / 'archive'
    folder = _record(root, 'book123', 'replace-recovery-abc')
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    items = list_replacement_recoveries(root, book_id='book123')
    assert len(items) == 1 and items[0].status == 'pending' and items[0].copies == 1
    assert before == {p.name: p.read_bytes() for p in folder.iterdir()}


def test_corrupt_or_missing_journal_requires_attention(tmp_path):
    root = tmp_path / 'archive'
    folder = _record(root, 'book123', 'replace-recovery-a')
    (folder/'transaction.json').write_text('{',encoding='utf-8')
    (root/'book123'/'replace-recovery-b').mkdir()
    entries = list_replacement_recoveries(root)
    assert len(entries) == 2 and all(e.status == 'attention' for e in entries)


def test_other_books_hidden_and_committed_visible(tmp_path):
    root = tmp_path / 'archive'
    _record(root, 'A', 'replace-recovery-1', status='committed')
    _record(root, 'B', 'replace-recovery-2', status='recovered')
    assert [x.status for x in list_replacement_recoveries(root, book_id='A')] == ['committed']


def test_no_archive_is_safe(tmp_path):
    assert list_replacement_recoveries(tmp_path/'absent') == []
