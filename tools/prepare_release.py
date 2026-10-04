"""Maak een schone, reproduceerbare QuietWriter build-stagingmap.

De ontwikkelmap mag rommelig zijn. Dit script gebruikt bewust een allowlist:
alleen bestanden die nodig zijn om de Windows portable build te maken worden
naar ``release/stage`` gekopieerd. Tests, PPM, reviewrapporten, caches en andere
ontwikkelartefacten kunnen daardoor nooit per ongeluk in de release belanden.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = ROOT / "release"
STAGE = Path(os.environ.get("QUIETWRITER_STAGE_DIR", str(RELEASE_ROOT / "stage")))

# Complete directories that belong to the application/runtime source.
ALLOWED_DIRS = (
    "quietwriter",
)

# Only these top-level/build files are needed to create the portable release.
ALLOWED_FILES = (
    "main.py",
    "documents/LEESMIJ.txt",
    "documents/licenses/LICENSE",
    "documents/licenses/THIRD_PARTY_LICENSES.md",
    "packaging/quietwriter.spec",
    "packaging/make_version_info.py",
    "tools/fetch_bundled_fonts.py",
    "tools/fetch_dictionaries.py",
)

# Font binaries are fetched *inside* staging. Keep only the manifest/licenses
# from the development tree so the stage is reproducible and small.
FONT_METADATA = (
    "resources/fonts/font_manifest.json",
    "resources/fonts/merriweather/OFL.txt",
    "resources/fonts/literata/OFL.txt",
    "resources/fonts/sourceserif4/OFL.txt",
    "resources/fonts/ebgaramond/OFL.txt",
)

FORBIDDEN_PARTS = {
    ".git", ".github", ".idea", ".vscode", ".venv", "venv",
    "__pycache__", ".pytest_cache", "tests", "ppm", "build", "dist",
}
FORBIDDEN_PREFIXES = (
    "REVIEW_NOTES_", "QUIETWRITER_REVIEW_FINDINGS_", "TUSSENTIJDS_RAPPORT_",
    "TRANSLATION_AUDIT_",
)
FORBIDDEN_SUFFIXES = (".pyc", ".pyo", ".log", ".tmp")


def _copy_file(relative: str) -> None:
    src = ROOT / relative
    if not src.is_file():
        raise SystemExit(f"Verplicht releasebestand ontbreekt: {relative}")
    dst = STAGE / relative
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _ignore(_path: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in FORBIDDEN_PARTS or name.endswith(FORBIDDEN_SUFFIXES):
            ignored.add(name)
    return ignored


def _version() -> str:
    namespace: dict[str, object] = {}
    exec((ROOT / "quietwriter" / "__init__.py").read_text(encoding="utf-8"), namespace)
    value = str(namespace.get("__version__", "")).strip()
    if not value:
        raise SystemExit("Geen QuietWriter-versie gevonden.")
    return value


def _validate_stage() -> list[str]:
    errors: list[str] = []
    required = [*ALLOWED_FILES, *FONT_METADATA, "quietwriter/__init__.py"]
    for rel in required:
        if not (STAGE / rel).is_file():
            errors.append(f"ontbreekt: {rel}")

    for path in STAGE.rglob("*"):
        rel = path.relative_to(STAGE)
        parts = set(rel.parts)
        name = path.name
        if parts & FORBIDDEN_PARTS:
            errors.append(f"verboden map/bestand: {rel.as_posix()}")
        if name.startswith(FORBIDDEN_PREFIXES):
            errors.append(f"ontwikkelrapport in stage: {rel.as_posix()}")
        if name.endswith(FORBIDDEN_SUFFIXES):
            errors.append(f"tijdelijk bestand in stage: {rel.as_posix()}")
    return sorted(set(errors))


def _manifest(version: str) -> None:
    entries = []
    for path in sorted(p for p in STAGE.rglob("*") if p.is_file()):
        if path.name == "STAGE_MANIFEST.json":
            continue
        data = path.read_bytes()
        entries.append({
            "path": path.relative_to(STAGE).as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    payload = {
        "product": "QuietWriter",
        "version": version,
        "purpose": "clean PyInstaller build staging",
        "files": entries,
    }
    (STAGE / "STAGE_MANIFEST.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def prepare() -> None:
    version = _version()
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True, exist_ok=True)

    for relative in ALLOWED_DIRS:
        src = ROOT / relative
        if not src.is_dir():
            raise SystemExit(f"Verplichte releasemap ontbreekt: {relative}")
        shutil.copytree(src, STAGE / relative, ignore=_ignore)

    for relative in (*ALLOWED_FILES, *FONT_METADATA):
        _copy_file(relative)

    errors = _validate_stage()
    if errors:
        raise SystemExit("Release staging ongeldig:\n- " + "\n- ".join(errors))
    _manifest(version)
    print(f"Schone stagingmap klaar: {STAGE}")
    print(f"QuietWriter {version}: alleen allowlisted build/runtimebestanden opgenomen.")


def check() -> None:
    if not STAGE.is_dir():
        raise SystemExit("release/stage bestaat niet; draai eerst prepare_release.py")
    errors = _validate_stage()
    if errors:
        raise SystemExit("Release staging ongeldig:\n- " + "\n- ".join(errors))
    print("Release staging: OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="controleer bestaande release/stage")
    args = parser.parse_args()
    check() if args.check else prepare()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
