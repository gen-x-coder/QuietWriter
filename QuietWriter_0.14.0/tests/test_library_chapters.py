import tempfile
import unittest
from pathlib import Path

from quietwriter.storage import Library


class LibraryChapterTests(unittest.TestCase):
    def test_rename_duplicate_and_delete_preserve_content(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Library(Path(td)); book = lib.create_book('Testboek')
            chapter = book.sections[0].chapters[0]
            lib.save_chapter(book, chapter, 'Oorspronkelijke tekst')
            lib.rename_chapter(book, chapter.id, 'Nieuwe titel')
            self.assertEqual(chapter.title, 'Nieuwe titel')
            copy = lib.duplicate_chapter(book, chapter.id)
            self.assertIsNotNone(copy)
            self.assertEqual(lib.read_chapter(book, copy), 'Oorspronkelijke tekst')
            self.assertEqual(len(book.sections[0].chapters), 2)
            self.assertTrue(lib.delete_chapter(book, chapter.id))
            self.assertEqual(len(book.sections[0].chapters), 1)
            trash = list((lib.trash_dir / 'chapters' / book.id).glob('*.md'))
            self.assertEqual(len(trash), 1)
            self.assertEqual(trash[0].read_text(encoding='utf-8'), 'Oorspronkelijke tekst')

    def test_cannot_delete_last_chapter(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Library(Path(td)); book = lib.create_book('Testboek')
            chapter = book.sections[0].chapters[0]
            self.assertFalse(lib.delete_chapter(book, chapter.id))
            self.assertEqual(len(book.sections[0].chapters), 1)


    def test_library_uses_locate_chapter_name_for_three_tuple_lookup(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Library(Path(td)); book = lib.create_book('Testboek')
            chapter = book.sections[0].chapters[0]
            section, index, found = lib.locate_chapter(book, chapter.id)
            self.assertIs(section, book.sections[0])
            self.assertEqual(index, 0)
            self.assertIs(found, chapter)
            self.assertFalse(hasattr(lib, 'find_chapter'))


if __name__ == '__main__':
    unittest.main()
