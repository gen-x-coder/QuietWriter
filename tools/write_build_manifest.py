"""Schrijf de bewijs-/hashmetadata van een bevroren Windows releasecandidate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGES = (
    "PySide6",
    "PySide6_Addons",
    "PySide6_Essentials",
    "shiboken6",
    "requests",
    "certifi",
    "charset-normalizer",
    "idna",
    "urllib3",
    "spylls",
    "python-docx",
    "lxml",
    "typing_extensions",
    "pyinstaller",
    "altgraph",
    "packaging",
    "pefile",
    "pyinstaller-hooks-contrib",
    "pywin32-ctypes",
    "setuptools",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "NIET GEINSTALLEERD"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--zip", dest="zip_path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.exe.is_file():
        raise SystemExit(f"EXE ontbreekt: {args.exe}")
    if not args.zip_path.is_file():
        raise SystemExit(f"ZIP ontbreekt: {args.zip_path}")

    lines = [
        "QuietWriter Windows releasecandidate build manifest",
        "===================================================",
        f"Version: {args.version}",
        f"Source commit: {args.source_commit}",
        f"Built UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Python: {platform.python_version()}",
        f"Python executable: {sys.executable}",
        f"Platform: {platform.platform()}",
        "",
        "Pinned packages:",
    ]
    lines.extend(f"- {name}=={package_version(name)}" for name in PACKAGES)
    lines.extend([
        "",
        f"EXE: {args.exe.name}",
        f"EXE SHA-256: {sha256(args.exe)}",
        f"ZIP: {args.zip_path.name}",
        f"ZIP SHA-256: {sha256(args.zip_path)}",
        "",
        "Release rule: reputatietests en publicatie gebruiken exact deze bytes; niet opnieuw bouwen.",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Build manifest: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
