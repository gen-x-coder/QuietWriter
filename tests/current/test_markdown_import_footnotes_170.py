"""Markdown-import houdt ^[...]-voetnoten (1.7; vielen eerder stil weg)."""
from quietwriter.storage import Library


def test_markdown_import_keeps_footnotes(tmp_path):
    lib = Library(tmp_path / 'ws')
    source = tmp_path / 'b.md'
    source.write_text('---\ntitle: T\n---\n\n# A\n\nTekst.^[Noot *een*.] En **vet**.\n', encoding='utf-8')
    book = lib.load_book(lib.import_markdown_book(source).path)
    texts = [p.read_text(encoding='utf-8') for p in book.path.rglob('chapters/**/*.md')]
    assert texts == ['Tekst.^[Noot *een*.] En **vet**.']
