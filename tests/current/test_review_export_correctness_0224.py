"""Regression coverage for QuietWriter 0.22.4 export correctness fixes.

Findings 9-12 from external review round 3 plus the typography refresh
regression found manually after 0.22.3.
"""
from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from quietwriter.exporting.epub_exporter import export_epub
from quietwriter.exporting.markup import inline_to_xhtml, markdown_to_xhtml
from quietwriter.exporting.markdown_exporter import export_markdown
from quietwriter.exporting.models import ExportChapter, ExportDocument, ExportItem, ExportSection
from quietwriter.exporting.settings import default_export_settings
from quietwriter.markdown_io import parse_markdown_book, split_frontmatter

ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT_EDITOR_SOURCE = ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py'


def _document(markdown: str, *, contents_depth: str = 'chapters') -> ExportDocument:
    return ExportDocument(
        id='22222222-2222-2222-2222-222222222224',
        title='Testboek: vervolg', author='Ada Auteur', language='nl', slug='testboek-vervolg',
        metadata={'description': 'Regel een\nRegel twee', 'tags': 'yes'},
        sections=(ExportSection('root', 'Manuscript', (
            ExportChapter('c1', 'Hoofdstuk één', markdown),
        )),),
        front_matter=(ExportItem('contents', 'generated', {'depth': contents_depth}),),
        back_matter=(), assets=(), cover_asset_id=None, epub_isbn='',
    )


def test_one_enter_is_one_epub_paragraph():
    body = markdown_to_xhtml('Eerste alinea.\nTweede alinea.\nDerde alinea.')
    assert body == '<p>Eerste alinea.</p>\n<p>Tweede alinea.</p>\n<p>Derde alinea.</p>'


def test_crossed_inline_spans_are_balanced_xml():
    bold_italic = inline_to_xhtml('**een *twee** drie*')
    bold_strike = inline_to_xhtml('**vet ~~door** heen~~')

    assert bold_italic == '<strong>een <em>twee</em></strong><em> drie</em>'
    assert bold_strike == '<strong>vet <s>door</s></strong><s> heen</s>'
    ET.fromstring(f'<root>{bold_italic}</root>')
    ET.fromstring(f'<root>{bold_strike}</root>')


def test_quoted_frontmatter_scalars_are_decoded_on_import():
    metadata, body = split_frontmatter(
        '---\n'
        'title: "Mijn boek: het vervolg"\n'
        'description: "Regel een\\nRegel twee"\n'
        'tags: "yes"\n'
        "author: 'O''Brien'\n"
        '---\n'
        'Tekst.\n'
    )
    assert metadata['title'] == 'Mijn boek: het vervolg'
    assert metadata['description'] == 'Regel een\nRegel twee'
    assert metadata['tags'] == 'yes'
    assert metadata['author'] == "O'Brien"
    assert body == 'Tekst.'


def test_public_markdown_export_import_roundtrip_does_not_accumulate_quotes():
    document = _document('Eerste.\nTweede.')
    with tempfile.TemporaryDirectory() as td:
        first = Path(td) / 'first.md'
        export_markdown(document, first, {})
        parsed = parse_markdown_book(first)
        assert parsed['title'] == 'Testboek: vervolg'
        assert parsed['metadata']['description'] == 'Regel een\nRegel twee'
        assert parsed['metadata']['tags'] == 'yes'
        assert not parsed['title'].startswith('"')


def test_epub_contents_and_nav_include_heading_anchors_when_requested():
    document = _document('Begin.\n## Eerste *tussenkop*\nTekst.\n## Tweede tussenkop\nEinde.', contents_depth='headings')
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'headings.epub'
        settings = default_export_settings(); settings['epub']['include_cover'] = False
        export_epub(document, path, settings)
        with zipfile.ZipFile(path) as zf:
            chapter = zf.read('EPUB/text/chapter-001-001.xhtml').decode('utf-8')
            toc = zf.read('EPUB/text/contents.xhtml').decode('utf-8')
            nav = zf.read('EPUB/nav.xhtml').decode('utf-8')

    assert '<h2 id="h-1">Eerste <em>tussenkop</em></h2>' in chapter
    assert '<h2 id="h-2">Tweede tussenkop</h2>' in chapter
    assert 'href="chapter-001-001.xhtml#h-1">Eerste tussenkop</a>' in toc
    assert 'href="chapter-001-001.xhtml#h-2">Tweede tussenkop</a>' in toc
    assert 'href="text/chapter-001-001.xhtml#h-1">Eerste tussenkop</a>' in nav
    assert 'href="text/chapter-001-001.xhtml#h-2">Tweede tussenkop</a>' in nav
    ET.fromstring(chapter.encode('utf-8'))
    ET.fromstring(toc.encode('utf-8'))
    ET.fromstring(nav.encode('utf-8'))


def test_epub_contents_stays_chapter_only_when_requested():
    document = _document('Begin.\n## Niet in inhoud\nEinde.', contents_depth='chapters')
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'chapters-only.epub'
        settings = default_export_settings(); settings['epub']['include_cover'] = False
        export_epub(document, path, settings)
        with zipfile.ZipFile(path) as zf:
            toc = zf.read('EPUB/text/contents.xhtml').decode('utf-8')
            nav = zf.read('EPUB/nav.xhtml').decode('utf-8')
    assert '#h-1' not in toc
    assert '#h-1' not in nav


def test_apply_typography_rebases_existing_document_characters_source_guard():
    source = MANUSCRIPT_EDITOR_SOURCE.read_text(encoding='utf-8')
    method = source.split('    def apply_typography(self, typography: WritingTypography):', 1)[1].split(
        '    def apply_manuscript_style', 1
    )[0]
    assert 'cursor.select(QTextCursor.SelectionType.Document)' in method
    assert 'base_format.setFont(font)' in method
    assert 'cursor.mergeCharFormat(base_format)' in method
    assert 'self.blockSignals(True)' in method
    assert 'document.setModified(was_modified)' in method
    assert 'presentation_highlighter.rehighlight()' in method


def test_apply_typography_updates_existing_text_at_runtime():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    QtWidgets = pytest.importorskip('PySide6.QtWidgets')
    QtGui = pytest.importorskip('PySide6.QtGui')
    from quietwriter.typography import WritingTypography
    from quietwriter.ui.manuscript_editor import ManuscriptEditor

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    editor = ManuscriptEditor()
    try:
        general = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.GeneralFont).family()
        fixed = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont).family()
        editor.apply_typography(WritingTypography(general, 14))
        editor.setPlainText('Bestaande tekst die open blijft.')
        editor.apply_typography(WritingTypography(fixed, 19))
        app.processEvents()

        block = editor.document().firstBlock()
        fragment = block.begin().fragment()
        char_font = fragment.charFormat().font()
        assert round(char_font.pointSizeF()) == 19
        assert char_font.family() == QtGui.QFont(fixed).family()
    finally:
        editor.deleteLater()
        app.processEvents()
