import json
import tempfile
from pathlib import Path

import pytest

from quietwriter.ai.planning_context import PlanningSelection, build_planning_context, options_for_book
from quietwriter.planning_validation import FuturePlanningFormatError
from quietwriter.storage import Library


def _future_outline(book):
    path = book.path / 'planning' / 'outline.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'version': 2, 'scenes': []}), encoding='utf-8')
    return path


def test_ai_planning_context_degrades_gracefully_for_future_planning():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('Future planning')
        _future_outline(book)
        book = lib.load_book(book.path)

        options = options_for_book(lib, book)
        assert 'nieuwere QuietWriter' in options.error
        assert options.characters == []
        assert options.scenes == []

        text, labels = build_planning_context(
            lib, book, PlanningSelection(scene_ids={'s1'})
        )
        assert text == ''
        assert labels == []


def test_ai_planning_context_degrades_gracefully_for_corrupt_structure():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('Corrupt planning')
        path = book.path / 'planning' / 'outline.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'version': 1, 'scenes': 5}), encoding='utf-8')
        book = lib.load_book(book.path)

        options = options_for_book(lib, book)
        assert 'niet betrouwbaar' in options.error
        text, labels = build_planning_context(
            lib, book, PlanningSelection(scene_ids={'s1'})
        )
        assert text == ''
        assert labels == []


def test_history_restore_refuses_to_roll_back_future_planning():
    with tempfile.TemporaryDirectory() as td:
        lib = Library(Path(td) / 'workspace')
        book = lib.create_book('History guard')
        planning = book.path / 'planning'
        planning.mkdir(parents=True, exist_ok=True)
        outline = planning / 'outline.json'
        outline.write_text(json.dumps({'version': 1, 'scenes': []}), encoding='utf-8')
        lib.refresh_book_revision(book)
        version = lib.create_version(book, kind='manual')

        future_bytes = json.dumps({'version': 2, 'scenes': [{'id': 'newer'}]}).encode('utf-8')
        outline.write_bytes(future_bytes)
        lib.refresh_book_revision(book)

        with pytest.raises(FuturePlanningFormatError):
            lib.restore_version(book, version['id'])
        assert outline.read_bytes() == future_bytes


def test_visual_contract_for_context_labels_and_rail_separator():
    themes = Path('quietwriter/themes.py').read_text(encoding='utf-8')
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'qproperty-indent: 0' in themes
    assert 'min-height: 2px; max-height: 2px' in themes
    assert 'separator.setFixedHeight(2)' in main
