from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ai_context_copy_is_transparent_about_every_request_and_precedence():
    nl = (ROOT / 'quietwriter' / 'locales' / 'nl.json').read_text(encoding='utf-8')
    assert nl.count('Bij iedere AI-vraag') >= 3
    assert 'gekozen AI-provider' in nl
    assert 'boekprofiel' in nl.lower()
    assert 'voorrang' in nl.lower()


def test_program_group_is_fixed_outside_scroll_area_and_collapsed_groups_have_separators():
    source = (ROOT / 'quietwriter' / 'ui' / 'main_window.py').read_text(encoding='utf-8')
    assert "self.rail_shell_layout.addWidget(self.rail_scroll, 1)" in source
    assert "self.rail_shell_layout.addWidget(self.program_host, 0)" in source
    assert "self._register_nav_separator('current_book')" in source
    assert "self._register_nav_separator('ai_context')" in source
    assert "self._register_nav_separator('program', layout=self.program_layout)" in source
    assert "separator.setVisible((not self.rail_expanded)" in source
