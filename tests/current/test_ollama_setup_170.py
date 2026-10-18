"""1.7.0 (dev18): Ollama eenvoudiger instellen. Zonder netwerk: alles is nagebootst."""
from __future__ import annotations

import json
import os
import time

import pytest

from quietwriter.ai import ollama_setup as core

pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


# ---- kern -----------------------------------------------------------------

def test_suggested_model_follows_memory():
    assert core.suggested_model(None).level == 'light'      # onbekend: voorzichtig
    assert core.suggested_model(8).level == 'light'
    assert core.suggested_model(16).level == 'medium'
    assert core.suggested_model(64).level == 'strong'
    assert all(m.name and ':' in m.name for m in core.RECOMMENDED_MODELS)


def test_check_ollama_states(monkeypatch):
    class Resp:
        def __init__(self, models): self._models = models
        def raise_for_status(self): pass
        def json(self): return {'models': self._models}

    monkeypatch.setattr(core.requests, 'get', lambda *a, **k: Resp([]))
    assert core.check_ollama('http://x') == (core.NO_MODELS, [])
    monkeypatch.setattr(core.requests, 'get', lambda *a, **k: Resp([{'name': 'gemma4:12b'}]))
    assert core.check_ollama('http://x') == (core.READY, ['gemma4:12b'])

    def refuse(*a, **k):
        raise core.requests.ConnectionError('weg')
    monkeypatch.setattr(core.requests, 'get', refuse)
    assert core.check_ollama('http://x') == (core.MISSING, [])


class _Stream:
    def __init__(self, rows, ok=True):
        self.rows, self.ok, self.status_code = rows, ok, 200 if ok else 500
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def iter_lines(self): return [json.dumps(r).encode() for r in self.rows]
    def json(self): return {'error': 'kapot'}


def test_pull_model_reports_progress_and_errors(monkeypatch):
    seen = []
    rows = [{'status': 'pulling manifest'}, {'status': 'downloading', 'total': 200, 'completed': 50},
            {'status': 'downloading', 'total': 200, 'completed': 200}, {'status': 'success'}]
    monkeypatch.setattr(core.requests, 'post', lambda *a, **k: _Stream(rows))
    core.pull_model('http://x', 'm:1', on_progress=lambda f, s: seen.append(f))
    assert seen == [None, 0.25, 1.0, None]

    monkeypatch.setattr(core.requests, 'post', lambda *a, **k: _Stream([{'error': 'file does not exist'}]))
    with pytest.raises(RuntimeError, match='file does not exist'):
        core.pull_model('http://x', 'weg:1')

    monkeypatch.setattr(core.requests, 'post', lambda *a, **k: _Stream([{'status': 'downloading'}]))
    with pytest.raises(core.PullCancelled):
        core.pull_model('http://x', 'm:1', should_stop=lambda: True)

    monkeypatch.setattr(core.requests, 'post', lambda *a, **k: _Stream([{'status': 'downloading'}]))
    with pytest.raises(RuntimeError):   # stroom stopt zonder 'success'
        core.pull_model('http://x', 'm:1')


# ---- interface ------------------------------------------------------------

