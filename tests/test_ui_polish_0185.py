from pathlib import Path


def _source(path):
    return Path(path).read_text(encoding="utf-8")


def test_bookshelf_hero_is_full_width_with_transparent_inner():
    source = _source("quietwriter/ui/bookshelf.py")
    theme = _source("quietwriter/themes.py")
    assert "hero_layout = QVBoxLayout(hero)" in source
    assert "hero_layout.addWidget(_centered_host(hero_inner))" in source
    assert "hero_inner.setObjectName('bookshelfHeroInner')" in source
    assert "QWidget#centeredMaxWidthHost, QWidget#bookshelfHeroInner {{ background: transparent; }}" in theme


def test_centered_host_expands_to_available_width_instead_of_three_equal_columns():
    source = _source("quietwriter/ui/bookshelf.py")
    assert "self._content.setFixedWidth(min(self._max_width, available))" in source
    assert "row.addWidget(content, 0, Qt.AlignHCenter)" in source
    assert source.count("row.addStretch(1)") == 0
