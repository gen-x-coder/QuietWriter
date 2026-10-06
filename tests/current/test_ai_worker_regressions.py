from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding='utf-8')


def test_ai_worker_callbacks_are_scoped_to_book_generation_and_worker():
    source = _source('quietwriter/ai/ui.py')
    assert 'self._book_generation += 1' in source
    assert 'self._workers = set()' in source
    assert 'self._workers.add(worker)' in source
    assert 'self._workers.discard(worker)' in source
    set_book = source[source.index('    def set_book(self, book):'):source.index('    def clear_conversation', source.index('    def set_book(self, book):'))]
    assert '_wait_for_workers(' not in set_book
    assert 'self._request_serial += 1' in source
    assert 'request_id = (self._book_generation, self._request_serial)' in source
    assert 'def _request_is_current(self, worker, request_id) -> bool:' in source
    assert 'worker is self.worker' in source
    assert 'request_id == self._active_request_id' in source
    assert 'request_id[0] == self._book_generation' in source
    for signal in ('token', 'thinking', 'failed', 'finished_ok', 'cancelled', 'finished'):
        assert f'worker.{signal}.connect(' in source
        assert 'w=worker, rid=request_id' in source


def test_stale_worker_finished_cannot_clear_new_worker_reference():
    source = _source('quietwriter/ai/ui.py')
    start = source.index('    def _chat_thread_finished(self, worker, request_id):')
    end = source.index('    def apply_theme', start)
    block = source[start:end]
    assert 'if self.worker is worker:' in block
    assert 'self.worker = None' in block
    assert 'worker.deleteLater()' in block
    assert 'obj=self.worker' not in block
    assert 'self._workers.discard(worker)' in block


def test_provider_switch_repopulates_model_combo_from_live_provider():
    source = _source('quietwriter/ui/settings_page.py')
    assert 'self.ai_provider.currentIndexChanged.connect(self._ai_provider_changed)' in source
    start = source.index('    def _populate_models(')
    end = source.index('    def _update_ai_controls', start)
    block = source[start:end]
    assert "self.ai_provider.currentData()" in block
    assert "self.settings.value('ai_provider'" not in block
    assert "self._ai_models_by_provider" in block
    assert "self._ai_model_drafts" in block


def test_provider_models_are_saved_per_provider_not_cross_assigned():
    source = _source('quietwriter/ui/settings_page.py')
    start = source.index('    def save_settings(self):')
    end = source.index('    def begin_session(self):', start)
    block = source[start:end]
    assert "values['ollama_model'] = self._ai_model_drafts.get('ollama', '')" in block
    assert "values['openrouter_model'] = self._ai_model_drafts.get('openrouter', '')" in block


def test_context_has_stale_section_and_read_error_guards():
    source = _source('quietwriter/ai/context.py')
    assert 'if section is None:' in source
    assert "ai.context.section_unavailable_label" in source
    assert "ContextBundle(tr('ai.context.section_unavailable_label'" in source
    assert 'except (OSError, UnicodeError) as exc:' in source
    assert 'kon niet worden gelezen' in source


def test_add_flyout_uses_subtle_corners():
    source = _source('quietwriter/themes.py')
    assert "QFrame#flyout {{ background: {t['panel']}; border: 1px solid {t['border']}; border-radius: 4px; }}" in source
    assert 'QPushButton#flyoutButton {{ background: transparent; border: 1px solid transparent; border-radius: 4px;' in source
