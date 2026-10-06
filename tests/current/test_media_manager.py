from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from quietwriter.media.manager import MediaCleanupError, MediaManager
from quietwriter.media.markup import build_image_markdown
from quietwriter.media.store import MediaStore
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import Library


PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlZ3ioAAAAASUVORK5CYII='
)


class MediaManager0270Tests(unittest.TestCase):
    def _image(self, root: Path, name: str, suffix: bytes = b'') -> Path:
        path = root / name
        path.write_bytes(PNG_1X1 + suffix)
        return path

    def _book(self, root: Path):
        library = Library(root / 'workspace')
        book = library.create_book('Media manager')
        return library, book, MediaStore(library), MediaManager(library)

    def test_inventory_distinguishes_used_unused_missing_modified_and_untracked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            used = media.import_image(book, self._image(root, 'used.png'))
            unused = media.import_image(book, self._image(root, 'unused.png', b'1'))
            missing = media.import_image(book, self._image(root, 'missing.png', b'2'))
            modified = media.import_image(book, self._image(root, 'modified.png', b'3'))

            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, used), 'Used'))
            (book.path / missing.file).unlink()
            (book.path / modified.file).write_bytes(PNG_1X1 + b'changed')
            orphan = book.path / 'assets/images/orphan.png'
            orphan.write_bytes(PNG_1X1)

            inventory = manager.inspect(book, include_history=False)
            by_id = {item.id: item for item in inventory.items}
            self.assertEqual(by_id[used.id].status, 'used')
            self.assertEqual(by_id[used.id].reference_count, 1)
            self.assertEqual(by_id[unused.id].status, 'unused')
            self.assertEqual(by_id[missing.id].status, 'missing')
            self.assertEqual(by_id[modified.id].status, 'modified')
            self.assertEqual([row.file for row in inventory.untracked_files], ['assets/images/orphan.png'])
            self.assertEqual(inventory.used_count, 1)
            self.assertEqual(inventory.unused_count, 3)
            self.assertEqual(inventory.problem_count, 3)  # missing + modified + untracked

    def test_inventory_scans_all_book_markdown_not_only_chapters(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'publication.png'))
            publication = book.path / 'publication/texts'
            publication.mkdir(parents=True, exist_ok=True)
            source = publication / 'afterword.md'
            source.write_text(build_image_markdown('../../' + asset.file, 'Publicatie'), encoding='utf-8')
            library.track_book(book)

            inventory = manager.inspect(book, include_history=False)
            row = next(item for item in inventory.items if item.id == asset.id)
            self.assertEqual(row.reference_count, 1)
            self.assertEqual(row.usages[0].source_file, 'publication/texts/afterword.md')

    def test_untracked_file_that_is_referenced_is_reported_but_never_auto_deleted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, _media, manager = self._book(root)
            orphan = book.path / 'assets/images/manual.png'
            orphan.write_bytes(PNG_1X1)
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown('../assets/images/manual.png', 'Handmatig'))

            inventory = manager.inspect(book, include_history=False)
            self.assertEqual(len(inventory.untracked_files), 1)
            self.assertEqual(inventory.untracked_files[0].reference_count, 1)
            result = manager.cleanup_unused(book)
            self.assertFalse(result.removed_ids)
            self.assertTrue(orphan.is_file())

    def test_cleanup_removes_only_unused_assets_and_creates_one_recoverable_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            used = media.import_image(book, self._image(root, 'used.png'))
            unused = media.import_image(book, self._image(root, 'unused.png', b'1'))
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, used), 'Used'))

            result = manager.cleanup_unused(book)
            self.assertEqual(result.removed_ids, (unused.id,))
            self.assertTrue(result.checkpoint_version_id)
            self.assertTrue((book.path / used.file).is_file())
            self.assertFalse((book.path / unused.file).exists())
            self.assertEqual({a.id for a in media.assets(book)}, {used.id})

            versions = {row['id']: row for row in library.list_versions(book)}
            checkpoint = versions[result.checkpoint_version_id]
            self.assertEqual(checkpoint['kind'], 'media_cleanup')
            self.assertTrue((checkpoint['path'] / unused.file).is_file())

            restored = library.restore_version(book, result.checkpoint_version_id)
            self.assertTrue((restored.path / unused.file).is_file())
            self.assertIn(unused.id, {a.id for a in media.assets(restored)})

    def test_cleanup_can_target_selected_unused_asset(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _library, book, media, manager = self._book(root)
            a = media.import_image(book, self._image(root, 'a.png'))
            b = media.import_image(book, self._image(root, 'b.png', b'2'))
            result = manager.cleanup_unused(book, [a.id])
            self.assertEqual(result.removed_ids, (a.id,))
            self.assertEqual({row.id for row in media.assets(book)}, {b.id})
            self.assertTrue((book.path / b.file).is_file())

    def test_history_reference_is_safe_when_snapshot_has_own_binary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'history.png'))
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, asset), 'Historie'))
            version = library.create_version(book)
            library.save_chapter(book, chapter, 'Nu zonder afbeelding.')

            inventory = manager.inspect(book)
            row = next(item for item in inventory.items if item.id == asset.id)
            self.assertTrue(row.unused)
            self.assertEqual(row.history_reference_count, 1)
            self.assertEqual(row.history_versions, (version['id'],))
            self.assertTrue(row.history_safe)
            result = manager.cleanup_unused(book)
            self.assertEqual(result.removed_ids, (asset.id,))
            self.assertTrue((version['path'] / asset.file).is_file())

    def test_cleanup_refuses_when_history_references_asset_without_own_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'unsafe.png'))
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, asset), 'Historie'))
            version = library.create_version(book)
            (version['path'] / asset.file).unlink()
            library.save_chapter(book, chapter, 'Nu zonder afbeelding.')

            row = next(item for item in manager.inspect(book).items if item.id == asset.id)
            self.assertFalse(row.history_safe)
            with self.assertRaises(MediaCleanupError):
                manager.cleanup_unused(book)
            self.assertTrue((book.path / asset.file).is_file())
            self.assertIn(asset.id, {a.id for a in media.assets(book)})

    def test_history_guard_is_conservative_when_snapshot_markdown_is_unreadable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'legacy-unsafe.png'))
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, asset), 'Historie'))
            version = library.create_version(book)
            (version['path'] / asset.file).unlink()
            # Make the historical Markdown unreadable so reference parsing cannot
            # prove usage. The historical manifest still names the missing asset.
            (version['path'] / chapter.file).write_bytes(b'\xff\xfe\xff')
            library.save_chapter(book, chapter, 'Nu zonder afbeelding.')

            row = next(item for item in manager.inspect(book).items if item.id == asset.id)
            self.assertFalse(row.history_safe)
            with self.assertRaises(MediaCleanupError):
                manager.cleanup_unused(book)
            self.assertTrue((book.path / asset.file).is_file())

    def test_cleanup_is_blocked_if_any_markdown_source_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'unused.png'))
            bad = book.path / 'planning/bad.md'
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_bytes(b'\xff\xfe\xff')
            library.track_book(book)

            inventory = manager.inspect(book)
            self.assertTrue(inventory.source_errors)
            with self.assertRaises(MediaCleanupError):
                manager.cleanup_unused(book)
            self.assertTrue((book.path / asset.file).is_file())

    def test_cleanup_respects_revision_guard_before_any_checkpoint_or_delete(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'unused.png'))
            manifest = book.path / 'assets/manifest.json'
            manifest.write_text(manifest.read_text(encoding='utf-8') + '\n', encoding='utf-8')
            before = list((library.archive_dir / book.id).glob('*')) if (library.archive_dir / book.id).exists() else []
            with self.assertRaises(ExternalModificationError):
                manager.cleanup_unused(book)
            after = list((library.archive_dir / book.id).glob('*')) if (library.archive_dir / book.id).exists() else []
            self.assertEqual(before, after)
            self.assertTrue((book.path / asset.file).is_file())


    def test_trashed_chapter_reference_keeps_asset_in_use_until_trash_is_deleted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'trash-only.png'))
            first = book.sections[0].chapters[0]
            second = library.add_chapter(book, book.sections[0], 'Tijdelijk hoofdstuk')
            library.save_chapter(book, second, build_image_markdown(media.reference_for_chapter(second, asset), 'Prullenbak'))
            self.assertTrue(library.delete_chapter(book, second.id))

            row = next(item for item in manager.inspect(book).items if item.id == asset.id)
            self.assertEqual(row.status, 'used')
            self.assertEqual(row.reference_count, 1)
            self.assertFalse(row.can_cleanup)
            self.assertTrue(row.usages[0].source_file.startswith('Prullenbak:'))
            result = manager.cleanup_unused(book)
            self.assertFalse(result.removed_ids)
            self.assertTrue((book.path / asset.file).is_file())

            trashed = next(r for r in library.list_trashed_chapters() if r['chapter_id'] == second.id)
            restored = library.restore_trashed_chapter(trashed['path'], book)
            self.assertIn(asset.id, {a.id for a in media.assets(book)})
            self.assertTrue((book.path / asset.file).is_file())
            self.assertIn('assets/images/', library.read_chapter(book, restored))

    def test_unreadable_trashed_chapter_blocks_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            asset = media.import_image(book, self._image(root, 'unused.png'))
            second = library.add_chapter(book, book.sections[0], 'Kapotte prullenbak')
            self.assertTrue(library.delete_chapter(book, second.id))
            trashed = next(r for r in library.list_trashed_chapters() if r['chapter_id'] == second.id)
            Path(trashed['path']).write_bytes(b'\xff\xfe\xff')

            inventory = manager.inspect(book)
            self.assertTrue(any('Prullenbak:' in error for error in inventory.source_errors))
            with self.assertRaises(MediaCleanupError):
                manager.cleanup_unused(book)
            self.assertTrue((book.path / asset.file).is_file())

    def test_explicit_cleanable_subset_does_not_get_blocked_by_other_unsafe_unused_asset(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, media, manager = self._book(root)
            safe = media.import_image(book, self._image(root, 'safe.png'))
            unsafe = media.import_image(book, self._image(root, 'unsafe.png', b'2'))
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, unsafe), 'Historie'))
            version = library.create_version(book)
            (version['path'] / unsafe.file).unlink()
            library.save_chapter(book, chapter, 'Geen afbeeldingen meer.')

            inventory = manager.inspect(book)
            by_id = {item.id: item for item in inventory.items}
            self.assertTrue(by_id[safe.id].can_cleanup)
            self.assertFalse(by_id[unsafe.id].can_cleanup)
            result = manager.cleanup_unused(book, asset_ids=[safe.id])
            self.assertEqual(result.removed_ids, (safe.id,))
            self.assertFalse((book.path / safe.file).exists())
            self.assertTrue((book.path / unsafe.file).is_file())

    def test_cover_is_reported_but_not_part_of_inline_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library, book, _media, manager = self._book(root)
            cover = self._image(root, 'cover.png')
            target = library.set_cover(book, cover)
            inventory = manager.inspect(book, include_history=False)
            self.assertEqual(inventory.cover_file, target.relative_to(book.path).as_posix())
            self.assertGreater(inventory.cover_size, 0)
            manager.cleanup_unused(book)
            self.assertTrue(target.is_file())


if __name__ == '__main__':
    unittest.main()
