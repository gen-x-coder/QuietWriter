from pathlib import Path
import importlib.util


def _load_make_version_info():
    root = Path(__file__).resolve().parents[2]
    path = root / "packaging" / "make_version_info.py"
    spec = importlib.util.spec_from_file_location("qw_make_version_info", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_rc_uses_semver_core_for_windows_numeric_version():
    module = _load_make_version_info()
    assert module.version_tuple("1.0.0-rc1") == (1, 0, 0, 0)
    assert module.version_tuple("1.0.0") == (1, 0, 0, 0)


def test_rc_release_notes_and_workflow_are_wired():
    root = Path(__file__).resolve().parents[2]
    notes = root / "documents" / "RELEASE_NOTES_1.0.0-rc1.md"
    workflow = (root / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")
    changelog = (root / "documents" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert notes.is_file()
    assert "body_path: documents/RELEASE_NOTES_1.0.0-rc1.md" in workflow
    assert "contains(github.ref_name, 'rc')" in workflow
    assert changelog.startswith("# Changelog\n\n## 1.0.0-rc1")
