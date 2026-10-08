import unittest

from quietwriter.manuscript_markup import (
    ManuscriptStyle, apply_block_style, parse_inline_spans,
    UnsafeMarkdownInsertionError, prepare_markdown_insertion, prepare_markdown_removal, smart_double_quote, toggle_inline,
)


class ManuscriptMarkupTests(unittest.TestCase):
    def test_inline_bold_roundtrip(self):
        text = 'Dit is belangrijk.'
        new, start, end = toggle_inline(text, 7, 17, 'bold')
        self.assertEqual(new, 'Dit is **belangrijk**.')
        self.assertEqual(new[start:end], 'belangrijk')
        restored, rstart, rend = toggle_inline(new, start, end, 'bold')
        self.assertEqual(restored, text)
        self.assertEqual(restored[rstart:rend], 'belangrijk')

    def test_heading_uses_double_hash_to_preserve_chapter_boundary(self):
        text = 'Tussenkop\nTekst'
        new, _, _ = apply_block_style(text, 0, 9, 'heading')
        self.assertTrue(new.startswith('## Tussenkop'))
        self.assertFalse(new.startswith('# Tussenkop\n'))

    def test_bullet_toggle(self):
        text = 'Een\nTwee'
        new, start, end = apply_block_style(text, 0, len(text), 'bullet')
        self.assertEqual(new, '- Een\n- Twee')
        restored, _, _ = apply_block_style(new, start, end, 'bullet')
        self.assertEqual(restored, text)

    def test_numbered_list_is_renumbered(self):
        text = 'Een\nTwee\nDrie'
        new, _, _ = apply_block_style(text, 0, len(text), 'numbered')
        self.assertEqual(new, '1. Een\n2. Twee\n3. Drie')

    def test_quote_context(self):
        self.assertEqual(smart_double_quote('', 0), '“')
        self.assertEqual(smart_double_quote('Hij zei ', 8), '“')
        self.assertEqual(smart_double_quote('“Hallo', 6), '”')

    def test_style_values_are_clamped(self):
        style = ManuscriptStyle.from_values(999, -5, 999, True)
        self.assertEqual(style.line_spacing_percent, 200)
        self.assertEqual(style.paragraph_indent_px, 0)
        self.assertEqual(style.paragraph_spacing_px, 24)


if __name__ == '__main__':
    unittest.main()

class ManuscriptCombinedFormattingTests(unittest.TestCase):
    def test_bold_then_italic_preserves_both_styles(self):
        from quietwriter.manuscript_markup import selection_format_states
        text, start, end = toggle_inline('tekst', 0, 5, 'bold')
        text, start, end = toggle_inline(text, start, end, 'italic')
        self.assertEqual(text, '***tekst***')
        states = selection_format_states(text, start, end)
        self.assertTrue(states['bold'])
        self.assertTrue(states['italic'])

    def test_removing_one_combined_style_preserves_the_other(self):
        from quietwriter.manuscript_markup import selection_format_states
        text, start, end = toggle_inline('tekst', 0, 5, 'bold')
        text, start, end = toggle_inline(text, start, end, 'italic')
        text, start, end = toggle_inline(text, start, end, 'bold')
        self.assertEqual(text, '*tekst*')
        states = selection_format_states(text, start, end)
        self.assertFalse(states['bold'])
        self.assertTrue(states['italic'])

    def test_mixed_italic_selection_normalises_then_clears(self):
        from quietwriter.manuscript_markup import selection_format_states
        original = 'Een *cursief* woord en gewoon.'
        text, start, end = toggle_inline(original, 0, len(original), 'italic')
        self.assertEqual(text, '*Een cursief woord en gewoon.*')
        self.assertTrue(selection_format_states(text, start, end)['italic'])
        text, start, end = toggle_inline(text, start, end, 'italic')
        self.assertEqual(text, 'Een cursief woord en gewoon.')
        self.assertFalse(selection_format_states(text, start, end)['italic'])

    def test_applying_italic_to_text_with_bold_preserves_bold_source(self):
        from quietwriter.manuscript_markup import selection_format_states
        original = '**vet** en gewoon'
        text, start, end = toggle_inline(original, 0, len(original), 'italic')
        self.assertIn('**vet**', text)
        self.assertTrue(selection_format_states(text, start, end)['italic'])
        text, start, end = toggle_inline(text, start, end, 'italic')
        self.assertEqual(text, original)

