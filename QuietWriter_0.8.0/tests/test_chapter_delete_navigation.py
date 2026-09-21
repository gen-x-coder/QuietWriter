import tempfile
import unittest
from pathlib import Path

from quietwriter.storage import Library, Section


class ChapterDeleteNavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.library = Library(Path(self.tmp.name))
        self.book = self.library.create_book('Test')
        root = self.book.sections[0]
        root.chapters[0].title = 'Eerste'
        self.second = self.library.add_chapter(self.book, root, 'Tweede')
        self.third = self.library.add_chapter(self.book, root, 'Derde')
        self.library.save_manifest(self.book)

    def tearDown(self):
        self.tmp.cleanup()

    def test_delete_middle_prefers_previous_chapter(self):
        neighbour = self.library.adjacent_chapter_for_delete(self.book, self.second.id)
        self.assertEqual(neighbour.title, 'Eerste')

    def test_delete_first_uses_following_chapter(self):
        first = self.book.sections[0].chapters[0]
        neighbour = self.library.adjacent_chapter_for_delete(self.book, first.id)
        self.assertEqual(neighbour.title, 'Tweede')

    def test_delete_across_sections_prefers_previous_in_manuscript_order(self):
        sec2 = self.library.add_section(self.book, 'Sectie 2')
        fourth = self.library.add_chapter(self.book, sec2, 'Vierde')
        neighbour = self.library.adjacent_chapter_for_delete(self.book, fourth.id)
        self.assertEqual(neighbour.title, 'Derde')

    def test_last_remaining_chapter_has_no_delete_neighbour(self):
        only = self.library.create_book('Solo')
        chapter = only.sections[0].chapters[0]
        self.assertIsNone(self.library.adjacent_chapter_for_delete(only, chapter.id))


if __name__ == '__main__':
    unittest.main()
