"""Structural guard for the non-authoritative Planning UI controls."""
from pathlib import Path

def test_outline_group_controls_keep_planning_store_as_only_writer():
    code = Path('quietwriter/ui/planning/outline_page.py').read_text(encoding='utf-8')
    assert 'def toggle_group(self, key):' in code
    assert 'def move_scene(self, scene_id, direction):' in code
    assert 'self.scenes[current], self.scenes[other]' in code
    assert 'result = self._save()' in code
    assert "if result == 'failed':" in code
    assert 'self._collapsed_groups.clear()' in code
