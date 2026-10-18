"""1.7.0: rustige grafiek van de laatste 30 dagen in Boekdetails."""
import os
from datetime import date, timedelta

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from quietwriter.i18n import set_locale
from quietwriter.storage import Library
from quietwriter.themes import THEMES
from quietwriter.ui.progress_strip import ProgressStrip, strip_summary
from quietwriter.writing_progress import WritingProgressStore


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def dutch():
    set_locale('nl')
    yield
    set_locale('nl')


TODAY = date(2026, 10, 16)


def test_recent_days_is_always_thirty_days_oldest_first(tmp_path):
    store = WritingProgressStore(tmp_path / 'werkmap')
    store.add('boek', 500, on_date=TODAY)
    store.add('boek', 120, on_date=TODAY - timedelta(days=29))
    store.add('boek', 999, on_date=TODAY - timedelta(days=30))  # valt er net buiten
    store.add('ander', 50, on_date=TODAY)
    days = store.recent_days('boek', 30, on_date=TODAY)
    assert len(days) == 30
    assert days[0] == (TODAY - timedelta(days=29), 120)
    assert days[-1] == (TODAY, 500)
    assert sum(count for _d, count in days) == 620
    assert all(count == 0 for _d, count in days[1:-1])
    assert len(WritingProgressStore(tmp_path / 'werkmap').recent_days('onbekend', 30, on_date=TODAY)) == 30


def test_summary_counts_only_days_with_words():
    days = [(TODAY - timedelta(days=i), 0) for i in range(29, -1, -1)]
    days[3] = (days[3][0], 1200)
    days[-1] = (TODAY, 34)
    assert strip_summary(days) == '1.234 woorden op 2 van de 30 dagen · alleen op deze computer'


def test_strip_draws_bars_and_quiet_baseline_and_tooltips(app):
    settings = QSettings()
    strip = ProgressStrip(settings)
    strip.resize(450, 54)
    days = [(TODAY - timedelta(days=29 - i), 0) for i in range(30)]
    days[-1] = (TODAY, 800)
    days[10] = (days[10][0], 400)
    strip.set_days(days)
    image = strip.grab().toImage()
    accent = QColor(THEMES[str(settings.value('theme', 'Helder'))]['accent'])
    today_column = strip.bar_rect(29)
    pixel = QColor(image.pixel(int(today_column.center().x()), 40))
    assert abs(pixel.red() - accent.red()) < 8 and abs(pixel.blue() - accent.blue()) < 8
    background = image.pixel(int(strip.bar_rect(0).center().x()), 10)  # lege dag
    assert image.pixel(int(strip.bar_rect(10).center().x()), 10) == background  # half zo hoog: bovenin leeg
    assert image.pixel(int(strip.bar_rect(10).center().x()), 40) != background
    assert image.pixel(int(strip.bar_rect(0).center().x()), 47) != background  # dun grijs streepje
    assert strip.index_at(today_column.center().x()) == 29
    assert strip.index_at(strip.bar_rect(0).right() + 1.5) is None  # tussen twee staafjes
    assert strip.tooltip_text(29).endswith('800 woorden')
    assert strip.tooltip_text(0).endswith('niet geschreven')
    assert 'woorden op 2 van de 30 dagen' in strip.accessibleName()


def _page(tmp_path, *, enabled, words_today=0):
    from quietwriter.ui.book_details import BookDetailsPage
    library = Library(tmp_path / 'werkmap')
    book = library.create_book('Grafiek')
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    settings.setValue('writing_progress_enabled', enabled)
    if words_today:
        WritingProgressStore(library.root).add(book.id, words_today)
    return BookDetailsPage(library, settings, book), library, book


def test_details_points_to_settings_when_tracking_is_off_even_with_old_counts(app, tmp_path):
    # dev14: de regel staat er altijd, anders weet niemand dat hij bestaat (Windows-test Lucas).
    page, _lib, _book = _page(tmp_path, enabled=False, words_today=300)
    try:
        assert page._details_form.isRowVisible(page.progress_box)
        assert page.progress_strip.isHidden()
        assert page.progress_strip.days() == []
        assert 'Instellingen' in page.progress_summary.text()
        assert not page.has_pending_changes()
    finally:
        page.close()


def test_details_shows_quiet_empty_strip_without_counts(app, tmp_path):
    page, _lib, _book = _page(tmp_path, enabled=True)
    try:
        assert page._details_form.isRowVisible(page.progress_box)
        assert not page.progress_strip.isHidden()
        assert len(page.progress_strip.days()) == 30
        assert page.progress_summary.text().startswith('Nog geen woorden geteld')
    finally:
        page.close()


def test_word_goal_field_is_compact(app, tmp_path):
    page, _lib, _book = _page(tmp_path, enabled=True)
    try:
        assert page.word_goal.maximumWidth() <= 210
        assert page.word_goal.lineEdit().textMargins().left() >= 8
    finally:
        page.close()


def test_details_shows_row_and_updates_when_shown_again(app, tmp_path):
    page, library, book = _page(tmp_path, enabled=True, words_today=300)
    try:
        assert page._details_form.isRowVisible(page.progress_box)
        assert page.progress_summary.text().startswith('300 woorden op 1 van de 30 dagen')
        WritingProgressStore(library.root).add(book.id, 50)  # de editor telt door
        page.show()
        assert page.progress_summary.text().startswith('350 woorden')
        assert not page.has_pending_changes()  # alleen weergave
    finally:
        page.close()
