"""Regression: spylls suggest() must not block the GUI for minutes.

The bundled OpenTaal nl_NL dictionary has a MAP table (aáàäâå, eéèëê, ...).
spylls expands MAP permutations exponentially and has no time limit, so a
long unknown word could freeze the spelling panel (1.3.0 report).
"""
import time

import pytest

from quietwriter import spell_engine
from quietwriter.spell_engine import WordDictionary

pytestmark = pytest.mark.skipif(spell_engine.HunspellDictionary is None, reason='spylls not installed')


def _write_dictionary(tmp_path):
    (tmp_path / 'xx_XX.aff').write_text('SET UTF-8\nTRY aeiou\nMAP 2\nMAP aáàäâå\nMAP eéèëê\n', encoding='utf-8')
    (tmp_path / 'xx_XX.dic').write_text('3\nbanaan\nbaard\nkaart\n', encoding='utf-8')
    return tmp_path / 'xx_XX.dic'


def test_suggest_on_pathological_word_respects_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(spell_engine, 'SUGGEST_BUDGET_SECONDS', 0.3, raising=False)
    d = WordDictionary(); d.load_dic(_write_dictionary(tmp_path))
    assert d.hunspell is not None
    started = time.monotonic()
    d.suggest('a' * 28 + 'e' * 12 + 'x')
    assert time.monotonic() - started < 5


def test_suggest_still_finds_normal_corrections(tmp_path):
    d = WordDictionary(); d.load_dic(_write_dictionary(tmp_path))
    assert 'banaan' in d.suggest('bannaan')
    assert d._suggest_deadline is None
    assert d.known('kaart') and not d.known('kaartt')
