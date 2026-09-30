from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class MediaUiSource0200Tests(unittest.TestCase):
    def test_media_is_separate_module_and_insert_panel_owns_image_flow(self):
        for relative in ('quietwriter/media/models.py', 'quietwriter/media/store.py', 'quietwriter/media/markup.py', 'quietwriter/ui/image_insert_widget.py'):
            self.assertTrue((ROOT / relative).is_file(), relative)
        insert = (ROOT / 'quietwriter/ui/insert_panel.py').read_text(encoding='utf-8')
        self.assertIn('imageInsertRequested = Signal(str, str, str, str, str, bool)', insert)
        self.assertIn('ImageInsertWidget', insert)
        editor = (ROOT / 'quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
        self.assertIn('self.media_store = MediaStore(main.library)', editor)
        self.assertIn('self.insert.imageInsertRequested.connect(self._insert_image_from_panel)', editor)

    def test_editor_does_not_embed_binary_image_data_in_chapter_source(self):
        editor = (ROOT / 'quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
        self.assertIn('build_image_markdown(', editor)
        self.assertIn('width=width, align=align, wrap=wrap', editor)
        self.assertNotIn('data:image/', editor)
        self.assertNotIn('toBase64', editor)

    def test_epub_exporter_uses_snapshot_assets_not_live_media_store(self):
        exporter = (ROOT / 'quietwriter/exporting/epub_exporter.py').read_text(encoding='utf-8')
        self.assertIn("if asset.role != 'inline':", exporter)
        self.assertIn("files['EPUB/' + href] = asset.data", exporter)
        self.assertNotIn('MediaStore(', exporter)

    def test_book_local_cover_has_legacy_fallback(self):
        source = (ROOT / 'quietwriter/storage.py').read_text(encoding='utf-8')
        self.assertIn("book.path / 'assets' / 'cover'", source)
        self.assertIn('self.covers_dir', source)
        self.assertIn("book.metadata['cover_file'] = target.relative_to(book.path).as_posix()", source)


if __name__ == '__main__':
    unittest.main()
