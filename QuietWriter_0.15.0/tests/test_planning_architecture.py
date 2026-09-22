import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlanningArchitectureTests(unittest.TestCase):
    def test_planning_is_split_into_own_ui_modules(self):
        base = ROOT / 'quietwriter' / 'ui' / 'planning'
        for name in ('planning_page.py', 'characters_page.py', 'outline_page.py', 'notes_page.py'):
            self.assertTrue((base / name).exists(), name)

    def test_main_window_exposes_one_planning_mode(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
        self.assertIn('self.planning_page = PlanningPage(self)', source)
        self.assertIn("tr('nav.planning', 'Planning')", source)

    def test_planning_is_kept_out_of_book_manifest_model(self):
        source = (ROOT / 'quietwriter' / 'storage.py').read_text(encoding='utf-8')
        self.assertNotIn("'characters': [", source)
        self.assertTrue((ROOT / 'quietwriter' / 'planning_storage.py').exists())


if __name__ == '__main__':
    unittest.main()
