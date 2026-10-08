import importlib.util
from pathlib import Path

import pytest


if importlib.util.find_spec('PySide6') is not None:
    from PySide6.QtCore import QStandardPaths
    QStandardPaths.setTestModeEnabled(True)


@pytest.fixture(autouse=True)
def fail_on_unexpected_modal_dialog(monkeypatch):
    """Prevent any unexpected modal Qt dialog from hanging the test suite.

    Direct calls fail immediately. Calls raised inside a Qt slot/timer may be
    swallowed by the event loop, so every invocation is also recorded and
    asserted in teardown. Tests that intentionally exercise a dialog can
    monkeypatch the relevant method again in their own body/fixture.
    """
    if importlib.util.find_spec('PySide6') is None:
        yield
        return

    from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox

    calls = []

    def unexpected(kind):
        def fail(*args, **kwargs):
            title = ''
            if kind.endswith('.exec'):
                box = args[0] if args else None
                try:
                    title = box.windowTitle() if box is not None else ''
                except Exception:
                    title = ''
            elif len(args) > 1:
                title = str(args[1])
            calls.append(f'{kind}: {title}'.rstrip())
            raise AssertionError(f'Unexpected {kind}: {title}'.rstrip())
        return fail

    # QMessageBox convenience APIs plus every QDialog-based exec path.
    monkeypatch.setattr(QMessageBox, 'information', unexpected('QMessageBox.information'))
    monkeypatch.setattr(QMessageBox, 'warning', unexpected('QMessageBox.warning'))
    monkeypatch.setattr(QMessageBox, 'critical', unexpected('QMessageBox.critical'))
    monkeypatch.setattr(QMessageBox, 'question', unexpected('QMessageBox.question'))
    monkeypatch.setattr(QMessageBox, 'exec', unexpected('QMessageBox.exec'))
    monkeypatch.setattr(QDialog, 'exec', unexpected('QDialog.exec'))

    # Static convenience dialogs that do not necessarily go through QDialog.exec.
    monkeypatch.setattr(QInputDialog, 'getText', unexpected('QInputDialog.getText'))
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', unexpected('QFileDialog.getOpenFileName'))
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', unexpected('QFileDialog.getExistingDirectory'))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', unexpected('QFileDialog.getSaveFileName'))

    yield
    assert not calls, 'Unexpected modal dialogs during Qt event processing: ' + '; '.join(calls)


@pytest.fixture(autouse=True)
def _close_leaked_qt_windows():
    """Ruim na elke test achtergebleven top-level Qt-vensters op."""
    yield
    if importlib.util.find_spec('PySide6') is None:
        return

    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        return

    for window in list(QApplication.topLevelWidgets()):
        try:
            window.close()
            window.deleteLater()
        except RuntimeError:
            pass

    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


def pytest_collection_modifyitems(config, items):
    """Mark tests that exercise real PySide6/Qt runtime as ``qt``.

    File names are intentionally irrelevant: a test is marked when its module
    imports PySide6 or when it uses the shared ``app`` fixture. This keeps
    ``pytest -m qt`` complete as Qt coverage grows.
    """
    qt_marker = pytest.mark.qt
    for item in items:
        if 'qt' in item.keywords:
            continue
        uses_app_fixture = 'app' in getattr(item, 'fixturenames', ())
        module = getattr(item, 'module', None)
        module_file = Path(getattr(module, '__file__', '') or '')
        imports_pyside = False
        if module_file.is_file():
            try:
                imports_pyside = 'PySide6' in module_file.read_text(encoding='utf-8', errors='ignore')
            except OSError:
                pass
        if uses_app_fixture or imports_pyside:
            item.add_marker(qt_marker)


@pytest.fixture(scope='session', autouse=True)
def _cleanup_qt_test_artifacts():
    """Verwijder alleen testartefacten die deze testrun zelf kan hebben gemaakt.

    QStandardPaths test mode gebruikt ~/.qttest. Die map is uitsluitend Qt-testdata.
    De standaardwoordenboekmap onder ~/QuietWriter wordt alleen verwijderd als hij
    vóór de suite niet bestond en na afloop nog leeg is; echte gebruikersdata wordt
    dus nooit aangeraakt.
    """
    import shutil

    qt_test_root = Path.home() / '.qttest'
    qt_test_root_existed = qt_test_root.exists()
    dictionary_dir = Path.home() / 'QuietWriter' / 'dictionaries'
    dictionary_existed = dictionary_dir.exists()
    yield

    if importlib.util.find_spec('PySide6') is not None and not qt_test_root_existed:
        shutil.rmtree(qt_test_root, ignore_errors=True)

    if not dictionary_existed:
        try:
            if dictionary_dir.is_dir() and not any(dictionary_dir.iterdir()):
                dictionary_dir.rmdir()
                parent = dictionary_dir.parent
                if parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()
        except OSError:
            pass
