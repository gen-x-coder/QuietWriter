from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_about_navigation_follows_spelling_without_preceding_stretch():
    source = read('quietwriter/ui/settings_page.py')
    spell = source.index("self._add_settings_category(nav_lay, tr('settings.spelling'")
    about = source.index("self._add_settings_category(nav_lay, tr('settings.about'")
    stretch = source.index('nav_lay.addStretch(1)', about)
    between = source[spell:about]
    assert 'nav_lay.addStretch(1)' not in between
    assert spell < about < stretch


def test_removed_about_sections_do_not_return():
    source = read('quietwriter/ui/about_page.py')
    assert 'AboutInfoCard' not in source
    assert 'about.principles.title' not in source
    assert 'about.maker.title' not in source
    assert 'about.technical.title' in source
