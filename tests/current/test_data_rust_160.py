"""1.6.0: bewaarbeleid dagversies, conflicten per hoofdstuk zonder dialoog,
'Ongedaan maken' na hoofdstuk verwijderen."""
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import Library


def _book(td, chapters=2):
    lib = Library(Path(td) / 'ws')
    book = lib.create_book('Pip')
    section = book.sections[0]
    for n in range(2, chapters + 1):
        lib.add_chapter(book, section, f'Hoofdstuk {n}')
    lib.track_book(book)
    for i, chapter in enumerate(section.chapters, 1):
        lib.save_chapter(book, chapter, f'Tekst {i}.')
    return lib, book


def _external_write(book, chapter, text):
    path = book.path / chapter.file
    time.sleep(0.01)
    path.write_text(text, encoding='utf-8')


# --- bewaarbeleid ----------------------------------------------------------------

def _row(vid, days_ago, kind='daily', starred=False, now=datetime(2026, 10, 15, 12)):
    return {'id': vid, 'kind': kind, 'starred': starred,
            'created_at': (now - timedelta(days=days_ago)).isoformat(timespec='seconds')}


def test_retention_policy_keeps_recent_weekly_monthly_and_never_touches_other_kinds():
    lib = Library.__new__(Library)  # pure functie, geen werkmap nodig
    now = datetime(2026, 10, 15, 12)
    rows = [_row(f'd{d}', d) for d in range(0, 400)]
    rows += [_row('manual-old', 300, kind='manual'), _row('star-old', 300, starred=True),
             _row('conflict-old', 300, kind='conflict_local'), _row('pre-restore-old', 300, kind='pre_restore')]
    doomed = set(lib.daily_versions_to_thin(rows, now))
    assert not any(f'd{d}' in doomed for d in range(0, 30))                   # laatste 30 dagen: alles
    kept_30_180 = [d for d in range(30, 180) if f'd{d}' not in doomed]
    assert 18 <= len(kept_30_180) <= 23                                       # ~één per week
    kept_old = [d for d in range(180, 400) if f'd{d}' not in doomed]
    assert 6 <= len(kept_old) <= 9                                            # ~één per maand
    assert not doomed & {'manual-old', 'star-old', 'conflict-old', 'pre-restore-old'}


def test_thinning_is_off_without_the_app_and_removes_folders_and_index_when_on():
    with tempfile.TemporaryDirectory() as td:
        lib, book = _book(td)
        assert lib.thin_daily_versions is False
        root = lib._history_root(book)
        # Vast op een woensdagmiddag ~60 dagen terug: met 'nu + uren' kon de reeks
        # 's avonds over een weekgrens (zondag → maandag) heen lopen.
        old = (datetime.now() - timedelta(days=60)).replace(hour=12, minute=0, second=0, microsecond=0)
        old -= timedelta(days=old.weekday() - 2)
        for i in range(5):  # vijf dagversies in dezelfde week, 60 dagen oud
            v = lib.create_version(book, kind='daily')
            index = lib._load_history_index(book)
            index['versions'][v['id']]['created_at'] = (old + timedelta(minutes=i)).isoformat(timespec='seconds')
            lib._save_history_index(book, index)
        manual = lib.create_version(book, kind='manual')
        removed = lib.thin_daily_history(book)
        assert len(removed) == 4
        left = {r['id'] for r in lib.list_versions(book)}
        assert manual['id'] in left and len(left) == 2
        assert all(not (root / vid).exists() for vid in removed)


# --- conflicten per hoofdstuk -----------------------------------------------------

def test_change_to_another_chapter_is_adopted_silently():
    with tempfile.TemporaryDirectory() as td:
        lib, book = _book(td)
        one, two = book.sections[0].chapters
        _external_write(book, two, 'Van de laptop.')
        lib.save_chapter(book, one, 'Hier geschreven.')                       # geen fout
        assert lib.pop_adopted_external_chapters(book) == [two.file]
        assert lib.read_chapter(book, two) == 'Van de laptop.'
        assert lib.read_chapter(book, one) == 'Hier geschreven.'


def test_change_to_this_chapter_or_structure_still_raises():
    with tempfile.TemporaryDirectory() as td:
        lib, book = _book(td)
        one, _ = book.sections[0].chapters
        _external_write(book, one, 'Van de laptop.')
        with pytest.raises(ExternalModificationError):
            lib.save_chapter(book, one, 'Hier geschreven.')
    with tempfile.TemporaryDirectory() as td:
        lib, book = _book(td)
        one, _ = book.sections[0].chapters
        manifest = book.path / 'book.json'
        time.sleep(0.01)
        manifest.write_text(manifest.read_text(encoding='utf-8').replace('"Pip"', '"Pip!"', 1), encoding='utf-8')
        with pytest.raises(ExternalModificationError):
            lib.save_chapter(book, one, 'Hier geschreven.')


