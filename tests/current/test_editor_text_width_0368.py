from pathlib import Path

from quietwriter.editor_view import (
    DEFAULT_TEXT_WIDTH,
    TEXT_WIDTHS,
    normalize_text_width,
    text_width_pixels,
)


def test_text_width_presets_are_stable_and_ordered():
    assert list(TEXT_WIDTHS) == ['extra_narrow', 'narrow', 'normal', 'wide', 'extra_wide']
    assert TEXT_WIDTHS['extra_narrow'] < TEXT_WIDTHS['narrow'] < TEXT_WIDTHS['normal'] < TEXT_WIDTHS['wide'] < TEXT_WIDTHS['extra_wide']
    assert DEFAULT_TEXT_WIDTH == 'normal'


def test_unknown_text_width_falls_back_to_normal():
    assert normalize_text_width(None) == 'normal'
    assert normalize_text_width('unknown') == 'normal'
    assert text_width_pixels('unknown') == TEXT_WIDTHS['normal']


def test_editor_width_is_presentation_only_contract():
    source = Path('quietwriter/ui/manuscript_editor.py').read_text(encoding='utf-8')
    body = source.split('def apply_text_width', 1)[1].split('def _update_margins', 1)[0]
    assert 'setPlainText' not in body
    assert 'QTextCursor' not in body
    assert 'setViewportMargins' not in body  # centralized in _update_margins
    assert 'self.max_text_width = text_width_pixels' in body


def test_editor_and_settings_share_global_setting():
    editor = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    settings = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    assert "setValue('editor_text_width', preset)" in editor
    assert "'editor_text_width': normalize_text_width(self.editor_text_width.currentData())" in settings
    assert "settings.value('editor_text_width', DEFAULT_TEXT_WIDTH)" in settings
