import unittest

from quietwriter.manuscript_markup import apply_block_style, smart_double_quote, toggle_inline, ManuscriptStyle


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
