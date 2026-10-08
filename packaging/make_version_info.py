"""Schrijft build/version_info.txt voor PyInstaller op basis van quietwriter.__version__.

Windows toont deze gegevens bij Eigenschappen → Details van QuietWriter.exe.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_version() -> str:
    text = (ROOT / 'quietwriter' / '__init__.py').read_text(encoding='utf-8')
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise SystemExit('Geen __version__ gevonden in quietwriter/__init__.py')
    return match.group(1)


def version_tuple(version: str) -> tuple[int, int, int, int]:
    # Windows requires a numeric 4-part file version. Use only the SemVer core
    # so 1.0.0-rc1 and the later 1.0.0 both map to 1.0.0.0; the complete
    # prerelease label remains visible in FileVersion/ProductVersion strings.
    core = version.split('-', 1)[0].split('+', 1)[0]
    numbers = [int(n) for n in re.findall(r'\d+', core)[:3]]
    return tuple((numbers + [0, 0, 0, 0])[:3] + [0])  # type: ignore[return-value]


TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(filevers={tup}, prodvers={tup}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('041304B0', [
      StringStruct('CompanyName', 'Lucas Bonsel'),
      StringStruct('FileDescription', 'QuietWriter'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'QuietWriter'),
      StringStruct('LegalCopyright', '© 2026 Lucas Bonsel.'),
      StringStruct('OriginalFilename', 'QuietWriter.exe'),
      StringStruct('ProductName', 'QuietWriter'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [0x0413, 1200])])
  ]
)
"""


def main() -> int:
    version = read_version()
    out = ROOT / 'build' / 'version_info.txt'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TEMPLATE.format(tup=version_tuple(version), version=version), encoding='utf-8')
    print(f'{out.relative_to(ROOT)} -> {version}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
