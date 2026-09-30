from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(*parts):
    return (ROOT.joinpath(*parts)).read_text(encoding='utf-8')


def test_manuscript_viewport_keeps_text_cursor():
    source = _source('quietwriter', 'ui', 'manuscript_editor.py')
    assert 'self.viewport().setCursor(Qt.IBeamCursor)' in source
    assert 'self.viewport().unsetCursor()' not in source
    assert 'self.scene_delete_button.setCursor(Qt.PointingHandCursor)' in source


def test_editor_specific_button_states_are_explicit():
    source = _source('quietwriter', 'themes.py')
    for selector in (
        'QPushButton#secondaryButton:hover',
        'QPushButton#secondaryButton:pressed',
        'QPushButton#railButton:pressed',
        'QPushButton#navButton:pressed',
        'QPushButton#compactButton:hover',
        'QPushButton#compactButton:pressed',
        'QPushButton#suggestionButton:pressed',
        'QPushButton#restoreButton:focus',
        'QPushButton#historyExitButton:pressed',
    ):
        assert selector in source
    assert 'QFrame#insertChoiceCard:hover' not in source


def test_add_flyout_and_right_panels_have_escape_paths():
    source = _source('quietwriter', 'ui', 'editor_page.py')
    assert 'chapter_btn.setFocus()' in source
    assert 'QShortcut(QKeySequence(Qt.Key_Escape), popup)' in source
    assert 'self.add_content_button.setFocus()' in source
    assert 'QShortcut(QKeySequence(Qt.Key_Escape), self.right)' in source
    assert 'self._close_right_panel_from_keyboard' in source


def test_contents_tree_has_explicit_keyboard_activation():
    tree = _source('quietwriter', 'ui', 'manuscript_tree.py')
    page = _source('quietwriter', 'ui', 'editor_page.py')
    assert 'keyboardActivated = Signal(object)' in tree
    assert 'Qt.Key_Return, Qt.Key_Enter' in tree
    assert 'self.tree.keyboardActivated.connect(self.tree_keyboard_activated)' in page
    assert "if data[0] in ('chapter', 'publication')" in page


def test_editor_and_search_define_logical_tab_order():
    page = _source('quietwriter', 'ui', 'editor_page.py')
    search = _source('quietwriter', 'ui', 'search_panel.py')
    spell = _source('quietwriter', 'ui', 'spell_panel.py')
    assert 'def _configure_tab_order(self):' in page
    assert 'self.add_content_button' in page and 'self.chapter_title' in page
    assert 'self.scope, self.query, self.case_sensitive, self.whole_word' in search
    assert 'QWidget.setTabOrder(first, second)' in search
    assert 'list(self.suggestions._buttons)' in spell


def test_undo_redo_state_and_accessibility_are_synchronized():
    page = _source('quietwriter', 'ui', 'editor_page.py')
    main = _source('quietwriter', 'ui', 'main_window.py')
    assert 'self.editor.undoAvailable.connect(self._schedule_undo_redo_sync)' in page
    assert 'self.editor.redoAvailable.connect(self._schedule_undo_redo_sync)' in page
    assert 'def _sync_undo_redo(self):' in page
    assert 'setAccessibleName' in page
    assert 'b.setToolTip(tip); b.setAccessibleName(tip)' in main
    assert 'b.setToolTip(label); b.setAccessibleName(label)' in main