def test_keep_both_puts_disk_version_directly_below_and_keeps_local_text():
    with tempfile.TemporaryDirectory() as td:
        lib, book = _book(td, chapters=3)
        one, two, three = book.sections[0].chapters
        _external_write(book, two, 'Versie van de laptop.')
        with pytest.raises(ExternalModificationError) as info:
            lib.save_chapter(book, two, 'Versie van hier.')
        assert lib.external_change_is_same_chapter_only(book, two, info.value)
        other = lib.save_chapter_keep_both(book, two, 'Versie van hier.')
        order = [c.id for c in book.sections[0].chapters]
        assert order == [one.id, two.id, other.id, three.id]
        assert lib.read_chapter(book, two) == 'Versie van hier.'
        assert lib.read_chapter(book, other) == 'Versie van de laptop.'
        assert '(andere computer' in other.title
        assert any(v['kind'] == 'conflict_local' for v in lib.list_versions(book))
        reloaded = lib.load_book(book.path)
        assert [c.id for c in reloaded.sections[0].chapters] == order
        lib.save_chapter(book, two, 'Verder schrijven.')                     # bewaking klopt weer


# --- in het echte venster ----------------------------------------------------------

@pytest.fixture(scope='module')
def app():
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _window(root):
    from PySide6.QtCore import QSettings
    from quietwriter.ui.main_window import MainWindow
    settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
    return MainWindow(settings, Library(root / 'workspace'), [])


def test_editor_keeps_both_versions_without_a_dialog(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            lib = window.library
            book = lib.create_book('Pip')
            window.open_book(book)
            page = window.editor_page
            chapter = page.chapter
            page.editor.setPlainText('Hier getypt.')
            page.dirty = True
            _external_write(page.book, chapter, 'Op de laptop getypt.')
            assert page.save() is True                                         # geen modale dialoog
            chapters = page.book.sections[0].chapters
            assert len(chapters) == 2
            assert lib.read_chapter(page.book, chapters[0]) == 'Hier getypt.'
            assert lib.read_chapter(page.book, chapters[1]) == 'Op de laptop getypt.'
            assert 'andere computer' in window.status.currentMessage()
        finally:
            window.search_index.close(); window.close(); app.processEvents()


def test_undo_after_chapter_delete_puts_it_back(app, monkeypatch):
    from quietwriter.ui import editor_page as ep
    monkeypatch.setattr(ep, 'confirm', lambda *a, **k: True)
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            lib = window.library
            book = lib.create_book('Pip')
            lib.track_book(book)
            lib.add_chapter(book, book.sections[0], 'Tweede')
            window.open_book(lib.load_book(book.path))
            page = window.editor_page
            second = page.book.sections[0].chapters[1]
            page.delete_chapter(second.id)
            assert [c.title for c in page.book.sections[0].chapters] == ['Hoofdstuk 1']
            label, button = window._undo_notice_widgets
            button.click()
            assert [c.title for c in page.book.sections[0].chapters] == ['Hoofdstuk 1', 'Tweede']
            assert window._undo_notice_widgets == ()
        finally:
            window.search_index.close(); window.close(); app.processEvents()


def test_unchanged_open_chapter_is_reloaded_when_returning_to_the_app(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            book = window.library.create_book('Pip')
            window.open_book(book)
            page = window.editor_page
            _external_write(page.book, page.chapter, 'Op de laptop getypt.')
            assert page.refresh_open_chapter_from_disk() is True
            assert page.editor.toPlainText() == 'Op de laptop getypt.'
            assert page.refresh_open_chapter_from_disk() is False            # niets nieuws meer
            page.editor.setPlainText('Hier verder.'); page.dirty = True
            assert page.save() is True                                        # geen conflict meer
        finally:
            window.search_index.close(); window.close(); app.processEvents()


def test_dirty_open_chapter_is_never_reloaded(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            book = window.library.create_book('Pip')
            window.open_book(book)
            page = window.editor_page
            page.editor.setPlainText('Niet opgeslagen.'); page.dirty = True
            _external_write(page.book, page.chapter, 'Op de laptop getypt.')
            assert page.refresh_open_chapter_from_disk() is False
            assert page.editor.toPlainText() == 'Niet opgeslagen.'
        finally:
            window.search_index.close(); window.close(); app.processEvents()
