from pathlib import Path

import quietwriter


def test_stable_1_0_release_metadata():
    assert quietwriter.__version__ == "1.3.0"

    changelog = Path("documents/CHANGELOG.md").read_text(encoding="utf-8-sig")
    assert changelog.startswith("## 1.3.0 —")

    notes = Path("documents/RELEASE_NOTES_1.3.0-rc1.md")
    assert notes.exists()
    assert "library.json" in notes.read_text(encoding="utf-8").lower()

    history = Path("documents/ROADMAP_HISTORY_TO_1_2_13.md").read_text(encoding="utf-8")
    assert "### 1.0.0 — uitgebracht" in history
