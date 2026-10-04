from pathlib import Path

import quietwriter


def test_stable_1_0_release_metadata():
    assert quietwriter.__version__ == "1.0.1"

    changelog = Path("documents/CHANGELOG.md").read_text(encoding="utf-8-sig")
    assert changelog.startswith("## 1.0.1 —")

    notes = Path("documents/RELEASE_NOTES_1.0.0.md")
    assert notes.exists()
    assert "eerste stabiele release" in notes.read_text(encoding="utf-8").lower()

    roadmap = Path("documents/ROADMAP_AND_IDEAS.md").read_text(encoding="utf-8")
    assert "### 1.0.0 — uitgebracht" in roadmap
