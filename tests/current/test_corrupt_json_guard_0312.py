import tempfile
from pathlib import Path
import pytest
from quietwriter.storage import Library, CorruptSourceError
from quietwriter.planning_storage import PlanningStore
from quietwriter.publication_storage import PublicationStore
from quietwriter.exporting.settings import ExportSettingsStore, default_export_settings
from quietwriter.integrity import BookIntegrityChecker

def make_book():
    td=tempfile.TemporaryDirectory(); lib=Library(Path(td.name)); book=lib.create_book("Test"); return td,lib,book

def test_planning_json_utf8_is_tolerant_but_not_overwritable():
    td,lib,book=make_book(); store=PlanningStore(lib); p=Path(book.path)/"planning/characters.json"; p.parent.mkdir(exist_ok=True); p.write_bytes(b"\xff")
    assert store.load_characters(book)==[]
    with pytest.raises(CorruptSourceError): store.save_characters(book,[])
    assert p.read_bytes()==b"\xff"; td.cleanup()

def test_publication_json_utf8_is_tolerant_but_not_overwritable():
    td,lib,book=make_book(); store=PublicationStore(lib); p=store.config_path(book); p.parent.mkdir(exist_ok=True); p.write_bytes(b"\xff")
    store.load(book)
    with pytest.raises(CorruptSourceError): store.save(book, store.load(book))
    assert p.read_bytes()==b"\xff"; td.cleanup()

def test_export_settings_utf8_is_tolerant_but_not_overwritable_and_audited():
    td,lib,book=make_book(); store=ExportSettingsStore(); p=store.path(book); p.parent.mkdir(exist_ok=True); p.write_bytes(b"\xff")
    assert store.load(book)["format"]=="epub"
    with pytest.raises(CorruptSourceError): store.save(book, default_export_settings())
    report=BookIntegrityChecker().audit_folder(Path(book.path))
    assert any(i.path=="export/settings.json" for i in report.issues)
    assert p.read_bytes()==b"\xff"; td.cleanup()
