"""Vul de Windows-LEESMIJ aan vanuit de applicatieversie in de schone stage."""
from __future__ import annotations
import argparse
import re
from pathlib import Path


def render(template: str, version: str) -> str:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-(?:dev|rc)[.0-9A-Za-z-]*)?", version):
        raise ValueError(f"Ongeldige QuietWriter-versie: {version!r}")
    preview = "-dev" in version or "-rc" in version
    status_nl = ("Dit is een ontwikkel- of testversie, geen stabiele publieke release." if preview
                 else "Dit is een stabiele QuietWriter-release.")
    status_en = ("This is a development or test build, not a stable public release." if preview
                 else "This is a stable QuietWriter release.")
    values = {"{{VERSION}}": version, "{{STATUS_NL}}": status_nl, "{{STATUS_EN}}": status_en}
    for placeholder, value in values.items():
        if template.count(placeholder) != (2 if placeholder == "{{VERSION}}" else 1):
            raise ValueError(f"Ongeldig aantal {placeholder} in LEESMIJ.txt")
        template = template.replace(placeholder, value)
    if re.search(r"\{\{[^{}]+\}\}", template):
        raise ValueError("Onvervangen variabele in LEESMIJ.txt")
    return template


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--template", type=Path, required=True)
    p.add_argument("--version-file", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    ns: dict[str, object] = {}
    exec(a.version_file.read_text(encoding="utf-8"), ns)
    version = str(ns.get("__version__", ""))
    result = render(a.template.read_text(encoding="utf-8-sig"), version)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(result, encoding="utf-8-sig")
    print(f"LEESMIJ.txt voor QuietWriter {version} aangemaakt")


if __name__ == "__main__":
    main()
