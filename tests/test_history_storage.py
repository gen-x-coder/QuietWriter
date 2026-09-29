import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quietwriter.storage import Library, StorageWriteError, _safe_atomic_write_text
import quietwriter.storage as storage


class SafeWriteTests(unittest.TestCase):
    def test_replace_permission_error_is_retried(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'book.json'
            path.write_text('old', encoding='utf-8')
            real_replace = storage.os.replace
            calls = {'n': 0}

            def flaky(src, dst):
                calls['n'] += 1
                if calls['n'] <= 2:
                    raise PermissionError(5, 'sharing violation')
                return real_replace(src, dst)

            with patch.object(storage.os, 'replace', side_effect=flaky):
                _safe_atomic_write_text(path, 'new', replace_retries=5)
            self.assertEqual(path.read_text(encoding='utf-8'), 'new')
            self.assertGreaterEqual(calls['n'], 3)

    def test_persistent_replace_lock_preserves_original_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'book.json'
            path.write_text('old', encoding='utf-8')
            with patch.object(storage.os, 'replace', side_effect=PermissionError(5, 'blocked')):
                with self.assertRaises(StorageWriteError):
                    _safe_atomic_write_text(path, 'fallback', replace_retries=1)
            self.assertEqual(path.read_bytes(), b'old')
            self.assertFalse(list(Path(td).glob('*.tmp')))


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lib = Library(Path(self.tmp.name))
        self.book = self.lib.create_book('Testboek')
        self.chapter = self.book.sections[0].chapters[0]
        self.lib.save_chapter(self.book, self.chapter, 'eerste versie')

    def tearDown(self):
        self.tmp.cleanup()

    def test_manual_version_and_star(self):
        row = self.lib.create_version(self.book)
        versions = self.lib.list_versions(self.book)
        self.assertTrue(any(v['id'] == row['id'] for v in versions))
        self.lib.set_version_starred(self.book, row['id'], True)
        versions = self.lib.list_versions(self.book)
        hit = next(v for v in versions if v['id'] == row['id'])
        self.assertTrue(hit['starred'])

    def test_restore_preserves_current_as_new_history_version(self):
        old = self.lib.create_version(self.book)
        self.lib.save_chapter(self.book, self.chapter, 'gewijzigde versie')
        before = {v['id'] for v in self.lib.list_versions(self.book)}
        restored = self.lib.restore_version(self.book, old['id'])
        restored_chapter = restored.sections[0].chapters[0]
        self.assertEqual(self.lib.read_chapter(restored, restored_chapter), 'eerste versie')
        after = self.lib.list_versions(restored)
        new_rows = [v for v in after if v['id'] not in before]
        self.assertTrue(any(v['kind'] == 'pre_restore' for v in new_rows))
        # The preserved version must contain the text that existed just before restore.
        pre = next(v for v in new_rows if v['kind'] == 'pre_restore')
        pre_book = self.lib.load_version(restored, pre['id'])
        self.assertEqual(self.lib.read_chapter(pre_book, pre_book.sections[0].chapters[0]), 'gewijzigde versie')

    def test_version_is_complete_book_snapshot(self):
        second = self.lib.add_section(self.book, 'Deel 2')
        c2 = self.lib.add_chapter(self.book, second, 'Hoofdstuk 2')
        self.lib.save_chapter(self.book, c2, 'tweede hoofdstuk')
        row = self.lib.create_version(self.book)
        snap = self.lib.load_version(self.book, row['id'])
        self.assertEqual(len(snap.sections), 2)
        self.assertEqual(sum(len(s.chapters) for s in snap.sections), 2)
        self.assertEqual(self.lib.read_chapter(snap, snap.sections[1].chapters[0]), 'tweede hoofdstuk')


if __name__ == '__main__':
    unittest.main()
