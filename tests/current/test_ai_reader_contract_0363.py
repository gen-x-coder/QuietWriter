from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def test_reader_quick_actions_do_not_offer_rewriting():
    source = (ROOT / 'quietwriter' / 'ai' / 'quick_actions.py').read_text(encoding='utf-8')
    assert "'rewrite_selection'" not in source
    assert 'Herschrijf selectie' not in source


def test_reader_system_prompt_forbids_ghostwriting():
    source = (ROOT / 'quietwriter' / 'ai' / 'prompting.py').read_text(encoding='utf-8')
    assert 'meelees-assistent' in source
    assert 'geen co-auteur of tekstgenerator' in source
    assert 'Schrijf of herschrijf geen manuscripttekst' in source
    assert 'Formuleer geen kant-en-klare vervangende passages' in source


def test_reader_positioning_is_localized_and_warmup_is_explicit():
    for language in ('nl', 'en'):
        data = json.loads((ROOT / 'quietwriter' / 'locales' / f'{language}.json').read_text(encoding='utf-8'))
        for key in ('settings.ai', 'settings.ai.intro', 'persona.info', 'ai.title', 'ai.warmup.loading', 'ai.warmup.prompt', 'ai.role_label'):
            assert data.get(key), f'{language}: missing {key}'
        assert 'rewrite_selection' not in '\n'.join(data.keys())


def test_warmup_is_started_from_opening_reader_not_book_loading():
    editor = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    panel = (ROOT / 'quietwriter' / 'ai' / 'ui.py').read_text(encoding='utf-8')
    assert 'self.ai.ensure_warmup()' in editor
    assert 'def ensure_warmup(self):' in panel
    assert "ContextBundle(tr('ai.warmup.context_label'" in panel
    assert 'No manuscript text is sent for this introduction.' in panel
