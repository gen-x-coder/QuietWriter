import tempfile
import unittest
from pathlib import Path

from quietwriter.spell_engine import WordDictionary


class SpellEngineTests(unittest.TestCase):
    def make_dic(self, root: Path):
        p = root / 'nl_NL.dic'
        p.write_text('6\ndit\nis\neen\nboek\nwoord\ncorrect\n', encoding='utf-8')
        return p

    def test_persistent_ignore_is_separate_from_personal_dictionary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = WordDictionary(); d.load_dic(self.make_dic(root))
            d.load_personal(root / 'persoonlijk.txt')
            d.load_persistent_ignored(root / 'altijd_negeren.txt')
            self.assertFalse(d.known('fantasienaam'))
            d.ignore_always('fantasienaam')
            self.assertTrue(d.known('fantasienaam'))
            self.assertNotIn('fantasienaam', d.personal_words)
            self.assertIn('fantasienaam', (root / 'altijd_negeren.txt').read_text(encoding='utf-8'))
            d2 = WordDictionary(); d2.load_dic(self.make_dic(root)); d2.load_persistent_ignored(root / 'altijd_negeren.txt')
            self.assertTrue(d2.known('fantasienaam'))

    def test_session_ignore_is_not_persisted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); d = WordDictionary(); d.load_dic(self.make_dic(root)); d.ignore('tijdelijkwoord')
            self.assertTrue(d.known('tijdelijkwoord'))
            d2 = WordDictionary(); d2.load_dic(self.make_dic(root))
            self.assertFalse(d2.known('tijdelijkwoord'))

    def test_large_repeated_chapter_scans_without_changing_result(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); d = WordDictionary(); d.load_dic(self.make_dic(root))
            text = ('dit is een correct woord foutwoord ' * 5000).strip()
            rows = d.misspellings(text)
            self.assertEqual(len(rows), 5000)
            self.assertTrue(all(row[0] == 'foutwoord' for row in rows))
            # A second scan exercises the known-word cache and must be identical.
            self.assertEqual(d.misspellings(text), rows)

if __name__ == '__main__':
    unittest.main()
