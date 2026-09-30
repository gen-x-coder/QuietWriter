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
        self.assertIn("'editor_font': new_typography.family", settings)
        self.assertIn("'editor_font_size': int(self.editor_font_size.value())", settings)
        self.assertIn('self._populate_font_combo(self.original_typography.family)', settings)
        self.assertIn('recommended_families(families)', settings)
        self.assertIn('system_families_excluding_recommended(families)', settings)

    def test_committed_font_change_rebases_existing_document_characters(self):
        editor = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
        start = editor.index('    def apply_typography(self, typography: WritingTypography):')
        end = editor.index('    def set_editor_font(', start)
        block = editor[start:end]
        self.assertIn('self.setFont(font)', block)
        self.assertIn('document.setDefaultFont(font)', block)
        self.assertIn('cursor.select(QTextCursor.SelectionType.Document)', block)
        self.assertIn('base_format.setFont(font)', block)
        self.assertIn('cursor.mergeCharFormat(base_format)', block)
        self.assertIn('self.blockSignals(True)', block)
        self.assertIn('document.setModified(was_modified)', block)
        self.assertIn('presentation_highlighter.rehighlight()', block)

    def test_no_code_copies_an_unknown_negative_point_size(self):
        quietwriter = ROOT / 'quietwriter'
        sources = '\n'.join(p.read_text(encoding='utf-8') for p in quietwriter.rglob('*.py'))
        self.assertNotIn('.pointSize()', sources)
        self.assertNotIn('setPointSize(max(9,', sources)


if __name__ == '__main__':
    unittest.main()
