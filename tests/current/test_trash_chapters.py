import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from quietwriter.storage import Library


def _book_with_two_chapters(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Prullenbaktest')
    first = book.sections[0].chapters[0]
    first.title = 'Eerste hoofdstuk'
    lib.save_manifest(book)
    lib.save_chapter(book, first, 'eerste inhoud')
    second = lib.add_chapter(book, book.sections[0], 'Tweede hoofdstuk')
    lib.save_chapter(book, second, 'tweede inhoud')
    return lib, book, first, second


def test_deleted_chapter_has_metadata_and_is_listed():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, _second = _book_with_two_chapters(Path(td))
        assert lib.delete_chapter(book, first.id)

        rows = lib.list_trashed_chapters()
        assert len(rows) == 1
        row = rows[0]
        assert row['book_id'] == book.id
        assert row['book_title'] == book.title
        assert row['chapter_id'] == first.id
        assert row['title'] == 'Eerste hoofdstuk'
        assert row['section_id'] == book.sections[0].id
        assert row['book_available'] is True
        assert row['metadata_path'].exists()
        meta = json.loads(row['metadata_path'].read_text(encoding='utf-8'))
        assert meta['chapter_index'] == 0
        assert meta['chapter_title'] == 'Eerste hoofdstuk'


def test_restore_deleted_chapter_restores_content_and_position():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, second = _book_with_two_chapters(Path(td))
        first_id = first.id
        assert lib.delete_chapter(book, first_id)
        row = lib.list_trashed_chapters()[0]

        restored = lib.restore_trashed_chapter(row['path'], book=book)
        assert restored.id == first_id
        assert [c.id for c in book.sections[0].chapters] == [first_id, second.id]
        assert lib.read_chapter(book, restored) == 'eerste inhoud'
        assert lib.list_trashed_chapters() == []

        reloaded = lib.load_book(book.path)
        assert [c.id for c in reloaded.sections[0].chapters] == [first_id, second.id]
        assert lib.read_chapter(reloaded, reloaded.sections[0].chapters[0]) == 'eerste inhoud'


def test_restore_with_tracked_active_book_refreshes_revision():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, _second = _book_with_two_chapters(Path(td))
        lib.track_book(book)
        assert lib.delete_chapter(book, first.id)
        row = lib.list_trashed_chapters()[0]
        before_restore = lib.tracked_revision(book)
        restored = lib.restore_trashed_chapter(row['path'], book=book)
        after_restore = lib.tracked_revision(book)
        assert restored.id == first.id
        assert after_restore is not None and after_restore != before_restore
        # A subsequent normal save must not see the restore itself as an external change.
        lib.save_chapter(book, restored, 'na herstel aangepast')
        assert lib.read_chapter(book, restored) == 'na herstel aangepast'


def test_restore_recreates_deleted_original_section():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td))
        book = lib.create_book('Sectietest')
        original = lib.add_section(book, 'Oude sectie')
        chapter = lib.add_chapter(book, original, 'Terugkomer')
        lib.save_chapter(book, chapter, 'inhoud')
        assert lib.delete_chapter(book, chapter.id)
        # Section is now empty; remove it to simulate a later structure edit.
        book.sections.remove(original)
        lib.save_manifest(book)

        row = lib.list_trashed_chapters()[0]
        restored = lib.restore_trashed_chapter(row['path'], book=book)
        section = next(sec for sec in book.sections if sec.id == original.id)
        assert section.title == 'Oude sectie'
        assert section.chapters[0].id == restored.id
        assert lib.read_chapter(book, restored) == 'inhoud'


def test_restore_legacy_0213_chapter_without_sidecar_uses_first_section():
    with tempfile.TemporaryDirectory() as td:
        lib, book, _first, _second = _book_with_two_chapters(Path(td))
        legacy_id = 'legacy-chapter-id'
        folder = lib.trash_dir / 'chapters' / book.id
        folder.mkdir(parents=True, exist_ok=True)
        legacy = folder / f'20260923-120000__{legacy_id}__oude-titel.md'
        legacy.write_text('legacy inhoud', encoding='utf-8')

        rows = lib.list_trashed_chapters()
        row = next(row for row in rows if row['chapter_id'] == legacy_id)
        assert row['title'] == 'Oude titel'
        restored = lib.restore_trashed_chapter(legacy, book=book)
        assert restored.id == legacy_id
        assert restored.title == 'Oude titel'
        assert lib.read_chapter(book, restored) == 'legacy inhoud'


def test_restoring_chapter_requires_its_book_to_be_available():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, _second = _book_with_two_chapters(Path(td))
        assert lib.delete_chapter(book, first.id)
        chapter_path = lib.list_trashed_chapters()[0]['path']
        lib.delete_book(book)

        with pytest.raises(RuntimeError, match='Herstel eerst het bijbehorende boek'):
            lib.restore_trashed_chapter(chapter_path)

        trashed_book = lib.list_trashed_books()[0]
        restored_book = lib.restore_trashed_book(trashed_book['path'])
        restored_chapter = lib.restore_trashed_chapter(chapter_path, book=restored_book)
        assert lib.read_chapter(restored_book, restored_chapter) == 'eerste inhoud'


def test_permanent_book_delete_also_purges_its_chapter_trash():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, _second = _book_with_two_chapters(Path(td))
        assert lib.delete_chapter(book, first.id)
        chapter_root = lib.trash_dir / 'chapters' / book.id
        assert chapter_root.exists()
        lib.delete_book(book)
        trash_book = lib.list_trashed_books()[0]['path']

        lib.permanently_delete_trashed_book(trash_book)
        assert not trash_book.exists()
        assert not chapter_root.exists()


def test_empty_trash_removes_book_and_chapter_trash():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, _second = _book_with_two_chapters(Path(td))
        assert lib.delete_chapter(book, first.id)
        lib.delete_book(book)
        lib.empty_trash()
        assert lib.list_trashed_books() == []
        assert lib.list_trashed_chapters() == []


def test_restore_manifest_failure_rolls_back_live_file_and_model_but_keeps_trash():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, second = _book_with_two_chapters(Path(td))
        assert lib.delete_chapter(book, first.id)
        row = lib.list_trashed_chapters()[0]
        before = [c.id for c in book.sections[0].chapters]

        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('disk full')):
            with pytest.raises(OSError, match='disk full'):
                lib.restore_trashed_chapter(row['path'], book=book)

        assert [c.id for c in book.sections[0].chapters] == before == [second.id]
        assert row['path'].exists()
        assert row['metadata_path'].exists()
        assert not any((book.path / 'chapters').glob(f'{first.id}.md'))


def test_trash_ui_and_text_prompt_source_contracts():
    root = Path(__file__).resolve().parents[2]
    trash = (root / 'quietwriter/ui/trash_page.py').read_text(encoding='utf-8')
    dialogs = (root / 'quietwriter/ui/dialogs.py').read_text(encoding='utf-8')
    editor = (root / 'quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'list_trashed_chapters()' in trash
    assert 'restore_trashed_chapter' in trash
    assert 'permanently_delete_trashed_chapter' in trash
    assert 'errors = []' in trash
    assert "save.setText(tr('common.save', 'Opslaan'))" in dialogs
    assert "cancel.setText(tr('common.cancel', 'Annuleren'))" in dialogs
    assert "prompt_text(self, tr('editor.rename_chapter.title', 'Hoofdstuk hernoemen')" in editor
    assert 'QInputDialog.getText' not in editor
