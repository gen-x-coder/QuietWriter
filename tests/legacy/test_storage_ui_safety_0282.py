import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

from quietwriter.storage import Library, StorageWriteError, _safe_atomic_write_bytes
from quietwriter.migrations import MigrationError, validate_manifest_structure

class StorageSafety0282Tests(unittest.TestCase):
    def test_metadata_must_be_object_or_null(self):
        base={'format':2,'id':'b','title':'B','sections':[]}
        for bad in ([], 'abc', 3):
            data=dict(base, metadata=bad)
            with self.assertRaises(MigrationError): validate_manifest_structure(data)
        validate_manifest_structure(dict(base, metadata=None))
        validate_manifest_structure(dict(base, metadata={'x':1}))

    def test_atomic_text_exposes_one_domain_write_error_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as td:
            lib=Library(Path(td)); book=lib.create_book('B'); chapter=book.sections[0].chapters[0]
            target=book.path/chapter.file; target.write_text('oud', encoding='utf-8'); lib.track_book(book)
            real_replace=__import__('os').replace
            def locked(src,dst):
                if Path(dst)==target: raise PermissionError('locked')
                return real_replace(src,dst)
            with patch('quietwriter.storage.os.replace', side_effect=locked):
                with self.assertRaises(StorageWriteError) as cm: lib.save_chapter(book, chapter, 'nieuw')
            self.assertEqual(cm.exception.path, target)
            self.assertEqual(target.read_text(encoding='utf-8'), 'oud')

    def test_atomic_bytes_retries_transient_lock(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'x.bin'; target.write_bytes(b'old')
            real_replace=__import__('os').replace; calls={'n':0}
            def flaky(src,dst):
                calls['n']+=1
                if calls['n']<3: raise PermissionError('brief lock')
                return real_replace(src,dst)
            with patch('quietwriter.storage.os.replace', side_effect=flaky), patch('quietwriter.storage.time.sleep'):
                _safe_atomic_write_bytes(target,b'new')
            self.assertEqual(target.read_bytes(),b'new'); self.assertEqual(calls['n'],3)

    def test_editor_source_handles_storage_error_and_future_format(self):
        src=Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
        self.assertIn('except StorageWriteError as exc:', src)
        self.assertIn('except FutureBookFormatError:', src)
        self.assertIn('force_return_to_bookshelf', src)

    def test_close_event_has_unexpected_save_fail_safe(self):
        src=Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("QMessageBox.critical(self, 'Afsluiten gestopt'", src)
        self.assertIn('event.ignore()', src)
