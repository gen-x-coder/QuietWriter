"""1.5.2: typografie tijdens typen, venstertitel, sneltoetsen, boek dupliceren,
exporteren vanaf de kast en de schrijftest voor de werkmap."""
import os
import tempfile
from pathlib import Path

import pytest

from quietwriter.manuscript_markup import typographic_replacement as typo


# --- typografie: pure regels -------------------------------------------------

@pytest.mark.parametrize('prefix, typed, lang, expected', [
    ('Hij zei ', '"', 'nl', (0, '“')),
    ('“Hallo', '"', 'nl', (0, '”')),
    ('Er sagte ', '"', 'de', (0, '„')),
    ('„Hallo', '"', 'de', (0, '“')),
    ('Il dit ', '"', 'fr', (0, '« ')),
    ('« Bonjour ', '"', 'fr', (1, ' »')),
    ('Dijo ', '"', 'es', (0, '«')),
    ('zo', "'", 'nl', (0, '’')),          # zo’n
    ('auto', "'", 'nl', (0, '’')),        # auto’s
    ('Hij zei ', "'", 'nl', (0, '‘')),
    ('‘ja', "'", 'nl', (0, '’')),
    ('Hij wacht -', '-', 'nl', (1, '–')),
    ('He waits -', '-', 'en', (1, '—')),
    ('wacht..', '.', 'nl', (2, '…')),
    ('op ‘s', ' ', 'nl', (2, '’s ')),     # ’s avonds
    ('‘s', '-', 'nl', (2, '’s-')),        # ’s-Hertogenbosch
    ('in ‘', '9', 'nl', (1, '’9')),       # ’90
    ('In the ‘s', ' ', 'en', None),        # alleen Nederlands
])
def test_typographic_replacements(prefix, typed, lang, expected):
    assert typo(prefix, typed, lang) == expected


@pytest.mark.parametrize('prefix, typed', [
    ('-', '-'),          # begin van de regel: mogelijk Markdown-structuur
    ('--', '-'),
    ('a\\-', '-'),        # ge-escapet streepje
    ('wacht...', '.'),   # vierde punt: niets meer doen
    ('a\\..', '.'),
    ('tekst', 'a'),
    ('', ' '),
])
def test_no_replacement_where_markdown_or_plain_typing_is_meant(prefix, typed):
    assert typo(prefix, typed, 'nl') is None


def test_unknown_language_falls_back_to_dutch():
    assert typo('Hij zei ', '"', 'pt-BR') == (0, '“')
    assert typo('Hij zei ', '"', None) == (0, '“')


# --- typografie in de echte editor -------------------------------------------

@pytest.fixture(scope='module')
def app():
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _type(editor, text):
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    for ch in text:
        editor.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_unknown if ch not in ' ' else Qt.Key_Space, Qt.NoModifier, ch))


def test_editor_types_dutch_typography(app):
    from quietwriter.ui.manuscript_editor import ManuscriptEditor
    editor = ManuscriptEditor()
    editor.typing_language = 'nl'
    _type(editor, 'Hij zei "zo\'n ding" -- en op \'s avonds... ja')
    assert editor.toPlainText() == 'Hij zei “zo’n ding” – en op ’s avonds… ja'


def test_one_undo_takes_back_the_automatic_dash(app):
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from quietwriter.ui.manuscript_editor import ManuscriptEditor
    editor = ManuscriptEditor()
    _type(editor, 'Hij wacht --')
    assert editor.toPlainText() == 'Hij wacht –'
    editor.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Z, Qt.ControlModifier, ''))
    assert editor.toPlainText() == 'Hij wacht -'


def test_editor_respects_setting_off(app):
    from quietwriter.manuscript_markup import ManuscriptStyle
    from quietwriter.ui.manuscript_editor import ManuscriptEditor
    editor = ManuscriptEditor()
    editor.apply_manuscript_style(ManuscriptStyle.from_values(smart_quotes=False))
    _type(editor, 'a -- "b"...')
    assert editor.toPlainText() == 'a -- "b"...'


def test_editor_uses_german_quotes_for_a_german_book(app):
    from quietwriter.ui.manuscript_editor import ManuscriptEditor
    editor = ManuscriptEditor()
    editor.typing_language = 'de'
    _type(editor, 'Er sagte "Hallo"')
    assert editor.toPlainText() == 'Er sagte „Hallo“'


