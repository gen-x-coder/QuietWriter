import tempfile
import unittest
from pathlib import Path

from quietwriter.publication_models import PublicationData, item_definition
from quietwriter.publication_storage import PublicationStore
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import Library


class PublicationStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.library = Library(Path(self.tmp.name))
        self.book = self.library.create_book('Publicatieboek')
        self.book.metadata['author'] = 'Auteur Test'
        self.library.save_manifest(self.book)
        self.library.track_book(self.book)
        self.store = PublicationStore(self.library)

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_model_is_non_destructive_and_uses_book_identity(self):
        data = self.store.load(self.book)
        self.assertEqual(data.enabled, [])
        self.assertEqual(data.title_page['title'], 'Publicatieboek')
        self.assertEqual(data.title_page['author'], 'Auteur Test')
        self.assertFalse((self.book.path / 'publication' / 'publication.json').exists())

    def test_structured_publication_roundtrip(self):
        data = self.store.load(self.book)
        data.enabled = ['title_page', 'copyright', 'contents', 'about_author']
        data.title_page['subtitle'] = 'Een test'
        data.copyright['year'] = '2027'
        data.contents['depth'] = 'headings'
        self.store.save(self.book, data)
        loaded = self.store.load(self.book)
        self.assertEqual(loaded.enabled, data.enabled)
        self.assertEqual(loaded.title_page['subtitle'], 'Een test')
        self.assertEqual(loaded.copyright['year'], '2027')
        self.assertEqual(loaded.contents['depth'], 'headings')

    def test_free_text_publication_item_is_plain_markdown(self):
        text = '# Voorwoord\n\nDit blijft **Markdown**.'
        self.store.save_text(self.book, 'foreword', text)
        self.assertEqual(self.store.load_text(self.book, 'foreword'), text)

    def test_non_text_item_cannot_be_written_as_free_text(self):
        self.assertEqual(item_definition('copyright')['kind'], 'structured')
        with self.assertRaises(ValueError):
            self.store.save_text(self.book, 'copyright', 'mag niet')

    def test_publication_files_are_revision_guarded(self):
        self.store.save_text(self.book, 'foreword', 'eerste versie')
        path = self.book.path / 'publication' / 'texts' / 'foreword.md'
        path.write_text('extern gewijzigd', encoding='utf-8')
        with self.assertRaises(ExternalModificationError):
            self.store.save_text(self.book, 'foreword', 'lokale versie')
        self.assertEqual(path.read_text(encoding='utf-8'), 'extern gewijzigd')

    def test_publication_files_are_part_of_book_revision(self):
        rev = self.library.capture_revision(self.book)
        self.assertIn('publication/publication.json', rev.files)
        self.assertIsNone(rev.files['publication/publication.json'])
        self.store.save_text(self.book, 'dedication', 'Voor jou.')
        rev = self.library.capture_revision(self.book)
        self.assertIn('publication/texts/dedication.md', rev.files)

    def test_history_restore_restores_publication_tree(self):
        data = self.store.load(self.book)
        data.enabled = ['foreword']
        self.store.save(self.book, data)
        self.store.save_text(self.book, 'foreword', 'oude versie')
        snapshot = self.library.create_version(self.book, kind='manual')
        self.store.save_text(self.book, 'foreword', 'nieuwe versie')
        restored = self.library.restore_version(self.book, snapshot['id'])
        self.library.track_book(restored)
        self.assertEqual(self.store.load_text(restored, 'foreword'), 'oude versie')

    def test_old_snapshot_without_publication_does_not_erase_new_publication_data(self):
        # Simulate a legacy snapshot from before publication/ existed.
        legacy = self.library.create_version(self.book, kind='manual')
        legacy_dir = Path(legacy['path'])
        publication_dir = legacy_dir / 'publication'
        if publication_dir.exists():
            import shutil
            shutil.rmtree(publication_dir)
        self.store.save_text(self.book, 'foreword', 'nieuwere publicatiedata')
        restored = self.library.restore_version(self.book, legacy['id'])
        self.library.track_book(restored)
        self.assertEqual(self.store.load_text(restored, 'foreword'), 'nieuwere publicatiedata')



if __name__ == '__main__':
    unittest.main()
