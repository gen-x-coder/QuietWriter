import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from quietwriter.ai.conversations import ConversationStore
from quietwriter.ai.providers import ProviderFactory
from quietwriter.ai.context import ContextBuilder
from quietwriter.story_index import StoryIndex


class FakeSettings:
    def __init__(self, data=None): self.data = data or {}
    def value(self, key, default=None, *args): return self.data.get(key, default)


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
            rows = [ConversationStore.entry('user','Hallo'), ConversationStore.entry('assistant','**Hoi**')]
            store.save(rows)
            self.assertEqual([x['content'] for x in store.load()], ['Hallo','**Hoi**'])

    def test_story_context_uses_metadata_and_tags(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); stories=root/'stories'; stories.mkdir()
            (stories/'boerderij.md').write_text('---\ntitle: Erf\ndescription: Boerderijverhaal\ntags: boerderij, familie\n---\nEen oud erf.',encoding='utf-8')
            (stories/'stad.md').write_text('---\ntitle: Stad\ntags: stad\n---\nDrukke straten.',encoding='utf-8')
            idx=StoryIndex(root/'stories.db'); idx.rebuild(stories)
            main=SimpleNamespace(story_index=idx, settings=FakeSettings(), library=SimpleNamespace(), editor_page=None)
            builder=ContextBuilder(main)
            rows=builder._library_sources('boerderij familie',18)
            self.assertTrue(rows)
            self.assertEqual(rows[0]['title'],'Erf')
            bundle=builder.library_bundle_from_rows(rows,5)
            self.assertIn('Erf',bundle.text)
            self.assertEqual(bundle.sources[0]['title'],'Erf')


if __name__ == '__main__': unittest.main()

class EmbeddingCacheTests(unittest.TestCase):
    def test_embedding_cache_roundtrip_and_mtime_invalidation(self):
        from quietwriter.ai.embedding_cache import EmbeddingCache, cosine
        with tempfile.TemporaryDirectory() as td:
            cache=EmbeddingCache(Path(td)/'emb.db')
            cache.put('story.md','embed-model',10.0,[1.0,0.0])
            self.assertEqual(cache.get('story.md','embed-model',10.0),[1.0,0.0])
            self.assertIsNone(cache.get('story.md','embed-model',11.0))
            self.assertAlmostEqual(cosine([1,0],[1,0]),1.0)
            cache.close()
