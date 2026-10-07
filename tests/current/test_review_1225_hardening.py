import re

from quietwriter.document_view import parse_document, visible_projection
from quietwriter.manuscript_markup import escape_literal_text
from quietwriter.media.markup import replace_searchable_text, searchable_matches
from quietwriter.placeholders import marker_ranges, parse_open_points


def test_visible_projection_searches_across_escapes_and_formatting():
    source = 'nummer \\*31623455 en 5\\*3\nHij was **heel** moe.'
    visible = visible_projection(source)
    assert visible.text == 'nummer *31623455 en 5*3\nHij was heel moe.'
    for query in ('*31623455', '5*3', 'was heel moe'):
        matches = searchable_matches(source, re.compile(re.escape(query)))
        assert len(matches) == 1


def test_search_replacement_is_literal_and_consumes_escape_prefix():
    source = '5\\*3 en Bram.'
    replaced = replace_searchable_text(source, re.compile(r'5\*3'), '*Bram*')
    assert replaced.startswith(r'\*Bram\*')
    assert visible_projection(replaced).text == '*Bram* en Bram.'


def test_document_view_only_splits_on_physical_newline():
    source = 'Regel een\u2028- twee'
    view = parse_document(source)
    assert len(view.blocks) == 1
    assert view.blocks[0].kind == 'paragraph'
    assert view.blocks[0].text == source


def test_block_like_plain_text_and_image_syntax_are_encoded_literal():
    cases = [
        '- Kom je mee?',
        '1944. Het was koud.',
        '## geen kop',
        '> geen citaat',
        '***',
        '![foto](assets/images/0123456789abcdef0123456789abcdef.png)',
    ]
    for visible in cases:
        source = escape_literal_text(visible)
        view = parse_document(source)
        assert len(view.blocks) == 1
        assert view.blocks[0].kind == 'paragraph', (visible, source, view.blocks[0].kind)
        assert visible_projection(source).text == visible


def test_escaped_open_point_marker_is_literal_text():
    source = r'\<!--qw:todo:abcdef123456-->x\<!--/qw:todo-->'
    assert parse_open_points(source) == []
    assert marker_ranges(source) == []


def test_old_midline_backslash_dot_dash_hash_are_not_new_escapes():
    # Structural escapes are only meaningful at a physical line prefix.
    cases = [r'C:\Users\lucas\.config', r'pijl \-> rechts', r'regex a\.b', r'woord \#tag']
    for source in cases:
        assert visible_projection(source).text == source


def test_midline_literal_fragments_do_not_gain_structural_escapes():
    # A fragment inserted in the middle of a line cannot start a QuietWriter block.
    for visible in ('1944. Het', '- Kom mee', '## kop', '> citaat'):
        encoded = escape_literal_text(visible, at_line_start=False)
        combined = 'Begin ' + encoded
        assert visible_projection(combined).text == 'Begin ' + visible
        assert '\\-' not in combined and '\\>' not in combined and '\\##' not in combined
        if visible.startswith('1944.'):
            assert '1944\\.' not in combined


def test_structural_escape_stays_hidden_after_prefix_space_is_removed():
    for source, visible in [(r'\-', '-'), (r'\-Kom', '-Kom'), (r'\>Kom', '>Kom'), (r'\##Kom', '##Kom')]:
        assert visible_projection(source).text == visible
        assert parse_document(source).blocks[0].kind == 'paragraph'


def test_replace_across_format_boundary_is_skipped_instead_of_leaving_marker():
    source = 'was **heel** moe'
    assert replace_searchable_text(source, re.compile('was heel'), 'zij') == source
    assert replace_searchable_text(source, re.compile('heel'), 'erg') == 'was **erg** moe'
    assert replace_searchable_text(source, re.compile('was heel moe'), 'zij') == 'zij'
