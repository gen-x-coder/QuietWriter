from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from quietwriter.exporting.builder import build_export_document
from quietwriter.exporting.epub_exporter import export_epub
from quietwriter.exporting.markup import inline_to_xhtml, markdown_to_xhtml
from quietwriter.exporting.markdown_exporter import export_markdown
from quietwriter.exporting.models import ExportChapter, ExportDocument, ExportItem, ExportSection
from quietwriter.exporting.preflight import run_preflight
from quietwriter.exporting.settings import default_export_settings
from quietwriter.publication_models import PublicationData
from quietwriter.publication_storage import PublicationStore
from quietwriter.storage import Library


class Exporting0191Tests(unittest.TestCase):
    def _document(self):
        return ExportDocument(
            id='12345678-1234-1234-1234-123456789abc',
            title='Testboek', author='Ada Auteur', language='nl', slug='testboek',
            metadata={'description': 'Test'},
            sections=(ExportSection('root', 'Manuscript', (
                ExportChapter('c1', 'Eerste hoofdstuk', 'Een **sterke** zin.\n\n***\n\nDaarna *verder*.'),
            )),),
            front_matter=(), back_matter=(), assets=(), cover_asset_id=None, epub_isbn='',
        )

    def test_inline_markup_is_rendered_and_escaped(self):
        self.assertEqual(inline_to_xhtml('**dik** & *schuin*'), '<strong>dik</strong> &amp; <em>schuin</em>')
        value = markdown_to_xhtml('Hallo <wereld>.\n\n***')
        self.assertIn('&lt;wereld&gt;', value)
        self.assertIn('class="scene-break"', value)

    def test_preflight_allows_missing_optional_cover_and_isbn(self):
        report = run_preflight(self._document(), 'epub', default_export_settings())
        self.assertTrue(report.can_export)
        self.assertIn('cover_missing', [x.key for x in report.items])
        self.assertIn('isbn', [x.key for x in report.items])

    def test_epub_container_is_structurally_valid(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'book.epub'
            settings = default_export_settings(); settings['epub']['include_cover'] = False
            export_epub(self._document(), path, settings)
            self.assertTrue(path.exists())
            with zipfile.ZipFile(path) as zf:
                infos = zf.infolist()
                self.assertEqual(infos[0].filename, 'mimetype')
                self.assertEqual(infos[0].compress_type, zipfile.ZIP_STORED)
                self.assertEqual(zf.read('mimetype'), b'application/epub+zip')
                names = set(zf.namelist())
                for required in ('META-INF/container.xml', 'EPUB/package.opf', 'EPUB/nav.xhtml', 'EPUB/styles/book.css', 'EPUB/text/chapter-001-001.xhtml'):
                    self.assertIn(required, names)
                    if required.endswith(('.xml', '.opf', '.xhtml')):
                        ET.fromstring(zf.read(required))
                package = zf.read('EPUB/package.opf').decode('utf-8')
                self.assertIn('version="3.0"', package)
                self.assertIn('Testboek', package)
                chapter = zf.read('EPUB/text/chapter-001-001.xhtml').decode('utf-8')
                self.assertIn('<strong>sterke</strong>', chapter)
                self.assertIn('scene-break', chapter)

    def test_builder_captures_saved_manuscript_and_publication(self):
        with tempfile.TemporaryDirectory() as td:
            library = Library(Path(td))
            book = library.create_book('Snapshotboek')
            book.metadata['author'] = 'Auteur'
            book.metadata['language'] = 'nl'
            library.save_manifest(book)
            chapter = book.sections[0].chapters[0]
            library.save_chapter(book, chapter, 'Eerste alinea.')
            publication = PublicationData.defaults_for_book(book)
            publication.enabled = ['title_page', 'contents', 'about_author']
            store = PublicationStore(library)
            store.save(book, publication)
            store.save_text(book, 'about_author', 'Over de schrijver.')
            doc = build_export_document(library, book)
            self.assertEqual(doc.title, 'Snapshotboek')
            self.assertEqual(doc.author, 'Auteur')
            self.assertEqual(doc.sections[0].chapters[0].markdown, 'Eerste alinea.')
            self.assertEqual([x.key for x in doc.front_matter], ['title_page', 'contents'])
            self.assertEqual([x.key for x in doc.back_matter], ['about_author'])
            self.assertEqual(doc.back_matter[0].text, 'Over de schrijver.')

    def test_generated_contents_uses_paths_relative_to_text_folder(self):
        document = self._document()
        document = ExportDocument(
            id=document.id, title=document.title, author=document.author, language=document.language, slug=document.slug,
            metadata=document.metadata, sections=document.sections, front_matter=(ExportItem('contents', 'generated'),),
            back_matter=(), assets=(), cover_asset_id=None, epub_isbn='',
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'contents.epub'
            settings = default_export_settings(); settings['epub']['include_cover'] = False
            export_epub(document, path, settings)
            with zipfile.ZipFile(path) as zf:
                toc = zf.read('EPUB/text/contents.xhtml').decode('utf-8')
                self.assertIn('href="chapter-001-001.xhtml"', toc)
                self.assertNotIn('href="text/chapter-001-001.xhtml"', toc)

    def test_public_markdown_uses_fixed_header_and_omits_redundant_h1(self):
        document = ExportDocument(
            id='99999999-9999-9999-9999-999999999999',
            title='Aan mijn lezers', author='Gemini', language='nl', slug='aan-mijn-lezers',
            metadata={
                'date': '2025-12-10T16:00',
                'description': 'Beschrijving',
                'meta': 'Meta tekst',
                'intro': 'Intro tekst',
                'author': 'Gemini',
                'tags': 'tag een, tag twee',
                'language': 'nl', 'published': 'No', 'synopsis': 'Niet voor publicatieheader',
            },
            sections=(ExportSection('root', 'Manuscript', (
                ExportChapter('c1', 'Aan mijn lezers', 'Eerste alinea.\n\nTweede alinea.'),
            )),),
            front_matter=(), back_matter=(), assets=(), cover_asset_id=None, epub_isbn='',
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'aan-mijn-lezers.md'
            # Obsolete 0.19.1 flags must no longer be able to disable the fixed format.
            export_markdown(document, path, {'markdown': {'include_frontmatter': False, 'include_section_markers': False}})
            text = path.read_text(encoding='utf-8')
        expected = (
            '---\n'
            'title: Aan mijn lezers\n'
            'date: 2025-12-10T16:00\n'
            'slug: aan-mijn-lezers\n'
            'description: Beschrijving\n'
            'meta: Meta tekst\n'
            'intro: Intro tekst\n'
            'author: Gemini\n'
            'tags: tag een, tag twee\n'
            '---\n'
        )
        self.assertTrue(text.startswith(expected))
        self.assertNotIn('# Aan mijn lezers', text)
        self.assertNotIn('language:', text)
        self.assertNotIn('published:', text)
        self.assertNotIn('synopsis:', text)
        self.assertTrue(text.endswith('Eerste alinea.\n\nTweede alinea.\n'))

    def test_public_markdown_keeps_structure_for_multi_chapter_books(self):
        document = ExportDocument(
            id='88888888-8888-8888-8888-888888888888', title='Boek', author='Auteur',
            language='nl', slug='boek', metadata={},
            sections=(
                ExportSection('s1', 'Deel een', (ExportChapter('c1', 'Begin', 'Een.'),)),
                ExportSection('s2', 'Deel twee', (ExportChapter('c2', 'Einde', 'Twee.'),)),
            ),
            front_matter=(), back_matter=(), assets=(), cover_asset_id=None, epub_isbn='',
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'boek.md'
            export_markdown(document, path, {})
            text = path.read_text(encoding='utf-8')
        self.assertIn('<!-- quietwriter-section: Deel een -->', text)
        self.assertIn('# Begin', text)
        self.assertIn('<!-- quietwriter-section: Deel twee -->', text)
        self.assertIn('# Einde', text)



if __name__ == '__main__':
    unittest.main()
