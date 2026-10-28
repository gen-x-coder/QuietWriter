"""1.7.0-dev15: controle per pagina en paneel (designtaal en foutjes)."""
import os

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QEvent, QCoreApplication, QSettings, QPoint
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library


def _settle(app):
    for _ in range(3):
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.processEvents()


@pytest.fixture
def window(tmp_path):
    app = QApplication.instance() or QApplication([])
    from quietwriter.ui.main_window import MainWindow
    lib = Library(tmp_path / 'ws')
    book = lib.create_book('Een heel lange titel over een zomer die nooit leek te eindigen')
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(lib.root))
    w = MainWindow(settings, lib, [])
    w.resize(1280, 700); w.show(); w.open_book(book); w.show_editor(); _settle(app)
    yield app, w
    w.close()


def test_toolbar_title_is_elided_to_its_real_width(window):
    app, w = window
    page = w.editor_page
    page._toggle_right_widget(page.chapter_context, page.chapter_context); _settle(app)
    label = page.book_title_label
    assert label.full_text().startswith('Een heel lange titel')
    # Offscreen Qt mag de flexibele titelruimte tot nul verkleinen. Controleer
    # het afkorten met een expliciete, niet-nul breedte; verberg geen layoutfout.
    label.resize(110, max(20, label.height()))
    label._apply()
    assert label.width() == 110
    assert label.text().endswith('…')
    assert label.fontMetrics().horizontalAdvance(label.text()) <= label.width()


def test_contents_tab_stays_inside_the_editor_edge(window):
    app, w = window
    page = w.editor_page
    page._toggle_right_widget(page.search, page.search); _settle(app)
    page._position_contents_edge_button()
    edge_x = page.center.mapTo(page, QPoint(0, 0)).x()
    assert page.contents_edge_button.x() >= edge_x


def test_right_panel_titles_line_up(window):
    app, w = window
    page = w.editor_page
    tops = {}
    for name in ('search', 'chapter_context', 'open_points', 'spell', 'history'):
        panel = getattr(page, name)
        page._toggle_right_widget(panel, panel); _settle(app)
        tops[name] = panel.panel_help.title.mapTo(panel, QPoint(0, 0)).y()
    assert len(set(tops.values())) == 1, tops


def test_spell_actions_are_disabled_without_a_word(window):
    app, w = window
    page = w.editor_page
    page.dictionary.words = set()
    page.spell.refresh()
    assert not any(b.isEnabled() for b in (page.spell.change_btn, page.spell.ignore_btn, page.spell.ignore_all_btn,
                                            page.spell.ignore_always_btn, page.spell.add_btn))


def test_empty_trash_keeps_text_at_the_top(window):
    app, w = window
    w.show_trash(); _settle(app)
    trash = w.trash
    assert trash.list.isHidden() and not trash._empty_spacer.isHidden()
    assert trash.empty.geometry().top() < 200


def test_empty_characters_page_says_what_to_do(window):
    app, w = window
    w.show_planning(); _settle(app)
    page = w.planning_page.characters_page
    assert page.canvas.currentWidget() is page.blank
    assert 'Nieuw personage' in page.blank_hint.text()
