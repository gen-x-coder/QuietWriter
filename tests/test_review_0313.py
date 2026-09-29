import tempfile
from pathlib import Path

import pytest

from quietwriter.exporting.settings import ExportSettingsStore, default_export_settings
from quietwriter.planning_storage import PlanningStore
from quietwriter.publication_storage import PublicationStore
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import CorruptSourceError, Library


def make_book():
    td = tempfile.TemporaryDirectory()
    lib = Library(Path(td.name))
    book = lib.create_book('Review 0.31.3')
    lib.track_book(book)
    return td, lib, book


def test_export_settings_save_refreshes_revision_baseline():
    td, lib, book = make_book()
    try:
        store = ExportSettingsStore(lib)
        settings = default_export_settings()
        settings['format'] = 'pdf'
        store.save(book, settings)
        # A later normal save may not see our own export preference write as external.
        lib.verify_book_unchanged(book)
    finally:
        td.cleanup()


def test_export_settings_still_detect_external_change():
    td, lib, book = make_book()
    try:
        store = ExportSettingsStore(lib)
        store.save(book, default_export_settings())
        store.path(book).write_text('{"format":"markdown"}', encoding='utf-8')
        with pytest.raises(ExternalModificationError):
            store.save(book, default_export_settings())
    finally:
        td.cleanup()


@pytest.mark.parametrize('name,save', [
    ('characters.json', lambda store, book: store.save_characters(book, [])),
    ('outline.json', lambda store, book: store.save_scenes(book, [])),
])
def test_truncated_planning_json_is_not_overwritten(name, save):
    td, lib, book = make_book()
    try:
        store = PlanningStore(lib)
        path = Path(book.path) / 'planning' / name
        path.parent.mkdir(exist_ok=True)
        original = b'{"version":1,"characters":[{"name":"Alfa"}'
        if name == 'outline.json':
            original = b'{"version":1,"scenes":[{"title":"Alfa"}'
        path.write_bytes(original)
        lib.refresh_book_revision(book)
        with pytest.raises(CorruptSourceError):
            save(store, book)
        assert path.read_bytes() == original
    finally:
        td.cleanup()


def test_truncated_publication_json_is_not_overwritten():
    td, lib, book = make_book()
    try:
        store = PublicationStore(lib)
        path = store.config_path(book)
        path.parent.mkdir(exist_ok=True)
        original = b'{"version":1,"enabled":["foreword"'
        path.write_bytes(original)
        lib.refresh_book_revision(book)
        with pytest.raises(CorruptSourceError):
            store.save(book, store.load(book))
        assert path.read_bytes() == original
    finally:
        td.cleanup()


def test_truncated_export_json_is_not_overwritten():
    td, lib, book = make_book()
    try:
        store = ExportSettingsStore(lib)
        path = store.path(book)
        path.parent.mkdir(exist_ok=True)
        original = b'{"version":1,"format":"pdf"'
        path.write_bytes(original)
        lib.refresh_book_revision(book)
        with pytest.raises(CorruptSourceError):
            store.save(book, default_export_settings())
        assert path.read_bytes() == original
    finally:
        td.cleanup()


def test_corrupt_publication_text_loads_tolerantly_but_cannot_be_overwritten():
    td, lib, book = make_book()
    try:
        store = PublicationStore(lib)
        path = store.text_path(book, 'foreword')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'voorwoord-\xff')
        lib.refresh_book_revision(book)
        assert store.text_is_corrupt(book, 'foreword') is True
        assert store.load_text(book, 'foreword') == ''
        with pytest.raises(CorruptSourceError):
            store.save_text(book, 'foreword', 'nieuw')
        assert path.read_bytes() == b'voorwoord-\xff'
    finally:
        td.cleanup()


def test_spell_follow_refreshes_rows_when_document_revision_changes_by_source():
    source = Path('quietwriter/ui/spell_panel.py').read_text(encoding='utf-8')
    assert "revision != self._rows_rev" in source
    assert "self.refresh(select_in_editor=False)" in source


def test_editor_spell_follow_uses_contents_change_instead_of_revision_skip_by_source():
    source = Path('quietwriter/ui/editor_page.py').read_text(encoding='utf-8')
    assert 'contentsChange.connect(self._spell_contents_changed)' in source
    assert 'removed + added <= 0' in source
    assert '_spell_last_revision' not in source


def test_integrity_gap_visibility_tracks_book_mode_by_source():
    source = Path('quietwriter/ui/main_window.py').read_text(encoding='utf-8')
    assert "advanced = self.settings.value('advanced_options', True, bool)" in source
    assert 'self.integrity_gap.setVisible(self.rail_expanded and has_book and advanced)' in source