@pytest.fixture
def app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _wait(app, condition, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


def _box(checker, puller=None, ready=None, ram=16):
    from quietwriter.ui.ollama_setup import OllamaSetupBox
    box = OllamaSetupBox(lambda: 'http://127.0.0.1:11434', ready, ram_gb=ram, checker=checker, puller=puller)
    box.resize(700, 200); box.show()
    return box


def test_missing_shows_download_link_and_retry(app):
    box = _box(lambda url: (core.MISSING, []))
    box.refresh()
    assert _wait(app, lambda: box.state == core.MISSING)
    assert box.download_ollama.isVisible() and box.retry.isVisible()
    assert not box.chooser.isVisible()
    assert '127.0.0.1:11434' in box.status.text()


def test_no_models_preselects_suitable_model_and_pulls(app):
    calls, ready = [], []

    def puller(url, name, on_progress=None, should_stop=None):
        calls.append(name); on_progress(0.5, 'downloading'); on_progress(None, 'success')

    box = _box(lambda url: (core.NO_MODELS, []), puller, ready.append, ram=16)
    box.refresh()
    assert _wait(app, lambda: box.state == core.NO_MODELS)
    assert box.chooser.isVisible() and not box.download_ollama.isVisible()
    assert box.model_choice.currentData() == core.suggested_model(16).name
    box.start_pull()
    assert _wait(app, lambda: ready)
    assert calls == [core.suggested_model(16).name] and ready == calls
    assert box.state == core.READY and not box.chooser.isVisible() and box.more.isVisible()


def test_failed_and_stopped_pull_keep_chooser_open(app):
    def broken(url, name, on_progress=None, should_stop=None):
        raise RuntimeError('schijf vol')

    box = _box(lambda url: (core.NO_MODELS, []), broken)
    box.refresh(); assert _wait(app, lambda: box.state == core.NO_MODELS)
    box.start_pull()
    assert _wait(app, lambda: 'schijf vol' in box.pull_status.text())
    assert box.chooser.isVisible() and box.pull_button.isVisible()

    def stops(url, name, on_progress=None, should_stop=None):
        raise core.PullCancelled()
    box._puller = stops
    box.start_pull()
    assert _wait(app, lambda: not box._busy)
    assert box.pull_button.isVisible() and box.pull_status.isVisible()


def test_settings_page_shows_box_only_for_ollama(app, tmp_path, monkeypatch):
    from PySide6.QtCore import QSettings
    monkeypatch.setattr(core, 'check_ollama', lambda url, timeout=2.0: (core.MISSING, []))
    from quietwriter.ui import ollama_setup as ui_module
    monkeypatch.setattr(ui_module.core, 'check_ollama', lambda url, timeout=2.0: (core.MISSING, []))
    from quietwriter.storage import Library
    from quietwriter.ui.main_window import MainWindow
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(tmp_path / 'ws'))
    settings.setValue('ai_enabled', True); settings.setValue('ai_provider', 'ollama')
    settings.setValue('spell_enabled', False)
    window = MainWindow(settings, Library(tmp_path / 'ws'), [])
    window.resize(1200, 850); window.show(); window.open_settings(); app.processEvents()
    page = window.settings_page
    assert not page.ollama_setup_row.isHidden()
    page.ai_provider.setCurrentIndex(page.ai_provider.findData('openrouter')); app.processEvents()
    assert page.ollama_setup_row.isHidden()
    window.close()


def test_model_field_fits_long_ollama_names(app, tmp_path):
    """Lucas (dev18): het modelveld was te smal voor namen als hf.co/…/…:Q5_K_M."""
    from PySide6.QtCore import QSettings
    from quietwriter.storage import Library
    from quietwriter.ui.main_window import MainWindow
    from quietwriter.ui.settings_page import MODEL_FIELD_WIDTH
    long_name = 'hf.co/HauhauCS/Gemma-4-E4B-Uncensored-HauhauCS-Aggressive:Q5_K_M'
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(tmp_path / 'ws'))
    settings.setValue('ai_enabled', True); settings.setValue('ai_provider', 'ollama')
    settings.setValue('ollama_model', long_name); settings.setValue('spell_enabled', False)
    window = MainWindow(settings, Library(tmp_path / 'ws'), ['qwen3.5:4b', long_name])
    window.resize(1400, 850); window.show(); window.open_settings(); app.processEvents()
    page = window.settings_page
    page._ai_models_by_provider['ollama'] = ['qwen3.5:4b', long_name]
    page._ai_model_drafts['ollama'] = long_name
    page._populate_models('ollama')
    assert page.model.minimumWidth() >= MODEL_FIELD_WIDTH >= 500
    assert page.model.toolTip() == long_name
    assert page.model.view().minimumWidth() >= page.model.view().fontMetrics().horizontalAdvance(long_name)
    window.close()


def test_only_the_latest_check_counts(app):
    """Review dev19: een trage oudere controle overschrijft de nieuwere niet."""
    import threading
    release = threading.Event()
    answers = iter([(core.MISSING, [], True), (core.READY, ['a:1'], False)])

    def checker(url):
        state, models, slow = next(answers)
        if slow:
            release.wait(2)
        return state, models

    box = _box(checker)
    box.refresh(); box.refresh()
    assert _wait(app, lambda: box.state == core.READY)
    release.set()
    _wait(app, lambda: False, timeout=0.3)
    assert box.state == core.READY and box.models == ['a:1']


def test_checker_error_does_not_hang_on_searching(app):
    def broken(url):
        raise ValueError('onverwacht')
    box = _box(broken)
    box.refresh()
    assert _wait(app, lambda: box.state == core.MISSING)
