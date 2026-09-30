import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_splash_tracks_real_startup_instead_of_fixed_timeout():
    app = read('quietwriter/app.py')
    splash = read('quietwriter/ui/splash.py')
    assert 'splash.exec()' not in app
    assert 'singleShot(450' not in app
    assert 'win=MainWindow(settings,library,models)' in app
    assert 'win.show()' in app
    assert 'splash.finish_when_ready(win)' in app
    assert 'handle.isExposed()' in splash
    assert 'Qt.WindowStaysOnTopHint' in splash


def test_splash_has_single_identity_status_progress_and_footer():
    source = read('quietwriter/ui/splash.py')
    assert "tr('splash.tagline'" in source
    assert "splashEyebrow" not in source
    assert "APP_NAME.upper()" not in source
    assert 'QProgressBar' in source
    assert "tr('splash.version'" in source
    assert "tr('splash.copyright'" in source
    assert "self.status.setText(tr('splash.ready'" in source


def test_about_page_is_compact_with_privacy_copyright_and_technical_context():
    source = read('quietwriter/ui/about_page.py')
    assert "hero.setObjectName('aboutHero')" in source
    assert "about.principles.title" not in source
    assert "about.maker.title" not in source
    assert "tr('about.privacy.title'" in source
    assert "'about.privacy.text'" in source
    assert "'about.technical.title'" in source
    assert "'about.runtime'" in source
    assert "'about.copyright'" in source
    assert 'LicenseCard' in source


def test_startup_and_about_locale_keys_exist_in_both_languages():
    required = {
        'splash.tagline', 'splash.fonts', 'splash.workspace', 'splash.ollama',
        'splash.interface', 'splash.window', 'splash.ready', 'splash.version',
        'splash.copyright', 'about.tagline', 'about.product.title',
        'about.privacy.title', 'about.privacy.text', 'about.technical.title',
        'about.runtime', 'about.copyright',
    }
    for language in ('nl', 'en'):
        data = json.loads(read(f'quietwriter/locales/{language}.json'))
        missing = required - set(data)
        assert not missing, f'{language} mist locale-keys: {sorted(missing)}'
