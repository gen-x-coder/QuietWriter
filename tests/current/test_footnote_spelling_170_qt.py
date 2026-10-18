"""1.7.0-dev14: spelling in de notenstrook (stond uit sinds dev10)."""
import os

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow


def _underlined(edit, word):
    text = edit.toPlainText()
    start = text.index(word)
    block = edit.document().firstBlock()
    for fmt_range in block.layout().formats():
        if fmt_range.start <= start < fmt_range.start + fmt_range.length:
            if fmt_range.format.underlineStyle() == QTextCharFormat.SpellCheckUnderline:
                return True
    return False


@pytest.fixture
def page(tmp_path):
    app = QApplication.instance() or QApplication([])
    lib = Library(tmp_path / 'ws')
    book = lib.create_book('Noten')
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(lib.root))
    window = MainWindow(settings, lib, [])
    window.resize(1100, 700); window.show(); window.open_book(book)
    page = window.editor_page
    page.dictionary.words = {'het', 'huis', 'stond', 'aan', 'de', 'dijk', 'gebouwd', 'in', 'hoofdstuk'}
    page.dictionary._clear_caches()
    page.highlighter.set_active(True)
    page.editor.setPlainText('Het huis stond^[Gebouwd in 1902 aan de dikj.] aan de dijk.')
    page.footnote_strip.refresh()
    app.processEvents()
    yield page
    window.close()


def test_note_strip_underlines_misspellings_like_the_text(page):
    note = page.footnote_strip.rows[0].edit
    assert _underlined(note, 'dikj')
    assert not _underlined(note, 'Gebouwd')
    # Woord toevoegen aan het woordenboek: ook in de noot weg.
    page.dictionary.ignore('dikj')
    page.highlighter.rehighlight()
    assert not _underlined(note, 'dikj')
    # Spelling uit: geen onderstreping meer.
    page.dictionary.ignored_words.clear(); page.dictionary._clear_caches()
    page.highlighter.set_active(False)
    assert not _underlined(note, 'dikj')
    page.highlighter.set_active(True)
    assert _underlined(note, 'dikj')


def test_spell_panel_selects_and_fixes_a_word_in_a_note(page):
    panel = page.spell
    panel.refresh()
    words = [row[1] for row in panel.rows]
    assert words == ['dikj']
    note = page.footnote_strip.rows[0].edit
    assert note.hasFocus() or note.textCursor().selectedText() == 'dikj'
    assert note.textCursor().selectedText() == 'dikj'
    panel.suggestions.set_suggestions(['dijk'])
    panel.change()
    assert page.editor.toPlainText() == 'Het huis stond^[Gebouwd in 1902 aan de dijk.] aan de dijk.'
    assert note.toPlainText() == 'Gebouwd in 1902 aan de dijk.'