class ManuscriptProtectionTests(unittest.TestCase):
    def test_scene_break_survives_all_inline_toggles(self):
        for kind in ('bold', 'italic', 'underline', 'strike', 'code'):
            original = 'Voor\n***\nNa'
            new, _, _ = toggle_inline(original, 0, len(original), kind)
            self.assertEqual(new.splitlines()[1], '***', kind)

    def test_scene_break_survives_all_block_styles(self):
        for style in ('paragraph', 'heading', 'quote', 'bullet', 'numbered'):
            original = 'Voor\n***\nNa'
            new, _, _ = apply_block_style(original, 0, len(original), style)
            self.assertEqual(new.splitlines()[1], '***', style)

    def test_scene_break_does_not_make_inline_state_mixed(self):
        from quietwriter.manuscript_markup import inline_style_state
        text = '**Voor**\n***\n**Na**'
        self.assertTrue(inline_style_state(text, 0, len(text), 'bold'))

    def test_other_styles_never_inject_markers_inside_code_span(self):
        original = '`code` en meer'
        # Start inside the literal code content and continue past it.
        start = original.index('d')
        end = len(original)
        for kind in ('bold', 'italic', 'underline', 'strike'):
            new, _, _ = toggle_inline(original, start, end, kind)
            self.assertIn('`code`', new, kind)
            code_start = new.index('`')
            code_end = new.index('`', code_start + 1)
            self.assertEqual(new[code_start:code_end + 1], '`code`', kind)

    def test_style_crossing_code_only_formats_outside_literal_region(self):
        original = 'voor `code` na'
        new, _, _ = toggle_inline(original, 0, len(original), 'bold')
        self.assertEqual(new, '**voor **`code`** na**')
        self.assertIn('`code`', new)

    def test_multiline_mixed_style_state_requires_full_visible_selection(self):
        from quietwriter.manuscript_markup import inline_style_state
        mixed = '**Een**\nTwee'
        self.assertFalse(inline_style_state(mixed, 0, len(mixed), 'bold'))
        complete = '**Een**\n**Twee**'
        self.assertTrue(inline_style_state(complete, 0, len(complete), 'bold'))


