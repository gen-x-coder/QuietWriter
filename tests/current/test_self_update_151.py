"""Contract voor zelf bijwerken via Velopack (1.5.1).

Wat hier NIET getest kan worden: een echte Velopack-installatie, downloaden van
GitHub en het vervangen van de programmamap. Dat is een Windows-acceptatietest
(zie documents/RELEASE_PROCESS.md).
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


class FakeAsset:
    def __init__(self, version='1.5.2', notes='Nieuw'):
        self.Version = version
        self.NotesMarkdown = notes


class FakeInfo:
    def __init__(self, version='1.5.2'):
        self.TargetFullRelease = FakeAsset(version)


class FakeManager:
    def __init__(self, info=None, portable=True):
        self.info = info
        self.portable = portable
        self.calls = []

    def get_is_portable(self):
        return self.portable

    def get_current_version(self):
        return '1.5.1'

    def check_for_updates(self):
        self.calls.append('check')
        return self.info

    def download_updates(self, info, progress=None):
        self.calls.append('download')
        if progress is not None:
            progress(50)
            progress(100)

    def wait_exit_then_apply_updates(self, info, silent, restart, args):
        self.calls.append(('apply', silent, restart, args))


def test_updater_reports_unavailable_when_not_packaged():
    from quietwriter.self_update import SelfUpdater

    def broken():
        raise RuntimeError('This application is not properly installed')

    updater = SelfUpdater(manager_factory=broken)
    assert not updater.available
    assert updater.reason == 'not-installed'


def test_real_velopack_outside_package_is_unavailable_not_crashing():
    pytest.importorskip('velopack')
    from quietwriter.self_update import SelfUpdater

    # In de testomgeving is QuietWriter niet via vpk verpakt.
    assert SelfUpdater().available is False


def test_check_download_and_apply_use_velopack_contract():
    from quietwriter.self_update import SelfUpdater

    manager = FakeManager(FakeInfo('1.5.2'))
    updater = SelfUpdater(manager_factory=lambda: manager)
    assert updater.available and updater.is_portable
    update = updater.check()
    assert update.version == '1.5.2' and update.notes == 'Nieuw'
    seen = []
    updater.download(update, seen.append)
    assert seen == [50, 100]
    updater.apply_when_closed(update)
    # Niet stil (Velopack toont voortgang) en altijd herstarten.
    assert manager.calls[-1] == ('apply', False, True, None)


def test_no_update_returns_none():
    from quietwriter.self_update import SelfUpdater

    updater = SelfUpdater(manager_factory=lambda: FakeManager(None))
    assert updater.check() is None


def test_worker_emits_found_progress_and_failure_synchronously():
    from PySide6.QtWidgets import QApplication
    from quietwriter.self_update import SelfUpdater, SelfUpdateWorker

    # QApplication (geen QCoreApplication): latere Qt-widgettests in dezelfde run hebben er een nodig.
    QApplication.instance() or QApplication([])
    updater = SelfUpdater(manager_factory=lambda: FakeManager(FakeInfo()))

    found, progress, done, failed = [], [], [], []
    worker = SelfUpdateWorker(updater, 'check')
    worker.found.connect(found.append)
    worker.run()
    assert found and found[0].version == '1.5.2'

    worker = SelfUpdateWorker(updater, 'download', found[0])
    worker.progress.connect(progress.append)
    worker.downloaded.connect(done.append)
    worker.run()
    assert progress == [50, 100] and done == [found[0]]

    worker = SelfUpdateWorker(updater, 'onzin')
    worker.failed.connect(failed.append)
    worker.run()
    assert failed and 'onzin' in failed[0]


def _fake_window(close_result, updater, quits):
    return SimpleNamespace(
        close=lambda: close_result,
        _self_updater=lambda: updater,
        _close_self_update_progress=lambda: None,
        _quit_application=lambda: quits.append(True),
    )


def test_update_is_only_applied_after_normal_close_and_then_the_process_quits(monkeypatch):
    from quietwriter.ui import main_window as mw

    applied, notices, quits = [], [], []
    updater = SimpleNamespace(apply_when_closed=lambda u: applied.append(u))
    monkeypatch.setattr(mw, 'notice_information', lambda *a, **k: notices.append(a))
    update = SimpleNamespace(version='1.5.2')

    mw.MainWindow._self_update_downloaded(_fake_window(False, updater, quits), update)
    assert applied == [] and quits == [] and len(notices) == 1   # afsluiten geweigerd: niets forceren

    mw.MainWindow._self_update_downloaded(_fake_window(True, updater, quits), update)
    assert applied == [update]
    assert quits == [True]   # ook een open pop-out mag het proces niet in leven houden


def test_apply_failure_is_shown_to_the_writer(monkeypatch):
    from quietwriter.ui import main_window as mw

    warnings, quits = [], []
    def broken(_update):
        raise RuntimeError('Update.exe ontbreekt')
    monkeypatch.setattr(mw, 'notice_warning', lambda *a, **k: warnings.append(a))
    monkeypatch.setattr(mw, 'log_exception', lambda *a, **k: None)
    mw.MainWindow._self_update_downloaded(_fake_window(True, SimpleNamespace(apply_when_closed=broken), quits), SimpleNamespace(version='1.5.2'))
    assert len(warnings) == 1 and 'Update.exe ontbreekt' in warnings[0][2]
    assert quits == [True]


def test_download_failure_has_its_own_message(monkeypatch):
    from quietwriter.ui import main_window as mw

    warnings = []
    monkeypatch.setattr(mw, 'notice_warning', lambda *a, **k: warnings.append(a))
    fake = SimpleNamespace(_update_op=SimpleNamespace(mode='download', silent=False),
                           _close_self_update_progress=lambda: None)
    mw.MainWindow._self_update_failed(fake, 'schijf vol')
    assert warnings and warnings[0][1] != mw.tr('updates.error_title', 'Controleren op updates')
    assert 'schijf vol' in warnings[0][2]


def test_silent_check_failure_stays_silent_and_manual_click_upgrades_running_check(monkeypatch):
    from quietwriter.ui import main_window as mw

    warnings = []
    monkeypatch.setattr(mw, 'notice_warning', lambda *a, **k: warnings.append(a))
    op = SimpleNamespace(mode='check', silent=True)
    fake = SimpleNamespace(_update_op=op, _close_self_update_progress=lambda: None)
    mw.MainWindow._self_update_failed(fake, 'offline')
    assert warnings == []

    # Handmatige klik tijdens een lopende automatische controle: niet dubbel starten,
    # wel het resultaat laten zien.
    mw.MainWindow.check_for_updates(fake, silent=False)
    assert op.silent is False
    mw.MainWindow._self_update_failed(fake, 'offline')
    assert len(warnings) == 1


def test_worker_runs_in_a_daemon_thread_so_closing_never_waits(qapp=None):
    import threading
    from PySide6.QtWidgets import QApplication
    from quietwriter.self_update import SelfUpdater, SelfUpdateWorker

    QApplication.instance() or QApplication([])
    gate = threading.Event()

    class SlowManager(FakeManager):
        def check_for_updates(self):
            gate.wait(5)
            return None

    worker = SelfUpdateWorker(SelfUpdater(manager_factory=lambda: SlowManager()), 'check')
    worker.start()
    assert worker.isRunning() and worker._thread.daemon
    gate.set()
    worker._thread.join(5)
    assert not worker.isRunning()


def test_local_update_source_override(monkeypatch):
    from quietwriter import self_update
    monkeypatch.setenv(self_update.SOURCE_OVERRIDE_ENV, r'C:\QW\release\velopack')
    assert self_update.update_source_override() == r'C:\QW\release\velopack'
    monkeypatch.delenv(self_update.SOURCE_OVERRIDE_ENV)
    assert self_update.update_source_override() == ''


def test_velopack_hook_runs_before_the_app_is_imported():
    main = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert main.index('_velopack_startup()\n') < main.index('from quietwriter.app import run')
    assert 'update-health-check' not in main


def test_old_updater_lab_is_gone_from_the_package():
    leftovers = sorted(p.name for p in (ROOT / 'quietwriter').glob('*.py')
                       if 'updat' in p.name and p.name not in {'update_checker.py', 'self_update.py'})
    assert leftovers == []


def test_build_packs_with_velopack():
    build = (ROOT / 'build_exe.cmd').read_text(encoding='utf-8')
    assert 'vpk pack' in build
    assert '--packId LucasBonsel.QuietWriter' in build
    assert 'hoort gelijk te zijn aan velopack' in build          # versieverschil stopt de build
    assert 'releases.win.json ontbreekt' in build
    assert 'current/quietwriter.exe' in build
    lock = (ROOT / 'packaging/requirements-runtime.lock').read_text(encoding='utf-8')
    assert 'velopack==' in lock
    workflow = (ROOT / '.github/workflows/build-windows.yml').read_text(encoding='utf-8')
    assert 'Smoke test portable zip' in workflow
    assert 'dotnet tool install -g vpk }' not in workflow             # geen ongepinde terugval


def test_keyring_and_its_dependencies_are_pinned_for_the_windows_build():
    lock = (ROOT / 'packaging/requirements-runtime.lock').read_text(encoding='utf-8')
    for package in ('keyring==', 'jaraco.classes==', 'jaraco.functools==', 'jaraco.context==',
                    'more-itertools==', 'pywin32-ctypes=='):
        assert package in lock
    licenses = (ROOT / 'documents/licenses/THIRD_PARTY_LICENSES.md').read_text(encoding='utf-8')
    assert 'keyring' in licenses
    smoke = (ROOT / 'quietwriter/smoke_test.py').read_text(encoding='utf-8')
    assert 'WinVaultKeyring' in smoke and 'import velopack' in smoke
