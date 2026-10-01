from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'release' / 'stage'


def _prepare() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / 'tools' / 'prepare_release.py')],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_release_staging_is_allowlist_based_and_clean():
    _prepare()
    assert (STAGE / 'main.py').is_file()
    assert (STAGE / 'quietwriter' / 'app.py').is_file()
    assert (STAGE / 'packaging' / 'quietwriter.spec').is_file()
    assert (STAGE / 'tools' / 'fetch_bundled_fonts.py').is_file()
    assert (STAGE / 'tools' / 'fetch_dictionaries.py').is_file()
    assert (STAGE / 'documents' / 'licenses' / 'LICENSE').is_file()
    assert (STAGE / 'documents' / 'licenses' / 'THIRD_PARTY_LICENSES.md').is_file()

    forbidden_dirs = {'tests', 'ppm', '.git', '.github', '.venv', '__pycache__'}
    for path in STAGE.rglob('*'):
        assert not (set(path.relative_to(STAGE).parts) & forbidden_dirs), path
        assert not path.name.startswith('REVIEW_NOTES_'), path
        assert not path.name.startswith('QUIETWRITER_REVIEW_FINDINGS_'), path
        assert not path.name.startswith('TUSSENTIJDS_RAPPORT_'), path


def test_stage_manifest_matches_version_and_has_hashes():
    _prepare()
    data = json.loads((STAGE / 'STAGE_MANIFEST.json').read_text(encoding='utf-8'))
    assert data['product'] == 'QuietWriter'
    assert data['version'] == '1.0.0-rc1'
    assert data['files']
    assert all(item['path'] and len(item['sha256']) == 64 and item['bytes'] >= 0 for item in data['files'])


def test_stage_contains_font_metadata_but_not_downloaded_font_binaries():
    _prepare()
    font_root = STAGE / 'resources' / 'fonts'
    assert (font_root / 'font_manifest.json').is_file()
    assert len(list(font_root.rglob('OFL.txt'))) == 4
    assert not list(font_root.rglob('*.ttf'))
    assert not list(font_root.rglob('*.otf'))
