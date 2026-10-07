"""Begeleid exporteren in the real UI (offscreen). Design §5, tests 9–17."""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.media.markup import build_image_markdown
from quietwriter.media.store import MediaStore
from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow

pytestmark = pytest.mark.qt


def _window(tmp_path: Path, name='ws', *, guided=None):
    app = QApplication.instance() or QApplication([])
    lib = Library(tmp_path / name)
    settings = QSettings(str(tmp_path / f'{name}.ini'), QSettings.IniFormat)
    settings.setValue('spell_enabled', False)
    settings.setValue('ai_enabled', False)
    settings.setValue('advanced_options', False)
    if guided is not None:
        settings.setValue('export/guided', guided)
    out = tmp_path / f'{name}-out'
    out.mkdir(exist_ok=True)
    settings.setValue('export/output_dir', str(out))
    return app, lib, settings, MainWindow(settings, lib, []), out


def _book(tmp_path: Path, lib: Library, *, chat=False):
    md = '---\ntitle: Haven\nauthor: Lucas\n---\n\n# Een\n\nTekst een.\n\n# Twee\n\nTekst twee.\n'
    source = tmp_path / 'haven.md'
    source.write_text(md, encoding='utf-8')
    book = lib.import_markdown_book(source)
    lib.track_book(book)
    if chat:
        path = Path(book.path) / '.quietwriter' / 'ai_chat.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[{"role":"user","content":"geheim"}]', encoding='utf-8')
    lib.create_version(book, 'manual')
    return lib.load_book(book.path)


def _open_export(window, book):
    window.open_book(book)
    window.show_export()
    QApplication.processEvents()
    return window.export_page, window.export_page.wizard


def test_guided_is_default_and_mode_choice_is_remembered(tmp_path):
    _app, lib, settings, window, _out = _window(tmp_path)
    try:
        page, wizard = _open_export(window, _book(tmp_path, lib))
        assert page.mode_stack.currentWidget() is wizard
        assert wizard.step == 'purpose' and not wizard.next_button.isEnabled()
        page.manual_mode_button.click()
        assert page.mode_stack.currentWidget() is page.manual_view
        assert settings.value('export/guided', True, bool) is False
    finally:
        window.close()
    _app, _lib, _settings, window2, _out = _window(tmp_path)
    try:
        assert window2.export_page.mode_stack.currentWidget() is window2.export_page.manual_view
    finally:
        window2.close()


def test_settings_page_switch_controls_the_mode(tmp_path):
    _app, lib, settings, window, _out = _window(tmp_path, guided=True)
    try:
        page, wizard = _open_export(window, _book(tmp_path, lib))
        window.open_settings()
        window.settings_page.guided_export.setChecked(False)
        window.settings_page.save_settings()
        assert settings.value('export/guided', True, bool) is False
        assert page.mode_stack.currentWidget() is page.manual_view
    finally:
        window.close()


def test_ereader_route_exports_and_commits_settings_only_at_the_end(tmp_path):
    _app, lib, _settings, window, out = _window(tmp_path)
    try:
        book = _book(tmp_path, lib)
        page, wizard = _open_export(window, book)
        settings_file = Path(book.path) / 'export' / 'settings.json'
        before = settings_file.read_bytes() if settings_file.exists() else None
        wizard.purpose_cards['ereader'].click()
        wizard.go_next(); assert wizard.step == 'check'
        wizard.go_next(); assert wizard.step == 'content'
        wizard.go_next(); assert wizard.step == 'appearance'
        wizard.template_cards['literary'].click()
        wizard.go_next(); assert wizard.step == 'export'
        current = settings_file.read_bytes() if settings_file.exists() else None
        assert current == before, 'a wizard draft must not be written before the export'
        wizard.go_next()
        assert wizard.step == 'done'
        assert (out / 'haven.epub').exists()
        saved = json.loads(settings_file.read_text(encoding='utf-8'))
        assert saved['purpose'] == 'ereader' and saved['format'] == 'epub' and saved['epub']['template'] == 'literary'
        assert wizard.done_open_file.isVisibleTo(wizard)
    finally:
        window.close()


def test_successful_export_does_not_claim_settings_were_saved_when_persist_fails(tmp_path, monkeypatch):
    _app, lib, _settings, window, out = _window(tmp_path)
    try:
        page, wizard = _open_export(window, _book(tmp_path, lib))
        wizard.purpose_cards['website'].click()
        wizard.go_next(); wizard.go_next(); wizard.go_next()
        assert wizard.step == 'export'
        monkeypatch.setattr(page, 'persist_settings_dict', lambda _settings: False)
        wizard.go_next()
        assert wizard.step == 'done'
        assert (out / 'haven.md').exists()
        assert 'niet voor het boek worden onthouden' in wizard.done_detail.text().lower()
    finally:
        window.close()


def test_switching_to_manual_halfway_discards_the_draft(tmp_path):
    _app, lib, _settings, window, _out = _window(tmp_path)
    try:
        book = _book(tmp_path, lib)
        page, wizard = _open_export(window, book)
        settings_file = Path(book.path) / 'export' / 'settings.json'
        wizard.purpose_cards['print'].click()
        wizard.go_next(); wizard.go_next(); wizard.go_next()
        assert wizard.step == 'appearance'
        wizard.template_cards['modern'].click()
        before = settings_file.read_bytes() if settings_file.exists() else None
        page.manual_mode_button.click()
        after = settings_file.read_bytes() if settings_file.exists() else None
        assert before == after
        assert page.pdf_template_combo.currentData() != 'modern'
        page.guided_mode_button.click()
        assert wizard.step == 'purpose'
    finally:
        window.close()


