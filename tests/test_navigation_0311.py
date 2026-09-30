from pathlib import Path
import unittest

from quietwriter.ui.rail_model import RAIL_ITEMS

ROOT = Path(__file__).resolve().parents[1]


class Navigation0311Tests(unittest.TestCase):
    def test_current_book_order_matches_033_information_architecture(self):
        current = [item.key for item in RAIL_ITEMS if item.group == 'current_book']
        self.assertEqual(current, ['contents', 'planning', 'media', 'book_details', 'export', 'integrity'])

    def test_memory_profile_integrity_have_distinct_icons(self):
        source=(ROOT/'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("self.book_memory_button = self._register_nav_item('book_memory', 'memory'", source)
        self.assertIn("self.book_profile_button = self._register_nav_item('book_profile', 'book-profile'", source)
        self.assertIn("self.integrity_button = self._register_nav_item('integrity', 'shield'", source)
        for name in ('memory.svg','book-profile.svg','shield.svg'):
            self.assertTrue((ROOT/'quietwriter/icons'/name).is_file())

    def test_integrity_is_a_current_book_advanced_item(self):
        integrity = next(item for item in RAIL_ITEMS if item.key == 'integrity')
        self.assertEqual(integrity.group, 'current_book')
        self.assertTrue(integrity.requires_book)
        self.assertTrue(integrity.requires_advanced)
