from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class EditorPolish0310Tests(unittest.TestCase):
    def test_editor_autosave_is_not_conditioned_on_setting(self):
        src = (ROOT / "quietwriter/ui/editor_page.py").read_text(encoding="utf-8")
        self.assertNotIn("settings.value('autosave'", src)
        self.assertIn("self.autosave_timer.start()", src)

    def test_settings_no_longer_offer_autosave_toggle(self):
        src = (ROOT / "quietwriter/ui/settings_page.py").read_text(encoding="utf-8")
        self.assertNotIn("self.autosave = QCheckBox", src)
        self.assertIn("self.settings.setValue('autosave', True)", src)

    def test_book_and_chapter_word_counts_share_statusbar(self):
        src = (ROOT / "quietwriter/ui/editor_page.py").read_text(encoding="utf-8")
        self.assertNotIn("self.book_words", src)
        self.assertIn("book_text = f'Boek: {total:,}'", src)
        self.assertIn("chapter_text = f'Hoofdstuk {chapter_index} van {chapter_total}: {words:,}'", src)

    def test_navigation_has_subtle_groups(self):
        src = (ROOT / "quietwriter/ui/main_window.py").read_text(encoding="utf-8")
        for label in ("BIBLIOTHEEK", "HUIDIG BOEK", "AI-CONTEXT", "PROGRAMMA"):
            self.assertIn(label, src)
        self.assertIn("navGroupLabel", src)

if __name__ == "__main__": unittest.main()
