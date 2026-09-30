import importlib.util

import pytest


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
