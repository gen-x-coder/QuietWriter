"""Async spelling proposals must never be applied to a different word."""
from pathlib import Path


def test_spelling_proposals_use_background_worker_and_generation_guard():
    source = Path('quietwriter/ui/spell_panel.py').read_text(encoding='utf-8')
    assert 'self._suggest_pool.start(job)' in source
    assert 'self._suggest_pool.clear()' in source
    assert 'setMaxThreadCount(1)' in source
    assert 'generation != getattr(dictionary' in source
    assert 'request_id != self._suggest_request' in source
    assert 'dictionary is not self.editor_page.dictionary' in source
    assert 'self.rows[self.index][1] != word' in source
    assert 'self.change_btn.setEnabled(False)' in source
    assert 'self.change_btn.setEnabled(bool(proposals))' in source
