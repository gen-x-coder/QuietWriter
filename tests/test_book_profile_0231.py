from pathlib import Path

import pytest

from quietwriter.book_profile import (
    SECTIONS, default_book_profile_markdown, empty_book_profile,
    has_meaningful_book_profile, parse_book_profile, render_book_profile,
)
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import Library


def test_book_profile_is_human_readable_markdown_roundtrip():
    profile = empty_book_profile()
    profile['genre_audience'] = 'Psychologische thriller voor volwassenen.'
    profile['tone'] = 'Beklemmend maar realistisch.'
    profile['persona_overrides'] = 'Voor dit boek kortere hoofdstukken dan gebruikelijk.'
    md = render_book_profile(profile)
    assert md.startswith('# Boekprofiel\n')
    for section in SECTIONS:
        assert f'## {section.title}' in md
    assert parse_book_profile(md) == profile
    assert has_meaningful_book_profile(md)


def test_unknown_book_profile_sections_are_preserved_in_additional():
    source = '# Boekprofiel\n\n## Genre & doelgroep\n\nFeelgood.\n\n## Eigen rubriek\n\nNiet verliezen.\n'
    parsed = parse_book_profile(source)
    assert parsed['genre_audience'] == 'Feelgood.'
    assert '## Eigen rubriek' in parsed['additional']
    assert 'Niet verliezen.' in render_book_profile(parsed)


def test_library_keeps_book_profile_as_plain_book_local_markdown(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Profieltest')
    path = lib.book_profile_path(book)
    assert path == book.path / 'ai' / 'boekprofiel.md'
    assert not path.exists()
    assert lib.read_book_profile(book) == default_book_profile_markdown()

    lib.track_book(book)
    profile = empty_book_profile(); profile['premise'] = 'Een geheim zet een vriendschap onder druk.'
    text = render_book_profile(profile)
    lib.save_book_profile(book, text)
    assert path.read_text(encoding='utf-8') == text


def test_book_profile_write_uses_external_change_guard(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Conflict')
    lib.track_book(book)
    book.manifest_path.write_text(book.manifest_path.read_text(encoding='utf-8') + '\n', encoding='utf-8')
    with pytest.raises(ExternalModificationError):
        lib.save_book_profile(book, render_book_profile(empty_book_profile()))


def test_book_profile_is_part_of_history_restore(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Historie')
    lib.track_book(book)
    first = empty_book_profile(); first['tone'] = 'Warm.'
    lib.save_book_profile(book, render_book_profile(first))
    version = lib.create_version(book, kind='manual')

    second = empty_book_profile(); second['tone'] = 'Donker.'
    lib.save_book_profile(book, render_book_profile(second))
    restored = lib.restore_version(book, version['id'])
    assert parse_book_profile(lib.read_book_profile(restored))['tone'] == 'Warm.'


def test_book_profile_navigation_and_ai_layering_are_wired():
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    page = Path('quietwriter/ui/book_profile_page.py').read_text(encoding='utf-8')
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    prompting = Path('quietwriter/ai/prompting.py').read_text(encoding='utf-8')
    revisions = Path('quietwriter/revisions.py').read_text(encoding='utf-8')
    assert 'BookProfilePage' in main
    assert "tr('nav.book_profile', 'Boekprofiel')" in main
    assert 'self.book_profile_page.adopt_book(book)' in main
    assert 'parse_book_profile(self.main.library.read_book_profile(self.book))' in page
    assert 'render_book_profile(self.profile)' in page
    assert 'BOEKPROFIEL (dit boek)' in prompting
    assert 'read_book_profile(active_book)' in ai
    assert "'ai/boekprofiel.md'" in revisions
    assert "('planning', 'publication', 'ai')" in revisions
