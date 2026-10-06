from pathlib import Path
import json

from quietwriter.integrity import BookIntegrityChecker
from quietwriter.storage import Library

ROOT = Path(__file__).resolve().parents[2]


def test_ai_switch_controls_all_ai_surfaces_without_deleting_sources():
    main = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    settings = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    rail = (ROOT / 'quietwriter' / 'ui' / 'rail_model.py').read_text(encoding='utf-8')
    assert "RailItemSpec('persona', 'program', requires_ai=True)" in rail
    assert "RailItemSpec('book_memory', 'ai_context', requires_book=True, requires_ai=True)" in rail
    assert "RailItemSpec('book_profile', 'ai_context', requires_book=True, requires_ai=True)" in rail
    assert "'ai_enabled': self.ai_enabled.isChecked()" in settings
    render = main[main.index('    def _render_rail'):main.index('    def _render_feature_buttons')]
    assert 'unlink(' not in render
    assert 'write_text(' not in render


def test_advanced_options_are_default_on_and_only_gate_integrity_for_now():
    main = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    settings = (ROOT / 'quietwriter' / 'ui' / 'settings_page.py').read_text(encoding='utf-8')
    rail = (ROOT / 'quietwriter' / 'ui' / 'rail_model.py').read_text(encoding='utf-8')
    assert "settings.value('advanced_options', True, bool)" in settings
    assert "'advanced_options': self.advanced_options.isChecked()" in settings
    assert "RailItemSpec('integrity', 'current_book', requires_book=True, requires_advanced=True)" in rail
    assert 'requires_advanced=True' not in rail.split("RailItemSpec('integrity'", 1)[0]
    assert "advanced=self.settings.value('advanced_options', True, bool)" not in main  # effective state owns reads

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
