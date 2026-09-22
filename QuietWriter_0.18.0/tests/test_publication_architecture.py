import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicationArchitectureTests(unittest.TestCase):
    def test_publication_layer_is_separate_from_planning(self):
        self.assertTrue((ROOT / 'quietwriter' / 'publication_models.py').exists())
        self.assertTrue((ROOT / 'quietwriter' / 'publication_storage.py').exists())
        self.assertTrue((ROOT / 'quietwriter' / 'ui' / 'publication' / 'publication_editor.py').exists())
        self.assertTrue((ROOT / 'quietwriter' / 'ui' / 'publication' / 'publication_setup.py').exists())

    def test_manuscript_tree_renders_front_body_and_back_matter_groups(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
        front = source.index("make_group('Voorwerk', 'front', editable=True)")
        body = source.index("make_group('Boek', 'body')", front)
        back = source.index("make_group('Achterwerk', 'back', editable=True)", body)
        self.assertLess(front, body)
        self.assertLess(body, back)
        self.assertIn("publication_btn = QPushButton('Publicatiestructuur')", source)

    def test_publication_has_three_content_kinds(self):
        source = (ROOT / 'quietwriter' / 'publication_models.py').read_text(encoding='utf-8')
        self.assertIn("'structured'", source)
        self.assertIn("'generated'", source)
        self.assertIn("'text'", source)

    def test_export_rendering_is_not_mixed_into_publication_model_yet(self):
        source = (ROOT / 'quietwriter' / 'publication_models.py').read_text(encoding='utf-8')
        self.assertNotIn('QPrinter', source)
        self.assertNotIn('EPUB', source)


if __name__ == '__main__':
    unittest.main()
