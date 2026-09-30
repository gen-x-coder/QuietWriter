import tempfile
import unittest
from pathlib import Path

from quietwriter.storage import Library
from quietwriter.markdown_io import parse_markdown_book, insert_scene_break, remove_scene_break


class MarkdownRoundTripTests(unittest.TestCase):
    def test_import_export_round_trip_preserves_metadata_sections_chapters_and_scene_break(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'bron.md'
            source.write_text(
                '---\n'
                'title: Mijn verhaal\n'
                'slug: mijn-verhaal\n'
                'date: 2025-11-11T12:10\n'
                'description: Kort voor de homepage\n'
                'intro: Intro boven het verhaal\n'
                'meta: Meta tekst\n'
                'image: /images/mijn-verhaal.jpg\n'
                'image_alt: Beschrijving van de afbeelding\n'
                'author: Gemini\n'
                'tags: boerderij, familie\n'
                'published: No\n'
                'synopsis: Uitgebreidere synopsis\n'
                'customfield: behouden\n'
                '---\n\n'
                '<!-- quietwriter-section: Eerste deel -->\n\n'
                '# Begin\n\nTekst één.\n\n***\n\nNieuwe scène.\n\n'
                '<!-- quietwriter-section: Tweede deel -->\n\n'
                '# Einde\n\nSlottekst.\n',
                encoding='utf-8'
            )
            lib = Library(root / 'workspace')
            book = lib.import_markdown_book(source)
            self.assertEqual(book.title, 'Mijn verhaal')
            self.assertEqual(book.metadata['description'], 'Kort voor de homepage')
            self.assertEqual(book.metadata['extra']['customfield'], 'behouden')
            self.assertEqual([s.title for s in book.sections], ['Eerste deel', 'Tweede deel'])
            self.assertEqual([c.title for s in book.sections for c in s.chapters], ['Begin', 'Einde'])
            self.assertIn('***', lib.read_chapter(book, book.sections[0].chapters[0]))

            exported = root / 'uit.md'
            lib.export_markdown_book(book, exported, image_ref='/images/mijn-verhaal.jpg')
            parsed = parse_markdown_book(exported)
            self.assertEqual(parsed['metadata']['image'], '/images/mijn-verhaal.jpg')
            self.assertEqual(parsed['metadata']['image_alt'], 'Beschrijving van de afbeelding')
            self.assertEqual(parsed['metadata']['date'], '2025-11-11T12:10')
            self.assertEqual(parsed['metadata']['published'], 'No')
            self.assertEqual(parsed['metadata']['synopsis'], 'Uitgebreidere synopsis')
            self.assertEqual(parsed['metadata']['customfield'], 'behouden')
            self.assertEqual([x[0] for x in parsed['sections']], ['Eerste deel', 'Tweede deel'])
            self.assertEqual(parsed['sections'][0][1][0]['title'], 'Begin')
            self.assertIn('***', parsed['sections'][0][1][0]['text'])

    def test_export_emits_complete_canonical_frontmatter_even_when_empty(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lib = Library(root / 'workspace')
            book = lib.create_book('Een nieuw begin van ons')
            book.metadata.update({
                'description': 'Korte beschrijving',
                'intro': 'Intro tekst',
                'meta': 'Meta tekst',
                'author': 'Gemini',
                'tags': 'romantisch, teder',
                'image_alt': '',
                'synopsis': '',
                'published': 'No',
            })
            lib.save_manifest(book)
            exported = root / 'uit.md'
            lib.export_markdown_book(book, exported, image_ref='')
            text = exported.read_text(encoding='utf-8')
            expected = [
                'title:', 'date:', 'slug:', 'description:', 'intro:', 'meta:',
                'image:', 'image_alt:', 'author:', 'tags:', 'published:', 'synopsis:'
            ]
            for key in expected:
                self.assertIn('\n' + key, '\n' + text)
            self.assertIn('\nimage: \n', '\n' + text)
            self.assertIn('\nimage_alt: \n', '\n' + text)


    def test_single_chapter_without_heading_imports_without_loss(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'los.md'
            path.write_text('---\ntitle: Los verhaal\ntags: test\n---\n\nEen verhaal zonder hoofdstukkop.', encoding='utf-8')
            parsed = parse_markdown_book(path)
            self.assertEqual(parsed['sections'][0][1][0]['title'], 'Los verhaal')
            self.assertEqual(parsed['sections'][0][1][0]['text'], 'Een verhaal zonder hoofdstukkop.')


class SceneBreakTests(unittest.TestCase):
    def test_scene_break_is_placed_on_own_line(self):
        text = 'Eerste alinea.\n\nTweede alinea.'
        out, pos = insert_scene_break(text, len('Eerste alinea.'))
        self.assertEqual(out, 'Eerste alinea.\n\n***\n\nTweede alinea.')
        self.assertEqual(out[:pos], 'Eerste alinea.\n\n***\n\n')

    def test_scene_break_at_end(self):
        out, _ = insert_scene_break('Einde.', 6)
        self.assertEqual(out, 'Einde.\n\n***')

    def test_remove_scene_break_restores_normal_paragraph_gap(self):
        text = 'Eerste alinea.\n\n***\n\nTweede alinea.'
        out, pos = remove_scene_break(text, text.index('***') + 1)
        self.assertEqual(out, 'Eerste alinea.\n\nTweede alinea.')
        self.assertEqual(pos, len('Eerste alinea.\n\n'))

    def test_remove_scene_break_ignores_normal_text(self):
        text = 'Eerste alinea.\n\nTweede alinea.'
        out, pos = remove_scene_break(text, 3)
        self.assertEqual(out, text)
        self.assertEqual(pos, 3)


if __name__ == '__main__':
    unittest.main()
