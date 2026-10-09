from pathlib import Path
import tempfile

from quietwriter.dictionary_catalog import DictionaryCatalog


def _write_dictionary(root: Path, locale: str = "nl_NL"):
    root.mkdir(parents=True, exist_ok=True)
    dic = root / f"{locale}.dic"
    aff = root / f"{locale}.aff"
    dic.write_text("2\nboek\nschrijven\n", encoding="utf-8")
    aff.write_text("SET UTF-8\n", encoding="utf-8")
    return dic, aff


def test_catalog_keeps_alternative_providers_for_same_locale():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bundled = root / "bundled"
        office = root / "onlyoffice"
        bundled_dic, _ = _write_dictionary(bundled)
        office_dic, _ = _write_dictionary(office)

        catalog = DictionaryCatalog(
            root / "workspace",
            extra_roots=[
                (bundled, "Meegeleverd"),
                (office, "ONLYOFFICE"),
            ],
        )
        matches = catalog.entries("nl_NL")
        sources = {entry.source for entry in matches}

        assert sources == {"Meegeleverd", "ONLYOFFICE"}
        assert catalog.get("nl_NL", "Meegeleverd").dic == bundled_dic
        assert catalog.get("nl_NL", "ONLYOFFICE").dic == office_dic


def test_explicit_source_falls_back_when_provider_is_unavailable():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bundled = root / "bundled"
        bundled_dic, _ = _write_dictionary(bundled)

        catalog = DictionaryCatalog(
            root / "workspace",
            extra_roots=[(bundled, "Meegeleverd")],
        )
        selected = catalog.get("nl_NL", "ONLYOFFICE")

        assert selected is not None
        assert selected.source == "Meegeleverd"
        assert selected.dic == bundled_dic


def test_custom_dictionary_remains_a_separate_provider_choice():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source_dir = root / "source"
        bundled = root / "bundled"
        source_dic, _ = _write_dictionary(source_dir)
        _write_dictionary(bundled)

        catalog = DictionaryCatalog(
            root / "workspace",
            extra_roots=[(bundled, "Meegeleverd")],
        )
        added = catalog.add_custom(source_dic)

        assert added.source == "Werkmap"
        assert catalog.get("nl_NL", "Werkmap").source == "Werkmap"
        assert {"Werkmap", "Meegeleverd"}.issubset(
            {entry.source for entry in catalog.entries("nl_NL")}
        )


def test_settings_and_editor_persist_dictionary_source_selection():
    settings = Path("quietwriter/ui/settings_page.py").read_text(encoding="utf-8")
    editor = Path("quietwriter/ui/editor_page.py").read_text(encoding="utf-8")

    assert "self.spell_dictionary_source = QuietComboBox()" in settings
    assert "'spell_dictionary_source': self.spell_dictionary_source.currentData() or ''" in settings
    assert "preserve_source=str(settings.value('spell_dictionary_source', '') or '')" in settings
    assert "source = str(self.main.settings.value('spell_dictionary_source', '') or '')" in editor
    assert "catalog.get(locale, source) if source else catalog.get(locale)" in editor
