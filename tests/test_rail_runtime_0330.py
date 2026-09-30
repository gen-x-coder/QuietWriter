import os
import tempfile
from itertools import product
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.storage import Library
from quietwriter.themes import stylesheet
from quietwriter.ui.main_window import MainWindow
from quietwriter.ui.rail_model import RailState, build_rail_view


@pytest.fixture(scope='module')
def app():
    instance = QApplication.instance() or QApplication([])
    instance.setStyleSheet(stylesheet('Helder'))
    return instance


def _settings(path: Path, *, ai=True, advanced=True, expanded=True):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('workspace', str(path.parent / 'workspace'))
    settings.setValue('spell_enabled', True)
    settings.setValue('ai_enabled', ai)
    settings.setValue('advanced_options', advanced)
    settings.setValue('nav_expanded', expanded)
    return settings


def _visible_keys(window):
    return tuple(key for key, widget in window._rail_item_widgets.items() if not widget.isHidden())


def test_all_16_book_ai_advanced_expanded_states_match_manual_model(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini'), lib, [])
        window.show(); app.processEvents()
        book = lib.create_book('Matrix')

        for has_book, ai, advanced, expanded in product((False, True), repeat=4):
            if has_book and window.active_book() is None:
                window.open_book(book); app.processEvents()
            elif not has_book and window.active_book() is not None:
                window.go_home(); app.processEvents()

            window.rail_expanded = expanded
            window._feature_visibility_preview = {'ai_enabled': ai, 'advanced': advanced}
            window._apply_nav_width(False); app.processEvents()

            expected = build_rail_view(RailState(has_book, ai, advanced))
            assert _visible_keys(window) == expected.visible_items
            for key, heading in window._rail_group_widgets.items():
                assert heading.isHidden() is (not (expanded and expected.is_group_visible(key)))

        window.close()


def test_low_height_rail_scrolls_without_forcing_window_taller(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini', ai=True, advanced=True, expanded=True), lib, [])
        window.show(); app.processEvents()
        window.open_book(lib.create_book('Hoogte')); app.processEvents()

        for height in (700, 720, 768):
            window.resize(1280, height); app.processEvents()
            assert window.height() <= height
            assert window.rail_scroll.viewport().width() >= 194
            if window.rail_scroll.verticalScrollBar().isVisible():
                assert window.rail_scroll.verticalScrollBar().width() <= 8
            # PROGRAMMA is outside the scrolling viewport and remains reachable.
            assert not window.program_host.isHidden()
            assert window.settings_button.geometry().bottom() <= window.program_host.height()

        window.close()


def test_commit_redirects_hidden_ai_context_page_but_preview_does_not(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        settings = _settings(root / 'settings.ini', ai=True, advanced=True, expanded=True)
        window = MainWindow(settings, lib, [])
        window.show(); app.processEvents()
        window.open_book(lib.create_book('Fallback AI')); app.processEvents()
        window.show_book_memory(); app.processEvents()
        assert window.stack.currentWidget() is window.book_memory_page

        window.open_settings(); app.processEvents()
        assert window._settings_return_page is window.book_memory_page
        window.preview_feature_visibility(ai_enabled=False, advanced=True); app.processEvents()
        assert window.stack.currentWidget() is window.settings_page
        assert window.book_memory_button.isHidden()
        assert window._settings_return_page is window.book_memory_page

        settings.setValue('ai_enabled', False); settings.sync()
        window.settings_saved(settings.value('workspace')); app.processEvents()
        assert window._settings_return_page is window.editor_page
        window.return_from_settings(); app.processEvents()
        assert window.stack.currentWidget() is window.editor_page
        window.close()


def test_commit_redirects_hidden_integrity_page_to_contents(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        settings = _settings(root / 'settings.ini', ai=True, advanced=True, expanded=True)
        window = MainWindow(settings, lib, [])
        window.show(); app.processEvents()
        window.open_book(lib.create_book('Fallback Integriteit')); app.processEvents()
        window.show_integrity(); app.processEvents()
        assert window.stack.currentWidget() is window.integrity_page

        window.open_settings(); app.processEvents()
        window.preview_feature_visibility(ai_enabled=True, advanced=False); app.processEvents()
        assert window._settings_return_page is window.integrity_page
        settings.setValue('advanced_options', False); settings.sync()
        window.settings_saved(settings.value('workspace')); app.processEvents()
        assert window._settings_return_page is window.editor_page
        window.return_from_settings(); app.processEvents()
        assert window.stack.currentWidget() is window.editor_page
        window.close()


def test_collapsed_rail_shows_group_separators_without_headings(app):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lib = Library(root / 'workspace')
        window = MainWindow(_settings(root / 'settings.ini', ai=True, advanced=True, expanded=False), lib, [])
        window.show(); app.processEvents()
        window.open_book(lib.create_book('Separators')); app.processEvents()
        window.rail_expanded = False
        window._apply_nav_width(False); app.processEvents()
        assert all(heading.isHidden() for heading in window._rail_group_widgets.values())
        assert all(not sep.isHidden() for sep in window._rail_separator_widgets.values())
        window.close()
