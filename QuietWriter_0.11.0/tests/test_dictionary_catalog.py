import tempfile
import unittest
from pathlib import Path

from quietwriter.dictionary_catalog import DictionaryCatalog, locale_label


class DictionaryCatalogTests(unittest.TestCase):
    def _dict(self, root, locale):
        folder = root / locale
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{locale}.dic').write_text('1\nwoord\n', encoding='utf-8')
        (folder / f'{locale}.aff').write_text('SET UTF-8\n', encoding='utf-8')

    def test_discovers_languages_outside_original_five(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as office:
            work = Path(work); office = Path(office)
            self._dict(office, 'it_IT')
            self._dict(office, 'pl_PL')
            catalog = DictionaryCatalog(work, extra_roots=[(office, 'ONLYOFFICE')])
            locales = {e.locale for e in catalog.entries()}
            self.assertIn('it_IT', locales)
            self.assertIn('pl_PL', locales)

    def test_ignores_hyphenation_dictionary(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as office:
            work = Path(work); office = Path(office)
            (office / 'hyph_nl_NL.dic').write_text('1\nwoord\n', encoding='utf-8')
            catalog = DictionaryCatalog(work, extra_roots=[(office, 'ONLYOFFICE')])
            self.assertFalse(any('hyph' in e.locale for e in catalog.entries()))

    def test_human_label(self):
        self.assertEqual(locale_label('nl_NL'), 'Nederlands - Nederland')
        self.assertEqual(locale_label('en_US'), 'Engels - VS')
        self.assertEqual(locale_label('it_IT'), 'Italiaans - Italië')

if __name__ == '__main__':
    unittest.main()

class DictionaryCatalogMutationTests(unittest.TestCase):
    def test_custom_dictionary_can_be_added_and_removed_without_touching_office(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as source:
            work = Path(work); source = Path(source)
            dic = source / 'sv_SE.dic'; aff = source / 'sv_SE.aff'
            dic.write_text('2\nhej\nord\n', encoding='utf-8'); aff.write_text('SET UTF-8\n', encoding='utf-8')
            catalog = DictionaryCatalog(work, extra_roots=[])
            entry = catalog.add_custom(dic)
            self.assertEqual(entry.source, 'Werkmap')
            self.assertTrue(entry.dic.exists())
            self.assertTrue(catalog.remove_custom('sv_SE'))
            self.assertIsNone(catalog.get('sv_SE'))

    def test_office_dictionary_is_read_only_from_quietwriter(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as office:
            work = Path(work); office = Path(office)
            folder = office / 'fr_FR'; folder.mkdir(parents=True, exist_ok=True)
            (folder / 'fr_FR.dic').write_text('1\nbonjour\n', encoding='utf-8')
            (folder / 'fr_FR.aff').write_text('SET UTF-8\n', encoding='utf-8')
            catalog = DictionaryCatalog(work, extra_roots=[(office, 'ONLYOFFICE')])
            entry = catalog.get('fr_FR')
            self.assertIsNotNone(entry)
            self.assertFalse(catalog.remove_custom('fr_FR'))
            self.assertTrue(entry.dic.exists())
