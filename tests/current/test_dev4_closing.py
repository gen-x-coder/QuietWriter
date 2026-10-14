"""Dev.4: no misleading recovery instruction and duplicate locale key regression."""
from pathlib import Path
import pytest
from tools.check_locales import _unique_pairs


def test_duplicate_locale_keys_are_rejected():
    with pytest.raises(ValueError, match='duplicate translation key: a'):
        _unique_pairs([('a', 'first'), ('b', 'ok'), ('a', 'second')])


def test_locale_normal_pairs_unchanged():
    assert _unique_pairs([('a', 'one'), ('b', 'two')]) == {'a': 'one', 'b': 'two'}


def test_incomplete_rollback_message_points_to_real_rescue_locations():
    source = (Path(__file__).resolve().parents[2] / 'quietwriter/backup_restore.py').read_text(encoding='utf-8')
    assert "f'Mogelijke reddingsbestanden staan in: {rescue_parent} en {workspace}. '" in source
    assert 'kies het in Instellingen > Herstellen.' not in source
    assert '.preserve-for-rescue' in source
