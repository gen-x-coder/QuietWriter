from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_document_wide_manuscript_rewrites_use_source_text():
    editor = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    manuscript = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
    for method in ('insert_scene_break', '_delete_image_block', '_insert_image_from_panel'):
        start = editor.index(f'    def {method}')
        end = editor.find('\n    def ', start + 8)
        block = editor[start:end if end != -1 else None]
        assert 'toPlainText()' not in block
        assert '_editor_source_text()' in block
    start = manuscript.index('    def _delete_hovered_scene_break')
    end = manuscript.find('\n    def ', start + 8)
    block = manuscript[start:end if end != -1 else None]
    assert 'toPlainText()' not in block
    assert 'source_text()' in block


def test_book_navigation_visibility_is_centralized_on_active_book():
    rail = (ROOT / 'quietwriter' / 'ui' / 'rail_model.py').read_text(encoding='utf-8')
    for key in ('contents', 'planning', 'media', 'book_details', 'export'):
        assert f"RailItemSpec('{key}', 'current_book', requires_book=True" in rail
    main = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    render = main[main.index('    def _render_rail'):main.index('    def _render_feature_buttons')]
    assert 'build_rail_view(state)' in render
    assert 'self.active_book()' not in render


def test_notes_and_publication_use_shared_source_text_for_persistence():
    notes = (ROOT / 'quietwriter' / 'ui' / 'planning' / 'notes_page.py').read_text(encoding='utf-8')
    publication = (ROOT / 'quietwriter' / 'ui' / 'publication' / 'publication_editor.py').read_text(encoding='utf-8')
    assert 'self._clean_text = self.editor.source_text()' in notes
    assert 'if self.editor.source_text() == self._clean_text:' in notes
    assert 'source_text = self.editor.source_text()' in notes
    assert 'text = self.free_text.editor.source_text()' in publication
