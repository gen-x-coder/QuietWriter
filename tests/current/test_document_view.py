from quietwriter.document_view import (classify_block_line, content_inline_runs, image_reference_for_block_line,
                                       inline_runs, parse_document)


def test_document_view_classifies_current_blocks_in_one_place():
    source = 'Gewoon\n***\n## Kop\n> citaat\n- item\n1. item\n'
    view = parse_document(source)
    assert [block.kind for block in view.blocks] == [
        'paragraph', 'scene', 'heading', 'quote', 'bullet', 'numbered', 'empty'
    ]


def test_literal_unpaired_star_stays_plain_text():
    source = 'de man tikte het telefoonnummer in *31623455'
    view = parse_document(source)
    assert view.blocks[0].kind == 'paragraph'
    assert view.blocks[0].inline_spans == ()
    assert view.blocks[0].text == source


def test_inline_spans_never_pair_across_paragraph_lines():
    source = 'Prijs 5*3 euro.\nEn 2*4 meter.'
    view = parse_document(source)
    assert all(block.inline_spans == () for block in view.blocks)


def test_current_ambiguous_prose_is_reported_not_rewritten():
    source = '- Kom je mee?\n1944. Het was een koude winter.'
    view = parse_document(source)
    assert view.source == source
    assert [block.kind for block in view.blocks] == ['bullet', 'numbered']
    assert [item.code for item in view.diagnostics] == [
        'ambiguous-leading-dash', 'ambiguous-leading-number'
    ]


def test_scene_break_is_centralized_and_spaced_variant_is_not_silently_promoted():
    assert classify_block_line('***') == 'scene'
    assert classify_block_line(' * * * ') != 'scene'


def test_inline_marker_ranges_are_exposed_as_hidden_source_ranges():
    source = 'Dit is **vet** en *schuin*.'
    view = parse_document(source)
    assert view.hidden_ranges
    hidden_text = [source[a:b] for a, b in view.hidden_ranges]
    assert hidden_text.count('**') == 2
    assert hidden_text.count('*') == 2


def test_word_count_uses_semantics_not_markup_tokens():
    from quietwriter.media.markup import count_words
    source = '## Een kop\n- twee woorden\n***\n**drie** woorden\n'
    # Een kop (2) + twee woorden (2) + drie woorden (2); scene marker is structural.
    assert count_words(source) == 6


def test_pdf_docx_and_xhtml_share_block_classification(tmp_path):
    from quietwriter.exporting.markup import markdown_to_xhtml
    from quietwriter.exporting.pdf_exporter import _markdown_to_pdf_html
    source = '## Kop\n> Citaat\n- item\n1. nummer\n***\nGewoon'
    xhtml = markdown_to_xhtml(source)
    pdf = _markdown_to_pdf_html(source, {}, 600)
    for fragment in ('<h2', '<blockquote>', '<ul>', '<ol>', 'scene-break', '<p'):
        assert fragment in xhtml
        assert fragment in pdf


def test_block_style_states_uses_document_view_classification():
    from quietwriter.manuscript_markup import block_style_states
    text = '## Kop\n## Nog een'
    states = block_style_states(text, 0, len(text))
    assert states['heading'] is True
    assert states['paragraph'] is False


def test_empty_source_returns_empty_document_view():
    view = parse_document('')
    assert view.source == ''
    assert view.blocks == ()
    assert view.hidden_ranges == ()
    assert view.protected_ranges == ()
    assert view.diagnostics == ()


def test_language_tools_mask_structure_but_preserve_offsets_and_prose():
    from quietwriter.document_view import text_for_language_tools
    source = '## Kop\n- Kom je?\nDit is **vet** en *schuin*.\n***'
    masked = text_for_language_tools(source)
    assert len(masked) == len(source)
    assert 'Kop' in masked
    assert 'Kom je?' in masked
    assert 'vet' in masked and 'schuin' in masked
    assert '**' not in masked
    assert '***' not in masked


def test_ai_context_uses_semantics_not_source_markers():
    from quietwriter.document_view import text_for_ai_context
    source = '## Tussenkop\nDit is **belangrijk**.\n***\n- punt'
    context = text_for_ai_context(source)
    assert '## Tussenkop' in context
    assert 'Dit is belangrijk.' in context
    assert '[Scènebreuk]' in context
    assert '- punt' in context
    assert '**' not in context


def test_language_tools_keep_literal_unpaired_star():
    from quietwriter.document_view import text_for_language_tools
    source = 'de man tikte *31623455 in'
    assert text_for_language_tools(source) == source


