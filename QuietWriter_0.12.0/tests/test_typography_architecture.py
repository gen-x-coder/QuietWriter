import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TypographyArchitectureTests(unittest.TestCase):
    def test_typography_is_isolated_from_theme_stylesheet(self):
        themes = (ROOT / 'quietwriter' / 'themes.py').read_text(encoding='utf-8')
        self.assertIn('def stylesheet(name: str)', themes)
        self.assertNotIn('editor_font:', themes)
        self.assertNotIn('font_stack', themes)
        widget_rule = themes.split('QWidget {', 1)[1].split('}', 1)[0]
        self.assertNotIn('font-family', widget_rule)
        self.assertNotIn('font-size', widget_rule)

    def test_writer_font_and_size_are_independent_settings(self):
        settings = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
        self.assertIn("self.settings.setValue('editor_font',", settings)
        self.assertIn("self.settings.setValue('editor_font_size',", settings)
        self.assertIn('self.editor_font.addItems(available_families())', settings)

    def test_live_font_change_does_not_rewrite_document_character_formats(self):
        editor = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
        start = editor.index('    def apply_typography(self, typography: WritingTypography):')
        end = editor.index('    def set_editor_font(', start)
        block = editor[start:end]
        self.assertIn('self.setFont(font)', block)
        self.assertIn('self.document().setDefaultFont(font)', block)
        self.assertNotIn('mergeCharFormat', block)
        self.assertNotIn('setFontFamilies', block)
        self.assertNotIn('setFontPointSize', block)

    def test_no_code_copies_an_unknown_negative_point_size(self):
        quietwriter = ROOT / 'quietwriter'
        sources = '\n'.join(p.read_text(encoding='utf-8') for p in quietwriter.rglob('*.py'))
        self.assertNotIn('.pointSize()', sources)
        self.assertNotIn('setPointSize(max(9,', sources)


if __name__ == '__main__':
    unittest.main()
