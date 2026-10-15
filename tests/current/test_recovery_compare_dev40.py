import hashlib
import json
import pytest
from quietwriter.recovery_overview import compare_recovery_files


def fixture(tmp_path):
    book = tmp_path / 'book1'
    (book / 'chapters').mkdir(parents=True)
    chapter = book / 'chapters' / 'chapter.md'
    chapter.write_text('New text', encoding='utf-8')
    folder = tmp_path / 'archives' / 'book1' / 'replace-recovery-a'
    folder.mkdir(parents=True)
    (folder / '00000.original').write_text('Old text', encoding='utf-8')
    data = {'schema': 1, 'book': 'book1', 'status': 'pending', 'files': [
        {'name': 'chapters/chapter.md', 'backup': '00000.original',
         'old_sha256': hashlib.sha256(b'Old text').hexdigest(),
         'new_sha256': hashlib.sha256(b'New text').hexdigest()}]}
    (folder / 'transaction.json').write_text(json.dumps(data), encoding='utf-8')
    return book, folder, chapter


def test_read_only_comparison(tmp_path):
    book, folder, chapter = fixture(tmp_path)
    original = {p: p.read_bytes() for p in (folder / 'transaction.json', folder / '00000.original', chapter)}
    records = compare_recovery_files(folder, book)
    assert len(records) == 1
    assert records[0].original == 'Old text'
    assert records[0].current == 'New text'
    assert records[0].state == 'changed'
    assert all(p.read_bytes() == value for p, value in original.items())


def test_missing_chapter_shown_not_created(tmp_path):
    book, folder, chapter = fixture(tmp_path)
    chapter.unlink()
    assert compare_recovery_files(folder, book)[0].state == 'missing'
    assert not chapter.exists()


def test_tampered_backup_rejected(tmp_path):
    book, folder, _ = fixture(tmp_path)
    (folder / '00000.original').write_text('Tampered', encoding='utf-8')
    with pytest.raises(ValueError):
        compare_recovery_files(folder, book)


@pytest.mark.parametrize('name', ['../outside.md', 'chapters/../other.md', 'chapters/C:\\file.md', '/tmp/a.md'])
def test_unsafe_path_rejected(tmp_path, name):
    book, folder, _ = fixture(tmp_path)
    journal = folder / 'transaction.json'
    doc = json.loads(journal.read_text(encoding='utf-8'))
    doc['files'][0]['name'] = name
    journal.write_text(json.dumps(doc), encoding='utf-8')
    with pytest.raises(ValueError):
        compare_recovery_files(folder, book)


def test_preview_limit(tmp_path):
    book, folder, _ = fixture(tmp_path)
    with pytest.raises(ValueError):
        compare_recovery_files(folder, book, max_bytes=4)
