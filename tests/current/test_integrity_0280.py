import json
from pathlib import Path

import pytest

from quietwriter.integrity import BookIntegrityChecker
from quietwriter.migrations import FutureBookFormatError, migrate_manifest_data
from quietwriter.storage import Library


def make_book(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Testboek')
    lib.track_book(book)
    return lib, book


def test_clean_book_has_no_integrity_errors(tmp_path):
    lib, book = make_book(tmp_path)
    report = BookIntegrityChecker().audit_folder(book.path)
    assert report.ok


def test_missing_chapter_is_reported_recoverable(tmp_path):
    lib, book = make_book(tmp_path)
    chapter = book.sections[0].chapters[0]
    (book.path / chapter.file).unlink()
    issue = next(i for i in BookIntegrityChecker().audit_folder(book.path).issues if i.code == 'chapter_missing')
    assert issue.recoverable


def test_corrupt_aux_json_is_not_silently_treated_as_empty(tmp_path):
    lib, book = make_book(tmp_path)
    path = book.path / 'planning' / 'characters.json'
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text('{broken', encoding='utf-8')
    report = BookIntegrityChecker().audit_folder(book.path)
    assert any(i.code == 'aux_json_invalid' and i.path == 'planning/characters.json' for i in report.errors)


def test_media_hash_mismatch_is_detected(tmp_path):
    lib, book = make_book(tmp_path)
    asset = book.path / 'assets' / 'images' / 'x.png'; asset.write_bytes(b'changed')
    manifest = {'version': 1, 'images': {'x': {'file':'assets/images/x.png','sha256':'0'*64}}}
    (book.path/'assets/manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    assert any(i.code == 'media_hash_mismatch' for i in BookIntegrityChecker().audit_folder(book.path).errors)


def test_future_format_is_refused_by_migration():
    with pytest.raises(FutureBookFormatError):
        migrate_manifest_data({'format': 99, 'id':'x', 'title':'x', 'sections':[]})


def test_v1_migration_preserves_unknown_fields():
    source={'id':'x','title':'Mijn Boek','sections':[],'custom':{'keep':True}}
    migrated, result=migrate_manifest_data(source)
    assert result.source_format == 1 and result.target_format == 2 and result.changed
    assert migrated['custom'] == {'keep': True}
    assert migrated['metadata']['slug'] == 'mijn-boek'
    assert 'format' not in source


def test_explicit_migration_creates_checkpoint(tmp_path):
    lib, book = make_book(tmp_path)
    data=json.loads(book.manifest_path.read_text(encoding='utf-8')); data.pop('format',None)
    book.manifest_path.write_text(json.dumps(data),encoding='utf-8')
    book=lib.load_book(book.path); lib.track_book(book)
    migrated,result,checkpoint=lib.migrate_book_format(book)
    assert result.changed and json.loads(migrated.manifest_path.read_text())['format']==2
    assert lib.load_version(migrated, checkpoint)


def test_restore_damaged_file_from_history_creates_checkpoint(tmp_path):
    lib, book=make_book(tmp_path); chapter=book.sections[0].chapters[0]
    lib.save_chapter(book, chapter, 'goede tekst')
    lib.create_version(book, kind='manual')
    lib.save_chapter(book, chapter, 'latere tekst')
    (book.path/chapter.file).write_bytes(b'\xff\xfe')
    # External damage becomes the currently tracked baseline only for this repair test.
    lib.refresh_book_revision(book)
    checkpoint=BookIntegrityChecker().restore_file_from_history(lib,book,chapter.file)
    assert (book.path/chapter.file).read_text(encoding='utf-8') == 'goede tekst'
    assert lib.load_version(book, checkpoint)


def test_repair_refuses_external_change(tmp_path):
    lib, book=make_book(tmp_path); chapter=book.sections[0].chapters[0]
    lib.save_chapter(book,chapter,'one'); lib.create_version(book)
    (book.path/chapter.file).write_text('external',encoding='utf-8')
    from quietwriter.revisions import ExternalModificationError
    with pytest.raises(ExternalModificationError):
        BookIntegrityChecker().restore_file_from_history(lib,book,chapter.file)

def test_corrupt_book_json_is_reported_without_crash(tmp_path):
    folder=tmp_path/'book'; folder.mkdir(); (folder/'book.json').write_text('{half',encoding='utf-8')
    report=BookIntegrityChecker().audit_folder(folder)
    assert [i.code for i in report.errors] == ['book_manifest_invalid']


def test_unsafe_chapter_path_is_rejected(tmp_path):
    folder=tmp_path/'book'; folder.mkdir()
    (folder/'book.json').write_text(json.dumps({'format':2,'id':'x','title':'x','metadata':{},'sections':[{'id':'s','title':'s','chapters':[{'id':'c','title':'c','file':'../outside.md'}]}]}),encoding='utf-8')
    assert any(i.code=='chapter_path_unsafe' for i in BookIntegrityChecker().audit_folder(folder).errors)


def test_failed_manifest_migration_preserves_original_bytes(tmp_path, monkeypatch):
    from quietwriter import migrations
    path=tmp_path/'book.json'; original=b'{"id":"x","title":"x","sections":[]}' ; path.write_bytes(original)
    def fail(*args, **kwargs): raise OSError('disk full')
    monkeypatch.setattr(migrations, '_safe_atomic_write_text', fail)
    with pytest.raises(OSError): migrations.migrate_manifest_file(path)
    assert path.read_bytes() == original
