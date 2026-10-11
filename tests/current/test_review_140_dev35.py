"""Regression protections for the dev.33 independent audit fixes."""
from pathlib import Path
import threading
import time

from quietwriter.spell_engine import WordDictionary
from quietwriter.storage import Library


def test_suggestion_workers_keep_independent_deadlines(monkeypatch):
    dictionary = WordDictionary()
    class FakeHunspell:
        def suggest(self, word):
            if word == 'slow':
                yield 'slow-fix'
                time.sleep(0.07)
                yield 'slow-late'
            else:
                yield 'fast-fix'
    dictionary.hunspell = FakeHunspell()
    import quietwriter.spell_engine as engine
    monkeypatch.setattr(engine, 'SUGGEST_BUDGET_SECONDS', 0.02)
    results = {}
    slow = threading.Thread(target=lambda: results.setdefault('slow', dictionary.suggest('slow')))
    slow.start()
    time.sleep(.01)
    assert dictionary.suggest('fast') == ['fast-fix']
    slow.join(timeout=1)
    assert not slow.is_alive()
    assert results['slow'] == ['slow-fix']


def test_dictionary_reload_prevents_stale_suggestion_cache():
    d = WordDictionary()
    class FakeHunspell:
        def suggest(self, word):
            d.clear()
            yield 'old-result'
    d.hunspell = FakeHunspell()
    d.suggest('typo')
    assert 'typo' not in d._suggest_cache


def test_new_history_version_does_not_list_older_versions(tmp_path, monkeypatch):
    lib = Library(tmp_path / 'library')
    book = lib.create_book('boek')
    lib.create_version(book)
    def forbidden(*args, **kwargs):
        raise AssertionError('create_version must not inspect all old history')
    monkeypatch.setattr(lib, 'list_versions', forbidden)
    row = lib.create_version(book)
    assert row['chapters'] >= 1
    assert row['id']


def test_restore_rescue_staging_is_not_auto_deleted(tmp_path):
    from quietwriter.backup_restore import _cleanup_old_restore_workspaces
    import os
    from datetime import datetime
    staged = tmp_path / 'restore-staging'
    staged.mkdir()
    preserved = staged / 'restore-protected'
    preserved.mkdir()
    (preserved / '.preserve-for-rescue').write_text('keep', encoding='utf-8')
    (preserved / 'previous-book').mkdir()
    os.utime(preserved, (time.time()-100000, time.time()-100000))
    _cleanup_old_restore_workspaces(staged)
    assert (preserved / 'previous-book').exists()
