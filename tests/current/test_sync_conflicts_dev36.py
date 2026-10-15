from pathlib import Path
import pytest

from quietwriter.sync_conflicts import discover_conflict_copies, is_conflict_copy


def test_conflict_copy_detection_and_no_modifications(tmp_path):
    books = tmp_path / 'books' / 'example' / 'chapters'
    books.mkdir(parents=True)
    original = books / 'chapter.md'
    original.write_text('original content', encoding='utf8')
    conflict = books / "chapter (Lucas's conflicted copy 2026-10-13).md"
    conflict.write_text('other content', encoding='utf8')
    assert is_conflict_copy(conflict.name)
    assert discover_conflict_copies(tmp_path) == [conflict]
    assert original.read_text(encoding='utf8') == 'original content'
    assert conflict.read_text(encoding='utf8') == 'other content'


def test_scan_respects_bounds_and_skips_links(tmp_path):
    books = tmp_path / 'books'
    books.mkdir()
    external = tmp_path / 'outside'
    external.mkdir()
    (external / 'foreign conflicted copy.md').write_text('private')
    try:
        (books / 'linked').symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        if getattr(exc, "winerror", None) == 1314 or isinstance(exc, NotImplementedError):
            pytest.skip("Windows account lacks symlink creation privilege")
        raise
    assert discover_conflict_copies(tmp_path) == []
    for i in range(4):
        (books / f'{i} conflicted copy.md').write_text(str(i))
    assert len(discover_conflict_copies(tmp_path,max_files=2)) == 2
    assert len(discover_conflict_copies(tmp_path,max_visited=2)) <= 2


def test_no_missing_workspace_created(tmp_path):
    missing = tmp_path / 'not_here'
    assert discover_conflict_copies(missing) == []
    assert not missing.exists()
