from pathlib import Path

import quietwriter


def test_release_metadata_and_preserved_history():
    assert quietwriter.__version__ == "1.7.0"

    changelog = Path("documents/CHANGELOG.md").read_text(encoding="utf-8-sig")
    assert changelog.startswith(f"## {quietwriter.__version__} —")

    # De ontwikkelgeschiedenis is gearchiveerd, niet weggegooid.
    archive = Path("documents/archive")
    assert (archive / "README.md").is_file()
    old = (archive / "CHANGELOG_TOT_1_5_0_DEV63.md").read_text(encoding="utf-8-sig")
    assert old.startswith("## 1.5.0-dev.63")
    notes = archive / "release-notes" / "RELEASE_NOTES_1.5.0-dev.28.md"
    assert "update" in notes.read_text(encoding="utf-8").lower()
    history = (archive / "research" / "ROADMAP_HISTORY_TO_1_2_13.md").read_text(encoding="utf-8")
    assert "### 1.0.0 — uitgebracht" in history


def test_agents_file_names_the_core_rules():
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    for rule in ("Blijf schrijven", "Markdown", "stil", "self_update.py", "documents/archive"):
        assert rule in agents
