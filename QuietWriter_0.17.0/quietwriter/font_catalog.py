from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from PySide6.QtGui import QFontDatabase


RESOURCE_ROOT = Path(__file__).resolve().parents[1] / 'resources' / 'fonts'
MANIFEST_PATH = RESOURCE_ROOT / 'font_manifest.json'


@dataclass(frozen=True)
class BundledFont:
    family: str
    slug: str
    recommended_order: int
    license_name: str
    copyright: str
    source: str
    files: tuple[str, ...]

    @property
    def folder(self) -> Path:
        return RESOURCE_ROOT / self.slug

    @property
    def license_path(self) -> Path:
        return self.folder / 'OFL.txt'

    @property
    def binary_paths(self) -> tuple[Path, ...]:
        return tuple(self.folder / name for name in self.files)


def _manifest_data() -> dict:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return {'fonts': []}


def bundled_fonts() -> tuple[BundledFont, ...]:
    result: list[BundledFont] = []
    for item in _manifest_data().get('fonts', []):
        try:
            result.append(BundledFont(
                family=str(item['family']),
                slug=str(item['slug']),
                recommended_order=int(item.get('recommended_order', 999)),
                license_name=str(item.get('license', '')),
                copyright=str(item.get('copyright', '')),
                source=str(item.get('source', '')),
                files=tuple(str(entry['name']) for entry in item.get('files', [])),
            ))
        except (KeyError, TypeError, ValueError):
            continue
    return tuple(sorted(result, key=lambda font: (font.recommended_order, font.family.casefold())))


def register_bundled_fonts() -> tuple[str, ...]:
    """Register font binaries shipped with QuietWriter for this process only.

    Missing/invalid binaries are ignored deliberately: QuietWriter must still start
    with ordinary system fonts if a source checkout has not populated resources/fonts.
    """
    registered: set[str] = set()
    for font in bundled_fonts():
        for path in font.binary_paths:
            if not path.is_file():
                continue
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id < 0:
                continue
            for family in QFontDatabase.applicationFontFamilies(font_id):
                if family:
                    registered.add(str(family))
    return tuple(sorted(registered, key=str.casefold))


def recommended_families(available: Iterable[str] | None = None) -> list[str]:
    available_names = list(available if available is not None else QFontDatabase.families())
    canonical = {str(name).casefold(): str(name) for name in available_names if str(name).strip()}
    result: list[str] = []
    for font in bundled_fonts():
        actual = canonical.get(font.family.casefold())
        if actual and actual not in result:
            result.append(actual)
    return result


def system_families_excluding_recommended(available: Iterable[str] | None = None) -> list[str]:
    names = list(available if available is not None else QFontDatabase.families())
    recommended = {name.casefold() for name in recommended_families(names)}
    return sorted(
        {str(name).strip() for name in names if str(name).strip() and str(name).casefold() not in recommended},
        key=str.casefold,
    )
