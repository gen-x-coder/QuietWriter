from pathlib import Path

import quietwriter


def test_release_metadata():
    version = quietwriter.__version__

    changelog = Path("documents/CHANGELOG.md").read_text(encoding="utf-8-sig")
    snapshot = Path("SNAPSHOT_INFO.txt").read_text(encoding="utf-8")

    assert changelog.startswith(f"## {version} —")
    assert f"Application version: {version}" in snapshot


def test_public_branding_references_exist():
    import re

    for readme in ("README.md", "README_EN.md"):
        body = Path(readme).read_text(encoding="utf-8")
        for target in re.findall(r"!\[[^]]*\]\((branding/[^)#]+)\)", body):
            assert Path(target).is_file(), f"{readme}: missing {target}"

    assert Path("CONTRIBUTING.md").is_file()
    assert Path("documents/RELEASE_PROCESS.md").is_file()