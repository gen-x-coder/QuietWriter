from pathlib import Path
import json

import pytest

from quietwriter.persona_profile import default_persona_markdown
from quietwriter.spell_engine import WordDictionary
from quietwriter.storage import Library, PersonaExternalModificationError


def test_persona_missing_file_is_treated_as_expected_missing_revision(tmp_path: Path):
    lib = Library(tmp_path)
    loaded = lib.capture_persona_revision()
    assert loaded is not None

    lib.persona_path().unlink()
    assert lib.capture_persona_revision() is None
    assert lib.read_persona() == default_persona_markdown()

    with pytest.raises(PersonaExternalModificationError):
        lib.save_persona('# lokaal\n', expected_revision=loaded)


def test_persona_expected_missing_refuses_file_that_reappeared(tmp_path: Path):
    lib = Library(tmp_path)
    lib.persona_path().unlink()
    loaded = lib.capture_persona_revision()
    assert loaded is None

    lib.persona_path().write_text('# extern teruggekomen\n', encoding='utf-8')
    with pytest.raises(PersonaExternalModificationError):
        lib.save_persona('# lokaal\n', expected_revision=loaded)

    assert lib.persona_path().read_text(encoding='utf-8') == '# extern teruggekomen\n'


def test_persona_expected_missing_can_create_atomically(tmp_path: Path):
    lib = Library(tmp_path)
    lib.persona_path().unlink()
    saved = lib.save_persona('# lokaal\n', expected_revision=None)

    assert saved is not None
    assert lib.persona_path().read_text(encoding='utf-8') == '# lokaal\n'


def test_persona_page_preserves_corrupt_local_text_and_can_close():
    source = Path('quietwriter/ui/persona_page.py').read_text(encoding='utf-8')
    assert 'except CorruptSourceError as exc:' in source
    assert 'create_persona_recovery(local_text' in source
    assert '_preserve_local_after_source_problem' in source
    assert 'return True' in source.split('def _preserve_local_after_source_problem', 1)[1]


@pytest.mark.parametrize('filename', ['nl.json', 'en.json'])
def test_locale_values_never_contain_literal_backslash_n(filename: str):
    data = json.loads((Path('quietwriter/locales') / filename).read_text(encoding='utf-8'))
    offenders = {key: value for key, value in data.items()
                 if isinstance(value, str) and r'\n' in value}
    assert offenders == {}


def test_personal_dictionary_merges_external_words_before_atomic_write(tmp_path: Path):
    path = tmp_path / 'persoonlijk.txt'
    path.write_text('lokaalwoord\n', encoding='utf-8')

    dictionary = WordDictionary()
    dictionary.load_personal(path)

    path.write_text('lokaalwoord\nwoordvanlaptop\n', encoding='utf-8')
    dictionary.add_personal('nieuwwoord')

    assert dictionary.personal_words == {'lokaalwoord', 'woordvanlaptop', 'nieuwwoord'}
    assert path.read_text(encoding='utf-8').splitlines() == [
        'lokaalwoord', 'nieuwwoord', 'woordvanlaptop'
    ]


def test_persistent_ignore_merges_external_words_before_atomic_write(tmp_path: Path):
    path = tmp_path / 'altijd_negeren.txt'
    path.write_text('bestaand\n', encoding='utf-8')

    dictionary = WordDictionary()
    dictionary.load_persistent_ignored(path)

    path.write_text('bestaand\nextern\n', encoding='utf-8')
    dictionary.ignore_always('nieuw')

    assert dictionary.persistent_ignored_words == {'bestaand', 'extern', 'nieuw'}
    assert path.read_text(encoding='utf-8').splitlines() == [
        'bestaand', 'extern', 'nieuw'
    ]
