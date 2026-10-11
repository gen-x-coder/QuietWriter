"""Regression coverage for Claude's dev.38 R1/R2 and main-window shutdown R3."""
import os
import time
from pathlib import Path


def test_trash_dates_with_and_without_collision_suffix(tmp_path):
    from quietwriter.storage import Library
    for name in ('20261001-120000__boek-abc', '20261001-120000-2__boek-abc'):
        folder = tmp_path / name
        folder.mkdir()
        os.utime(folder, (1600000000, 1600000000))
        stamp = Library._trash_deleted_time(folder)
        from datetime import datetime
        assert datetime.fromtimestamp(stamp).strftime('%Y%m%d-%H%M%S') == '20261001-120000'


def test_partial_copy_of_old_files_is_not_pruned(tmp_path):
    from quietwriter.storage import Library
    lib = Library(tmp_path / 'library')
    book = lib.create_book('Regressieboek')
    root = lib._history_root(book)
    partial = root / '.still-copying.partial'
    partial.mkdir()
    marker = partial / '.started'
    marker.touch()
    old_file = partial / 'book.json'
    old_file.write_text('old-file')
    old = time.time() - 3*86400
    os.utime(old_file, (old, old))
    lib._cleanup_partial_versions(book)
    assert partial.exists()
    # Unmarked partials may belong to another machine: also never remove them.
    marker.unlink()
    lib._cleanup_partial_versions(book)
    assert partial.exists()


def test_main_window_clears_pending_spelling_after_saves():
    path = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    end = path[path.index('    def closeEvent(self, event):'):path.index('    def restore_state(self):')]
    assert end.index('if self.editor_page.save() is False') < end.index('self.editor_page.spell._suggest_pool.clear()')
    assert end.index('self.editor_page.spell._suggest_pool.clear()') < end.index('super().closeEvent(event)')