def test_xhtml_heading_labels_use_document_view_visible_text():
    from quietwriter.exporting.markup import markdown_to_xhtml_with_headings
    body, headings = markdown_to_xhtml_with_headings('## **Sterke** kop')
    assert '<strong>Sterke</strong> kop' in body
    assert headings == [('h-1', 'Sterke kop')]


def test_image_masking_uses_document_view_block_ranges():
    from quietwriter.media.markup import build_image_markdown, text_without_image_blocks
    block = build_image_markdown('../assets/images/x.png', alt='kaart')
    source = 'Voor\n' + block + '\nNa'
    masked = text_without_image_blocks(source)
    assert masked.startswith('Voor\n')
    assert masked.endswith('\nNa')
    assert 'x.png' not in masked


def test_publication_heading_semantics_are_available_centrally():
    from quietwriter.document_view import parse_document, visible_block_text
    source = 'Gewoon\n## *Tussenkop*\nNa'
    headings = [visible_block_text(b) for b in parse_document(source).blocks if b.kind == 'heading']
    assert headings == ['Tussenkop']

def test_inline_runs_are_the_single_semantic_inline_view():
    runs = inline_runs('Voor **vet** en *schuin* en *31623455')
    assert [(run.text, run.styles) for run in runs] == [
        ('Voor ', frozenset()),
        ('vet', frozenset({'bold'})),
        (' en ', frozenset()),
        ('schuin', frozenset({'italic'})),
        (' en *31623455', frozenset()),
    ]


def test_content_inline_runs_remove_block_prefix_without_reparsing():
    block = parse_document('> Dit is **belangrijk**.').blocks[0]
    runs = content_inline_runs(block)
    assert ''.join(run.text for run in runs) == 'Dit is belangrijk.'
    assert any('bold' in run.styles for run in runs if run.text == 'belangrijk')


def test_image_interpretation_is_available_through_document_view_boundary():
    line = '![Alt](../assets/images/x.png "Bijschrift") <!-- qw:image width=medium align=right wrap=true -->'
    ref = image_reference_for_block_line(line)
    assert ref is not None
    assert ref.path.endswith('/x.png')
    block = parse_document(line).blocks[0]
    assert block.kind == 'image'
    assert block.attrs['caption'] == 'Bijschrift'
    assert block.attrs['align'] == 'right'



def test_backslash_escaped_inline_markers_are_literal_visible_text():
    from quietwriter.document_view import visible_inline_text
    source = r'De man tikte \*31623455 en 5\*3.'
    view = parse_document(source)
    assert view.blocks[0].inline_spans == ()
    assert visible_inline_text(source) == 'De man tikte *31623455 en 5*3.'
    assert (source.index('\\'), source.index('\\') + 1) in view.hidden_ranges


def test_backslash_escaped_block_prefixes_are_plain_paragraphs():
    assert classify_block_line(r'\- Kom je mee?') == 'paragraph'
    assert classify_block_line(r'\> Geen citaat') == 'paragraph'
    assert classify_block_line(r'\## Geen kop') == 'paragraph'
    assert classify_block_line(r'1944\. Het jaar') == 'paragraph'


def test_escaped_literal_prose_exports_as_literal_prose():
    from quietwriter.exporting.markup import markdown_to_xhtml
    source = '\\- Kom je mee?\n1944\\. Het jaar.\nPrijs: 5\\*3 = 15 en 2\\*4 = 8.'
    xhtml = markdown_to_xhtml(source)
    assert '<ul>' not in xhtml and '<ol>' not in xhtml
    assert '<em>' not in xhtml
    assert '<p>- Kom je mee?</p>' in xhtml
    assert '<p>1944. Het jaar.</p>' in xhtml
    assert 'Prijs: 5*3 = 15 en 2*4 = 8.' in xhtml


def test_explicit_unescaped_formatting_still_has_semantics():
    source = '**vet** en *cursief*'
    runs = inline_runs(source)
    assert any(run.text == 'vet' and 'bold' in run.styles for run in runs)
    assert any(run.text == 'cursief' and 'italic' in run.styles for run in runs)


def test_visible_text_and_word_count_share_central_semantics():
    from quietwriter.document_view import count_visible_words, visible_text
    source = '## **Kop**\n- twee woorden\n***\nPrijs: 5\\*3.'
    assert visible_text(source) == 'Kop\ntwee woorden\n\nPrijs: 5*3.'
    assert count_visible_words(source) == 5


def test_ai_context_preserves_actual_ordered_list_number():
    from quietwriter.document_view import text_for_ai_context
    assert text_for_ai_context('3. derde punt') == '3. derde punt'
