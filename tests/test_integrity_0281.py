import json
from pathlib import Path
import pytest
from quietwriter.storage import Library
from quietwriter.integrity import BookIntegrityChecker
from quietwriter.migrations import FutureBookFormatError, MigrationError, detected_book_format


def make(tmp_path):
    lib=Library(tmp_path/'w'); book=lib.create_book('B'); lib.track_book(book); return lib,book

def test_future_format_refused_on_load_and_preserved(tmp_path):
    lib,b=make(tmp_path); d=json.loads(b.manifest_path.read_text()); d['format']=99; d['future']={'x':1}; b.manifest_path.write_text(json.dumps(d))
    with pytest.raises(FutureBookFormatError): lib.load_book(b.path)
    assert json.loads(b.manifest_path.read_text())['future']=={'x':1}

def test_unknown_top_level_roundtrips(tmp_path):
    lib,b=make(tmp_path); d=json.loads(b.manifest_path.read_text()); d['custom']={'keep':True}; b.manifest_path.write_text(json.dumps(d)); b=lib.load_book(b.path); lib.track_book(b)
    lib.save_chapter(b,b.sections[0].chapters[0],'x')
    assert json.loads(b.manifest_path.read_text())['custom']=={'keep':True}

def test_format_requires_real_integer():
    for value in (True, 2.7, '2'):
        with pytest.raises(MigrationError): detected_book_format({'format':value})

def test_audit_rejects_fields_load_requires(tmp_path):
    lib,b=make(tmp_path); d=json.loads(b.manifest_path.read_text()); del d['sections'][0]['title']; b.manifest_path.write_text(json.dumps(d))
    assert not BookIntegrityChecker().audit_folder(b.path).ok
    with pytest.raises(MigrationError): lib.load_book(b.path)

def test_duplicate_normalizes_dot_and_case(tmp_path):
    lib,b=make(tmp_path); d=json.loads(b.manifest_path.read_text()); c=d['sections'][0]['chapters'][0]; c2=dict(c,id='two',file='chapters/./'+Path(c['file']).name.upper()); d['sections'][0]['chapters'].append(c2); b.manifest_path.write_text(json.dumps(d))
    assert any(i.code=='chapter_file_duplicate' for i in BookIntegrityChecker().audit_folder(b.path).errors)

def test_repair_is_byte_exact_crlf(tmp_path):
    lib,b=make(tmp_path); rel=b.sections[0].chapters[0].file; p=b.path/rel; p.write_bytes(b'a\r\nb\r\n'); lib.refresh_book_revision(b); lib.create_version(b,kind='manual'); p.write_bytes(b'bad'); lib.refresh_book_revision(b)
    BookIntegrityChecker().restore_file_from_history(lib,b,rel); assert p.read_bytes()==b'a\r\nb\r\n'

def test_repair_skips_pre_integrity_and_invalid_json(tmp_path):
    lib,b=make(tmp_path); rel='planning/characters.json'; p=b.path/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('{"good":1}'); lib.refresh_book_revision(b); lib.create_version(b,kind='manual'); p.write_text('[]'); lib.refresh_book_revision(b); lib.create_version(b,kind='pre_integrity_repair'); p.write_text('{broken'); lib.refresh_book_revision(b)
    BookIntegrityChecker().restore_file_from_history(lib,b,rel); assert json.loads(p.read_text())=={'good':1}

def test_repair_media_requires_live_manifest_hash(tmp_path):
    lib,b=make(tmp_path); rel='assets/images/x.png'; p=b.path/rel; p.write_bytes(b'good')
    import hashlib
    m={'version':1,'images':{'x':{'file':rel,'sha256':hashlib.sha256(b'good').hexdigest()}}}; (b.path/'assets/manifest.json').write_text(json.dumps(m)); lib.refresh_book_revision(b); lib.create_version(b,kind='manual'); p.write_bytes(b'bad'); lib.refresh_book_revision(b); lib.create_version(b,kind='daily'); p.write_bytes(b'rot'); lib.refresh_book_revision(b)
    BookIntegrityChecker().restore_file_from_history(lib,b,rel); assert p.read_bytes()==b'good'

def test_same_second_history_uses_id_tiebreaker(tmp_path):
    lib,b=make(tmp_path); rel=b.sections[0].chapters[0].file; p=b.path/rel; p.write_text('A'); lib.refresh_book_revision(b); a=lib.create_version(b); p.write_text('B'); lib.refresh_book_revision(b); z=lib.create_version(b)
    # metadata timestamps are intentionally whole seconds; later microsecond id must win
    assert lib.list_versions(b)[0]['id']==max(a['id'],z['id'])

def test_noop_migration_creates_no_checkpoint(tmp_path):
    lib,b=make(tmp_path); before=len(lib.list_versions(b)); migrated,res,checkpoint=lib.migrate_book_format(b); assert not res.changed and checkpoint is None and len(lib.list_versions(b))==before
