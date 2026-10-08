from pathlib import Path


def test_bookdetails_does_not_own_writing_progress_opt_in():
    source = Path('quietwriter/ui/book_details.py').read_text(encoding='utf-8')
    assert 'progress_tracking' not in source
    assert "setValue('writing_progress_enabled'" not in source


def test_planning_popup_blocks_mouse_replay_and_empty_filler_is_transparent():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    theme = Path('quietwriter/themes.py').read_text(encoding='utf-8')
    assert 'Qt.WA_NoMouseReplay' in source
    assert "self.empty_filler.setObjectName('planningOverlayFiller')" in source
    assert 'QWidget#planningOverlayFiller' in theme
    assert 'background: transparent' in theme[theme.find('QWidget#planningOverlayFiller'):theme.find('QWidget#planningOverlayFiller') + 120]


def test_active_settings_are_threaded_into_editor_and_tree():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    editor = Path('quietwriter/ui/manuscript_editor.py').read_text(encoding='utf-8')
    tree = Path('quietwriter/ui/manuscript_tree.py').read_text(encoding='utf-8')
    assert 'ManuscriptEditor(settings=self.main.settings)' in source
    assert 'ManuscriptTree(settings=self.main.settings)' in source
    assert "settings or QSettings('QuietWriter', 'QuietWriter')" in editor
    assert "settings or QSettings('QuietWriter', 'QuietWriter')" in tree


def test_form_controls_ignore_wheel_without_focus():
    source = Path('quietwriter/ui/form_controls.py').read_text(encoding='utf-8')
    assert 'if not self.hasFocus()' in source
    assert 'event.ignore()' in source
    assert 'Qt.StrongFocus' in source
