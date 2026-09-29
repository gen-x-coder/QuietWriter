from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path


PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlZ3ioAAAAASUVORK5CYII='
)


class MediaManagerSource0270Tests(unittest.TestCase):
    def test_main_window_wires_media_as_book_level_page(self):
        source = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn('MediaManagerPage', source)
        self.assertIn("tr('nav.media', 'Media')", source)
        self.assertIn('self.media_manager_page.adopt_book(book)', source)
        self.assertIn('def show_media(self):', source)
        self.assertIn('self.media_button.setVisible(has_book)', source)

    def test_media_page_is_text_first_and_uses_manager_cleanup(self):
        source = Path('quietwriter/ui/media_manager_page.py').read_text(encoding='utf-8')
        self.assertIn('QListWidget', source)
        self.assertNotIn('QPixmap', source)
        self.assertNotIn('QImage', source)
        self.assertIn('self.manager.inspect(self.book, include_history=True)', source)
        self.assertIn('self.manager.cleanup_unused(self.book, asset_ids=[item.id for item in candidates])', source)
        self.assertIn('except ExternalModificationError as exc:', source)
        self.assertIn('self.main.adopt_active_book(', source)
        self.assertIn('Versiegeschiedenis', source)


try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar
    from quietwriter.media.store import MediaStore
    from quietwriter.storage import Library
    from quietwriter.ui.media_manager_page import MediaManagerPage
except Exception:
    QApplication = None


@unittest.skipIf(QApplication is None, 'PySide6 niet beschikbaar')
class MediaManagerQt0270Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_page_refreshes_inventory_without_visual_interaction(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Media UI')
            source = root / 'unused.png'
            source.write_bytes(PNG_1X1)
            MediaStore(library).import_image(book, source)

            main = QMainWindow()
            main.library = library
            main.status = QStatusBar(main)
            page = MediaManagerPage(main)
            page.set_book(book)

            self.assertIsNotNone(page.inventory)
            self.assertEqual(len(page.inventory.items), 1)
            self.assertEqual(page.inventory.unused_count, 1)
            self.assertTrue(page.cleanup_button.isEnabled())
            self.assertEqual(page.list.count(), 1)


if __name__ == '__main__':
    unittest.main()
