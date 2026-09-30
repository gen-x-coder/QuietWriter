from pathlib import Path

import pytest

from quietwriter.book_memory import (
    SECTIONS, default_book_memory_markdown, empty_book_memory,
    has_meaningful_book_memory, parse_book_memory, render_book_memory,
)
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import Library


def test_book_memory_is_human_readable_markdown_roundtrip():
    memory = empty_book_memory()
    memory['canon'] = 'De rode sleutel bestaat maar één keer.'
    memory['book_style'] = 'Emoties worden vooral via gedrag getoond.'
    memory['decisions'] = 'De onthulling blijft tot hoofdstuk 12 verborgen.'
    md = render_book_memory(memory)
    assert md.startswith('# Boekgeheugen\n')
    for section in SECTIONS:
        assert f'## {section.title}' in md
    assert parse_book_memory(md) == memory
    assert has_meaningful_book_memory(md)


def test_unknown_book_memory_content_is_preserved_visibly():
    source = '# Boekgeheugen\n\nLosse regel.\n\n## Eigen rubriek\n\nNiet verliezen.\n'
    parsed = parse_book_memory(source)
    assert 'Losse regel.' in parsed['open_points']
    assert '## Eigen rubriek' in parsed['open_points']
    assert 'Niet verliezen.' in render_book_memory(parsed)


def test_library_keeps_book_memory_as_plain_book_local_markdown(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Geheugentest')
    path = lib.book_memory_path(book)
    assert path == book.path / 'ai' / 'memory.md'
    assert not path.exists()
    assert lib.read_book_memory(book) == default_book_memory_markdown()

    lib.track_book(book)
    memory = empty_book_memory(); memory['preferences'] = 'Dialoog compact houden.'
    text = render_book_memory(memory)
    lib.save_book_memory(book, text)
    assert path.read_text(encoding='utf-8') == text


def test_book_memory_write_uses_external_change_guard(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Conflict')
    lib.track_book(book)
    book.manifest_path.write_text(book.manifest_path.read_text(encoding='utf-8') + '\n', encoding='utf-8')
    with pytest.raises(ExternalModificationError):
        lib.save_book_memory(book, render_book_memory(empty_book_memory()))


def test_book_memory_is_part_of_history_restore(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Historie')
    lib.track_book(book)
    first = empty_book_memory(); first['decisions'] = 'Anna liegt in hoofdstuk 4.'
    lib.save_book_memory(book, render_book_memory(first))
    version = lib.create_version(book, kind='manual')

    second = empty_book_memory(); second['decisions'] = 'Anna vertelt de waarheid.'
    lib.save_book_memory(book, render_book_memory(second))
    restored = lib.restore_version(book, version['id'])
    assert parse_book_memory(lib.read_book_memory(restored))['decisions'] == 'Anna liegt in hoofdstuk 4.'


def test_book_memory_navigation_and_ai_layering_are_wired():
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    page = Path('quietwriter/ui/book_memory_page.py').read_text(encoding='utf-8')
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    prompting = Path('quietwriter/ai/prompting.py').read_text(encoding='utf-8')
    context = Path('quietwriter/ai/context.py').read_text(encoding='utf-8')
    revisions = Path('quietwriter/revisions.py').read_text(encoding='utf-8')
    assert 'BookMemoryPage' in main
    assert "tr('nav.book_memory', 'Boekgeheugen')" in main
    assert "self.book_memory_page.adopt_book(book, prepared=prepared['memory'], show_message=False)" in main
    assert 'parse_book_memory(self.main.library.read_book_memory(self.book))' in page
    assert 'render_book_memory(self.memory)' in page
    assert 'BOEKGEHEUGEN (dit boek)' in prompting
    assert 'read_book_memory(active_book)' in ai
    assert "['Schrijverspersona', 'Boekprofiel', 'Boekgeheugen']" in context
    assert "'ai/memory.md'" in revisions


def test_ai_never_writes_book_memory_automatically():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    prompting = Path('quietwriter/ai/prompting.py').read_text(encoding='utf-8')
    assert 'save_book_memory(' not in ai
