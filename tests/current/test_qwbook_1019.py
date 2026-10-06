from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from quietwriter.qwbook_io import (
    QwBookConflictError, QwBookError, QwBookFutureFormatError,
    export_qwbook, import_qwbook,
)
from quietwriter.storage import Library, _safe_atomic_write_text


def _filled_book(lib: Library):
    book = lib.create_book('Draagbaar boek')
    lib.track_book(book)
    chapter = book.sections[0].chapters[0]
    lib.save_chapter(book, chapter, '# Begin\n\nEen **belangrijk** hoofdstuk.\n')
    # Book-local optional state should travel with the package as bytes.
    files = {
        'planning/notes.md': 'Losse planning\n',
        'planning/characters.json': json.dumps({'version': 1, 'characters': []}),
        'publication/texts/preface.md': 'Voorwoord\n',
        'ai/boekprofiel.md': '## Toon\nRustig\n',
        'ai/memory.md': '## Feiten\nEen feit\n',
        'export/settings.json': json.dumps({'format': 'docx'}),
    }
    for rel, text in files.items():
        _safe_atomic_write_text(book.path / rel, text)
    # A binary book-local asset is included byte-exact too.
    asset = book.path / 'assets' / 'images' / 'example.bin'
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b'\x00\x01quietwriter\xff')
    lib.refresh_book_revision(book)
    return book


def _tree_bytes(root: Path):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob('*') if p.is_file()
    }


def test_qwbook_roundtrip_preserves_complete_book_folder(tmp_path):
    source_lib = Library(tmp_path / 'source')
    book = _filled_book(source_lib)
    expected = _tree_bytes(book.path)
    package = tmp_path / 'boek.qwbook'
    export_qwbook(source_lib, book, package)

    target_lib = Library(tmp_path / 'target')
    imported = import_qwbook(target_lib, package)
    assert imported.id == book.id
    assert imported.title == book.title
    assert _tree_bytes(imported.path) == expected
    assert target_lib.load_book(imported.path).sections[0].chapters[0].title == book.sections[0].chapters[0].title