class DarlingInsertionMarkupTests(unittest.TestCase):
    @staticmethod
    def _visible_with_styles(text):
        spans = parse_inline_spans(text)
        marker_positions = set()
        for span in spans:
            for a, b in span.marker_ranges:
                marker_positions.update(range(a, b))
        out = []
        for i, ch in enumerate(text):
            if i in marker_positions:
                continue
            styles = frozenset(
                span.kind for span in spans
                if span.content_start <= i < span.content_end
            )
            out.append((ch, styles))
        return out

    @classmethod
    def _visible_offset(cls, text, position):
        spans = parse_inline_spans(text)
        marker_positions = set()
        for span in spans:
            for a, b in span.marker_ranges:
                marker_positions.update(range(a, b))
        return sum(1 for i in range(min(position, len(text))) if i not in marker_positions)

    def test_darling_insertion_is_visually_and_stylistically_stable_at_every_source_position(self):
        source = 'Voor **vet woord** en *schuin* en ~~weg~~ en `code` na.'
        fragments = [
            'gewoon',
            '**vet fragment**',
            '*schuin fragment*',
            '~~weg fragment~~',
            '`code fragment`',
        ]
        base = self._visible_with_styles(source)
        for fragment in fragments:
            fragment_visible = self._visible_with_styles(fragment)
            for original_position in range(len(source) + 1):
                position, insertion = prepare_markdown_insertion(source, original_position, fragment)
                result = source[:position] + insertion + source[position:]
                offset = self._visible_offset(source, position)
                expected = base[:offset] + fragment_visible + base[offset:]
                self.assertEqual(
                    self._visible_with_styles(result), expected,
                    msg=f'pos={original_position}, normalized={position}, fragment={fragment!r}, result={result!r}',
                )


    def test_rich_darling_insertion_is_exact_or_safely_refused_at_every_position(self):
        sources = [
            'Voor **vet woord** en *schuin* en ~~weg~~ en `code` na.',
            '**helemaal vet met *schuin* erin** en gewoon.',
            'Start ***beide*** en <u>onderstreept</u> einde.',
            'Start ~~weg met **vet** erin~~ einde.',
            'Voor `code met **letterlijke sterren**` en **vet** na.',
            'Eerste alinea.\n***\nDaarna **vet** en *schuin*.',
        ]
        fragments = [
            'gewoon',
            '**vet** ',
            ' *cursief*',
            '**a** en *b*',
            'staat **vet**',
            '~~weg~~ ',
            '`code` ',
            '<u>onder</u> ',
            '***beide*** ',
        ]
        accepted = refused = 0
        for source in sources:
            base = self._visible_with_styles(source)
            for fragment in fragments:
                fragment_visible = self._visible_with_styles(fragment)
                for original_position in range(len(source) + 1):
                    try:
                        position, insertion = prepare_markdown_insertion(source, original_position, fragment)
                    except UnsafeMarkdownInsertionError:
                        refused += 1
                        continue
                    accepted += 1
                    result = source[:position] + insertion + source[position:]
                    offset = self._visible_offset(source, original_position)
                    expected = base[:offset] + fragment_visible + base[offset:]
                    self.assertEqual(
                        self._visible_with_styles(result), expected,
                        msg=(f'source={source!r}, pos={original_position}, normalized={position}, '
                             f'fragment={fragment!r}, result={result!r}'),
                    )
        self.assertGreater(accepted, 100)
        self.assertGreater(refused, 0)

    def test_boundary_before_bold_moves_before_opening_marker(self):
        source = 'Voor **vet woord** na.'
        content_start = source.index('vet woord')
        position, insertion = prepare_markdown_insertion(source, content_start, '**darling** ')
        self.assertEqual(position, source.index('**'))
        self.assertEqual(source[:position] + insertion + source[position:], 'Voor **darling** **vet woord** na.')
    def test_prepare_markdown_removal_preserves_remaining_formatting(self):
        cases = [
            ('Voor **vet woord** na.', 'woord'),
            ('Voor *schuin woord* na.', 'schuin'),
            ('Voor **vet** en *schuin* na.', 'vet'),
            ('Voor ~~weg woord~~ na.', 'woord'),
        ]
        for source, visible_piece in cases:
            start = source.index(visible_piece)
            end = start + len(visible_piece)
            a, b, replacement = prepare_markdown_removal(source, start, end)
            result = source[:a] + replacement + source[b:]
            base = self._visible_with_styles(source)
            so = self._visible_offset(source, start)
            eo = self._visible_offset(source, end)
            self.assertEqual(self._visible_with_styles(result), base[:so] + base[eo:])


    def test_prepare_markdown_removal_accepts_common_half_formatted_selections(self):
        cases = [
            ('Voor **vet woord** en daarna.', 'woord', ' en'),
            ('Voor *schuin woord* en daarna.', 'woord', ' en'),
            ('Start **vet woord** einde.', 'vet woord', None),
            ('Start *schuin woord* einde.', 'schuin woord', None),
        ]
        for source, piece, tail in cases:
            start = source.index(piece)
            end = (source.index(tail, start) + len(tail)) if tail else (start + len(piece))
            base = self._visible_with_styles(source)
            so = self._visible_offset(source, start)
            eo = self._visible_offset(source, end)
            a, b, replacement = prepare_markdown_removal(source, start, end)
            result = source[:a] + replacement + source[b:]
            self.assertEqual(self._visible_with_styles(result), base[:so] + base[eo:])


    def test_prepare_markdown_removal_does_not_leave_obvious_empty_spans(self):
        sources = [
            'Een **vet woord** en *schuin woord* en ~~weg woord~~ en `code woord` klaar.',
            'Begin ***vet en schuin*** naast **vet** en *schuin* einde.',
        ]
        empty_tokens = ('****', '~~~~', '``', '<u></u>')
        checked = 0
        for source in sources:
            for start in range(len(source)):
                for end in range(start + 1, len(source) + 1):
                    try:
                        a, b, replacement = prepare_markdown_removal(source, start, end)
                    except UnsafeMarkdownInsertionError:
                        continue
                    result = source[:a] + replacement + source[b:]
                    for token in empty_tokens:
                        self.assertNotIn(token, result, msg=(source, start, end, token, result))
                    checked += 1
        self.assertGreater(checked, 100)

    def test_existing_literal_empty_marker_text_elsewhere_does_not_block_cut(self):
        source = 'Gewone tekst om te knippen. Hij vloekte: ****! Daarna verder.'
        start = source.index('Gewone ')
        end = start + len('Gewone ')
        a, b, replacement = prepare_markdown_removal(source, start, end)
        result = source[:a] + replacement + source[b:]
        self.assertEqual(result, 'tekst om te knippen. Hij vloekte: ****! Daarna verder.')

    def test_linear_style_validation_handles_realistic_long_chapter(self):
        import time
        paragraph = 'Gewone tekst met **vet woord** en *schuin woord* voor een realistisch hoofdstuk.\n'
        source = paragraph * 500  # roughly a few thousand words; regression guard, not a benchmark contest.
        position = len(source) // 2
        started = time.perf_counter()
        prepare_markdown_insertion(source, position, '**fragment** ')
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 1.0, f'lineaire invoegcontrole duurde {elapsed:.3f}s')



