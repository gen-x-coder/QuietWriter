from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class QtCompatibilitySourceTests(unittest.TestCase):
    def test_line_height_normalizes_enum_to_int_and_height_to_float(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
        self.assertIn("hasattr(line_height_type, 'value')", source)
        self.assertIn('int(line_height_type)', source)
        self.assertIn('float(self.manuscript_style.line_spacing_percent)', source)
        self.assertNotIn('setLineHeight(self.manuscript_style.line_spacing_percent, QTextBlockFormat.ProportionalHeight)', source)


if __name__ == '__main__':
    unittest.main()
