from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExportUiSourceTests(unittest.TestCase):
    def test_export_is_own_navigation_page_after_book_details(self):
        source = (ROOT / 'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        book_pos = source.index("self.book_details_button = self._nav_button")
        export_pos = source.index("self.export_button = self._nav_button")
        self.assertGreater(export_pos, book_pos)
        self.assertIn('self.export_page = ExportPage(self)', source)

    def test_book_details_owns_language_but_no_export_button(self):
        source = (ROOT / 'quietwriter/ui/book_details.py').read_text(encoding='utf-8')
        self.assertIn("form.addRow(tr('book_details.field.language'", source)
        self.assertNotIn("export_btn = QPushButton", source)

    def test_cover_modes_are_explicit_and_future_asset_model_is_generic(self):
        source = (ROOT / 'quietwriter/ui/export_page.py').read_text(encoding='utf-8')
        self.assertIn("'artwork_with_text'", source)
        self.assertIn("'artwork_only'", source)
        model = (ROOT / 'quietwriter/exporting/models.py').read_text(encoding='utf-8')
        self.assertIn('class ExportAsset', model)
        self.assertIn("role: str = 'inline'", model)


if __name__ == '__main__':
    unittest.main()
