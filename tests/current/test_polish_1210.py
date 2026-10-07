from pathlib import Path

from quietwriter.placeholders import mask_open_point_markers, wrap_open_point


def test_mask_open_point_markers_preserves_offsets_and_hides_technical_words():
    source, *_ = wrap_open_point('Voor de haven na.', 5, 13, point_id='12345678abcd')
    masked = mask_open_point_markers(source)
    assert len(masked) == len(source)
    assert 'qw' not in masked.lower()
    assert 'todo' not in masked.lower()
    assert 'de haven' in masked


def test_spell_panel_masks_open_point_markers_before_dictionary_scan():
    source = Path('quietwriter/ui/spell_panel.py').read_text(encoding='utf-8')
    assert 'text_for_language_tools(' in source


def test_open_points_refresh_accepts_unsaved_current_chapter_source():
    source = Path('quietwriter/ui/open_points_panel.py').read_text(encoding='utf-8')
    assert 'current_chapter_id' in source
    assert 'current_source' in source
    editor = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'current_source=current_source' in editor
    assert 'current_source = self._editor_source_text()' in editor