def test_blocking_check_sends_to_media_and_rechecks_on_return(tmp_path):
    _app, lib, _settings, window, _out = _window(tmp_path)
    try:
        book = _book(tmp_path, lib)
        image = QImage(40, 30, QImage.Format_RGB32); image.fill(QColor('#335577')); image.save(str(tmp_path / 'kaart.png'))
        asset = MediaStore(lib).import_image(book, tmp_path / 'kaart.png'); book = lib.load_book(book.path); lib.track_book(book)
        chapter = [c for s in book.sections for c in s.chapters][0]
        lib.save_chapter(book, chapter, 'Tekst\n' + build_image_markdown('../' + asset.file, 'kaart') + '\nmeer')
        book = lib.load_book(book.path); lib.track_book(book)
        missing = Path(book.path) / asset.file
        data = missing.read_bytes(); missing.unlink()
        page, wizard = _open_export(window, book)
        wizard.purpose_cards['ereader'].click(); wizard.go_next()
        assert wizard.step == 'check'
        assert not wizard.next_button.isEnabled()
        assert any(item.key == 'missing_assets' for item in wizard.report.items)
        texts = ' '.join(label.text() for label in wizard.check_page.findChildren(type(wizard.hint_label)))
        assert 'assets/' not in texts, 'internal asset paths must not be shown to writers'
        wizard._first_issue_button.click()
        assert window.stack.currentWidget() is window.media_manager_page
        missing.write_bytes(data)
        window.show_export(); QApplication.processEvents()
        assert wizard.step == 'check'
        assert wizard.next_button.isEnabled()
    finally:
        window.close()


def test_share_route_leaves_out_history_and_conversation(tmp_path):
    _app, lib, _settings, window, out = _window(tmp_path)
    try:
        page, wizard = _open_export(window, _book(tmp_path, lib, chat=True))
        wizard.purpose_cards['share'].click()
        assert wizard.steps == ('purpose', 'check', 'content', 'export')
        wizard.go_next(); wizard.go_next()
        assert wizard.step == 'content'
        assert not wizard.chat_box.isChecked() and not wizard.history_box.isChecked()
        wizard.go_next(); wizard.go_next()
        assert wizard.step == 'done'
        package = out / 'haven.qwbook'
        with zipfile.ZipFile(package) as archive:
            names = archive.namelist()
        assert not any('ai_chat' in name for name in names)
        assert not any(name.startswith('history/') for name in names)
        assert not wizard.done_open_file.isVisibleTo(wizard)
        assert wizard.done_open_folder.isVisibleTo(wizard)
    finally:
        window.close()


def test_backup_route_keeps_history_and_conversation(tmp_path):
    _app, lib, _settings, window, out = _window(tmp_path)
    try:
        page, wizard = _open_export(window, _book(tmp_path, lib, chat=True))
        wizard.purpose_cards['backup'].click()
        wizard.go_next(); wizard.go_next()
        assert wizard.chat_box.isChecked() and wizard.history_box.isChecked()
        wizard.go_next(); wizard.go_next()
        with zipfile.ZipFile(out / 'haven.qwbook') as archive:
            names = archive.namelist()
        assert 'book/.quietwriter/ai_chat.json' in names
        assert any(name.startswith('history/') for name in names)
    finally:
        window.close()


def test_keyboard_moves_the_purpose_choice_and_enter_continues(tmp_path):
    _app, lib, _settings, window, _out = _window(tmp_path)
    try:
        page, wizard = _open_export(window, _book(tmp_path, lib))
        first = wizard.purpose_cards['ereader']
        first.click(); first.setFocus()
        QTest.keyClick(first, Qt.Key_Right)
        assert wizard.purpose_id == 'print'
        QTest.keyClick(wizard.purpose_cards['print'], Qt.Key_Return)
        assert wizard.step == 'check'
    finally:
        window.close()


def test_wizard_does_not_grow_the_main_window(tmp_path):
    _app, lib, _settings, window, _out = _window(tmp_path)
    try:
        window.resize(853, 467)
        window.show()
        page, wizard = _open_export(window, _book(tmp_path, lib))
        for purpose in ('ereader', 'share'):
            wizard.restart()
            wizard.purpose_cards[purpose].click()
            for _ in range(3):
                wizard.go_next(); QApplication.processEvents()
                hint = window.minimumSizeHint()
                assert hint.width() <= 1100 and hint.height() <= 700
    finally:
        window.close()


def test_opening_another_book_resets_the_wizard(tmp_path):
    _app, lib, _settings, window, _out = _window(tmp_path)
    try:
        book = _book(tmp_path, lib)
        page, wizard = _open_export(window, book)
        wizard.purpose_cards['word'].click(); wizard.go_next()
        assert wizard.step == 'check'
        other = lib.create_book('Ander boek'); lib.track_book(other)
        window.open_book(other); window.show_export(); QApplication.processEvents()
        assert wizard.book.id == other.id and wizard.step == 'purpose'
    finally:
        window.close()


def test_wizard_navigation_bar_is_above_scroll_content_and_choice_does_not_auto_advance(tmp_path):
    _app, lib, _settings, window, _out = _window(tmp_path)
    try:
        _page, wizard = _open_export(window, _book(tmp_path, lib))
        layout = wizard.layout()
        action_index = layout.indexOf(wizard.action_bar)
        scroll_index = layout.indexOf(wizard.scroll)
        assert action_index >= 0 and scroll_index >= 0
        assert action_index < scroll_index, 'wizard navigation must be visible before the scrollable content'

        wizard.purpose_cards['ereader'].click()
        assert wizard.step == 'purpose', 'selecting a card must not auto-advance the wizard'
        assert wizard.next_button.isEnabled()
    finally:
        window.close()
