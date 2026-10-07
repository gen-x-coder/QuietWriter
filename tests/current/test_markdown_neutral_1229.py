from pathlib import Path

from quietwriter.exporting.markdown_exporter import _public_markdown_body
from quietwriter.markdown_io import read_markdown_import_document
from quietwriter.import_document import serialize_import_chapter
from quietwriter.storage import Library


def test_public_markdown_separates_quietwriter_paragraphs_for_commonmark():
    assert _public_markdown_body('Eerste alinea.\nTweede alinea.\nDerde alinea.') == (
        'Eerste alinea.\n\nTweede alinea.\n\nDerde alinea.'
    )


def test_public_markdown_serializes_soft_break_as_commonmark_hard_break():
    assert _public_markdown_body('Regel een\u2028regel twee') == 'Regel een\\\nregel twee'


def test_markdown_import_collapses_wrapped_prose_to_one_quietwriter_paragraph(tmp_path: Path):
    path = tmp_path / 'wrapped.md'
    path.write_text(
        '---\ntitle: Test\n---\n\n# Hoofdstuk\n\n'
        'Dit is een lange alinea die\nin Markdown over twee bronregels staat.\n\n'
        'Dit is de tweede alinea.\n',
        encoding='utf-8',
    )
    document = read_markdown_import_document(path)
    chapter = document.sections[0].chapters[0]
    source = serialize_import_chapter(chapter)
    assert source == (
        'Dit is een lange alinea die in Markdown over twee bronregels staat.\n'
        'Dit is de tweede alinea.'
    )


def test_markdown_import_preserves_commonmark_hard_break_as_soft_break(tmp_path: Path):
    path = tmp_path / 'break.md'
    path.write_text('# H\n\nRegel een\\\nregel twee.\n', encoding='utf-8')
    document = read_markdown_import_document(path)
    source = serialize_import_chapter(document.sections[0].chapters[0])
    assert source == 'Regel een\u2028regel twee.'


def test_markdown_library_import_is_transactional_and_current_syntax(tmp_path: Path):
    path = tmp_path / 'book.md'
    path.write_text('---\ntitle: Boek\nauthor: Ada\ncustom: bewaard\n---\n\n# Een\n\nTekst.\n', encoding='utf-8')
    library = Library(tmp_path / 'workspace')
    book = library.import_markdown_book(path)
    assert book.metadata['author'] == 'Ada'
    assert book.metadata['extra']['custom'] == 'bewaard'
    assert book.extra_manifest.get('manuscript_syntax')
    assert library.read_chapter(book, book.sections[0].chapters[0]) == 'Tekst.'
    assert not list(library.books_dir.glob('.import-*'))
