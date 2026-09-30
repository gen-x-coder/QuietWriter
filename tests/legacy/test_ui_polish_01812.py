from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def _source(*parts):
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


def test_undo_redo_uses_document_state_and_post_format_sync():
    source = _source("quietwriter", "ui", "editor_page.py")
    assert "self.undo_redo_sync_timer" in source
    assert "document.isUndoAvailable()" in source
    assert "document.isRedoAvailable()" in source
    assert "self._schedule_undo_redo_sync()" in source
    assert "undo.clicked.connect(self._undo_editor)" in source
    assert "redo.clicked.connect(self._redo_editor)" in source


def test_search_results_navigate_on_single_click_and_keyboard_activation():
    source = _source("quietwriter", "ui", "search_panel.py")
    assert "self.results.itemClicked.connect(self._open_result_item)" in source
    assert "self.results.itemActivated.connect(self._open_result_item)" in source
    editor = _source("quietwriter", "ui", "editor_page.py")
    assert "self.select_tree_chapter(cid)" in editor[editor.index("def open_search_match"):editor.index("def search_next")]


def test_dragging_and_structural_rows_preserve_active_editor_selection():
    tree = _source("quietwriter", "ui", "manuscript_tree.py")
    assert "previous_current = self.currentItem()" in tree
    assert "structural_click" in tree
    assert "explicit_group_edit" in tree
    assert "preserve_current = self._drag_allowed" in tree
    page = _source("quietwriter", "ui", "editor_page.py")
    move = page[page.index("def move_chapter"):page.index("def tree_context_menu")]
    assert "current_chapter_id = self.chapter.id if self.chapter else None" in move
    assert "self.select_tree_chapter(current_chapter_id)" in move
    assert "self.select_tree_chapter(chapter_id)" not in move


def test_outline_dialog_and_confirmations_follow_app_locale():
    source = _source("quietwriter", "ui", "planning", "outline_page.py")
    assert "save_button.setText(tr('common.save', 'Opslaan'))" in source
    assert "cancel_button.setText(tr('common.cancel', 'Annuleren'))" in source
    assert "confirm(" in source
    assert "QMessageBox.question" not in source
    characters = _source("quietwriter", "ui", "planning", "characters_page.py")
    assert "QMessageBox.question" not in characters
    assert "confirm(self" in characters


def test_notes_have_explicit_save_action_with_dirty_state():
    source = _source("quietwriter", "ui", "planning", "notes_page.py")
    assert "self.save_button=QPushButton(tr('common.save', 'Opslaan'))" in source
    assert "self.save_button.setObjectName('primaryButton')" in source
    assert "self.save_button.setEnabled(True)" in source
    assert "self.save_button.setEnabled(False)" in source


def test_book_details_published_label_is_localized_but_metadata_stays_canonical():
    source = _source("quietwriter", "ui", "book_details.py")
    assert "self.published.addItem(tr('common.no', 'Nee'), 'No')" in source
    assert "self.published.addItem(tr('common.yes', 'Ja'), 'Yes')" in source
    assert "'published': self.published.currentData() or 'No'" in source
    assert "addItems(['No', 'Yes'])" not in source


def test_new_polish_strings_exist_in_both_locales():
    required = {
        "planning.outline.delete_confirm",
        "planning.notes.description",
        "book_details.field.published",
        "book_details.cover.choose",
        "book_details.trash_confirm",
    }
    for code in ("nl", "en"):
        data = json.loads(_source("quietwriter", "locales", f"{code}.json"))
        assert required <= data.keys()
