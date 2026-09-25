from __future__ import annotations

import base64
import tempfile
import unittest
import zipfile
from pathlib import Path

from quietwriter.exporting.builder import build_export_document
from quietwriter.exporting.epub_exporter import export_epub
from quietwriter.exporting.preflight import run_preflight
from quietwriter.exporting.settings import default_export_settings
from quietwriter.media.markup import (
    build_image_markdown, count_words, find_image_references,
    insert_image_block, mask_image_paths, text_for_ai,
)
from quietwriter.media.store import MediaStore
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import Library


PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlZ3ioAAAAASUVORK5CYII='
)


class Media0200Tests(unittest.TestCase):
    def _image(self, root: Path, name='bron.png') -> Path:
        path = root / name
        path.write_bytes(PNG_1X1)
        return path

    def test_import_is_book_local_uuid_named_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Media')
            media = MediaStore(library)
            source = self._image(root)
            first = media.import_image(book, source)
            second = media.import_image(book, source)
            self.assertEqual(first.id, second.id)
            self.assertTrue((book.path / first.file).is_file())
            self.assertTrue(first.file.startswith('assets/images/'))
            self.assertNotIn(source.name, Path(first.file).name)
            self.assertTrue((book.path / 'assets/manifest.json').is_file())
            chapter = book.sections[0].chapters[0]
            self.assertTrue(media.reference_for_chapter(chapter, first).startswith('../assets/images/'))

    def test_image_markup_is_block_inserted_and_not_counted_as_prose(self):
        block = build_image_markdown('../assets/images/a.png', 'Een boom', 'In de mist')
        text, position = insert_image_block('Voor.\n\nNa.', 5, block)
        self.assertIn('![Een boom](../assets/images/a.png "In de mist")', text)
        self.assertEqual(count_words(text), 2)
        self.assertGreater(position, 5)
        refs = find_image_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].alt, 'Een boom')
        masked = mask_image_paths(text)
        self.assertNotIn('assets/images', masked)
        self.assertIn('Een boom', masked)
        self.assertIn('In de mist', masked)
        self.assertIn('[Afbeelding: Een boom — In de mist]', text_for_ai(text))

    def test_manifest_is_revision_guarded_but_binary_is_not_hashed_each_save(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Revision')
            media = MediaStore(library)
            asset = media.import_image(book, self._image(root))
            tracked = library.tracked_revision(book)
            self.assertIn('assets/manifest.json', tracked.files)
            self.assertNotIn(asset.file, tracked.files)
            manifest = book.path / 'assets/manifest.json'
            manifest.write_text(manifest.read_text(encoding='utf-8') + '\n', encoding='utf-8')
            with self.assertRaises(ExternalModificationError):
                library.save_manifest(book)

    def test_epub_embeds_managed_image_and_renders_figure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Plaatjesboek')
            book.metadata['author'] = 'Auteur'
            library.save_manifest(book)
            media = MediaStore(library)
            asset = media.import_image(book, self._image(root))
            chapter = book.sections[0].chapters[0]
            ref = media.reference_for_chapter(chapter, asset)
            library.save_chapter(book, chapter, f'Vooraf.\n\n{build_image_markdown(ref, "Een punt", "Testbeeld")}\n\nDaarna.')
            document = build_export_document(library, book)
            self.assertEqual(document.inline_asset_count, 1)
            self.assertFalse(document.missing_assets)
            settings = default_export_settings()
            settings['epub']['include_cover'] = False
            output = root / 'book.epub'
            export_epub(document, output, settings)
            with zipfile.ZipFile(output) as zf:
                image_name = f'EPUB/images/{Path(asset.file).name}'
                self.assertIn(image_name, zf.namelist())
                chapter_xml = zf.read('EPUB/text/chapter-001-001.xhtml').decode('utf-8')
                self.assertIn('<figure class="manuscript-image image-width-full image-align-center">', chapter_xml)
                self.assertIn('alt="Een punt"', chapter_xml)
                self.assertIn('<figcaption>Testbeeld</figcaption>', chapter_xml)
                self.assertIn(f'../images/{Path(asset.file).name}', chapter_xml)
                opf = zf.read('EPUB/package.opf').decode('utf-8')
                self.assertIn(Path(asset.file).name, opf)

    def test_missing_or_modified_asset_blocks_export_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Kapotte media')
            media = MediaStore(library)
            asset = media.import_image(book, self._image(root))
            chapter = book.sections[0].chapters[0]
            ref = media.reference_for_chapter(chapter, asset)
            library.save_chapter(book, chapter, build_image_markdown(ref, 'Alt'))
            (book.path / asset.file).write_bytes(b'changed')
            document = build_export_document(library, book)
            self.assertTrue(document.missing_assets)
            report = run_preflight(document, 'epub', default_export_settings())
            self.assertFalse(report.can_export)
            self.assertIn('missing_assets', [item.key for item in report.items])

    def test_markdown_with_images_is_blocked_until_companion_assets_step(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Markdown media')
            media = MediaStore(library)
            asset = media.import_image(book, self._image(root))
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, asset), 'Alt'))
            document = build_export_document(library, book)
            report = run_preflight(document, 'markdown', default_export_settings())
            self.assertFalse(report.can_export)
            self.assertIn('markdown_images_pending', [item.key for item in report.items])

    def test_new_cover_is_stored_inside_book_and_old_global_cover_still_resolves(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Cover')
            source = self._image(root, 'cover.png')
            target = library.set_cover(book, source)
            self.assertEqual(target.parent, book.path / 'assets' / 'cover')
            self.assertTrue(book.metadata['cover_file'].startswith('assets/cover/'))
            self.assertEqual(library.cover_path(book), target)

            # Backward compatibility for a book whose metadata still points to
            # the legacy global cover directory.
            target.unlink()
            book.metadata['cover_file'] = 'legacy.png'
            legacy = library.covers_dir / 'legacy.png'
            legacy.write_bytes(PNG_1X1)
            self.assertEqual(library.cover_path(book), legacy)

    def test_history_snapshot_keeps_media_and_restore_does_not_delete_newer_binary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            library = Library(root / 'workspace')
            book = library.create_book('Historie media')
            media = MediaStore(library)
            first = media.import_image(book, self._image(root, 'one.png'))
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, build_image_markdown(media.reference_for_chapter(chapter, first), 'Eerste'))
            version = library.create_version(book)
            self.assertTrue((version['path'] / first.file).is_file())

            # A second UUID asset created after the snapshot should survive an
            # old-version restore; media cleanup is explicit, never implicit.
            second_source = root / 'two.png'
            second_source.write_bytes(PNG_1X1 + b'\x00')
            # Same PNG payload plus trailing byte is still a valid PNG for our
            # lightweight header/dimension validation and has a different hash.
            second = media.import_image(book, second_source)
            self.assertNotEqual(first.id, second.id)
            restored = library.restore_version(book, version['id'])
            self.assertTrue((restored.path / first.file).is_file())
            self.assertTrue((restored.path / second.file).is_file())



if __name__ == '__main__':
    unittest.main()