# --- boek dupliceren ----------------------------------------------------------

def test_duplicate_book_copies_text_and_shelf_but_not_local_ai_chat():
    from quietwriter.storage import Library
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'ws')
        shelf = lib.shelves.create_shelf('Serie')
        book = lib.create_book('Pip')
        lib.shelves.move_book(book.id, shelf.id)
        chapter = book.sections[0].chapters[0]
        lib.track_book(book)
        lib.save_chapter(book, chapter, 'Pip heeft geen haar.')
        (book.path / '.quietwriter').mkdir(exist_ok=True)
        (book.path / '.quietwriter' / 'ai_chat.json').write_text('{}', encoding='utf-8')

        copy = lib.duplicate_book(book)

        assert copy.id != book.id and copy.title == 'Pip (kopie)'
        assert lib.read_chapter(copy, copy.sections[0].chapters[0]) == 'Pip heeft geen haar.'
        assert not (copy.path / '.quietwriter').exists()
        assert lib.shelves.state().shelf_for_book(copy.id).id == shelf.id
        assert lib.read_chapter(book, chapter) == 'Pip heeft geen haar.'       # origineel onaangeroerd
        assert not any(p.name.startswith('.import-') for p in lib.books_dir.iterdir())


def test_duplicate_refuses_a_book_with_a_missing_chapter_and_leaves_nothing_behind():
    from quietwriter.storage import Library, ChapterNotAvailableError
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'ws')
        book = lib.create_book('Half gesynchroniseerd')
        (book.path / book.sections[0].chapters[0].file).unlink()
        with pytest.raises(ChapterNotAvailableError):
            lib.duplicate_book(book)
        assert [b.title for b in lib.list_books()] == ['Half gesynchroniseerd']


# --- schrijftest werkmap -----------------------------------------------------

def test_writable_check_reports_blocked_folder(monkeypatch, tmp_path):
    from quietwriter import workspace_path as wp

    def blocked(*a, **k):
        raise PermissionError(13, 'Access is denied')
    monkeypatch.setattr(wp.tempfile, 'NamedTemporaryFile', blocked)
    with pytest.raises(wp.WorkspaceNotWritable) as info:
        wp.require_writable_directory(tmp_path / 'Boeken')
    assert 'Boeken' in str(info.value)
    assert issubclass(wp.WorkspaceNotWritable, wp.UnsafeWorkspacePath)


def test_writable_check_creates_nothing(tmp_path):
    from quietwriter.workspace_path import require_writable_directory
    target = tmp_path / 'nieuw' / 'Boeken'
    require_writable_directory(target)
    assert not target.exists() and list(tmp_path.iterdir()) == []


# --- hoofdvenster: titel, sneltoetsen, kastacties ----------------------------

def _window(root):
    from PySide6.QtCore import QSettings
    from quietwriter.storage import Library
    from quietwriter.ui.main_window import MainWindow
    settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
    return MainWindow(settings, Library(root / 'workspace'), [])


def test_window_title_follows_open_book(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            base = window.windowTitle()
            book = window.library.create_book('De kat en de trap')
            window.open_book(book)
            assert window.windowTitle() == f'De kat en de trap — {base}'
            window.go_home()
            assert window.windowTitle() == base
        finally:
            window.search_index.close(); window.close(); app.processEvents()


def test_shortcuts_overview_opens_once(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            first = window.show_shortcuts()
            second = window.show_shortcuts()
            assert first is second and first.isVisible()
            first.close(); app.processEvents()
        finally:
            window.search_index.close(); window.close(); app.processEvents()


def test_shelf_duplicate_and_export_actions(app):
    with tempfile.TemporaryDirectory() as td:
        window = _window(Path(td))
        try:
            book = window.library.create_book('Pip')
            window.duplicate_book_from_shelf(book)
            assert sorted(b.title for b in window.library.list_books()) == ['Pip', 'Pip (kopie)']
            window.export_book_from_shelf(book)
            assert window.active_book().id == book.id
            assert window.stack.currentWidget() is window.export_page
        finally:
            window.search_index.close(); window.close(); app.processEvents()
