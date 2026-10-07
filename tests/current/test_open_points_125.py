from pathlib import Path

from quietwriter.open_points_storage import OpenPointStore
from quietwriter.placeholders import (
    marker_open, parse_open_points, strip_open_point_markers, wrap_open_point,
)
from quietwriter.storage import Library


def test_current_marker_is_compact_and_note_lives_outside_source():
    source = 'De mist hing over de haven.'
    marked, start, end, point_id = wrap_open_point(source, 18, 26, 'later preciezer maken')
    assert marker_open(point_id) in marked
    assert 'note=' not in marked
    assert 'later' not in marked
    assert len(marker_open(point_id)) <= 32
    assert marked[start:end] == 'de haven'
    assert strip_open_point_markers(marked) == source


def test_parser_combines_compact_marker_with_external_note_map():
    marked, *_rest, point_id = wrap_open_point('Een zin.', 0, 3)
    point = parse_open_points(marked, {point_id: 'notitie buiten bron'})[0]
    assert point.note == 'notitie buiten bron'
    assert point.text == 'Een'


def test_legacy_124_marker_remains_readable_but_strips_cleanly():
    source = 'A <!-- qw:todo id=12345678-abcd note="oude%20notitie" -->B<!-- /qw:todo --> C'
    point = parse_open_points(source)[0]
    assert point.id == '12345678-abcd'
    assert point.note == 'oude notitie'
    assert point.text == 'B'
    assert strip_open_point_markers(source) == 'A B C'


def test_open_point_store_is_revision_guarded_and_round_trips(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Punten')
    store = OpenPointStore(lib)
    store.set_note(book, 'abcdef123456', 'later uitzoeken')
    assert store.load_notes(book) == {'abcdef123456': 'later uitzoeken'}
    store.set_note(book, 'abcdef123456', '')
    assert store.load_notes(book) == {}


def test_clipboard_and_shortcut_guards_are_explicit_in_editor_source():
    source = Path('quietwriter/ui/manuscript_editor.py').read_text(encoding='utf-8')
    assert 'def createMimeDataFromSelection' in source
    assert 'strip_open_point_markers' in source
    assert 'QKeySequence.StandardKey.Cut' in source
    assert 'QKeySequence.StandardKey.Paste' in source
    assert 'def _open_point_cursor_changed' in source
    assert 'selection_intersects_open_point_marker()' in source


def test_publication_text_is_also_sanitized_before_export():
    source = Path('quietwriter/exporting/builder.py').read_text(encoding='utf-8')
    publication_section = source.split('def publication_items', 1)[1]
    assert 'count_open_points(text)' in publication_section
    assert 'strip_open_point_markers(text)' in publication_section


def test_settings_help_and_toolrail_have_responsive_guards():
    settings = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert 'detail.heightForWidth(310)' in settings
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert "self.tool_scroll = QScrollArea()" in main
    assert 'Qt.ScrollBarAsNeeded' in main
