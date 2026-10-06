from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from quietwriter.docx_io import paragraph_to_markdown, parse_docx_book
from quietwriter.exporting.builder import _bcp47_language


def _add_hyperlink(paragraph, text: str, url='https://example.com'):
    part = paragraph.part
    rid = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), rid)
    run = OxmlElement('w:r')
    t = OxmlElement('w:t'); t.text = text
    run.append(t); hyperlink.append(run); paragraph._p.append(hyperlink)


def test_page_oriented_import_keeps_long_first_paragraph_in_body(tmp_path: Path):
    path = tmp_path / 'long-first.docx'
    doc = Document()
    doc.add_paragraph('Titel', style='Title').add_run().add_break(WD_BREAK.PAGE)
    long_text = 'Het was een koude ochtend in maart toen Ilse de deur van de vuurtoren opende. ' * 4
    doc.add_paragraph(long_text).add_run().add_break(WD_BREAK.PAGE)
    doc.add_paragraph('Volgende').add_run().add_break(WD_BREAK.PAGE)
    doc.save(path)
    parsed = parse_docx_book(path)
    all_text = '\n'.join(ch['text'] for _, chapters in parsed.sections for ch in chapters)
    assert long_text.strip() in all_text
    assert any(ch['title'].startswith('Deel ') for _, chapters in parsed.sections for ch in chapters)


def test_hyperlink_text_is_preserved_in_import(tmp_path: Path):
    path = tmp_path / 'links.docx'
    doc = Document(); doc.add_heading('Hoofdstuk', level=1)
    p = doc.add_paragraph('Lees meer op '); _add_hyperlink(p, 'LINKTEKST_HIER'); p.add_run(' na de link.')
    doc.save(path)
    parsed = parse_docx_book(path)
    body = '\n'.join(ch['text'] for _, chapters in parsed.sections for ch in chapters)
    assert 'Lees meer op LINKTEKST_HIER na de link.' in body


def test_adjacent_equal_formatting_runs_are_merged_before_markdown():
    doc = Document(); p = doc.add_paragraph()
    for text in ('vet', ' gesplitst', ' woord'):
        r = p.add_run(text); r.bold = True
    assert paragraph_to_markdown(p) == '**vet gesplitst woord**'


def test_bcp47_language_normalization():
    assert _bcp47_language('nl_NL') == 'nl-NL'
    assert _bcp47_language('en_us') == 'en-US'
    assert _bcp47_language('nl') == 'nl'
