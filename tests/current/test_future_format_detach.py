from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class ReviewSafety0283SourceTests(unittest.TestCase):
    def test_future_format_detach_is_centralized(self):
        main = (ROOT/'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn('def preserve_local_and_close_future_book', main)
        self.assertIn("kind='conflict_local'", main)
        self.assertIn('self.force_return_to_bookshelf(book)', main)

    def test_planning_profile_memory_use_central_future_format_path(self):
        for rel in [
            'quietwriter/ui/planning/planning_page.py',
            'quietwriter/ui/book_profile_page.py',
            'quietwriter/ui/book_memory_page.py',
        ]:
            text=(ROOT/rel).read_text(encoding='utf-8')
            self.assertIn('except FutureBookFormatError:', text, rel)
            self.assertIn('preserve_local_and_close_future_book', text, rel)

    def test_book_details_is_guarded_on_navigation_home_and_close(self):
        main=(ROOT/'quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn('def _save_book_details_if_pending', main)
        self.assertGreaterEqual(main.count('_save_book_details_if_pending()'), 10)
        details=(ROOT/'quietwriter/ui/book_details.py').read_text(encoding='utf-8')
        self.assertIn('return True', details)
        self.assertIn('return False', details)

if __name__ == '__main__': unittest.main()
