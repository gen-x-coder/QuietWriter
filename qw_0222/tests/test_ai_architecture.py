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

    def test_context_builder_handles_missing_current_section(self):
        cursor = SimpleNamespace(selectedText=lambda: '')
        editor = SimpleNamespace(textCursor=lambda: cursor, toPlainText=lambda: 'heel hoofdstuk')
        chapter = SimpleNamespace(id='c1', title='Een hoofdstuk')
        book = SimpleNamespace(title='Boek', sections=[])
        page = SimpleNamespace(
            book=book, chapter=chapter, editor=editor,
            find_chapter_in_book=lambda _cid: (None, None),
        )
        main = SimpleNamespace(editor_page=page, library=SimpleNamespace(read_chapter=lambda b, c: 'tekst'))
        bundle = ContextBuilder(main).build('Huidige sectie')
        self.assertEqual(bundle.label, 'sectie niet beschikbaar')
        self.assertEqual(bundle.text, '')

    def test_context_builder_keeps_whole_book_usable_when_one_chapter_read_fails(self):
        cursor = SimpleNamespace(selectedText=lambda: '')
        editor = SimpleNamespace(textCursor=lambda: cursor, toPlainText=lambda: 'actuele tekst')
        current = SimpleNamespace(id='c1', title='Actueel')
        broken = SimpleNamespace(id='c2', title='Onleesbaar')
        section = SimpleNamespace(id='root', title='Boek', chapters=[current, broken])
        book = SimpleNamespace(title='Boek', sections=[section])
        page = SimpleNamespace(book=book, chapter=current, editor=editor)
        def read_chapter(_book, chapter):
            if chapter.id == 'c2':
                raise OSError('bestand bezet')
            return 'tekst'
        main = SimpleNamespace(editor_page=page, library=SimpleNamespace(read_chapter=read_chapter))
        bundle = ContextBuilder(main).build('Hele boek')
        self.assertIn('actuele tekst', bundle.text)
        self.assertIn('Onleesbaar', bundle.text)
        self.assertIn('kon niet worden gelezen', bundle.text)


if __name__ == '__main__':
    unittest.main()
