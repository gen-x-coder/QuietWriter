from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source(relative):
    return (ROOT / relative).read_text(encoding='utf-8')


def test_drag_guard_starts_before_qtreewidget_mouse_press_and_always_finishes():
    source = _source('quietwriter/ui/manuscript_tree.py')
    mouse_press = source[source.index('    def mousePressEvent'):source.index('    def mouseReleaseEvent')]
    start_drag = source[source.index('    def startDrag'):source.index('    def dragEnterEvent')]
    assert 'self._begin_drag_guard()' in mouse_press
    assert mouse_press.index('self._begin_drag_guard()') < mouse_press.index('super().mousePressEvent(event)')
    assert 'try:' in start_drag
    assert 'finally:' in start_drag
    assert 'drag.exec(Qt.MoveAction)' in start_drag
    assert 'self._schedule_drag_finish()' in start_drag
    assert 'dragStarted = Signal()' in source
    assert 'dragFinished = Signal()' in source


def test_handle_click_without_drag_releases_guard():
    source = _source('quietwriter/ui/manuscript_tree.py')
    release = source[source.index('    def mouseReleaseEvent'):source.index('    def startDrag')]
    assert 'armed_without_native_drag' in release
    assert 'self._schedule_drag_finish()' in release


def test_editor_pauses_both_autosave_paths_during_drag():
    source = _source('quietwriter/ui/editor_page.py')
    started = source[source.index('    def _on_tree_drag_started'):source.index('    def _on_tree_drag_finished')]
    finished = source[source.index('    def _on_tree_drag_finished'):source.index('    def _flush_deferred_tree_refresh')]
    assert 'self.autosave_timer.stop()' in started
    assert 'self.publication_editor.free_text.timer' in started
    assert 'publication_timer.stop()' in started
    assert 'self.autosave_timer.start(250)' in finished
    assert 'self.publication_editor.free_text.timer.start(250)' in finished


def test_populate_tree_coalesces_refresh_and_followup_until_drag_finished():
    source = _source('quietwriter/ui/editor_page.py')
    populate = source[source.index('    def populate_tree'):source.index('    def _populate_tree_now')]
    flush = source[source.index('    def _flush_deferred_tree_refresh'):source.index('    def populate_tree')]
    assert 'if self.tree.is_dragging:' in populate
    assert 'self._tree_refresh_pending = True' in populate
    assert 'self._tree_refresh_callbacks.append(after)' in populate
    assert 'self.tree.clear()' not in populate
    assert 'self._populate_tree_now()' in flush
    assert 'for callback in callbacks:' in flush


def test_save_conflict_and_title_rename_are_blocked_during_drag():
    source = _source('quietwriter/ui/editor_page.py')
    save = source[source.index('    def save(self):'):source.index('    def _handle_concurrency_issue')]
    rename = source[source.index('    def rename_current'):source.index('    def _book_chapter_ids')]
    resolve = source[source.index('    def _resolve_external_change'):source.index('    def _handle_verification_error')]
    persist = source[source.index('    def persist_publication_change'):source.index('    def _set_publication_context')]
    assert 'if self.tree.is_dragging:' in save
    assert 'self._save_pending_after_drag = True' in save
    assert 'if self.tree.is_dragging:' in rename
    assert 'self._rename_pending_after_drag = True' in rename
    assert 'if self.tree.is_dragging:' in resolve
    assert 'if self.tree.is_dragging:' in persist


def test_move_rebinds_current_chapter_after_deep_copy_commit():
    source = _source('quietwriter/ui/editor_page.py')
    move = source[source.index('    def move_chapter'):source.index('    def tree_context_menu')]
    assert 'current_chapter_id = self.chapter.id if self.chapter else None' in move
    assert 'self.book.sections = proposed' in move
    assert '_, rebound = self.find_chapter_in_book(current_chapter_id)' in move
    assert 'self.chapter = rebound' in move


def test_crash_logging_is_enabled_in_workspace_and_covers_python_and_native_failures():
    app = _source('quietwriter/app.py')
    logging_source = _source('quietwriter/crash_logging.py')
    assert "enable_crash_logging(root / 'logs' / 'crash.log')" in app
    assert 'faulthandler.enable(_LOG_HANDLE, all_threads=True)' in logging_source
    assert 'sys.excepthook = exception_hook' in logging_source
    assert 'threading.excepthook = thread_exception_hook' in logging_source


def test_main_window_does_not_close_or_replace_book_when_editor_save_is_deferred():
    source = _source('quietwriter/ui/main_window.py')
    assert 'if self.editor_page.close_book() is False:' in source
    assert 'if self.editor_page.load_book(live) is False:' in source
    assert 'live = self.library.touch_book(book)' in source
    close_event = source[source.index('    def closeEvent'):source.index('    def restore_state')]
    assert 'if self.editor_page.save() is False:' in close_event
    assert 'event.ignore()' in close_event
