from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from quietwriter.crash_logging import _open_crash_log, _rotate_if_needed
from quietwriter.exporting.markdown_exporter import render_publication_frontmatter
from quietwriter.exporting.models import ExportAsset, ExportDocument, ExportSection


def _document(**metadata):
    return ExportDocument(
        id='12345678-1234-1234-1234-123456789abc',
        title=metadata.pop('title', 'Testboek'),
        author=metadata.pop('author', 'Ada Auteur'),
        language='nl',
        slug=metadata.pop('slug', 'testboek'),
        metadata=metadata,
        sections=(ExportSection('root', 'Manuscript', ()),),
        front_matter=(), back_matter=(), assets=(), cover_asset_id=None, epub_isbn='',
    )


def test_public_frontmatter_quotes_yaml_sensitive_values_without_changing_simple_contract():
    text = render_publication_frontmatter(_document(
        title='Mijn boek: het vervolg',
        description='Regel één\nRegel twee',
        meta='tekst # met commentteken',
        intro='Gewone intro',
        author='Yes',
        tags='een, twee',
        date='2025-12-10T16:00',
    ))
    assert 'title: "Mijn boek: het vervolg"' in text
    assert 'description: "Regel één\\nRegel twee"' in text
    assert 'meta: "tekst # met commentteken"' in text
    assert 'author: "Yes"' in text
    assert 'date: 2025-12-10T16:00' in text
    assert 'intro: Gewone intro' in text


def test_public_frontmatter_is_parseable_yaml_when_pyyaml_is_available():
    yaml = pytest.importorskip('yaml')
    text = render_publication_frontmatter(_document(
        title='Mijn boek: het vervolg',
        description='Regel één\nRegel twee',
        meta='tekst # met commentteken',
        author='Yes',
        tags='een, twee',
    ))
    body = text.split('---\n', 2)[1]
    parsed = yaml.safe_load(body)
    assert parsed['title'] == 'Mijn boek: het vervolg'
    assert parsed['description'] == 'Regel één\nRegel twee'
    assert parsed['author'] == 'Yes'


def test_empty_cover_is_rejected_before_qt_is_needed():
    from quietwriter.exporting.cover import render_cover
    asset = ExportAsset('cover', 'cover.jpg', 'image/jpeg', b'', role='cover')
    with pytest.raises(ValueError, match='leeg'):
        render_cover(asset, 'Boek', 'Auteur', 'artwork_with_text')


def test_corrupt_nonempty_passthrough_cover_is_rejected_when_qt_available():
    pytest.importorskip('PySide6.QtGui')
    from quietwriter.exporting.cover import render_cover
    asset = ExportAsset('cover', 'cover.jpg', 'image/jpeg', b'not-a-real-jpeg', role='cover')
    with pytest.raises(ValueError, match='niet worden gelezen'):
        render_cover(asset, 'Boek', 'Auteur', 'artwork_with_text')


def test_crash_log_rotates_to_single_backup():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'crash.log'
        path.write_text('x' * 200, encoding='utf-8')
        _rotate_if_needed(path, max_bytes=100)
        assert not path.exists()
        backup = Path(td) / 'crash.log.1'
        assert backup.exists()
        assert backup.read_text(encoding='utf-8') == 'x' * 200


def test_crash_log_falls_back_to_temp_when_workspace_log_cannot_open():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocker = root / 'not-a-directory'
        blocker.write_text('file', encoding='utf-8')
        fallback_root = root / 'fallback'
        fallback_root.mkdir()
        with patch('quietwriter.crash_logging.tempfile.gettempdir', return_value=str(fallback_root)):
            handle, actual = _open_crash_log(blocker / 'logs' / 'crash.log')
        try:
            assert handle is not None
            assert actual == fallback_root / 'QuietWriter' / 'crash.log'
            handle.write('ok\n')
            handle.flush()
            assert actual.exists()
        finally:
            if handle is not None:
                handle.close()
