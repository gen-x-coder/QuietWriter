from pathlib import Path


def test_chapter_planning_is_explicit_opt_in_in_ai_panel_source():
    source = Path("quietwriter/ai/ui.py").read_text(encoding="utf-8")
    assert "value('ai_use_chapter_planning', False, bool)" in source
    assert "getattr(self.main.settings, 'contains', None)" in source
    assert "Staat standaard uit" in source
    assert "Bij een externe provider verlaten deze gegevens je computer." in source


def test_context_budget_is_deferred_not_silently_truncated():
    source = Path("quietwriter/ai/ui.py").read_text(encoding="utf-8")
    assert "def _active_chapter_planning_text" in source
    assert "preview.text" in source
    assert "[:" not in source[source.index("def _active_chapter_planning_text"):source.index("def refresh_context_summary") ]


def test_opt_in_notice_can_be_acknowledged_without_enabling_context():
    source = Path("quietwriter/ai/ui.py").read_text(encoding="utf-8")
    assert "self.chapter_planning_notice_ack = QPushButton(tr('common.understood', 'Begrepen'))" in source
    assert "def _acknowledge_chapter_planning_notice" in source
    acknowledge = source[source.index("def _acknowledge_chapter_planning_notice"):source.index("def _chapter_planning_toggled") ]
    assert "setValue('ai_use_chapter_planning', False)" in acknowledge