def test_qwbook_never_overwrites_same_book_identity(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = _filled_book(lib)
    package = tmp_path / 'boek.qwbook'
    export_qwbook(lib, book, package)
    before = _tree_bytes(book.path)
    with pytest.raises(QwBookConflictError):
        import_qwbook(lib, package)
    assert _tree_bytes(book.path) == before


def test_qwbook_detects_corrupt_payload_and_leaves_library_clean(tmp_path):
    source_lib = Library(tmp_path / 'source')
    book = _filled_book(source_lib)
    package = tmp_path / 'boek.qwbook'
    export_qwbook(source_lib, book, package)
    tampered = tmp_path / 'tampered.qwbook'
    with zipfile.ZipFile(package, 'r') as src, zipfile.ZipFile(tampered, 'w') as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename.startswith('book/chapters/'):
                data += b'TAMPER'
            dst.writestr(info, data)
    target = Library(tmp_path / 'target')
    with pytest.raises(QwBookError):
        import_qwbook(target, tampered)
    assert target.list_books() == []


def test_qwbook_refuses_future_package_version(tmp_path):
    path = tmp_path / 'future.qwbook'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('qwbook.json', json.dumps({
            'format': 'quietwriter-book', 'version': 999, 'book_id': 'x', 'title': 'X',
            'files': {'book.json': {'sha256': 'x', 'size': 1}},
        }))
        z.writestr('book/book.json', b'x')
    with pytest.raises(QwBookFutureFormatError):
        import_qwbook(Library(tmp_path / 'target'), path)


def test_qwbook_refuses_path_traversal_before_writing_outside_library(tmp_path):
    data = b'{}'
    package = {
        'format': 'quietwriter-book', 'version': 1, 'book_id': 'abc', 'title': 'X',
        'files': {
            'book.json': {'sha256': __import__('hashlib').sha256(data).hexdigest(), 'size': len(data)},
            '../outside.txt': {'sha256': __import__('hashlib').sha256(b'bad').hexdigest(), 'size': 3},
        },
    }
    path = tmp_path / 'evil.qwbook'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('qwbook.json', json.dumps(package))
        z.writestr('book/book.json', data)
        z.writestr('book/../outside.txt', b'bad')
    target_root = tmp_path / 'target'
    with pytest.raises(QwBookError):
        import_qwbook(Library(target_root), path)
    assert not (target_root / 'outside.txt').exists()

def test_export_settings_accept_qwbook_format(tmp_path):
    from quietwriter.exporting.settings import ExportSettingsStore
    lib = Library(tmp_path / 'workspace2')
    book = lib.create_book('Settings')
    lib.track_book(book)
    store = ExportSettingsStore(lib)
    settings = store.load(book)
    settings['format'] = 'qwbook'
    store.save(book, settings)
    assert store.load(book)['format'] == 'qwbook'


def test_qwbook_rejects_windows_specific_escape_paths(tmp_path):
    import hashlib

    def package_with(relative: str, entry_name: str | None = None):
        book_data = json.dumps({'id': 'abc', 'title': 'X', 'sections': [], 'metadata': {}}).encode('utf-8')
        bad = b'bad'
        manifest = {
            'format': 'quietwriter-book', 'version': 2, 'book_id': 'abc', 'title': 'X',
            'files': {
                'book.json': {'sha256': hashlib.sha256(book_data).hexdigest(), 'size': len(book_data)},
                relative: {'sha256': hashlib.sha256(bad).hexdigest(), 'size': len(bad)},
            },
            'history_files': {},
        }
        path = tmp_path / (relative.replace('/', '_').replace('\\', '_').replace(':', '_') + '.qwbook')
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('qwbook.json', json.dumps(manifest))
            z.writestr('book/book.json', book_data)
            z.writestr(entry_name or ('book/' + relative), bad)
        return path

    lib = Library(tmp_path / 'target-windows')
    for relative in ('..\\..\\x.txt', 'C:/Windows/x.txt', 'C:x.txt', 'bad. /x.txt'):
        with pytest.raises(QwBookError):
            import_qwbook(lib, package_with(relative))
    from quietwriter.qwbook_io import _safe_member_name
    with pytest.raises(QwBookError):
        _safe_member_name('nul\x00name.txt')


def test_qwbook_import_temp_is_outside_books_and_stale_cache_is_cleaned(tmp_path):
    source_lib = Library(tmp_path / 'source-temp')
    book = _filled_book(source_lib)
    package = export_qwbook(source_lib, book, tmp_path / 'temp.qwbook')
    target = Library(tmp_path / 'target-temp')
    stale = target.cache_dir / 'qwbook-import' / 'qwbook-import-old'
    stale.mkdir(parents=True)
    (stale / 'book.json').write_text('{"id":"ghost","title":"Ghost","sections":[]}', encoding='utf-8')
    assert target.list_books() == []
    imported = import_qwbook(target, package)
    assert imported.title == book.title
    assert not stale.exists()
    assert all(not p.name.startswith('.qwbook-import-') for p in target.books_dir.iterdir())


def test_qwbook_conflicts_with_same_identity_in_trash_and_restore_conflicts_with_live(tmp_path):
    source = Library(tmp_path / 'source-trash')
    book = _filled_book(source)
    package = export_qwbook(source, book, tmp_path / 'trash.qwbook')

    target = Library(tmp_path / 'target-trash')
    imported = import_qwbook(target, package)
    target.delete_book(imported)
    trash_row = target.list_trashed_books()[0]
    with pytest.raises(QwBookConflictError):
        import_qwbook(target, package)

    # Move the trashed copy aside, import again, then put the old trashed copy
    # back: restoring it must refuse the duplicate identity.
    trashed_path = Path(trash_row['path'])
    holding = tmp_path / 'holding-trash'
    trashed_path.rename(holding)
    imported2 = import_qwbook(target, package)
    restored_trash = target.trash_dir / 'books' / trashed_path.name
    restored_trash.parent.mkdir(parents=True, exist_ok=True)
    holding.rename(restored_trash)
    with pytest.raises(RuntimeError):
        target.restore_trashed_book(restored_trash)
    assert target.load_book(imported2.path).id == book.id


def test_qwbook_strips_local_source_path_and_includes_chat_and_history(tmp_path):
    lib = Library(tmp_path / 'source-private')
    book = _filled_book(lib)
    book.metadata['source_file'] = r'C:\\Users\\Lucas\\Documenten\\geheim\\manuscript.docx'
    lib.save_manifest(book)
    chat = book.path / '.quietwriter' / 'ai_chat.json'
    chat.parent.mkdir(parents=True, exist_ok=True)
    chat.write_text('[{"role":"user","content":"boekvraag"}]', encoding='utf-8')
    lib.refresh_book_revision(book)
    version = lib.create_version(book)
    assert version
    package = export_qwbook(lib, book, tmp_path / 'private.qwbook')

    with zipfile.ZipFile(package, 'r') as z:
        manifest = json.loads(z.read('qwbook.json'))
        exported_book = json.loads(z.read('book/book.json'))
        assert 'source_file' not in exported_book.get('metadata', {})
        assert 'book/.quietwriter/ai_chat.json' in z.namelist()
        assert manifest['history_files']
        history_book_jsons = [n for n in z.namelist() if n.startswith('history/') and n.endswith('/book.json')]
        assert history_book_jsons
        for name in history_book_jsons:
            assert 'source_file' not in json.loads(z.read(name)).get('metadata', {})

    target = Library(tmp_path / 'target-private')
    imported = import_qwbook(target, package)
    assert 'source_file' not in imported.metadata
    assert (imported.path / '.quietwriter' / 'ai_chat.json').exists()
    assert (target.archive_dir / imported.id / 'history.json').exists()


def test_qwbook_checks_declared_size_before_reading_payload(tmp_path, monkeypatch):
    import quietwriter.qwbook_io as qio
    data = json.dumps({'id': 'abc', 'title': 'X', 'sections': [], 'metadata': {}}).encode('utf-8')
    digest = __import__('hashlib').sha256(data).hexdigest()
    package = {
        'format': 'quietwriter-book', 'version': 2, 'book_id': 'abc', 'title': 'X',
        'files': {'book.json': {'sha256': digest, 'size': len(data)}}, 'history_files': {},
    }
    path = tmp_path / 'size.qwbook'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('qwbook.json', json.dumps(package))
        z.writestr('book/book.json', data)
    monkeypatch.setattr(qio, 'MAX_FILE_SIZE', max(1, len(data) - 1))
    with pytest.raises(QwBookError, match='te groot'):
        import_qwbook(Library(tmp_path / 'target-size'), path)


def test_qwbook_restore_backup_after_permanent_delete_with_orphan_history(tmp_path):
    source = Library(tmp_path / 'restore-source')
    book = _filled_book(source)
    source.create_version(book)
    package = export_qwbook(source, book, tmp_path / 'restore.qwbook')

    target = Library(tmp_path / 'restore-target')
    imported = import_qwbook(target, package)
    target.delete_book(imported)
    trashed = target.list_trashed_books()[0]
    # Simulate the 1.0.20 situation: definitive deletion removes the book but
    # leaves its archive behind.
    target.permanently_delete_trashed_book(Path(trashed['path']))
    archive = target.archive_dir / book.id
    archive.mkdir(parents=True, exist_ok=True)
    (archive / 'orphan.txt').write_text('oude weesgeschiedenis', encoding='utf-8')

    restored = import_qwbook(target, package)
    assert restored.id == book.id
    assert (target.archive_dir / restored.id / 'history.json').exists()
    orphaned = target.archive_dir / '.orphaned'
    assert orphaned.exists()
    assert any((p / 'orphan.txt').exists() for p in orphaned.iterdir() if p.is_dir())


def test_qwbook_can_export_without_history(tmp_path):
    lib = Library(tmp_path / 'no-history')
    book = _filled_book(lib)
    lib.create_version(book)
    package = export_qwbook(lib, book, tmp_path / 'small.qwbook', include_history=False)
    with zipfile.ZipFile(package, 'r') as z:
        manifest = json.loads(z.read('qwbook.json'))
        assert manifest['history_included'] is False
        assert manifest['history_files'] == {}
        assert not any(name.startswith('history/') for name in z.namelist())
    target = Library(tmp_path / 'no-history-target')
    imported = import_qwbook(target, package)
    assert imported.id == book.id
    assert not (target.archive_dir / book.id).exists()


def test_qwbook_import_sanitizes_source_file_from_legacy_v1_package(tmp_path):
    import hashlib
    payload = json.dumps({
        'id': 'legacy-id', 'title': 'Legacy', 'sections': [],
        'metadata': {'source_file': r'C:\\Users\\Lucas\\Documenten\\roman.docx'},
    }, ensure_ascii=False).encode('utf-8')
    package = {
        'format': 'quietwriter-book', 'version': 1, 'book_id': 'legacy-id', 'title': 'Legacy',
        'files': {'book.json': {'sha256': hashlib.sha256(payload).hexdigest(), 'size': len(payload)}},
    }
    path = tmp_path / 'legacy.qwbook'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('qwbook.json', json.dumps(package))
        z.writestr('book/book.json', payload)
    lib = Library(tmp_path / 'legacy-target')
    imported = import_qwbook(lib, path)
    assert 'source_file' not in imported.metadata
    saved = json.loads((imported.path / 'book.json').read_text(encoding='utf-8'))
    assert 'source_file' not in saved.get('metadata', {})


def test_qwbook_rejects_case_only_duplicate_names_for_windows(tmp_path):
    import hashlib
    book_data = json.dumps({'id': 'case-id', 'title': 'Case', 'sections': [], 'metadata': {}}).encode('utf-8')
    a = b'a'; b = b'b'
    manifest = {
        'format': 'quietwriter-book', 'version': 2, 'book_id': 'case-id', 'title': 'Case',
        'files': {
            'book.json': {'sha256': hashlib.sha256(book_data).hexdigest(), 'size': len(book_data)},
            'chapters/ABC.md': {'sha256': hashlib.sha256(a).hexdigest(), 'size': len(a)},
            'chapters/abc.md': {'sha256': hashlib.sha256(b).hexdigest(), 'size': len(b)},
        },
        'history_files': {},
    }
    path = tmp_path / 'case-collision.qwbook'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('qwbook.json', json.dumps(manifest))
        z.writestr('book/book.json', book_data)
        z.writestr('book/chapters/ABC.md', a)
        z.writestr('book/chapters/abc.md', b)
    with pytest.raises(QwBookError, match='Windows'):
        import_qwbook(Library(tmp_path / 'case-target'), path)


def test_qwbook_without_history_keeps_existing_archive_for_same_book(tmp_path):
    source = Library(tmp_path / 'keep-history-source')
    book = _filled_book(source)
    source.create_version(book)
    package = export_qwbook(source, book, tmp_path / 'keep-history.qwbook', include_history=False)

    target = Library(tmp_path / 'keep-history-target')
    archive = target.archive_dir / book.id
    archive.mkdir(parents=True, exist_ok=True)
    marker = archive / 'existing-version.txt'
    marker.write_text('blijven staan', encoding='utf-8')

    imported = import_qwbook(target, package)
    assert imported.id == book.id
    assert marker.read_text(encoding='utf-8') == 'blijven staan'
    orphaned = target.archive_dir / '.orphaned'
    assert not orphaned.exists() or not any(orphaned.iterdir())


def test_qwbook_failed_import_does_not_move_existing_orphan_history(tmp_path):
    source = Library(tmp_path / 'failed-history-source')
    book = _filled_book(source)
    source.create_version(book)
    package = export_qwbook(source, book, tmp_path / 'valid-history.qwbook')
    broken = tmp_path / 'broken-history.qwbook'
    with zipfile.ZipFile(package, 'r') as src, zipfile.ZipFile(broken, 'w') as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename.startswith('book/') and info.filename.endswith('.md'):
                data += b'corrupt'
            dst.writestr(info, data)

    target = Library(tmp_path / 'failed-history-target')
    archive = target.archive_dir / book.id
    archive.mkdir(parents=True, exist_ok=True)
    marker = archive / 'existing-version.txt'
    marker.write_text('nog zichtbaar', encoding='utf-8')

    with pytest.raises(QwBookError):
        import_qwbook(target, broken)
    assert marker.read_text(encoding='utf-8') == 'nog zichtbaar'
    orphaned = target.archive_dir / '.orphaned'
    assert not orphaned.exists() or not any(orphaned.iterdir())
