import os
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QMessageBox

from quietwriter.fragment_store import FragmentStore
from quietwriter.storage import Library
from quietwriter.ui.main_window import MainWindow


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _settings(path: Path):
    settings = QSettings(str(path), QSettings.IniFormat)
    settings.setValue('spell_enabled', False)
    settings.setValue('ai_enabled', False)
    settings.setValue('advanced_options', False)
    return settings


def _window_with_book(tmp_path: Path, source: str):
    workspace = tmp_path / 'workspace'
    lib = Library(workspace)
    book = lib.create_book('Testboek')
    chapter = next(c for sec in book.sections for c in sec.chapters)
    chapter_path = Path(book.path) / chapter.file
    chapter_path.write_text(source, encoding='utf-8')
    book = lib.load_book(book.path)
    window = MainWindow(_settings(tmp_path / 'settings.ini'), lib, [])
    window.open_book(book)
    return window, chapter_path


def test_copy_selection_runs_real_qt_path_and_does_not_modify_manuscript(app, tmp_path):
    source = 'Voor **vet woord** na.\n'
    window, chapter_path = _window_with_book(tmp_path, source)
    try:
        before = chapter_path.read_bytes()
        editor = window.editor_page.editor
        start = source.index('vet woord')
        cursor = editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + len('vet woord'), QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)

        assert window.editor_page.copy_selection_to_darlings() is True
        fragments = window.darlings_page.store.list_fragments()
        assert len(fragments) == 1
        assert fragments[0].text == '**vet woord**'
        assert fragments[0].source_book_title == 'Testboek'
        assert chapter_path.read_bytes() == before
    finally:
        window.close()


def test_search_saves_pending_metadata_before_refresh(app, tmp_path):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        fragment = window.darlings_page.store.create('Fragmenttekst')
        window.darlings_page.add_fragment(fragment)
        window.darlings_page.title_edit.setText('Mijn lokale titel')
        assert window.darlings_page.dirty is True

        # textChanged invokes refresh(); the pending title must be committed first.
        window.darlings_page.search.setText('bestaat-niet')
        saved = window.darlings_page.store.load(fragment.id)
        assert saved.title == 'Mijn lokale titel'
    finally:
        window.close()


def test_insert_at_cursor_keeps_fragment_and_is_one_undo_step(app, tmp_path):
    source = 'Voor na.\n'
    window, _chapter_path = _window_with_book(tmp_path, source)
    try:
        fragment = window.darlings_page.store.create('**bewaarde tekst**')
        page = window.darlings_page
        page.add_fragment(fragment)

        editor = window.editor_page.editor
        cursor = editor.textCursor()
        cursor.setPosition(source.index('na.'))
        editor.setTextCursor(cursor)
        before = editor.source_text()

        assert page.insert_at_cursor() is True
        assert editor.source_text() == 'Voor **bewaarde tekst**na.\n'
        assert len(page.store.list_fragments()) == 1

        editor.undo()
        assert editor.source_text() == before
    finally:
        window.close()


def test_insert_at_cursor_does_not_replace_existing_selection(app, tmp_path):
    source = 'Voor SELECTIE na.\n'
    window, _chapter_path = _window_with_book(tmp_path, source)
    try:
        fragment = window.darlings_page.store.create('*fragment*')
        window.darlings_page.add_fragment(fragment)
        editor = window.editor_page.editor
        cursor = editor.textCursor()
        start = source.index('SELECTIE')
        cursor.setPosition(start)
        cursor.setPosition(start + len('SELECTIE'), QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)
        active_end = cursor.position()

        assert window.darlings_page.insert_at_cursor() is True
        expected = source[:active_end] + '*fragment*' + source[active_end:]
        assert editor.source_text() == expected
        assert 'SELECTIE' in editor.source_text()
    finally:
        window.close()


def test_external_conflict_can_choose_disk_without_later_silent_overwrite(app, tmp_path, monkeypatch):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        page = window.darlings_page
        fragment = page.store.create('Fragmenttekst', title='Origineel', note='oud')
        page.add_fragment(fragment)
        page.title_edit.setText('LOKAAL')
        page.note_edit.setPlainText('lokale notitie')

        other = FragmentStore(page.store.root)
        disk = other.load(fragment.id)
        other.update_metadata(
            fragment.id, expected_revision=disk.revision,
            title='LAPTOP', note='notitie laptop', tags=['extern'],
        )
        monkeypatch.setattr(page, '_choose_external_conflict', lambda current: 'disk')

        assert page.save_metadata() is True
        assert page.title_edit.text() == 'LAPTOP'
        assert page.note_edit.toPlainText() == 'notitie laptop'
        assert page.dirty is False

        # Subsequent silent save routes have nothing pending and cannot overwrite it.
        page.search.setText('x')
        saved = page.store.load(fragment.id)
        assert saved.title == 'LAPTOP'
        assert saved.note == 'notitie laptop'
        assert saved.tags == ('extern',)
    finally:
        window.close()


