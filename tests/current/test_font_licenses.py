from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_bundled_font_licenses_contain_complete_ofl_11_text():
    files = sorted((ROOT / 'resources' / 'fonts').glob('*/OFL.txt'))
    assert len(files) == 4
    for path in files:
        text = path.read_text(encoding='utf-8')
        assert 'SIL OPEN FONT LICENSE Version 1.1' in text, path
        assert 'PERMISSION & CONDITIONS' in text, path
        assert 'TERMINATION' in text, path
        assert 'DISCLAIMER' in text, path
