from pathlib import Path
import json

from quietwriter.integrity import BookIntegrityChecker
from quietwriter.storage import Library

ROOT = Path(__file__).resolve().parents[1]


def test_ai_switch_controls_all_ai_surfaces_without_deleting_sources():
    main = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    settings = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    assert "ai_enabled = self.settings.value('ai_enabled', True, bool)" in main
    assert 'self.persona_button.setVisible(ai_enabled)' in main
    assert 'self.book_profile_button.setVisible(has_book and ai_enabled)' in main
    assert 'self.book_memory_button.setVisible(has_book and ai_enabled)' in main
    assert "self.settings.setValue('ai_enabled', self.ai_enabled.isChecked())" in settings
    # Feature switching is visibility-only: no source deletion belongs here.
    feature = main[main.index('    def _apply_feature_visibility'):main.index('    def _apply_ai_visibility')]
    assert 'unlink(' not in feature
    assert 'write_text(' not in feature


def test_advanced_options_are_default_on_and_only_gate_integrity_for_now():
    main = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    settings = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    assert "settings.value('advanced_options', True, bool)" in settings
    assert "self.settings.setValue('advanced_options', self.advanced_options.isChecked())" in settings
    assert "advanced = self.settings.value('advanced_options', True, bool)" in main
    assert 'self.integrity_button.setVisible(has_book and advanced)' in main
    assert 'self.integrity_gap.setVisible(self.rail_expanded and has_book and advanced)' in main


def test_disabling_spelling_forces_immediate_rehighlight_and_hides_tool():
    editor = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    main = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    assert 'self.highlighter.set_active(active)' in editor
    assert 'self.highlighter.rehighlight()' in editor
    assert 'document.markContentsDirty' in editor
    assert 'self.editor.viewport().update()' in editor
    assert 'self.spell_button.setVisible(spell_enabled)' in main


def test_recovery_candidate_exposes_version_provenance(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Herkomst')
    rel = 'ai/memory.md'
    target = Path(book.path) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('schijf', encoding='utf-8')
    version = lib.create_version_with_file_overrides(book, {rel: 'lokaal'}, kind='conflict_local')
    target.write_bytes(b'kapot-\xff')
    checker = BookIntegrityChecker()
    candidate = checker.latest_recovery_candidate(lib, book, rel)
    assert candidate is not None
    assert candidate['kind'] == 'conflict_local'
    assert candidate['id'] == version['id']
    assert candidate['path'].read_text(encoding='utf-8') == 'lokaal'


def test_new_copy_exists_in_both_locales():
    for language in ('nl', 'en'):
        data = json.loads((ROOT / 'quietwriter' / 'locales' / f'{language}.json').read_text(encoding='utf-8'))
        assert data['settings.general.advanced_options']
        assert data['settings.general.advanced_options_help']
        assert data['spell.disabled']
        assert data['integrity.recovery_source']
