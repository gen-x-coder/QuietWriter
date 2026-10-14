from pathlib import Path
import json


def test_save_conversation_explains_why_saving_is_not_possible():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    method = source.split('    def save_conversation(self):', 1)[1].split('    def open_archives(self):', 1)[0]
    assert method.index('if self.is_busy():') < method.index("if not any(m.get('role') == 'user'")
    assert 'ai.archive.wait_until_ready' in method
    assert 'ai.archive.nothing_to_save' in method
    assert 'ai.archive.book_required' in method


def test_approved_memory_suggestion_checks_disk_after_write():
    source = Path('quietwriter/ui/book_memory_page.py').read_text(encoding='utf-8')
    method = source.split('    def add_suggestion(', 1)[1].split('    def _resolve_external_change(', 1)[0]
    assert 'parse_book_memory(self.main.library.read_book_memory(self.book))' in method
    assert 'persisted_memory.get(section_key)' in method


def test_new_feedback_translated_in_all_languages():
    for language in ('nl', 'en', 'de', 'fr', 'es'):
        data = json.loads((Path('quietwriter/locales') / f'{language}.json').read_text(encoding='utf-8'))
        for key in ('ai.archive.wait_until_ready', 'ai.archive.book_required',
                    'book_memory.verify_title', 'book_memory.verify_failed'):
            assert data[key].strip()
