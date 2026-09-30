import tempfile
import unittest
from pathlib import Path

from quietwriter.storage import Library


class CorruptTextSafetyTests(unittest.TestCase):
    def test_invalid_utf8_chapter_is_not_silently_treated_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Library(Path(tmp))
            book = lib.create_book('Corrupt')
            chapter = book.sections[0].chapters[0]
            path = book.path / chapter.file
            path.write_bytes(b'goed\xfffout')
            with self.assertRaises(UnicodeDecodeError):
                lib.read_chapter(book, chapter)
            self.assertEqual(path.read_bytes(), b'goed\xfffout')

    def test_0292_ui_contains_readonly_corruption_guards(self):
        root = Path(__file__).resolve().parents[2] / 'quietwriter' / 'ui'
        editor = (root / 'editor_page.py').read_text(encoding='utf-8')
        integrity = (root / 'integrity_page.py').read_text(encoding='utf-8')
        notes = (root / 'planning' / 'notes_page.py').read_text(encoding='utf-8')
        profile = (root / 'book_profile_page.py').read_text(encoding='utf-8')
        memory = (root / 'book_memory_page.py').read_text(encoding='utf-8')
        self.assertIn('except UnicodeDecodeError:', editor)
        self.assertIn('Beschadigd · alleen-lezen', editor)
        self.assertIn('except Exception:', integrity)
        self.assertIn('except UnicodeDecodeError:', notes)
        self.assertIn('except UnicodeDecodeError:', profile)
        self.assertIn('except UnicodeDecodeError:', memory)


if __name__ == '__main__':
    unittest.main()
