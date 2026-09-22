from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_main_and_nested_page_stacks_ignore_hidden_page_size_hints_by_design():
    expected = [
        ROOT / 'quietwriter' / 'ui' / 'main_window.py',
        ROOT / 'quietwriter' / 'ui' / 'settings_page.py',
        ROOT / 'quietwriter' / 'ui' / 'editor_page.py',
        ROOT / 'quietwriter' / 'ui' / 'planning' / 'planning_page.py',
        ROOT / 'quietwriter' / 'ui' / 'planning' / 'characters_page.py',
        ROOT / 'quietwriter' / 'ui' / 'publication' / 'publication_editor.py',
    ]
    for path in expected:
        source = path.read_text(encoding='utf-8')
        assert 'CurrentPageStack' in source, path
        assert 'QStackedWidget()' not in source, path


def test_settings_pages_are_scroll_viewports_with_footer_outside_the_stack():
    source = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    assert "scroll.setObjectName('settingsContentScroll')" in source
    assert 'scroll.setWidgetResizable(True)' in source
    assert 'scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)' in source
    assert 'page_layout.addWidget(scroll, 1)' in source
    # Save belongs to SettingsPage itself, after the body, not inside each long page.
    assert "self.save_btn = QPushButton" in source
    assert "root.addLayout(buttons)" in source


def test_no_custom_window_geometry_clamp_returned():
    source = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    assert "self.settings.setValue('geometry', self.saveGeometry())" in source
    assert 'self.restoreGeometry(g)' in source
    assert 'def _safe_window_geometry' not in source
    assert 'window_geometry_v2' not in source
    assert '.setGeometry(' not in source
