"""1.7.0: omslag uit een seed (boek-ID) voor boeken zonder eigen omslag.

Alleen weergave: hetzelfde boek geeft altijd hetzelfde beeld, er wordt niets
geschreven, en een eigen omslag gaat altijd voor.
"""
import os
import uuid
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.bookshelf import BookCover
from quietwriter.ui.generated_cover import PATTERNS, cover_seed, cover_spec, generated_cover_pixmap


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def _lightness(hex_color):
    return QColor(hex_color).lightnessF()


def test_same_seed_gives_same_cover():
    seed = '3f2c8a8e-0000-4000-8000-000000000001'
    assert cover_spec(seed) == cover_spec(seed)
    assert cover_spec(seed) != cover_spec(seed[:-1] + '2')


def test_cover_spec_is_stable_across_releases():
    # Vastgepind: een nieuwe Python- of Qt-versie mag een bestaande omslag niet
    # veranderen. Pas dit alleen aan als het patroon bewust verandert.
    spec = cover_spec('quietwriter')
    assert (spec.pattern, spec.base, spec.shade, spec.accent, spec.ink) == (
        'bands', '#355056', '#4e6877', '#bba27c', '#ecf2f4')


def test_different_books_get_varied_covers():
    specs = [cover_spec(str(uuid.UUID(int=i * 104729 + 7))) for i in range(200)]
    assert {spec.pattern for spec in specs} == set(PATTERNS)
    assert len({spec.base for spec in specs}) > 150


def test_colours_stay_calm_and_title_stays_readable():
    for i in range(300):
        spec = cover_spec(f'boek-{i}')
        base = QColor(spec.base)
        assert 0.2 <= base.lightnessF() <= 0.45
        assert base.hslSaturationF() <= 0.45
        assert _lightness(spec.ink) >= 0.9


def test_seed_falls_back_to_title_without_id():
    class NoId:
        id = ''
        title = 'De Vuurtoren'
    class WithId:
        id = 'abc'
        title = 'De Vuurtoren'
    assert cover_seed(WithId()) == 'abc'
    assert cover_seed(NoId()) == 'title:de vuurtoren'


@pytest.mark.parametrize('pattern', PATTERNS)
def test_every_pattern_paints_something(app, pattern):
    seed = next(f's{i}' for i in range(500) if cover_spec(f's{i}').pattern == pattern)
    spec = cover_spec(seed)
    pix = generated_cover_pixmap(spec, 192, 307, title='Een heel lange titel die echt niet op twee regels past, zelfs niet klein', author='Lucas Bonsel')
    image = pix.toImage()
    assert image.width() == 192 and image.height() == 307
    base = QColor(spec.base).rgb()
    lower = {image.pixel(x, y) for x in range(0, 192, 6) for y in range(140, 307, 6)}
    assert len(lower - {base}) > 3, pattern
    # Titel staat erop. Tel pixels, geen kleurtinten: Windows tekent tekst in een
    # pixmap soms zonder overgangen (alleen achtergrond en inktkleur).
    upper = [image.pixel(x, y) for x in range(0, 192) for y in range(10, 60)]
    assert sum(1 for value in upper if value != base) > 50


def _snapshot(root):
    return sorted((str(p.relative_to(root)), p.stat().st_mtime_ns, p.stat().st_size) for p in root.rglob('*') if p.is_file())


def test_bookshelf_uses_generated_cover_without_writing(app, tmp_path):
    library = Library(tmp_path / 'werkmap')
    book = library.create_book('Zout op de dijk')
    twin = library.create_book('Zout op de dijk')
    before = _snapshot(tmp_path)
    widget = BookCover(library, book)
    try:
        first = widget.grab().toImage()
        assert widget._generated_pixmap() is widget._generated_pixmap()  # één keer tekenen
        assert BookCover(library, book).grab().toImage() == first
        assert BookCover(library, twin).grab().toImage() != first  # zelfde titel, ander boek
    finally:
        widget.close()
    assert _snapshot(tmp_path) == before


def test_own_cover_still_wins(app, tmp_path):
    library = Library(tmp_path / 'werkmap')
    book = library.create_book('Met omslag')
    source = tmp_path / 'omslag.png'
    pix = QPixmap(640, 1024)
    pix.fill(QColor('#ff0000'))
    assert pix.save(str(source))
    library.set_cover(book, source)
    image = BookCover(library, book).grab().toImage()
    assert QColor(image.pixel(96, 40)).red() > 240


def test_book_details_previews_generated_cover(app, tmp_path):
    from PySide6.QtCore import QSettings
    from quietwriter.ui.book_details import BookDetailsPage
    library = Library(tmp_path / 'werkmap')
    book = library.create_book('Voorbeeld')
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    page = BookDetailsPage(library, settings, book)
    try:
        pix = page.cover_preview.pixmap()
        assert pix is not None and not pix.isNull()
        assert not page.remove_cover_button.isEnabled()
        assert 'exporteren' in page.cover_name.text()
        assert not page.has_pending_changes()  # alleen weergave, geen wijziging
    finally:
        page.close()
