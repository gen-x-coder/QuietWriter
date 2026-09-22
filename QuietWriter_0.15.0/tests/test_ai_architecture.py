import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from quietwriter.ai.conversations import ConversationStore
from quietwriter.ai.providers import ProviderFactory
from quietwriter.ai.context import ContextBuilder


class FakeSettings:
    def __init__(self, data=None):
        self.data = data or {}

    def value(self, key, default=None, *args):
        return self.data.get(key, default)


class AIArchitectureTests(unittest.TestCase):
    def test_provider_factory_defaults_to_ollama(self):
        provider = ProviderFactory.from_settings(FakeSettings())
        self.assertEqual(provider.name, 'ollama')

    def test_openrouter_provider_can_be_selected_without_key(self):
        provider = ProviderFactory.from_settings(FakeSettings({'ai_provider': 'openrouter'}))
        self.assertEqual(provider.name, 'openrouter')
        self.assertFalse(provider.is_available())

    def test_conversation_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            book = SimpleNamespace(path=Path(td))
            store = ConversationStore(book)
            rows = [ConversationStore.entry('user', 'Hallo'), ConversationStore.entry('assistant', '**Hoi**')]
            store.save(rows)
            self.assertEqual([x['content'] for x in store.load()], ['Hallo', '**Hoi**'])

    def test_context_builder_prefers_selection(self):
        cursor = SimpleNamespace(selectedText=lambda: 'gekozen tekst')
        editor = SimpleNamespace(textCursor=lambda: cursor, toPlainText=lambda: 'heel hoofdstuk')
        chapter = SimpleNamespace(id='c1', title='Een hoofdstuk')
        book = SimpleNamespace(title='Boek', sections=[])
        page = SimpleNamespace(book=book, chapter=chapter, editor=editor)
        main = SimpleNamespace(editor_page=page, library=SimpleNamespace(read_chapter=lambda b, c: 'tekst'))
        bundle = ContextBuilder(main).build('Huidig hoofdstuk')
        self.assertEqual(bundle.label, 'geselecteerde tekst')
        self.assertEqual(bundle.text, 'gekozen tekst')


if __name__ == '__main__':
    unittest.main()
