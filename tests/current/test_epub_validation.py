from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from quietwriter.exporting.epub_exporter import export_epub
from quietwriter.exporting.epub_validation import EpubValidationError, validate_epub_archive
from quietwriter.exporting.models import ExportChapter, ExportDocument, ExportItem, ExportSection
from quietwriter.exporting.settings import default_export_settings


def _document(*, contents: bool = True) -> ExportDocument:
    front = (ExportItem('contents', 'generated'),) if contents else ()
    return ExportDocument(
        id='12345678-1234-1234-1234-123456789abc',
        title='Validatieboek',
        author='Ada Auteur',
        language='nl',
        slug='validatieboek',
        metadata={},
        sections=(
            ExportSection('root', 'Manuscript', (
                ExportChapter('c1', 'Begin', 'Eerste alinea.\n## Tussenkop\nTweede alinea.'),
            )),
        ),
        front_matter=front,
        back_matter=(),
        assets=(),
        cover_asset_id=None,
        epub_isbn='',
    )


def _settings() -> dict:
    settings = default_export_settings()
    settings['epub']['include_cover'] = False
    return settings


def test_exported_epub_passes_internal_archive_validation():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'book.epub'
        export_epub(_document(), path, _settings())
        report = validate_epub_archive(path)

    assert report.resource_count >= 4
    assert report.xhtml_count >= 3
    assert report.spine_count >= 2
    assert report.navigation_target_count >= 3


def test_navigation_document_has_minimal_landmarks_for_toc_and_bodymatter():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'book.epub'
        export_epub(_document(contents=True), path, _settings())
        with zipfile.ZipFile(path) as zf:
            nav = zf.read('EPUB/nav.xhtml').decode('utf-8')

    assert 'epub:type="landmarks"' in nav
    assert 'epub:type="toc" href="text/contents.xhtml"' in nav
    assert 'epub:type="bodymatter" href="text/chapter-001-001.xhtml"' in nav
    assert '>Start lezen<' in nav


def test_landmarks_without_in_book_contents_only_expose_bodymatter():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'book.epub'
        export_epub(_document(contents=False), path, _settings())
        with zipfile.ZipFile(path) as zf:
            nav = zf.read('EPUB/nav.xhtml').decode('utf-8')

    assert 'epub:type="landmarks"' in nav
    assert 'epub:type="bodymatter" href="text/chapter-001-001.xhtml"' in nav
    # The mandatory machine ToC remains, but no landmark points to a separate
    # generated contents.xhtml because that page is not part of the book.
    assert 'href="text/contents.xhtml"' not in nav


def test_validator_rejects_broken_local_navigation_target():
    with tempfile.TemporaryDirectory() as td:
        original = Path(td) / 'book.epub'
        broken = Path(td) / 'broken.epub'
        export_epub(_document(), original, _settings())

        with zipfile.ZipFile(original, 'r') as src, zipfile.ZipFile(broken, 'w') as dst:
            for index, info in enumerate(src.infolist()):
                data = src.read(info.filename)
                if info.filename == 'EPUB/nav.xhtml':
                    data = data.replace(b'text/chapter-001-001.xhtml', b'text/missing-chapter.xhtml')
                compress = zipfile.ZIP_STORED if index == 0 else zipfile.ZIP_DEFLATED
                dst.writestr(info.filename, data, compress_type=compress)

        with pytest.raises(EpubValidationError, match='ontbrekend bestand'):
            validate_epub_archive(broken)


def test_invalid_generated_archive_never_replaces_existing_destination():
    with tempfile.TemporaryDirectory() as td:
        destination = Path(td) / 'book.epub'
        destination.write_bytes(b'PREVIOUS-GOOD-EXPORT')

        with patch(
            'quietwriter.exporting.epub_exporter.validate_epub_archive',
            side_effect=EpubValidationError('simulated validation failure'),
        ):
            with pytest.raises(EpubValidationError):
                export_epub(_document(), destination, _settings())

        assert destination.read_bytes() == b'PREVIOUS-GOOD-EXPORT'
