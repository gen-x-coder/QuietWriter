from pathlib import Path
import importlib.util


def _module():
    path = Path(__file__).resolve().parents[2] / "tools" / "render_release_readme.py"
    spec = importlib.util.spec_from_file_location("render_release_readme", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_nl_en_dynamic_version_in_windows_guide():
    source = (Path(__file__).resolve().parents[2] / "documents" / "LEESMIJ.txt").read_text(encoding="utf-8-sig")
    render = _module().render
    for version, test in [("1.5.0-dev.1", True), ("1.5.0-rc1", True), ("1.5.0", False), ("1.5.1", False)]:
        output = render(source, version)
        assert output.count("QuietWriter " + version) == 2
        assert ("Dit is een ontwikkel- of testversie" in output) == test
        assert ("This is a development or test build" in output) == test
        assert "QuietWriter 1.0" not in output
        assert "{{" not in output

def test_invalid_version_or_missing_placeholder_fails_closed():
    import pytest
    render = _module().render
    with pytest.raises(ValueError):
        render("{{VERSION}} {{STATUS_NL}} {{STATUS_EN}}", "1.5.0; echo unsafe")
    with pytest.raises(ValueError):
        render("{{VERSION}}", "1.5.0")
