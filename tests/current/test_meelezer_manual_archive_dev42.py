from pathlib import Path
from types import SimpleNamespace
import json

from quietwriter.ai.conversations import SavedConversationArchive, ConversationStore


def test_manual_archive_only_written_on_save(tmp_path):
    book = SimpleNamespace(path=tmp_path / 'book')
    book.path.mkdir()
    archive = SavedConversationArchive(book)
    messages = [ConversationStore.entry('user', 'Is dit logisch?', {'selected_text': 'De brug was stil.'}),
                ConversationStore.entry('assistant', 'Dat klopt.')]
    assert not archive.folder.exists()
    path = archive.save_explicit(messages, 'De brug', provider='openrouter', model='openrouter/free')
    assert path.exists()
    assert len(archive.list_items()) == 1
    messages[0]['content'] = 'Gewijzigde vraag'
    assert archive.list_items()[0][1]['messages'][0]['content'] == 'Is dit logisch?'
    exported = archive.export_markdown(archive.list_items()[0][1])
    assert 'De brug was stil.' in exported and 'Dat klopt.' in exported
    assert not (book.path / '.quietwriter' / 'ai_chat.json').exists()


def test_archive_rejects_empty_and_ignores_bad_files(tmp_path):
    book = SimpleNamespace(path=tmp_path)
    archive = SavedConversationArchive(book)
    import pytest
    with pytest.raises(ValueError):
        archive.save_explicit([], 'Leeg')
    archive.folder.mkdir(parents=True)
    (archive.folder / 'bad.json').write_text('not json')
    assert archive.list_items() == []


def test_all_locales_have_reader_keys():
    root = Path(__file__).resolve().parents[2] / 'quietwriter' / 'locales'
    keys = {'ai.workspace.open','ai.workspace.close','ai.archive.save','ai.archive.open',
            'ai.archive.title_prompt','ai.archive.export','ai.error.general','ai.error.details'}
    for lang in ('nl','en','de','fr','es'):
        values = json.loads((root / f'{lang}.json').read_text(encoding='utf-8'))
        assert keys <= values.keys()
        assert all(values[k].strip() for k in keys)
