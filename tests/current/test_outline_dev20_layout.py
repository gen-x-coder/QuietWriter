from pathlib import Path

SOURCE = Path('quietwriter/ui/planning/outline_page.py')


def test_outline_is_left_aligned_and_bounded():
    text = SOURCE.read_text(encoding='utf-8')
    assert 'self.host.setMaximumWidth(1320)' in text
    assert 'centered.addWidget(self.host,1); centered.addStretch(0)' in text
    assert 'header_row.addWidget(header,1); header_row.addStretch(0)' in text


def test_scene_fields_are_always_visible_and_grouped():
    text = SOURCE.read_text(encoding='utf-8')
    assert "planning.outline.section.main" in text
    assert "planning.outline.section.depth" in text
    for field in ('goal', 'conflict', 'outcome', 'notes'):
        assert f"form.addRow(field_label(tr('planning.outline.field.{field}'" in text  # dev15: field_label
    assert 'details_toggle' not in text
    assert 'self.form_scroll.setWidget(form_host)' in text