def test_external_conflict_can_explicitly_keep_local_values(app, tmp_path, monkeypatch):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        page = window.darlings_page
        fragment = page.store.create('Fragmenttekst', title='Origineel', note='oud')
        page.add_fragment(fragment)
        page.title_edit.setText('LOKAAL')
        page.note_edit.setPlainText('lokale notitie')
        page.tags_edit.setText('mijn-tag')

        other = FragmentStore(page.store.root)
        disk = other.load(fragment.id)
        other.update_metadata(
            fragment.id, expected_revision=disk.revision,
            title='LAPTOP', note='notitie laptop', tags=['extern'],
        )
        monkeypatch.setattr(page, '_choose_external_conflict', lambda current: 'local')

        assert page.save_metadata() is True
        saved = page.store.load(fragment.id)
        assert saved.title == 'LOKAAL'
        assert saved.note == 'lokale notitie'
        assert saved.tags == ('mijn-tag',)
        assert page.dirty is False
    finally:
        window.close()


def test_external_conflict_cancel_keeps_local_fields_and_does_not_write(app, tmp_path, monkeypatch):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        page = window.darlings_page
        fragment = page.store.create('Fragmenttekst', title='Origineel', note='oud')
        page.add_fragment(fragment)
        page.title_edit.setText('LOKAAL')
        page.note_edit.setPlainText('lokale notitie')

        other = FragmentStore(page.store.root)
        disk = other.load(fragment.id)
        other.update_metadata(
            fragment.id, expected_revision=disk.revision,
            title='LAPTOP', note='notitie laptop', tags=['extern'],
        )
        monkeypatch.setattr(page, '_choose_external_conflict', lambda current: 'cancel')

        assert page.save_metadata() is False
        assert page.title_edit.text() == 'LOKAAL'
        assert page.note_edit.toPlainText() == 'lokale notitie'
        assert page.dirty is True
        saved = page.store.load(fragment.id)
        assert saved.title == 'LAPTOP'
        assert saved.note == 'notitie laptop'
    finally:
        # Resolve the pending conflict for a clean close without a dialog.
        monkeypatch.setattr(page, '_choose_external_conflict', lambda current: 'disk')
        page.save_metadata()
        window.close()


def test_cancelled_conflict_disables_search_until_resolved(app, tmp_path, monkeypatch):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        page = window.darlings_page
        fragment = page.store.create('Fragmenttekst', title='Origineel', note='oud')
        page.add_fragment(fragment)
        page.title_edit.setText('LOKAAL')

        other = FragmentStore(page.store.root)
        disk = other.load(fragment.id)
        other.update_metadata(
            fragment.id, expected_revision=disk.revision,
            title='LAPTOP', note='notitie laptop', tags=['extern'],
        )
        monkeypatch.setattr(page, '_choose_external_conflict', lambda current: 'cancel')

        assert page.save_metadata() is False
        assert page._conflict_pending is True
        assert page.search.isEnabled() is False
        assert page.tag_filter.isEnabled() is False
        page.search.setText('abc')
        saved = page.store.load(fragment.id)
        assert saved.title == 'LAPTOP'

        monkeypatch.setattr(page, '_choose_external_conflict', lambda current: 'disk')
        assert page.save_metadata() is True
        assert page._conflict_pending is False
        assert page.search.isEnabled() is True
        assert page.tag_filter.isEnabled() is True
    finally:
        window.close()


def test_move_fragment_to_trash_from_darlings_page(app, tmp_path, monkeypatch):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        page = window.darlings_page
        fragment = page.store.create('Fragmenttekst', title='Weg ermee')
        page.add_fragment(fragment)
        monkeypatch.setattr(page, '_confirm_move_to_trash', lambda: True)

        assert page.move_current_to_trash() is True
        assert page.store.list_fragments() == []
        trashed = page.store.list_trashed()
        assert len(trashed) == 1
        assert trashed[0][1].id == fragment.id
    finally:
        window.close()


def test_cut_selection_creates_fragment_and_removes_text_in_one_undo_step(app, tmp_path):
    source = 'Voor **vet woord** na.\n'
    window, chapter_path = _window_with_book(tmp_path, source)
    try:
        editor = window.editor_page.editor
        start = source.index('woord')
        cursor = editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + len('woord'), QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)

        assert window.editor_page.cut_selection_to_darlings() is True
        fragments = window.darlings_page.store.list_fragments()
        assert len(fragments) == 1
        assert fragments[0].text == '**woord**'
        assert 'woord' not in editor.source_text()
        assert '**vet **' in editor.source_text()

        editor.undo()
        assert editor.source_text() == source
        assert len(window.darlings_page.store.list_fragments()) == 1
    finally:
        window.close()


