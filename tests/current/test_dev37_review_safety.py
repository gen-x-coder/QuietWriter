"""Independent dev.36 review follow-up: incomplete history, chat, partial archives."""
import json
from pathlib import Path

from quietwriter.storage import Library
from quietwriter.automatic_backups import _legacy_folders


def test_registered_partial_history_never_breaks_history_list(tmp_path):
    library = Library(tmp_path / 'library')
    book = library.create_book('Geschiedenis')
    version = library.create_version(book)
    root = library.archive_dir / book.id
    index_file = root / 'history.json'
    index = json.loads(index_file.read_text(encoding='utf-8'))
    for key in ('title', 'words', 'chapters'):
        index['versions'][version['id']].pop(key, None)
    index_file.write_text(json.dumps(index), encoding='utf-8')
    (Path(version['path']) / 'book.json').unlink()
    # Incomplete legacy metadata must not leak a KeyError and hide other versions.
    rows = library.list_versions(book)
    assert any(row['id'] == version['id'] for row in rows)
    assert all({'title', 'words', 'chapters'} <= row.keys() for row in rows)


def test_legacy_archive_scan_ignores_hidden_partial_directories(tmp_path):
    library = Library(tmp_path / 'library')
    book = library.create_book('Boek')
    folder = library.archive_dir / book.id / '.old-version.partial'
    folder.mkdir(parents=True)
    (folder / 'book.json').write_text((book.path / 'book.json').read_text(encoding='utf-8'), encoding='utf-8')
    assert _legacy_folders(library, book, {}) == {}


def test_ai_chat_restore_uses_specific_chat_path():
    from quietwriter import backup_restore, qwbook_io
    import inspect
    source = inspect.getsource(backup_restore.replace_existing_book)
    assert 'retired_book / AI_CHAT_RELATIVE' in source
    assert "retired_book / 'ai'" not in source
    assert qwbook_io.AI_CHAT_RELATIVE == '.quietwriter/ai_chat.json'
