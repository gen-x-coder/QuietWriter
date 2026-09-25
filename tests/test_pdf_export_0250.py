from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from quietwriter.exporting.models import ExportAsset, ExportChapter, ExportDocument, ExportItem, ExportSection
from quietwriter.exporting.pdf_exporter import build_pdf_html, pdf_float_caption_safe
from quietwriter.exporting.preflight import run_preflight
from quietwriter.exporting.settings import ExportSettingsStore, default_export_settings


class _Book:
    def __init__(self, path: Path):
        self.path = path


class PdfExport0250Tests(unittest.TestCase):
    def _doc(self, markdown: str) -> ExportDocument:
        return ExportDocument(
            id='12345678-1234-1234-1234-123456789abc',
            title='PDF boek', author='Ada Auteur', language='nl', slug='pdf-boek', metadata={},
            sections=(ExportSection('root', 'Manuscript', (
                ExportChapter('c1', 'Hoofdstuk een', markdown),
            )),),
            front_matter=(ExportItem('title_page', 'structured', {'title': 'PDF boek', 'author': 'Ada Auteur'}),),
            back_matter=(),
            assets=(ExportAsset('inline-1', 'beeld.png', 'image/png', b'not-decoded-in-pure-test', 'inline'),),
            cover_asset_id=None, epub_isbn='',
        )

    def test_pdf_defaults_are_part_of_per_book_export_settings(self):
        settings = default_export_settings()
        self.assertEqual(settings['pdf']['paper_size'], 'A5')
        self.assertEqual(settings['pdf']['margin_preset'], 'standard')
        self.assertTrue(settings['pdf']['page_numbers'])
        self.assertTrue(settings['pdf']['running_header'])

    def test_pdf_format_and_preferences_roundtrip_in_settings_store(self):
        with tempfile.TemporaryDirectory() as td:
            book = _Book(Path(td))
            store = ExportSettingsStore()
            settings = default_export_settings()
            settings['format'] = 'pdf'
            settings['pdf'].update({'paper_size': 'A4', 'margin_preset': 'wide', 'template': 'literary'})
            store.save(book, settings)
            loaded = store.load(book)
        self.assertEqual(loaded['format'], 'pdf')
        self.assertEqual(loaded['pdf']['paper_size'], 'A4')
        self.assertEqual(loaded['pdf']['margin_preset'], 'wide')
        self.assertEqual(loaded['pdf']['template'], 'literary')

    def test_short_caption_can_float_but_long_caption_falls_back(self):
        self.assertTrue(pdf_float_caption_safe('Kort onderschrift'))
        self.assertFalse(pdf_float_caption_safe(
            'Dit is bewust een heel lang onderschrift dat over meerdere regels zal lopen en daarom niet veilig naast lopende tekst hoort te zweven.'
        ))

    def test_pdf_html_uses_float_for_short_caption_and_block_for_long_caption(self):
        short = '![Alt](../assets/images/beeld.png "Kort") <!-- qw:image width=medium align=right wrap=true -->'
        html_text, first_is_title = build_pdf_html(self._doc(short), default_export_settings(), 600)
        self.assertTrue(first_is_title)
        self.assertIn('float:right', html_text)
        self.assertIn('qw-asset://inline-1', html_text)
        self.assertIn('page-break-before: always', html_text)

        long_caption = 'Dit is bewust een heel lang onderschrift dat over meerdere regels loopt en bij PDF veilig zonder tekstomloop moet worden geplaatst.'
        long_md = f'![Alt](../assets/images/beeld.png "{long_caption}") <!-- qw:image width=medium align=right wrap=true -->'
        long_html, _ = build_pdf_html(self._doc(long_md), default_export_settings(), 600)
        self.assertNotIn('float:right', long_html)
        self.assertIn('margin:7px 0 12px auto', long_html)

    def test_preflight_warns_about_long_caption_wrap_fallback(self):
        caption = 'Dit is een lang onderschrift dat bewust ruim boven de veilige floatgrens uitkomt zodat de PDF-renderer naar een gewoon afbeeldingsblok terugvalt.'
        md = f'![Alt](../assets/images/beeld.png "{caption}") <!-- qw:image width=small align=left wrap=true -->'
        report = run_preflight(self._doc(md), 'pdf', default_export_settings())
        self.assertTrue(report.can_export)
        warnings = [item for item in report.items if item.key == 'pdf_wrap_fallback']
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].level, 'warning')
        self.assertEqual(warnings[0].value, '1')

    def test_pdf_exporter_keeps_qt_imports_runtime_local(self):
        source = (Path(__file__).resolve().parents[1] / 'quietwriter/exporting/pdf_exporter.py').read_text(encoding='utf-8')
        before_function = source.split('def export_pdf', 1)[0]
        self.assertNotIn('from PySide6', before_function)
        self.assertIn('QPdfWriter', source)
        self.assertIn('QTextDocument', source)
        self.assertIn('QPainter', source)

    def test_export_page_exposes_pdf_as_real_format(self):
        source = (Path(__file__).resolve().parents[1] / 'quietwriter/ui/export_page.py').read_text(encoding='utf-8')
        self.assertIn("export_pdf", source)
        self.assertIn("'PDF exporteren'", source)
        self.assertIn('self.pdf_panel', source)
        self.assertIn('self.pdf_paper_combo', source)
        self.assertNotIn("self.pdf_button.setEnabled(False)", source)


if __name__ == '__main__':
    unittest.main()
