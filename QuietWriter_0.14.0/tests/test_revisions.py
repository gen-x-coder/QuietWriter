import os
import tempfile
import time
import unittest
from pathlib import Path

from quietwriter.revisions import BookRevision, ExternalModificationError, file_revision
from quietwriter.storage import Library


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.library = Library(Path(self.tmp.name))
        self.book = self.library.create_book('Revision test')
        self.library.track_book(self.book)
        self.chapter = self.book.sections[0].chapters[0]

    def tearDown(self):
        self.tmp.cleanup()

    def chapter_path(self):
        return self.book.path / self.chapter.file

    def test_happy_path_save_updates_tracked_revision(self):
        before = self.library.tracked_revision(self.book)
        self.library.save_chapter(self.book, self.chapter, 'Nieuwe tekst')
        after = self.library.tracked_revision(self.book)
        self.assertNotEqual(before, after)
        self.assertEqual(self.chapter_path().read_text(encoding='utf-8'), 'Nieuwe tekst')
        self.library.verify_book_unchanged(self.book)

    def test_external_chapter_change_blocks_save_and_preserves_disk(self):
        self.chapter_path().write_text('EXTERN', encoding='utf-8')
        with self.assertRaises(ExternalModificationError) as ctx:
            self.library.save_chapter(self.book, self.chapter, 'LOKAAL')
        self.assertIn(Path(self.chapter.file).as_posix(), ctx.exception.changed_files)
        self.assertEqual(self.chapter_path().read_text(encoding='utf-8'), 'EXTERN')

    def test_external_manifest_change_blocks_save(self):
        text = self.book.manifest_path.read_text(encoding='utf-8')
        self.book.manifest_path.write_text(text.replace('Revision test', 'Extern gewijzigd'), encoding='utf-8')
        with self.assertRaises(ExternalModificationError) as ctx:
            self.library.save_chapter(self.book, self.chapter, 'LOKAAL')
        self.assertIn('book.json', ctx.exception.changed_files)
        self.assertEqual(self.chapter_path().read_text(encoding='utf-8'), '')

    def test_mtime_change_with_identical_content_is_not_a_conflict(self):
        path = self.chapter_path()
        original = path.read_bytes()
        before = file_revision(path)
        time.sleep(0.01)
        path.write_bytes(original)
        os.utime(path, None)
        after = file_revision(path)
        self.assertEqual(before.size, after.size)
        self.assertEqual(before.sha256, after.sha256)
        self.assertNotEqual(before.mtime_ns, after.mtime_ns)
        self.library.verify_book_unchanged(self.book)

    def test_externally_added_chapter_file_is_detected(self):
        orphan = self.book.path / 'chapters' / 'extern.md'
        orphan.write_text('extern', encoding='utf-8')
        with self.assertRaises(ExternalModificationError) as ctx:
            self.library.verify_book_unchanged(self.book)
        self.assertIn('chapters/extern.md', ctx.exception.changed_files)

    def test_structural_write_checks_before_mutating_model(self):
        self.chapter_path().write_text('extern', encoding='utf-8')
        original_sections = [section.title for section in self.book.sections]
        with self.assertRaises(ExternalModificationError):
            self.library.add_section(self.book, 'Mag niet verschijnen')
        self.assertEqual([section.title for section in self.book.sections], original_sections)

    def test_local_recovery_snapshot_uses_in_memory_text(self):
        self.chapter_path().write_text('EXTERN OP SCHIJF', encoding='utf-8')
        row = self.library.create_version_from_state(
            self.book, {self.chapter.file: 'LOKALE ONOPGESLAGEN TEKST'}, kind='conflict_local'
        )
        snap = self.library.load_version(self.book, row['id'])
        snap_chapter = snap.sections[0].chapters[0]
        self.assertEqual(self.library.read_chapter(snap, snap_chapter), 'LOKALE ONOPGESLAGEN TEKST')
        self.assertEqual(row['kind'], 'conflict_local')

    def test_book_revision_detects_missing_key_even_when_value_would_be_none(self):
        left = BookRevision({'book.json': None})
        right = BookRevision({})
        self.assertEqual(left.changed_files(right), ['book.json'])


if __name__ == '__main__':
    unittest.main()
