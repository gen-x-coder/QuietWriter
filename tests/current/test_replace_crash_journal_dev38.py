"""Durable batch replacement recovery, on disposable books only."""
import json
import pytest
from quietwriter.storage import Library, _safe_atomic_write_bytes
from quietwriter.replace_journal import digest, journal_write


def scenario(tmp_path):
    lib = Library(tmp_path / 'library')
    book = lib.create_book('Crash recovery')
    a = book.sections[0].chapters[0]
    b = lib.add_chapter(book, book.sections[0], 'Two')
    lib.save_chapter(book, a, 'before one')
    lib.save_chapter(book, b, 'before two')
    return lib,book,a,b


def pending(lib,book,chapter,old,new):
    folder = lib.archive_dir / book.id / 'replace-recovery-simulated'
    folder.mkdir(parents=True)
    _safe_atomic_write_bytes(folder / '00000.original', old.encode())
    journal_write(folder / 'transaction.json', {
        'schema':1, 'book':book.id,'status':'pending',
        'files':[{'name':chapter.file,'backup':'00000.original',
                  'old_sha256':digest(old.encode()),'new_sha256':digest(new.encode())}]}, _safe_atomic_write_bytes)
    return folder


def test_startup_restores_crash_changed_file(tmp_path):
    lib,book,a,b=scenario(tmp_path)
    folder=pending(lib,book,a,'before one','after one')
    _safe_atomic_write_bytes(book.path / a.file,b'after one')
    new_lib=Library(lib.root)
    assert not new_lib._replace_recovery_alerts
    assert (book.path / a.file).read_text() == 'before one'
    assert json.loads((folder / 'transaction.json').read_text())['status']=='recovered'


def test_startup_does_not_overwrite_external_sync_change(tmp_path):
    lib,book,a,b=scenario(tmp_path)
    folder=pending(lib,book,a,'before one','after one')
    _safe_atomic_write_bytes(book.path / a.file,b'Dropbox changed')
    new_lib=Library(lib.root)
    assert new_lib._replace_recovery_alerts
    assert (book.path / a.file).read_text() == 'Dropbox changed'
    assert json.loads((folder / 'transaction.json').read_text())['status']=='pending'


def test_committed_remains_committed_across_restart(tmp_path):
    lib,book,a,b=scenario(tmp_path)
    lib.replace_chapters_guarded(book,{a.id:('before one','after one'),b.id:('before two','after two')})
    new_lib=Library(lib.root)
    assert not new_lib._replace_recovery_alerts
    assert (book.path / a.file).read_text() == 'after one'


def test_corrupt_backup_never_overwrites(tmp_path):
    lib,book,a,b=scenario(tmp_path)
    folder=pending(lib,book,a,'before one','after one')
    (folder / '00000.original').write_bytes(b'broken')
    (book.path / a.file).write_text('after one')
    new_lib=Library(lib.root)
    assert new_lib._replace_recovery_alerts
    assert (book.path / a.file).read_text() == 'after one'


def test_second_writer_cannot_replace_while_book_locked(tmp_path):
    from quietwriter.replace_journal import replace_lock
    lib,book,a,b=scenario(tmp_path)
    with replace_lock(lib.archive_dir / book.id):
        with pytest.raises(RuntimeError, match='andere vervangactie'):
            lib.replace_chapters_guarded(book, {a.id:('before one','after one')})
    assert lib.read_chapter(book,a)=='before one'
