from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class EditorPolish0310Tests(unittest.TestCase):
    def test_editor_autosave_is_not_conditioned_on_setting(self):
        src = (ROOT / "quietwriter/ui/editor_page.py").read_text(encoding="utf-8")
        self.assertNotIn("settings.value('autosave'", src)
        self.assertIn("self.autosave_timer.start()", src)

    def test_settings_no_longer_offer_autosave_toggle(self):
        src = (ROOT / "quietwriter/ui/settings_page.py").read_text(encoding="utf-8")
        self.assertNotIn("self.autosave = QCheckBox", src)
        self.assertIn("self.settings.setValue('autosave', True)", src)

    def test_book_word_label_is_explicit(self):
        src = (ROOT / "quietwriter/ui/editor_page.py").read_text(encoding="utf-8")
        self.assertIn("Boek bevat 0 woorden", src)
        self.assertIn("'Boek bevat ' + f'{total:,}'", src)

    def test_navigation_has_subtle_groups(self):
        src = (ROOT / "quietwriter/ui/main_window.py").read_text(encoding="utf-8")
        for label in ("BIBLIOTHEEK", "HUIDIG BOEK", "SCHRIJVEN", "PROGRAMMA"):
            self.assertIn(label, src)
        self.assertIn("navGroupLabel", src)

if __name__ == "__main__": unittest.main()
