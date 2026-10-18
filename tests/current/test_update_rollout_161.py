"""1.6.1: eerst zelf testen, daarna pas bijwerken voor iedereen.

Zie documents/research/UPDATE_UITROL_ONDERZOEK.md. Wat hier NIET getest kan
worden: de echte GitHub-API en Velopack zelf (Windows-acceptatietest met een
pre-release, RELEASE_PROCESS.md).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from quietwriter import self_update
from quietwriter.self_update import (
    PILOT_MARKER, REPO_URL, build_source_and_options, is_pilot_copy, pilot_marker_candidates,
)

ROOT = Path(__file__).resolve().parents[2]


class FakeVelopack:
    class GithubSource:
        def __init__(self, url, token, prerelease):
            self.url, self.token, self.prerelease = url, token, prerelease

    class UpdateOptions:
        def __init__(self, allow_downgrade, max_deltas, channel=None):
            self.AllowVersionDowngrade = allow_downgrade
            self.MaximumDeltasBeforeFallback = max_deltas
            self.ExplicitChannel = channel


def _velopack_layout(root: Path) -> Path:
    (root / 'current').mkdir(parents=True)
    exe = root / 'current' / 'QuietWriter.exe'
    exe.write_bytes(b'')
    (root / 'Update.exe').write_bytes(b'')
    return exe


def test_normal_copy_reads_only_stable_releases_on_default_channel():
    source, options = build_source_and_options(FakeVelopack, override='', pilot=False)
    assert (source.url, source.token, source.prerelease) == (REPO_URL, None, False)
    assert options.ExplicitChannel is None
    assert options.AllowVersionDowngrade is False


def test_pilot_copy_reads_prereleases_and_pilot_feed():
    source, options = build_source_and_options(FakeVelopack, override='', pilot=True)
    assert source.prerelease is True and source.url == REPO_URL
    assert options.ExplicitChannel == 'pilot'
    assert options.AllowVersionDowngrade is False


def test_local_override_keeps_channel_of_the_copy():
    source, options = build_source_and_options(FakeVelopack, override=r'C:\QW\release\velopack', pilot=True)
    assert source == r'C:\QW\release\velopack'
    assert options.ExplicitChannel == 'pilot'
    source, options = build_source_and_options(FakeVelopack, override=r'C:\QW\release\velopack', pilot=False)
    assert options.ExplicitChannel is None


def test_github_override_uses_github_source_with_prereleases_for_pilot():
    url = 'https://github.com/gen-x-coder/QuietWriter-test'
    source, _ = build_source_and_options(FakeVelopack, override=url, pilot=True)
    assert source.url == url and source.prerelease is True
    source, _ = build_source_and_options(FakeVelopack, override=url, pilot=False)
    assert source.prerelease is False


def test_pilot_marker_next_to_update_exe_is_found():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        exe = _velopack_layout(root)
        assert not is_pilot_copy(exe)
        (root / PILOT_MARKER).write_bytes(b'')
        assert is_pilot_copy(exe)
        assert pilot_marker_candidates(exe)[0] == (root / PILOT_MARKER).resolve()


def test_pilot_marker_inside_current_does_not_count():
    # ChatGPT-review 1.6.1 #4: current\ wordt bij een update vervangen; een
    # marker daar zou na één update stil verdwijnen.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        exe = _velopack_layout(root)
        (root / 'current' / PILOT_MARKER).write_bytes(b'')
        assert not is_pilot_copy(exe)


def test_copy_without_velopack_layout_is_never_a_pilot_copy():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        exe = root / 'QuietWriter.exe'
        exe.write_bytes(b'')
        (root / PILOT_MARKER).write_bytes(b'')
        assert not is_pilot_copy(exe)
        (root / 'current').mkdir()
        assert pilot_marker_candidates(root / 'current' / 'QuietWriter.exe') == []   # geen Update.exe


def test_source_run_is_never_a_pilot_copy(monkeypatch):
    monkeypatch.delattr(self_update.sys, 'frozen', raising=False)
    assert pilot_marker_candidates() == []
    assert is_pilot_copy() is False


def test_selfupdater_passes_options_to_velopack(monkeypatch):
    created = {}

    class FakeManager:
        def __init__(self, source, options=None):
            created['source'], created['options'] = source, options

    fake = SimpleNamespace(GithubSource=FakeVelopack.GithubSource, UpdateOptions=FakeVelopack.UpdateOptions,
                           UpdateManager=FakeManager)
    monkeypatch.setitem(__import__('sys').modules, 'velopack', fake)
    monkeypatch.delenv(self_update.SOURCE_OVERRIDE_ENV, raising=False)
    monkeypatch.setattr(self_update, 'is_pilot_copy', lambda *a: True)
    updater = self_update.SelfUpdater()
    assert updater.available and updater.pilot
    assert created['options'].ExplicitChannel == 'pilot'
    assert created['source'].prerelease is True


def test_build_makes_pilot_feed_and_warns_against_vpk_upload():
    build = (ROOT / 'build_exe.cmd').read_text(encoding='utf-8')
    assert 'releases.pilot.json' in build
    assert 'releases.pilot.json ontbreekt' in build
    assert 'NIET "vpk upload github"' in build
    workflow = (ROOT / '.github/workflows/build-windows.yml').read_text(encoding='utf-8')
    assert 'releases.pilot.json' in workflow


def test_release_process_describes_three_stages():
    text = (ROOT / 'documents/RELEASE_PROCESS.md').read_text(encoding='utf-8')
    for needle in ('releases.pilot.json', '.quietwriter-update-pilot', 'pre-release', 'Bijwerken open'):
        assert needle in text


@pytest.mark.qt
def test_released_later_text_for_self_updating_copy(monkeypatch):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication, QMessageBox
    from quietwriter.storage import Library
    from quietwriter.ui.main_window import MainWindow
    from quietwriter.update_checker import UpdateResult
    from .test_self_update_151 import FakeManager

    app = QApplication.instance() or QApplication([])
    shown = []
    monkeypatch.setattr(QMessageBox, 'exec', lambda box: shown.append(box.informativeText()) or 0)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        window = MainWindow(QSettings(str(root / 's.ini'), QSettings.IniFormat), Library(root / 'w'), [])
        try:
            result = UpdateResult('1.6.1', '1.6.2', 'https://example.invalid', True)
            window._self_updater_instance = self_update.SelfUpdater(manager_factory=lambda: FakeManager(None))
            window._update_check_finished(result)
            window._self_updater_instance = self_update.SelfUpdater(manager_factory=lambda: (_ for _ in ()).throw(RuntimeError('x')))
            window._update_check_finished(result)
        finally:
            window.search_index.close(); window.close(); app.processEvents()
    assert 'nog niet vrijgegeven' in shown[0] or 'not been released' in shown[0]
    assert 'nog niet vrijgegeven' not in shown[1]


# --- ChatGPT-review 1.6.1 #1/#2: beide versies bewaren is terug te draaien ----------

from quietwriter import storage as storage_module
from quietwriter.revisions import ExternalModificationError
from .test_data_rust_160 import _book, _external_write


def _conflict(td):
    lib, book = _book(td, chapters=3)
    one, two, three = book.sections[0].chapters
    _external_write(book, two, 'Versie van de laptop.')
    with pytest.raises(ExternalModificationError):
        lib.save_chapter(book, two, 'Versie van hier.')
    return lib, book, two


def _chapter_files(book):
    return sorted(p.name for p in (book.path / 'chapters').glob('*.md'))


@pytest.mark.parametrize('failpoint', ['other_file', 'manifest', 'own_file'])
def test_keep_both_rolls_back_completely_when_a_write_fails(monkeypatch, failpoint):
    with tempfile.TemporaryDirectory() as td:
        lib, book, two = _conflict(td)
        manifest_before = book.manifest_path.read_bytes()
        files_before = _chapter_files(book)
        order_before = [c.id for c in book.sections[0].chapters]
        tracked_before = lib._tracked_revisions[book.id]
        real_write = storage_module._safe_atomic_write_text

        def failing(path, text, *args, **kwargs):
            path = Path(path)
            hit = {
                'other_file': path.parent.name == 'chapters' and text == 'Versie van de laptop.',
                'manifest': path == book.manifest_path,
                'own_file': path == book.path / two.file and text == 'Versie van hier.',
            }[failpoint]
            if hit:
                raise OSError('schijf vol (gesimuleerd)')
            return real_write(path, text, *args, **kwargs)

        monkeypatch.setattr(storage_module, '_safe_atomic_write_text', failing)
        with pytest.raises(OSError):
            lib.save_chapter_keep_both(book, two, 'Versie van hier.')
        monkeypatch.setattr(storage_module, '_safe_atomic_write_text', real_write)

        assert book.manifest_path.read_bytes() == manifest_before
        assert _chapter_files(book) == files_before
        assert [c.id for c in book.sections[0].chapters] == order_before
        assert [c.id for c in lib.load_book(book.path).sections[0].chapters] == order_before
        assert lib.read_chapter(book, two) == 'Versie van de laptop.'          # niets overschreven
        assert lib._tracked_revisions[book.id] is tracked_before                  # conflict blijft zichtbaar
        assert any(v['kind'] == 'conflict_local' for v in lib.list_versions(book))  # lokale tekst veilig
        with pytest.raises(ExternalModificationError):                             # gewone conflictkeuze volgt
            lib.save_chapter(book, two, 'Versie van hier.')
        other = lib.save_chapter_keep_both(book, two, 'Versie van hier.')        # en opnieuw proberen werkt
        assert lib.read_chapter(book, other) == 'Versie van de laptop.'
        assert lib.read_chapter(book, two) == 'Versie van hier.'


def test_keep_both_rollback_survives_failing_manifest_restore(monkeypatch):
    # Ook het terugzetten van book.json mislukt: dan blijft het extra hoofdstuk
    # (met de externe tekst) staan. Dubbel, maar niets kwijt.
    with tempfile.TemporaryDirectory() as td:
        lib, book, two = _conflict(td)
        real_write = storage_module._safe_atomic_write_text
        calls = {'manifest': 0}

        def failing(path, text, *args, **kwargs):
            path = Path(path)
            if path == book.manifest_path:
                calls['manifest'] += 1
                if calls['manifest'] >= 2:
                    raise OSError('book.json op slot')
            if path == book.path / two.file and text == 'Versie van hier.':
                raise OSError('hoofdstuk op slot')
            return real_write(path, text, *args, **kwargs)

        monkeypatch.setattr(storage_module, '_safe_atomic_write_text', failing)
        with pytest.raises(OSError):
            lib.save_chapter_keep_both(book, two, 'Versie van hier.')
        monkeypatch.setattr(storage_module, '_safe_atomic_write_text', real_write)
        reloaded = lib.load_book(book.path)
        texts = [lib.read_chapter(reloaded, c) for c in reloaded.sections[0].chapters]
        assert texts.count('Versie van de laptop.') == 2
        assert any(v['kind'] == 'conflict_local' for v in lib.list_versions(book))


def test_keep_both_is_not_repeated_without_a_new_external_change():
    # Een herhaalde of nagekomen synchronisatie van dezelfde wijziging mag geen
    # tweede "andere computer"-hoofdstuk opleveren.
    with tempfile.TemporaryDirectory() as td:
        lib, book, two = _conflict(td)
        lib.save_chapter_keep_both(book, two, 'Versie van hier.')
        count = len(book.sections[0].chapters)
        lib.save_chapter(book, two, 'Versie van hier, verder.')                 # geen conflict meer
        with pytest.raises(ExternalModificationError):
            lib.save_chapter_keep_both(book, two, 'Nog eens.')                     # geen botsing: weigert
        assert len(book.sections[0].chapters) == count
        assert len(lib.load_book(book.path).sections[0].chapters) == count
