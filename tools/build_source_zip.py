"""Make a complete, versioned source ZIP from Git-tracked project files.

Unlike the portable Windows build, this includes source documentation, branding,
screenshots, README_EN.md, tests and packaging files. It fails on missing tracked
assets and refuses uncommitted changes so uploaded ZIPs are reproducible.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def main() -> int:
    if git("status", "--porcelain"):
        print("ERROR: Commit or stash local changes before packaging.", file=sys.stderr)
        return 1

    text = (ROOT / "quietwriter" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\x27]([^"\x27]+)["\x27]', text, re.M)
    if not match:
        print("ERROR: No application version found.", file=sys.stderr)
        return 1
    version = match.group(1)
    paths = sorted(
        p.decode("utf-8") for p in git("ls-files", "-z").split(b"\0") if p
    )
    mandatory = {
        "README.md", "README_EN.md", "LICENSE",
        "branding/screenshots/hero-met-logo.png",
        "branding/screenshots/02-open-punten.png",
        "branding/screenshots/03-meelezer.png",
        "branding/screenshots/04-in-dit-hoofdstuk.png",
        "branding/screenshots/05-planning-personages.png",
        "branding/screenshots/07-bewaarplaats.png",
        "branding/screenshots/08-versiegeschiedenis.png",
        "branding/screenshots/11-exporteren.png",
        "branding/screenshots/13-themas.png",
        "branding/bron/emblem_src.svg",
        "branding/bron/wordmark_src.svg",
        "build_exe.cmd", "tools/build_source_zip.py",
    }
    missing = sorted(mandatory - set(paths))
    missing += [p for p in paths if not (ROOT / p).is_file()]
    if missing:
        print("ERROR: Missing required or Git-tracked files:", file=sys.stderr)
        for path in sorted(set(missing)):
            print(" -", path, file=sys.stderr)
        return 1

    output = ROOT / "release" / f"QuietWriter-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in paths:
            # Normalize metadata so source packages are reproducible.
            info = zipfile.ZipInfo(path, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, (ROOT / path).read_bytes(), compress_type=zipfile.ZIP_DEFLATED)

    with zipfile.ZipFile(output) as zf:
        assert set(zf.namelist()) == set(paths)
        assert zf.testzip() is None
    print(f"PASS: {output} ({len(paths)} tracked files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
