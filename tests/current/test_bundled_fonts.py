import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FONT_ROOT = ROOT / 'resources' / 'fonts'


class BundledFontResourceTests(unittest.TestCase):
    def test_manifest_contains_curated_writing_fonts(self):
        data = json.loads((FONT_ROOT / 'font_manifest.json').read_text(encoding='utf-8'))
        families = [item['family'] for item in data['fonts']]
        self.assertEqual(families, ['Merriweather', 'Literata', 'Source Serif 4', 'EB Garamond'])

    def test_each_font_has_license_and_two_variable_faces(self):
        data = json.loads((FONT_ROOT / 'font_manifest.json').read_text(encoding='utf-8'))
        for item in data['fonts']:
            with self.subTest(font=item['family']):
                license_path = FONT_ROOT / item['slug'] / 'OFL.txt'
                self.assertTrue(license_path.is_file())
                license_text = license_path.read_text(encoding='utf-8')
                self.assertIn('SIL OPEN FONT LICENSE Version 1.1', license_text)
                self.assertEqual(len(item['files']), 2)
                for face in item['files']:
                    self.assertTrue(face['url'].startswith('https://raw.githubusercontent.com/google/fonts/'))
                    self.assertTrue(face['name'].endswith('.ttf'))

    def test_application_registers_fonts_before_window_creation(self):
        source = (ROOT / 'quietwriter' / 'app.py').read_text(encoding='utf-8')
        self.assertIn('register_bundled_fonts()', source)
        self.assertLess(source.index('register_bundled_fonts()'), source.index('MainWindow(settings,library,models)'))

    def test_about_page_exposes_version_author_and_font_licenses(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'about_page.py').read_text(encoding='utf-8')
        self.assertIn('__version__', source)
        self.assertIn('Lucas Bonsel', source)
        self.assertIn('bundled_fonts()', source)
        self.assertIn('Licentietekst tonen', source)


if __name__ == '__main__':
    unittest.main()