class ManuscriptLiteralEscapingTests(unittest.TestCase):
    def test_direct_inline_punctuation_is_encoded_as_literal(self):
        from quietwriter.manuscript_markup import escape_literal_typed_char
        self.assertEqual(escape_literal_typed_char('*', 'telefoon '), r'\*')
        self.assertEqual(escape_literal_typed_char('~', 'woord'), r'\~')
        self.assertEqual(escape_literal_typed_char('`', ''), r'\`')
        self.assertEqual(escape_literal_typed_char('x', ''), 'x')

    def test_space_that_would_complete_block_markup_escapes_prefix(self):
        from quietwriter.manuscript_markup import escape_literal_space_prefix
        self.assertEqual(escape_literal_space_prefix('-'), (r'\-', 1))
        self.assertEqual(escape_literal_space_prefix('>'), (r'\>', 1))
        self.assertEqual(escape_literal_space_prefix('##'), (r'\##', 2))
        self.assertEqual(escape_literal_space_prefix('1944.'), (r'1944\.', 5))
        self.assertIsNone(escape_literal_space_prefix('woord'))

    def test_pasted_plain_text_is_encoded_but_visually_roundtrips(self):
        from quietwriter.manuscript_markup import escape_literal_text, unescape_literal_text
        visible = '- Kom je?\n1944. Winter.\nPrijs 5*3 en *31623455\n**niet bewust vet**'
        encoded = escape_literal_text(visible)
        self.assertIn(r'\- Kom je?', encoded)
        self.assertIn(r'1944\. Winter.', encoded)
        self.assertIn(r'5\*3', encoded)
        self.assertEqual(unescape_literal_text(encoded), visible)

    def test_escaped_stars_never_form_inline_span(self):
        from quietwriter.manuscript_markup import parse_inline_spans
        self.assertEqual(parse_inline_spans(r'Prijs 5\*3 en 2\*4.'), [])
        self.assertEqual(parse_inline_spans(r'\*woord\*'), [])
        self.assertTrue(any(s.kind == 'italic' for s in parse_inline_spans('*woord*')))


class ManuscriptSourceSerializationTests(unittest.TestCase):
    def test_serializer_escapes_literal_markup_before_adding_semantic_style(self):
        from quietwriter.document_view import inline_runs, visible_inline_text
        from quietwriter.manuscript_markup import serialize_inline_text

        source = serialize_inline_text('*316 en 5*3 en **letterlijk**', {'italic'})
        self.assertEqual(visible_inline_text(source), '*316 en 5*3 en **letterlijk**')
        runs = inline_runs(source)
        self.assertTrue(runs)
        self.assertTrue(all('italic' in run.styles for run in runs))

    def test_serializer_keeps_inline_styles_inside_each_physical_line(self):
        from quietwriter.document_view import parse_document, visible_block_text
        from quietwriter.manuscript_markup import serialize_inline_text

        source = serialize_inline_text('eerste\ntweede', {'bold'})
        self.assertEqual(source, '**eerste**\n**tweede**')
        blocks = parse_document(source).blocks
        self.assertEqual([visible_block_text(block) for block in blocks], ['eerste', 'tweede'])
        self.assertTrue(all(any(span.kind == 'bold' for span in block.inline_spans) for block in blocks))

    def test_block_serializer_is_explicit_structure_not_literal_prose(self):
        from quietwriter.document_view import classify_block_line, visible_block_text, parse_block_line
        from quietwriter.manuscript_markup import serialize_block_source, serialize_inline_text

        literal = serialize_inline_text('- Kom je mee?')
        self.assertEqual(classify_block_line(literal), 'paragraph')
        bullet = serialize_block_source('bullet', serialize_inline_text('Kom je mee?'))
        self.assertEqual(classify_block_line(bullet), 'bullet')
        self.assertEqual(visible_block_text(parse_block_line(bullet)), 'Kom je mee?')

    def test_scene_break_serializer_is_structural_and_rejects_content(self):
        from quietwriter.document_view import classify_block_line
        from quietwriter.manuscript_markup import serialize_block_source

        source = serialize_block_source('scene', '')
        self.assertEqual(source, '***')
        self.assertEqual(classify_block_line(source), 'scene')
        with self.assertRaises(ValueError):
            serialize_block_source('scene', 'tekst')


def test_scene_break_lines_are_not_parsed_as_inline_emphasis():
    from quietwriter.manuscript_syntax import parse_inline_spans

    source = 'Voor.\n\n***\n\nNa.\n\n***\n\nEinde.'
    spans = parse_inline_spans(source)
    assert not any(source[span.open_start:span.open_end].startswith('*') for span in spans)


def test_internal_fragment_with_scene_break_can_be_inserted_at_line_boundary():
    from quietwriter.manuscript_markup import prepare_markdown_insertion

    fragment = 'Regel een.\n\n**Vet** en *cursief*.\n\n***\n\nNa de breuk.'
    base = 'Bestaand hoofdstuk.\n'
    position, insertion = prepare_markdown_insertion(base, len(base), fragment)
    assert position == len(base)
    assert insertion == fragment
    result = base[:position] + insertion + base[position:]
    assert result.count('***') == 1
    assert '**Vet**' in result
    assert '*cursief*' in result
