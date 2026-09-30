from pathlib import Path
import json
import re

from quietwriter.exporting.markup import markdown_to_xhtml
from quietwriter.media.markup import (
    build_image_markdown,
    image_reference_for_line,
    mask_image_paths,
    replace_searchable_text,
)

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_legacy_image_line_keeps_historical_full_center_layout():
    line = '![Alt](../assets/images/a.png "Bijschrift")'
    ref = image_reference_for_line(line)
    assert ref is not None
    assert (ref.width, ref.align, ref.wrap) == ('full', 'center', False)
    assert build_image_markdown(ref.path, ref.alt, ref.caption) == line


def test_layout_metadata_roundtrips_as_readable_markdown_comment():
    line = build_image_markdown(
        '../assets/images/a.png', 'Alt', 'Bijschrift',
        width='medium', align='left', wrap=True,
    )
    assert line.endswith('<!-- qw:image width=medium align=left wrap=true -->')
    ref = image_reference_for_line(line)
    assert ref is not None
    assert (ref.width, ref.align, ref.wrap) == ('medium', 'left', True)


def test_invalid_or_meaningless_layout_is_normalized_safely():
    # Full width fills the measure: left/right alignment and wrapping have no effect.
    line = build_image_markdown(
        '../assets/images/a.png', 'Alt', width='full', align='right', wrap=True,
    )
    assert '<!--' not in line
    ref = image_reference_for_line(line)
    assert ref is not None
    assert (ref.width, ref.align, ref.wrap) == ('full', 'center', False)

    manual = '![Alt](../assets/images/a.png) <!-- qw:image width=unknown align=sideways wrap=true -->'
    parsed = image_reference_for_line(manual)
    assert parsed is not None
    assert (parsed.width, parsed.align, parsed.wrap) == ('full', 'center', False)


def test_layout_comment_is_protected_from_search_replace_but_caption_remains_editable():
    source = build_image_markdown(
        '../assets/images/a.png', 'Een foto', 'Links in beeld',
        width='small', align='left', wrap=True,
    )
    masked = mask_image_paths(source)
    assert 'Een foto' in masked
    assert 'Links in beeld' in masked
    assert 'width=small' not in masked
    assert 'align=left' not in masked

    changed = replace_searchable_text(source, re.compile('Links'), 'Rechts')
    assert '"Rechts in beeld"' in changed
    assert 'align=left' in changed

    untouched = replace_searchable_text(source, re.compile('left'), 'right')
    assert untouched == source


def test_epub_xhtml_gets_width_alignment_and_wrap_classes():
    source = build_image_markdown(
        '../assets/images/a.png', 'Alt', 'Bijschrift',
        width='medium', align='right', wrap=True,
    )
    xhtml = markdown_to_xhtml(source, {'../assets/images/a.png': '../images/a.png'})
    assert 'class="manuscript-image image-width-medium image-align-right image-wrap image-wrap-right"' in xhtml
    assert 'src="../images/a.png"' in xhtml
    assert '<figcaption>Bijschrift</figcaption>' in xhtml


def test_epub_templates_define_relative_sizes_alignment_and_float_wrap():
    for name in ('classic.css', 'modern.css', 'literary.css'):
        css = read(f'quietwriter/export_templates/{name}')
        assert 'image-width-small { width: 30%; }' in css
        assert 'image-width-medium { width: 50%; }' in css
        assert 'image-width-large { width: 70%; }' in css
        assert 'image-width-full { width: 100%; }' in css
        assert 'image-align-left' in css
        assert 'image-align-right' in css
        assert 'image-wrap-left' in css and 'float: left;' in css
        assert 'image-wrap-right' in css and 'float: right;' in css
        assert 'page-break-inside: avoid' in css


def test_image_panel_exposes_small_layout_model_without_freeform_pixels():
    src = read('quietwriter/ui/image_insert_widget.py')
    assert 'self.width_combo = QComboBox()' in src
    for value in ('small', 'medium', 'large', 'full'):
        assert f", '{value}')" in src
    assert 'self.align_combo = QComboBox()' in src
    for value in ('left', 'center', 'right'):
        assert f", '{value}')" in src
    assert 'self.wrap_check = QCheckBox' in src
    assert "width != 'full'" in src
    assert "align in {'left', 'right'}" in src
    assert 'QSpinBox' not in src


def test_insert_edit_pipeline_persists_layout_and_editor_card_represents_it():
    panel = read('quietwriter/ui/insert_panel.py')
    page = read('quietwriter/ui/editor_page.py')
    card = read('quietwriter/ui/image_block_card.py')
    editor = read('quietwriter/ui/manuscript_editor.py')

    assert 'imageInsertRequested = Signal(str, str, str, str, str, bool)' in panel
    assert 'imageEditRequested = Signal(str, str, str, str, str, bool, bool)' in panel
    assert 'width=ref.width, align=ref.align, wrap=ref.wrap' in page
    assert 'width=width, align=align, wrap=wrap' in page
    assert 'def layout_width_ratio' in card
    assert "'small': 0.30" in card
    assert "'medium': 0.50" in card
    assert "'large': 0.70" in card
    assert 'card.layout_width_ratio()' in editor
    assert 'card.layout_alignment()' in editor


def test_layout_locale_keys_exist_in_both_languages():
    keys = {
        'insert.image.width',
        'insert.image.width.small',
        'insert.image.width.medium',
        'insert.image.width.large',
        'insert.image.width.full',
        'insert.image.align',
        'insert.image.align.left',
        'insert.image.align.center',
        'insert.image.align.right',
        'insert.image.wrap',
        'insert.image.wrap.tip',
        'image_block.wrap_short',
    }
    for locale in ('nl.json', 'en.json'):
        data = json.loads(read(f'quietwriter/locales/{locale}'))
        assert keys <= data.keys()
