import json
from pathlib import Path

import pytest

from quietwriter.chapter_context import build_chapter_context
from quietwriter.integrity import BookIntegrityChecker
from quietwriter.planning_models import Character, Scene
from quietwriter.planning_storage import PlanningStore
from quietwriter.planning_validation import FuturePlanningFormatError
from quietwriter.storage import CorruptSourceError, Library


def make(tmp_path):
    library = Library(Path(tmp_path))
    book = library.create_book('Test')
    library.track_book(book)
    return library, book, PlanningStore(library)


@pytest.mark.parametrize('payload', [
    {'version': 1, 'scenes': 5},
    {'version': 1, 'scenes': [{'id': 's1', 'character_ids': None}]},
])
def test_outline_wrong_shape_fails_closed(tmp_path, payload):
    _library, book, store = make(tmp_path)
    path = store.root(book) / 'outline.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(CorruptSourceError):
        store.load_scenes(book)


@pytest.mark.parametrize('payload', [
    {'version': 1, 'characters': 5},
    {'version': 1, 'characters': [{'id': 'c1', 'relations': 5}]},
])
def test_characters_wrong_shape_fails_closed(tmp_path, payload):
    _library, book, store = make(tmp_path)
    path = store.root(book) / 'characters.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(CorruptSourceError):
        store.load_characters(book)


def test_integrity_reports_structural_planning_error(tmp_path):
    _library, book, store = make(tmp_path)
    path = store.root(book) / 'outline.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'version': 1, 'scenes': 5}), encoding='utf-8')
    report = BookIntegrityChecker().audit_folder(book.path)
    assert any(issue.code == 'aux_json_invalid' and issue.path == 'planning/outline.json' for issue in report.errors)


def test_chapter_context_contains_full_saved_scene_detail():
    person = Character(id='c1', name='Anna')
    scene = Scene(
        id='s1', chapter_id='h1', title='Aankomst', synopsis='Korte synopsis',
        character_ids=['c1'], location='Delft', status='uitgewerkt',
        goal='Binnenkomen', conflict='De deur zit vast', outcome='Ze vindt een sleutel', notes='Let op de regen.'
    )
    context = build_chapter_context('h1', [scene], [person])
    row = context.scenes[0]
    assert (row.goal, row.conflict, row.outcome, row.notes) == (
        'Binnenkomen', 'De deur zit vast', 'Ze vindt een sleutel', 'Let op de regen.'
    )


def test_statusbar_uses_persistent_document_status_contract():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert 'self.main.set_document_status(' in source
    assert 'def _status_message_changed' in main
    assert 'def _restore_document_status' in main


def test_collapsed_separator_is_real_styled_frame():
    main = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    theme = Path('quietwriter/themes.py').read_text(encoding='utf-8')
    assert 'separator.setFrameShape(QFrame.NoFrame)' in main
    assert "QFrame#navGroupSeparator {{ background: {t['border']}" in theme


def test_newer_planning_format_is_not_corruption(tmp_path):
    _library, book, store = make(tmp_path)
    for relative, payload, loader in (
        ('outline.json', {'version': 2, 'scenes': []}, store.load_scenes),
        ('characters.json', {'version': 2, 'characters': []}, store.load_characters),
    ):
        path = store.root(book) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding='utf-8')
        with pytest.raises(FuturePlanningFormatError):
            loader(book)


def test_integrity_newer_planning_format_is_not_recoverable(tmp_path):
    _library, book, store = make(tmp_path)
    path = store.root(book) / 'outline.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'version': 2, 'scenes': [{'id': 'new'}]}), encoding='utf-8')
    report = BookIntegrityChecker().audit_folder(book.path)
    issue = next(i for i in report.errors if i.path == 'planning/outline.json')
    assert issue.code == 'aux_json_newer'
    assert issue.recoverable is False
    assert 'Werk QuietWriter bij' in issue.message
