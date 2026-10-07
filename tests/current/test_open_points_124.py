from pathlib import Path
import re

from quietwriter.placeholders import (
    count_open_points, marker_ranges, mask_open_point_markers, open_point_at,
    parse_open_points, resolve_open_point, strip_open_point_markers,
    update_open_point_note, wrap_open_point,
)
from quietwriter.media.markup import count_words, searchable_matches
from quietwriter.exporting.models import ExportDocument, ExportSection, ExportChapter
from quietwriter.exporting.preflight import run_preflight


def test_open_point_round_trip_and_resolve_preserves_visible_text():
    source = 'De deur ging open.'
    marked, start, end, point_id = wrap_open_point(source, 3, 7, 'ander werkwoord')
    points = parse_open_points(marked)
    assert len(points) == 1
    assert points[0].id == point_id
    assert points[0].text == 'deur'
    assert points[0].note == ''
    assert parse_open_points(marked, {point_id: 'ander werkwoord'})[0].note == 'ander werkwoord'
    assert marked[start:end] == 'deur'
    assert strip_open_point_markers(marked) == source
    assert count_open_points(marked) == 1
    assert open_point_at(marked, start + 1).id == point_id

    resolved = resolve_open_point(marked, point_id)
    assert resolved is not None
    clean, sel_start, sel_end = resolved
    assert clean == source
    assert clean[sel_start:sel_end] == 'deur'


def test_empty_selection_inserts_writer_visible_placeholder():
    marked, start, end, _ = wrap_open_point('Begin einde', 6, 6, 'later invullen')
    assert strip_open_point_markers(marked) == 'Begin […]einde'
    assert marked[start:end] == '[…]'


def test_note_update_does_not_change_visible_manuscript():
    marked, _start, _end, point_id = wrap_open_point('Een zin.', 0, 3, 'eerste')
    updated = update_open_point_note(marked, point_id, 'tweede & later')
    assert updated is not None
    assert strip_open_point_markers(updated) == 'Een zin.'
    assert parse_open_points(updated, {point_id: 'tweede & later'})[0].note == 'tweede & later'
    assert 'tweede' not in updated


def test_marker_mask_preserves_offsets_and_search_never_matches_marker_syntax():
    marked, *_ = wrap_open_point('alpha beta gamma', 6, 10, 'TODO woord')
    masked = mask_open_point_markers(marked)
    assert len(masked) == len(marked)
    for a, b in marker_ranges(marked):
        assert masked[a:b].isspace()
    matches = searchable_matches(marked, re.compile('beta', re.I))
    assert len(matches) == 1
    assert marked[matches[0].start():matches[0].end()] == 'beta'
    assert not searchable_matches(marked, re.compile('qw:todo', re.I))


def test_word_count_ignores_technical_markers_but_counts_visible_placeholder_text():
    marked, *_ = wrap_open_point('een twee drie', 4, 8, 'vier vijf zes')
    assert count_words(marked) == 3


def test_preflight_warns_for_open_points_except_qwbook():
    doc = ExportDocument(
        id='b', title='Boek', author='Auteur', language='nl', slug='boek', metadata={},
        sections=(ExportSection('s', 'S', (ExportChapter('c', 'C', 'tekst'),)),),
        front_matter=(), back_matter=(), open_point_count=2,
    )
    pdf = run_preflight(doc, 'pdf', {})
    assert any(i.key == 'open_points' and i.level == 'warning' for i in pdf.items)
    qw = run_preflight(doc, 'qwbook', {})
    assert not any(i.key == 'open_points' for i in qw.items)


def test_placeholder_source_is_export_presentation_only():
    builder = Path('quietwriter/exporting/builder.py').read_text(encoding='utf-8')
    assert 'strip_open_point_markers(markdown)' in builder
    panel_help = Path('quietwriter/ui/panel_help.py').read_text(encoding='utf-8')
    locale = Path('quietwriter/locales/nl.json').read_text(encoding='utf-8')
    assert 'panel_help.open_points' in locale
    assert 'XXX' in locale and 'TODO' in locale
    assert '_explain_open_points_once' not in Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')


def test_open_points_have_book_overview_and_export_navigation():
    panel = Path('quietwriter/ui/open_points_panel.py').read_text(encoding='utf-8')
    assert "PanelHelp(" in panel and "'open_points'" in panel
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'self.open_points_button' in main
    assert 'def show_open_points(self):' in main
    wizard = Path('quietwriter/ui/export_wizard.py').read_text(encoding='utf-8')
    assert "'open_points':" in wizard
    assert 'main.show_open_points' in wizard


def test_editor_refuses_nested_open_points():
    editor = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'selection_intersects_open_point_marker()' in editor
    assert 'current_open_point() is not None' in editor
