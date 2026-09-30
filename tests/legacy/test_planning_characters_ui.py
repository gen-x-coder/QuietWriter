import os
import unittest

try:
    from PySide6.QtWidgets import QApplication
    from quietwriter.planning_models import Character
    from quietwriter.ui.planning.characters_page import CharactersPage
    HAS_QT = True
except ImportError:
    HAS_QT = False


class _Store:
    def __init__(self, characters):
        self.characters = characters

    def load_characters(self, _book):
        return list(self.characters)


class _Owner:
    def __init__(self, characters):
        self.book = object()
        self.store = _Store(characters)
        self.persist_calls = []
        self.source_errors = {}

    def persist_characters(self, characters):
        self.persist_calls.append(list(characters))
        return True

    def set_source_error(self, kind, error):
        self.source_errors[kind] = error

    def clear_source_error(self, kind):
        self.source_errors.pop(kind, None)


@unittest.skipUnless(HAS_QT, 'PySide6 is not installed')
class CharacterPageRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def test_load_does_not_auto_open_first_character(self):
        page = CharactersPage(_Owner([Character(name='Jan'), Character(name='Kees')]))
        page.load()
        self.assertEqual(page.list.currentRow(), -1)
        self.assertTrue(page.detail.isHidden())

    def test_new_character_is_unsaved_draft_until_save(self):
        owner = _Owner([])
        page = CharactersPage(owner)
        page.load()
        page.add_character()
        self.assertEqual(owner.persist_calls, [])
        self.assertFalse(page.detail.isHidden())
        self.assertEqual(page.detail.name.text(), '')

        page.detail.name.setText('Kees')
        page.detail._save()
        self.assertEqual(len(owner.persist_calls), 1)
        self.assertEqual(owner.persist_calls[0][0].name, 'Kees')
        self.assertTrue(page.detail.isHidden())
        self.assertEqual(page.list.currentRow(), -1)

    def test_saving_existing_character_closes_detail(self):
        owner = _Owner([Character(name='Jan')])
        page = CharactersPage(owner)
        page.load()
        page.list.setCurrentRow(0)
        self.assertFalse(page.detail.isHidden())
        page.detail.role.setText('Hoofdpersoon')
        page.detail._save()
        self.assertTrue(page.detail.isHidden())
        self.assertEqual(page.list.currentRow(), -1)
        self.assertEqual(owner.persist_calls[-1][0].role, 'Hoofdpersoon')


if __name__ == '__main__':
    unittest.main()
