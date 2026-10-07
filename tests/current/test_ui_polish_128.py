from pathlib import Path


def _source(path):
    return Path(path).read_text(encoding="utf-8")


def test_workspace_picker_can_shrink_on_hidpi_widths():
    source = _source("quietwriter/ui/settings_page.py")
    assert "box.setMinimumWidth(0)" in source
    assert "box.setMaximumWidth(760)" in source
    assert "self.root.setMinimumWidth(320)" in source
    assert "box.setMinimumWidth(680)" not in source


def test_dictionary_info_uses_actual_runtime_width_for_wrapped_height():
    source = _source("quietwriter/ui/settings_page.py")
    assert "class WrappedHeightLabel" in source
    assert "needed = self.heightForWidth(width)" in source
    assert "self.dictionary_info = WrappedHeightLabel('')" in source
    assert "self.dictionary_info.sync_height()" in source


def test_chapter_context_empty_state_has_expanding_filler():
    source = _source("quietwriter/ui/chapter_context_panel.py")
    assert "self.empty_filler = QWidget()" in source
    assert "self.empty_filler.setObjectName('chapterContextFiller')" in source
    assert "self.empty_filler.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)" in source
    assert "self.empty_filler.show()" in source
    assert "self.empty_filler.hide()" in source
