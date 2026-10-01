from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THEMES = ROOT / 'quietwriter' / 'themes.py'
GUIDE = ROOT / 'documents' / 'dev' / 'UI_GUIDE.md'


def _theme_source():
    return THEMES.read_text(encoding='utf-8')


def test_global_buttons_have_explicit_focus_and_pressed_states():
    source = _theme_source()
    assert 'QPushButton:focus' in source
    assert 'QPushButton:pressed' in source
    assert 'QPushButton#primaryButton:focus' in source
    assert 'QPushButton#primaryButton:pressed' in source
    assert 'QPushButton#dangerButton:pressed' in source


def test_borderless_button_families_reserve_focus_border():
    source = _theme_source()
    for selector in (
        'QPushButton#railButton',
        'QPushButton#navButton',
        'QPushButton#compactButton',
        'QPushButton#flyoutButton',
        'QPushButton#formatButton',
        'QPushButton#planningNavButton',
        'QPushButton#settingsNavButton',
        'QPushButton#relationChip',
    ):
        start = source.index(selector + ' {{')
        block = source[start:source.index('}}', start)]
        assert 'border: 1px solid transparent' in block


def test_keyboard_focus_covers_choice_and_item_views():
    source = _theme_source()
    assert 'QCheckBox:focus, QRadioButton:focus' in source
    assert 'QListWidget:focus, QTreeWidget:focus' in source
    assert "border-color: {t['focus']}" in source


def test_ui_guide_defines_cursor_and_tab_semantics():
    source = GUIDE.read_text(encoding='utf-8')
    assert 'Cursorsemantiek volgt desktopconventies' in source
    assert 'Tab en Shift+Tab volgen de visuele/logische leesvolgorde' in source
    assert 'NoFocus' in source
