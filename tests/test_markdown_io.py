import tempfile
import unittest
from pathlib import Path

from quietwriter.storage import Library
from quietwriter.markdown_io import parse_markdown_book, insert_scene_break


class MarkdownRoundTripTests(unittest.TestCase):
    def test_import_export_round_trip_preserves_metadata_sections_chapters_and_scene_break(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'bron.md'
            source.write_text(
                '---\n'
                'title: Mijn verhaal\n'
                'slug: mijn-verhaal\n'
                'description: Kort voor de homepage\n'
                'intro: Intro boven het verhaal\n'
                'tags: boerderij, familie\n'
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
            self.assertEqual(parsed['metadata']['customfield'], 'behouden')
            self.assertEqual([x[0] for x in parsed['sections']], ['Eerste deel', 'Tweede deel'])
            self.assertEqual(parsed['sections'][0][1][0]['title'], 'Begin')
            self.assertIn('***', parsed['sections'][0][1][0]['text'])

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


if __name__ == '__main__':
    unittest.main()