def test_cut_fragment_write_failure_leaves_manuscript_untouched(app, tmp_path, monkeypatch):
    source = 'Voor selectie na.\n'
    window, _chapter_path = _window_with_book(tmp_path, source)
    try:
        editor = window.editor_page.editor
        start = source.index('selectie')
        cursor = editor.textCursor(); cursor.setPosition(start); cursor.setPosition(start + 8, QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)
        monkeypatch.setattr(window.darlings_page.store, 'create', lambda *a, **k: (_ for _ in ()).throw(OSError('disk vol')))
        monkeypatch.setattr(QMessageBox, 'critical', lambda *a, **k: QMessageBox.Ok)
        assert window.editor_page.cut_selection_to_darlings() is False
        assert editor.source_text() == source
    finally:
        window.close()


def test_fragment_is_restorable_from_trash_page(app, tmp_path, monkeypatch):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        fragment = window.darlings_page.store.create('Bewaar mij', title='Herstelbaar')
        window.darlings_page.store.move_to_trash(fragment.id)
        window.trash.refresh()
        fragment_items = [window.trash.list.item(i) for i in range(window.trash.list.count())
                          if window.trash.list.item(i).data(Qt.UserRole).get('kind') == 'fragment']
        assert len(fragment_items) == 1
        fragment_items[0].setSelected(True)
        window.trash.restore_selected()
        assert window.darlings_page.store.load(fragment.id).text == 'Bewaar mij'
    finally:
        window.close()


def test_darlings_page_shows_book_and_chapter_origin_explicitly(app, tmp_path):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst om te bewaren.\n')
    try:
        editor = window.editor_page.editor
        source = editor.source_text()
        start = source.index('Tekst')
        cursor = editor.textCursor(); cursor.setPosition(start); cursor.setPosition(start + len('Tekst'), QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)
        assert window.editor_page.copy_selection_to_darlings() is True
        page = window.darlings_page
        assert page._loaded_fragment is not None
        assert page.source_book.text().startswith('Boek: ')
        assert page._loaded_fragment.source_book_title in page.source_book.text()
        assert page.source_chapter.text().startswith('Hoofdstuk: ')
        assert page._loaded_fragment.source_chapter_title in page.source_chapter.text()
        assert page.trash_button.text() == 'Naar prullenbak'
    finally:
        window.close()


def test_editor_darlings_right_panel_is_primary_copy_cut_route(app, tmp_path):
    window, _chapter_path = _window_with_book(tmp_path, 'Voor selectie na.\n')
    try:
        editor = window.editor_page.editor
        source = editor.source_text()
        start = source.index('selectie')
        cursor = editor.textCursor(); cursor.setPosition(start); cursor.setPosition(start + len('selectie'), QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)
        window.editor_page.darlings_actions.refresh()
        assert window.editor_page.darlings_actions.copy_button.isEnabled()
        assert window.editor_page.darlings_actions.cut_button.isEnabled()
        window.editor_page.show_darlings_actions()
        assert window.editor_page.right.currentWidget() is window.editor_page.darlings_actions
        window.editor_page.darlings_actions.copy_button.click()
        fragments = window.darlings_page.store.list_fragments()
        assert len(fragments) == 1
        assert fragments[0].text == 'selectie'
        assert editor.source_text() == source
    finally:
        window.close()


def test_opening_right_panels_preserves_existing_editor_selection(app, tmp_path, monkeypatch):
    window, _chapter_path = _window_with_book(tmp_path, 'Voor geselecteerde tekst na.\n')
    try:
        editor = window.editor_page.editor
        source = editor.source_text()
        start = source.index('geselecteerde tekst')
        cursor = editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + len('geselecteerde tekst'), QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)
        selected = editor.textCursor().selectedText()

        # AI is normally disabled in this fixture; enable it without triggering
        # a provider warmup so the panel-switch behaviour itself is tested.
        window.settings.setValue('ai_enabled', True)
        monkeypatch.setattr(window.editor_page.ai, 'ensure_warmup', lambda: None)

        openers = [
            window.editor_page.show_search,
            window.editor_page.show_darlings_actions,
            window.editor_page.show_insert_menu,
            window.editor_page.show_history,
            window.editor_page.show_chapter_context,
            window.editor_page.show_ai,
        ]
        for open_panel in openers:
            open_panel()
            assert editor.textCursor().selectedText() == selected, open_panel.__name__
    finally:
        window.close()


def test_darlings_uses_distinct_icon_from_bookshelf(app, tmp_path):
    window, _chapter_path = _window_with_book(tmp_path, 'Tekst.\n')
    try:
        assert window.bookshelf_button.property('iconName') == 'shelf'
        assert window.darlings_button.property('iconName') == 'darlings'
        assert window.darlings_tool_button.property('iconName') == 'darlings'
    finally:
        window.close()
