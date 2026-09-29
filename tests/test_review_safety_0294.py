import tempfile
import unittest
from pathlib import Path

from quietwriter.storage import Library, CorruptSourceError


class ReviewSafety0294Tests(unittest.TestCase):
    def test_duplicate_corrupt_chapter_is_refused_without_writes(self):
        with tempfile.TemporaryDirectory() as td:
            lib = Library(Path(td))
            book = lib.create_book('Test')
            chapter = book.sections[0].chapters[0]
            path = book.path / chapter.file
            path.write_bytes(b'goed\xffkapot')
            before = {p.relative_to(book.path).as_posix(): p.read_bytes() for p in book.path.rglob('*') if p.is_file()}
            with self.assertRaises(CorruptSourceError):
                lib.duplicate_chapter(book, chapter.id)
            after = {p.relative_to(book.path).as_posix(): p.read_bytes() for p in book.path.rglob('*') if p.is_file()}
            self.assertEqual(before, after)
