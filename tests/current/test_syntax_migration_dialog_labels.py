from pathlib import Path
import json


def test_syntax_migration_buttons_are_owned_and_translated():
    source = Path("quietwriter/ui/main_window.py").read_text(encoding="utf-8")
    section = source[source.index("migration_box = QMessageBox"):source.index("assume_escape_era = None")]
    assert "QMessageBox.Yes | QMessageBox.Cancel" not in section
    assert "book.syntax_migration.update_button" in section
    assert "book.syntax_migration.do_not_open_button" in section
    for lang in ("nl", "en", "de", "fr", "es"):
        data = json.loads(Path(f"quietwriter/locales/{lang}.json").read_text(encoding="utf-8"))
        assert data["book.syntax_migration.update_button"]
        assert data["book.syntax_migration.do_not_open_button"]


def test_dutch_migration_actions_are_explicit():
    data = json.loads(Path("quietwriter/locales/nl.json").read_text(encoding="utf-8"))
    assert data["book.syntax_migration.update_button"] == "Boek bijwerken"
    assert data["book.syntax_migration.do_not_open_button"] == "Niet openen"
