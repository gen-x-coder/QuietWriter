from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FONT_ROOT = ROOT / "resources" / "fonts"
MANIFEST = FONT_ROOT / "font_manifest.json"


def fetch(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "QuietWriter font packager"})
    with urlopen(request, timeout=60) as response:
        data = response.read()
    if len(data) < 10_000:
        raise RuntimeError(f"Downloaded file is unexpectedly small: {url}")
    target.write_bytes(data)
    print(f"{target.relative_to(ROOT)} ({len(data):,} bytes)")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for font in manifest.get("fonts", []):
        folder = FONT_ROOT / font["slug"]
        for item in font.get("files", []):
            fetch(item["url"], folder / item["name"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
