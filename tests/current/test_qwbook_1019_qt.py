from pathlib import Path
import os
import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QFileDialog

from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow


def _window(tmp_path: Path, name='workspace'):
    app = QApplication.instance() or QApplication([])
    lib = Library(tmp_path / name)
    settings = QSettings(str(tmp_path / f'{name}.ini'), QSettings.IniFormat)
    settings.setValue('spell_enabled', False)
    settings.setValue('ai_enabled', False)
    settings.setValue('advanced_options', False)
    return app, lib, MainWindow(settings, lib, [])


def test_export_page_can_create_qwbook(tmp_path: Path):
    _app, lib, window = _window(tmp_path)
    try:
        book = lib.create_book('Portable')
        lib.save_chapter(book, book.sections[0].chapters[0], 'Bewaar **alles**.')
        window.open_book(book)
        page = window.export_page
        page.set_book(window._active_book)
        page.qwbook_button.setChecked(True)
        page._format_changed()
        out = tmp_path / 'out'; out.mkdir()
        window.settings.setValue('export/output_dir', str(out))
        page._export()
        files = list(out.glob('*.qwbook'))
        assert len(files) == 1
        assert files[0].stat().st_size > 0
    finally:
        window.close()


def test_main_window_imports_qwbook_and_opens_it(tmp_path: Path, monkeypatch):
    from quietwriter.qwbook_io import export_qwbook
    source_lib = Library(tmp_path / 'source')
    book = source_lib.create_book('Overgezet')
    source_lib.track_book(book)
    source_lib.save_chapter(book, book.sections[0].chapters[0], 'Volledige tekst')
    package = export_qwbook(source_lib, book, tmp_path / 'boek.qwbook')

    _app, target_lib, window = _window(tmp_path, 'target')
    try:
        monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: (str(package), 'QuietWriter book (*.qwbook)'))
        window.import_book()
        assert window._active_book is not None
        assert window._active_book.title == 'Overgezet'
        assert target_lib.read_chapter(window._active_book, window._active_book.sections[0].chapters[0]) == 'Volledige tekst'
    finally:
        window.close()


def test_qwbook_hides_open_file_action_after_export(tmp_path: Path):
    _app, lib, window = _window(tmp_path, 'open-action')
    try:
        book = lib.create_book('Niet openen')
        window.open_book(book)
        page = window.export_page
        page.set_book(window._active_book)
        page.qwbook_button.setChecked(True)
        page._format_changed()
        assert page.open_file_button.isHidden()
        page.epub_button.setChecked(True)
        page._format_changed()
        assert not page.open_file_button.isHidden()
    finally:
        window.close()


def test_qwbook_export_can_disable_version_history(tmp_path: Path):
    _app, lib, window = _window(tmp_path, 'history-option')
    try:
        book = lib.create_book('Kleine overdracht')
        lib.create_version(book)
        window.open_book(book)
        page = window.export_page
        page.set_book(window._active_book)
        page.qwbook_button.setChecked(True)
        page._format_changed()
        assert not page.qwbook_panel.isHidden()
        page.qwbook_include_history.setChecked(False)
        out = tmp_path / 'out-small'; out.mkdir()
        window.settings.setValue('export/output_dir', str(out))
        page._export()
        package = next(out.glob('*.qwbook'))
        import json, zipfile
        with zipfile.ZipFile(package, 'r') as z:
            manifest = json.loads(z.read('qwbook.json'))
            assert manifest['history_included'] is False
            assert manifest['history_files'] == {}
    finally:
        window.close()


def test_qwbook_include_history_choice_survives_set_book(tmp_path: Path):
    _app, lib, window = _window(tmp_path, 'history-persist')
    try:
        book = lib.create_book('Voorkeur onthouden')
        window.open_book(book)
        page = window.export_page
        page.set_book(window._active_book)
        page.qwbook_button.setChecked(True)
        page._format_changed()
        page.qwbook_include_history.setChecked(False)
        page._options_changed()
        page.set_book(window._active_book)
        assert not page.qwbook_include_history.isChecked()
    finally:
        window.close()
