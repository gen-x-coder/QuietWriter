import tempfile
from pathlib import Path
from unittest import mock

import pytest

from quietwriter.storage import Library



def _book_with_two_chapters(tmp_path: Path):
    lib = Library(tmp_path)
    book = lib.create_book('Review test')
    first = book.sections[0].chapters[0]
    lib.save_chapter(book, first, 'eerste hoofdstuk')
    second = lib.add_chapter(book, book.sections[0], 'Tweede')
    lib.save_chapter(book, second, 'tweede hoofdstuk')
    return lib, book, first, second


def test_delete_chapter_manifest_failure_keeps_model_and_source_and_rolls_back_trash():
    with tempfile.TemporaryDirectory() as td:
        lib, book, first, second = _book_with_two_chapters(Path(td))
        source = book.path / first.file
        before_ids = [c.id for c in book.sections[0].chapters]

        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('disk full')):
            with pytest.raises(OSError, match='disk full'):
                lib.delete_chapter(book, first.id)

        assert [c.id for c in book.sections[0].chapters] == before_ids
        assert source.exists()
        assert source.read_text(encoding='utf-8') == 'eerste hoofdstuk'
        trash_dir = lib.trash_dir / 'chapters' / book.id
        assert not trash_dir.exists() or not list(trash_dir.glob('*.md'))
        reloaded = lib.load_book(book.path)
        assert [c.id for c in reloaded.sections[0].chapters] == before_ids


def test_add_section_manifest_failure_rolls_back_live_model():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td)); book = lib.create_book('Review test')
        before = list(book.sections)
        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('write failed')):
            with pytest.raises(OSError):
                lib.add_section(book, 'Nieuwe sectie')
        assert book.sections == before


def test_add_chapter_manifest_failure_removes_live_chapter_and_new_file():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td)); book = lib.create_book('Review test')
        section = book.sections[0]
        before_ids = [c.id for c in section.chapters]
        existing_files = set((book.path / 'chapters').glob('*.md'))
        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('write failed')):
            with pytest.raises(OSError):
                lib.add_chapter(book, section, 'Mislukt')
        assert [c.id for c in section.chapters] == before_ids
        assert set((book.path / 'chapters').glob('*.md')) == existing_files


def test_rename_chapter_and_section_roll_back_on_manifest_failure():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td)); book = lib.create_book('Review test')
        chapter = book.sections[0].chapters[0]
        section = book.sections[0]
        chapter_title = chapter.title
        section_title = section.title
        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('write failed')):
            with pytest.raises(OSError):
                lib.rename_chapter(book, chapter.id, 'Andere titel')
        assert chapter.title == chapter_title
        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('write failed')):
            with pytest.raises(OSError):
                lib.rename_section(book, section.id, 'Andere sectie')
        assert section.title == section_title


def test_duplicate_chapter_manifest_failure_removes_copy_and_file():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td)); book = lib.create_book('Review test')
        source = book.sections[0].chapters[0]
        lib.save_chapter(book, source, 'inhoud')
        before_ids = [c.id for c in book.sections[0].chapters]
        before_files = set((book.path / 'chapters').glob('*.md'))
        with mock.patch.object(lib, '_write_manifest_unchecked', side_effect=OSError('write failed')):
            with pytest.raises(OSError):
                lib.duplicate_chapter(book, source.id)
        assert [c.id for c in book.sections[0].chapters] == before_ids
        assert set((book.path / 'chapters').glob('*.md')) == before_files


def test_move_chapter_retries_user_intent_after_external_conflict_in_source():
    source = (Path(__file__).resolve().parents[1] / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    move = source[source.index('    def move_chapter'):source.index('    def tree_context_menu')]
    assert 'retried_after_conflict = False' in move
    assert 'if not self._handle_concurrency_issue(exc):' in move
    assert 'retried_after_conflict = True' in move
    assert 'continue' in move
    # The retry must calculate a fresh proposal from the potentially reloaded book.
    assert move.count('proposed = copy.deepcopy(self.book.sections)') == 1
    assert 'while True:' in move
    assert 'source_exists' in move and 'target_still_exists' in move


def test_structural_ui_operations_handle_non_conflict_io_failures_in_source():
    source = (Path(__file__).resolve().parents[1] / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
    # Storage now rolls back safely; the UI must still turn ordinary write failures
    # into a user-visible failed action instead of an uncaught traceback.
    required_messages = [
        'Het hoofdstuk is niet hernoemd.',
        'Het hoofdstuk is niet gedupliceerd.',
        'De sectie is niet hernoemd.',
        'De sectie is niet verwijderd.',
        'De sectie is niet toegevoegd.',
        'Het hoofdstuk is niet toegevoegd.',
    ]
    for message in required_messages:
        assert message in source
