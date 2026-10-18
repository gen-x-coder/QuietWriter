"""1.7.0: een zacht regeleinde (Shift+Enter, U+2028) wordt in elke export een
echt regeleinde. Lucas zag in ONLYOFFICE "SEP"-tekens in een DOCX-export."""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

SOURCE = '**Aaaa**  foud FOUD Foud   Dit is een test.'


def _book(td):
    from quietwriter.storage import Library
    lib = Library(Path(td) / 'ws')
    book = lib.create_book('Test')
    lib.track_book(book)
    lib.save_chapter(book, book.sections[0].chapters[0], SOURCE)
    return lib, book


def _document_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read('word/document.xml').decode('utf-8')


def test_docx_and_submission_use_real_line_breaks():
    from quietwriter.exporting import build_export_document
    from quietwriter.exporting.runner import destination_for, run_export
    with tempfile.TemporaryDirectory() as td:
        lib, book = _book(td)
        document = build_export_document(lib, book)
        for fmt in ('docx', 'submission'):
            dest = destination_for(Path(td), document, fmt)
            run_export(lib, book, document, fmt, {}, dest)
            xml = _document_xml(dest)
            assert ' ' not in xml, fmt
            assert xml.count('<w:br/>') >= 4, fmt
            assert 'foud FOUD Foud' in xml


def test_xhtml_renderers_turn_soft_breaks_into_br():
    from quietwriter.exporting.markup import inline_to_xhtml
    from quietwriter.exporting.xhtml import render_inline
    assert inline_to_xhtml('een twee') == 'een<br/>twee'
    assert '<br/>' in inline_to_xhtml('**een**\u2028twee')
    assert render_inline('een twee') == 'een<br/>twee'
    assert ' ' not in render_inline('*een* twee') and '<br/>' in render_inline('*een* twee')


def test_epub_contains_no_raw_line_separator():
    from quietwriter.exporting import build_export_document
    from quietwriter.exporting.runner import destination_for, run_export
    with tempfile.TemporaryDirectory() as td:
        lib, book = _book(td)
        document = build_export_document(lib, book)
        dest = destination_for(Path(td), document, 'epub')
        run_export(lib, book, document, 'epub', {'epub': {'include_cover': False}}, dest)
        with zipfile.ZipFile(dest) as archive:
            text = ''.join(archive.read(n).decode('utf-8', 'ignore') for n in archive.namelist() if n.endswith('.xhtml'))
        assert ' ' not in text and '<br/>' in text
