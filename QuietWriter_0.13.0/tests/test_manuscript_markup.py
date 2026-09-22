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
