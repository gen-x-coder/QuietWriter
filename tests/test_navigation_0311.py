from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Navigation0311Tests(unittest.TestCase):
    def test_current_book_order_matches_workflow(self):
        source=(ROOT/'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        names=['write_button','planning_button','book_memory_button','book_profile_button','media_button','book_details_button','export_button','integrity_button']
        positions=[source.index('self.'+name+' = self._nav_button') for name in names]
        self.assertEqual(positions, sorted(positions))
    def test_memory_profile_integrity_have_distinct_icons(self):
        source=(ROOT/'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("self.book_memory_button = self._nav_button('memory'", source)
        self.assertIn("self.book_profile_button = self._nav_button('book-profile'", source)
        self.assertIn("self.integrity_button = self._nav_button('shield'", source)
        for name in ('memory.svg','book-profile.svg','shield.svg'):
            self.assertTrue((ROOT/'quietwriter/icons'/name).is_file())
    def test_integrity_gap_only_expanded_with_open_book(self):
        source=(ROOT/'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("self.integrity_gap.setVisible(self.rail_expanded and has_book and advanced)", source)
