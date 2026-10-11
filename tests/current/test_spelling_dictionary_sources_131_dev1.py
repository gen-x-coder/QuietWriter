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
        bundled_dic, _ = _write_dictionary(root / "bundled")
        office_dic, _ = _write_dictionary(root / "onlyoffice")
        catalog = DictionaryCatalog(
            root / "workspace",
            extra_roots=[
                (root / "bundled", "Meegeleverd"),
                (root / "onlyoffice", "ONLYOFFICE"),
            ],
        )
        sources = {entry.source for entry in catalog.entries("nl_NL")}
        assert sources == {"Meegeleverd", "ONLYOFFICE"}
        assert catalog.get("nl_NL", "Meegeleverd").dic == bundled_dic
        assert catalog.get("nl_NL", "ONLYOFFICE").dic == office_dic

def test_explicit_source_falls_back_when_provider_is_unavailable():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bundled_dic, _ = _write_dictionary(root / "bundled")
        catalog = DictionaryCatalog(
            root / "workspace",
            extra_roots=[(root / "bundled", "Meegeleverd")],
        )
        selected = catalog.get("nl_NL", "ONLYOFFICE")
        assert selected is not None
        assert selected.source == "Meegeleverd"
        assert selected.dic == bundled_dic

def test_custom_dictionary_remains_a_separate_provider_choice():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source_dic, _ = _write_dictionary(root / "source")
        bundled_dic, _ = _write_dictionary(root / "bundled")
        catalog = DictionaryCatalog(
            root / "workspace",
            extra_roots=[(root / "bundled", "Meegeleverd")],
        )
        added = catalog.add_custom(source_dic)
        assert added.source == "Werkmap"
        assert catalog.get("nl_NL", "Werkmap").source == "Werkmap"
        assert {"Werkmap", "Meegeleverd"}.issubset(
            {entry.source for entry in catalog.entries("nl_NL")}
        )
