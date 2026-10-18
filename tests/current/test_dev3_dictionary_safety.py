from pathlib import Path
from quietwriter.dictionary_catalog import DictionaryCatalog
from quietwriter.spell_engine import WordDictionary


def test_catalog_does_not_treat_dic_without_aff_as_ready(tmp_path):
    (tmp_path / 'de_DE.dic').write_text('1\nWort\n')
    entry = next(x for x in DictionaryCatalog(tmp_path, extra_roots=[]).entries() if x.locale == 'de_DE')
    assert entry.aff is None


def test_first_run_uses_shared_catalog_and_no_fabricated_nl():
    source = Path('quietwriter/ui/first_run_wizard.py').read_text()
    method = source.split('    def _populate_dictionaries(self', 1)[1].split('    def _choose_workspace', 1)[0]
    assert 'DictionaryCatalog(' in method
    assert 'entry.aff is None' in method
    assert "locales.add('nl_NL')" not in method


def test_no_bundled_dictionary_any_more():
    # 1.7: OpenTaal wordt niet meer meegeleverd; je downloadt het of gebruikt Office.
    catalog = Path('quietwriter/dictionary_catalog.py').read_text(encoding='utf-8')
    assert "'Meegeleverd'" not in catalog
    assert not Path('tools/fetch_dictionaries.py').exists()


def test_case_sensitive_spell_suggestions_cache(tmp_path):
    engine = WordDictionary.__new__(WordDictionary)
    engine._generation = 0
    engine._suggest_cache = {}
    engine.hunspell = None
    engine.words = {'voorbeeld'}
    engine.personal_words = set()
    assert engine.suggest('Voorbeel') == ['Voorbeeld']
    assert engine.suggest('VOORBEEL') == ['VOORBEELD']
    assert engine.suggest('voorbeel') == ['voorbeeld']
