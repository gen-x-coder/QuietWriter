from pathlib import Path


def test_memory_confirmation_is_rendered_as_local_chat_notice():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "ConversationStore.entry('notice', text)" in ai
    assert "Opgeslagen in Boekgeheugen ·" in ai
    assert "elif role == 'notice':" in ai
    assert '<b>QuietWriter</b> · {body}' in ai


def test_local_notice_is_not_sent_back_to_provider():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    # Provider history remains restricted to actual user/assistant conversation.
    assert "if m.get('role') in {'user','assistant'}" in ai


def test_direct_and_edited_memory_acceptance_both_add_confirmation():
    ai = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    remember_start = ai.index('    def _remember_suggestion(')
    remember_end = ai.index('    def _ignore_suggestion(', remember_start)
    edit_start = ai.index('    def _edit_suggestion(')
    edit_end = ai.index('    def clear_conversation(', edit_start)
    assert '_append_chat_notice(' in ai[remember_start:remember_end]
    assert '_append_chat_notice(' in ai[edit_start:edit_end]
