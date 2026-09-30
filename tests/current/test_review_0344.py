import json
import tempfile
from pathlib import Path

import pytest

from quietwriter.ai.planning_context import (
    PlanningSelection,
    build_planning_context_result,
    chapter_planning_preview,
)
from quietwriter.planning_models import Character, Scene
from quietwriter.planning_storage import PlanningStore
from quietwriter.planning_validation import FuturePlanningFormatError
from quietwriter.storage import Library


def test_chapter_planning_preview_shows_saved_scene_fields_but_is_separate_from_selected_context():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('Preview')
        chapter = next(c for sec in book.sections for c in sec.chapters)
        store = PlanningStore(lib)
        char = Character(id='c1', name='Anna')
        scene = Scene(
            id='s1', chapter_id=chapter.id, title='Aankomst', synopsis='Anna arriveert.',
            character_ids=['c1'], location='Station', goal='Een kamer vinden',
            conflict='Alles is vol', outcome='Ze slaapt bij Bram', notes='Regen benadrukken',
            status='concept',
        )
        store.save_characters(book, [char])
        store.save_scenes(book, [scene])
        book = lib.load_book(book.path)

        preview = chapter_planning_preview(lib, book, chapter.id)
        assert preview.error == ''
        assert preview.labels == ['1 scène', '1 personage']
        for text in ('Aankomst', 'Anna arriveert.', 'Een kamer vinden', 'Alles is vol', 'Ze slaapt bij Bram', 'Regen benadrukken', 'Anna'):
            assert text in preview.text

        selected = build_planning_context_result(lib, book, PlanningSelection())
        assert selected.text == ''
        assert selected.labels == []
        assert selected.error == ''


def test_planning_context_error_is_structured_not_encoded_in_labels():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('Future')
        path = book.path / 'planning' / 'outline.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'version': 2, 'scenes': []}), encoding='utf-8')
        book = lib.load_book(book.path)

        result = build_planning_context_result(lib, book, PlanningSelection(scene_ids={'s1'}))
        assert result.text == ''
        assert result.labels == []
        assert 'nieuwere QuietWriter' in result.error


def test_future_planning_with_utf8_bom_is_still_recognised_as_newer_and_blocks_history_restore():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('BOM future')
        planning = book.path / 'planning'
        planning.mkdir(parents=True, exist_ok=True)
        outline = planning / 'outline.json'
        outline.write_text(json.dumps({'version': 1, 'scenes': []}), encoding='utf-8')
        lib.refresh_book_revision(book)
        version = lib.create_version(book, kind='manual')

        payload = json.dumps({'version': 2, 'scenes': []}, ensure_ascii=False).encode('utf-8')
        outline.write_bytes(b'\xef\xbb\xbf' + payload)
        lib.refresh_book_revision(book)

        # PlanningStore uses utf-8-sig, so this is newer data rather than corruption.
        with pytest.raises(FuturePlanningFormatError):
            PlanningStore(lib).load_scenes(book)
        with pytest.raises(FuturePlanningFormatError):
            lib.restore_version(book, version['id'])


def test_ai_ui_makes_chapter_planning_explicit_and_user_controllable():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    assert "QCheckBox('Planning van dit hoofdstuk gebruiken')" in source
    assert "ai_use_chapter_planning" in source
    assert "wordt meegestuurd" in source
    assert "wordt niet meegestuurd" in source
    send_start = source.index('    def send(self):')
    send_end = source.index('    def _continue_send(', send_start)
    send_body = source[send_start:send_end]
    assert 'chapter_planning_text = self._active_chapter_planning_text()' in send_body
    assert 'planning.text, chapter_planning_text' in send_body
