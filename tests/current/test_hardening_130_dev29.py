from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_book_open_has_real_loading_feedback_without_cloud_detection():
    src = read('quietwriter/ui/main_window.py')
    assert "tr('book.loading', 'Boek laden…')" in src
    assert 'QProgressDialog' in src
    helper = src[src.index('def _show_book_loading'):src.index('def open_book')]
    assert 'dropbox' not in helper.casefold()
    assert 'onedrive' not in helper.casefold()


def test_integrity_is_explicit_and_reports_busy_state():
    src = read('quietwriter/ui/integrity_page.py')
    set_book = src[src.index('def set_book'):src.index('def adopt_book')]
    assert 'self.refresh()' not in set_book
    assert "'Integriteit controleren'" in src
    assert "'Controleren...'" in src
    assert 'self.refresh_button.setEnabled(False)' in src


def test_manuscript_tree_uses_theme_accent_not_os_highlight():
    src = read('quietwriter/ui/manuscript_tree.py')
    paint = src[src.index('def paintEvent'):]
    assert "QColor(theme['accent'])" in paint
    assert 'QPalette.Highlight' not in paint


def test_normal_ai_pages_do_not_show_source_paths():
    for rel in ('quietwriter/ui/persona_page.py', 'quietwriter/ui/book_profile_page.py', 'quietwriter/ui/book_memory_page.py'):
        src = read(rel)
        # Error/recovery paths may still mention technical files, but the normal
        # page construction must no longer add a visible source-file explanation.
        before_body = src[:src.index('body = QHBoxLayout')]
        assert 'Bronbestand:' not in before_body


def test_typing_has_explicit_idle_and_whitespace_undo_boundaries():
    src = read('quietwriter/ui/manuscript_editor.py')
    assert 'self._typing_idle_timer.setInterval(900)' in src
    assert 'if typed.isspace():' in src
    assert 'self._format_timer.setInterval(1000)' in src


def test_test_cleanup_preserves_preexisting_qttest_root():
    src = read('tests/conftest.py')
    assert 'qt_test_root_existed = qt_test_root.exists()' in src
    assert "and not qt_test_root_existed" in src
