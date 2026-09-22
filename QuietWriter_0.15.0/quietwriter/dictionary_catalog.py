from __future__ import annotations
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

# Dutch display names for common Hunspell locale codes. Unknown but valid locale
# codes are still shown; QuietWriter no longer filters dictionaries by this list.
LANGUAGE_NAMES = {
    'af': 'Afrikaans', 'ar': 'Arabisch', 'bg': 'Bulgaars', 'ca': 'Catalaans',
    'cs': 'Tsjechisch', 'da': 'Deens', 'de': 'Duits', 'el': 'Grieks',
    'en': 'Engels', 'es': 'Spaans', 'et': 'Ests', 'fi': 'Fins', 'fr': 'Frans',
    'he': 'Hebreeuws', 'hr': 'Kroatisch', 'hu': 'Hongaars', 'id': 'Indonesisch',
    'is': 'IJslands', 'it': 'Italiaans', 'lt': 'Litouws', 'lv': 'Lets',
    'nb': 'Noors Bokmål', 'nn': 'Noors Nynorsk', 'nl': 'Nederlands', 'pl': 'Pools',
    'pt': 'Portugees', 'ro': 'Roemeens', 'ru': 'Russisch', 'sk': 'Slowaaks',
    'sl': 'Sloveens', 'sr': 'Servisch', 'sv': 'Zweeds', 'tr': 'Turks',
    'uk': 'Oekraïens', 'vi': 'Vietnamees',
}
COUNTRY_NAMES = {
    'AT': 'Oostenrijk', 'AU': 'Australië', 'BE': 'België', 'BR': 'Brazilië',
    'CA': 'Canada', 'CH': 'Zwitserland', 'DE': 'Duitsland', 'DK': 'Denemarken',
    'ES': 'Spanje', 'FI': 'Finland', 'FR': 'Frankrijk', 'GB': 'VK', 'IE': 'Ierland',
    'IN': 'India', 'IT': 'Italië', 'LU': 'Luxemburg', 'MX': 'Mexico',
    'NL': 'Nederland', 'NO': 'Noorwegen', 'NZ': 'Nieuw-Zeeland', 'PL': 'Polen',
    'PT': 'Portugal', 'SE': 'Zweden', 'US': 'VS', 'ZA': 'Zuid-Afrika',
}


def normalize_locale(value: str) -> str:
    value = (value or '').strip().replace('-', '_')
    m = re.match(r'^([A-Za-z]{2,3})(?:_([A-Za-z]{2}))?$', value)
    if not m:
        return value
    lang = m.group(1).lower()
    country = m.group(2).upper() if m.group(2) else ''
    return f'{lang}_{country}' if country else lang


def locale_label(locale: str) -> str:
    locale = normalize_locale(locale)
    parts = locale.split('_', 1)
    language = LANGUAGE_NAMES.get(parts[0], parts[0])
    if len(parts) == 1:
        return language
    country = COUNTRY_NAMES.get(parts[1], parts[1])
    return f'{language} - {country}'


@dataclass(frozen=True)
class DictionaryEntry:
    locale: str
    label: str
    dic: Path
    aff: Path | None
    source: str = ''


class DictionaryCatalog:
    """Discover Hunspell dictionaries in QuietWriter and Office installations.

    All discovered spelling dictionaries are eligible. Hyphenation dictionaries
    (hyph_*.dic) are ignored because they are not spelling dictionaries.
    """
    def __init__(self, workspace_dir: Path, extra_roots: list[tuple[Path, str]] | None = None):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.extra_roots = extra_roots
        self._entries: dict[str, DictionaryEntry] = {}
        self.scan()

    @staticmethod
    def _infer_locale(dic: Path) -> str:
        candidates = [dic.stem, dic.parent.name]
        for value in candidates:
            locale = normalize_locale(value)
            if re.match(r'^[a-z]{2,3}(?:_[A-Z]{2})?$', locale):
                return locale
        return normalize_locale(dic.stem)

    def _add_dic(self, dic: Path, source: str):
        locale = self._infer_locale(dic)
        if not locale or locale.lower().startswith('hyph_'):
            return
        aff = dic.with_suffix('.aff')
        if not aff.exists():
            aff = None
        label = locale_label(locale)
        current = self._entries.get(locale)
        priority = {'Werkmap': 4, 'Meegeleverd': 3, 'ONLYOFFICE': 2, 'LibreOffice': 2, 'OpenOffice': 2, 'Extern': 1}
        if current and priority.get(current.source, 0) >= priority.get(source, 0):
            return
        self._entries[locale] = DictionaryEntry(locale, label, dic, aff, source)

    def _scan_root(self, root: Path, source: str):
        if not root.exists():
            return
        try:
            dictionaries = root.rglob('*.dic')
            for dic in dictionaries:
                if dic.name.lower().startswith('hyph_'):
                    continue
                self._add_dic(dic, source)
        except (OSError, PermissionError):
            return

    def scan(self):
        self._entries.clear()
        self._scan_root(self.workspace_dir, 'Werkmap')
        bundled = Path(__file__).resolve().parent.parent / 'dictionaries'
        if bundled.resolve() != self.workspace_dir.resolve():
            self._scan_root(bundled, 'Meegeleverd')

        roots = self.extra_roots if self.extra_roots is not None else [
            (Path(r'C:/Program Files/ONLYOFFICE/DesktopEditors/dictionaries'), 'ONLYOFFICE'),
            (Path(r'C:/Program Files (x86)/ONLYOFFICE/DesktopEditors/dictionaries'), 'ONLYOFFICE'),
            (Path(r'C:/Program Files/LibreOffice/share/extensions'), 'LibreOffice'),
            (Path(r'C:/Program Files (x86)/LibreOffice/share/extensions'), 'LibreOffice'),
            (Path(r'C:/Program Files/OpenOffice 4/share/extensions'), 'OpenOffice'),
            (Path(r'C:/Program Files (x86)/OpenOffice 4/share/extensions'), 'OpenOffice'),
        ]
        for root, source in roots:
            self._scan_root(root, source)

    def entries(self) -> list[DictionaryEntry]:
        return sorted(self._entries.values(), key=lambda e: (e.label.casefold(), e.locale.casefold()))

    def get(self, locale: str) -> DictionaryEntry | None:
        return self._entries.get(normalize_locale(locale))

    def add_custom(self, dic: Path) -> DictionaryEntry:
        dic = Path(dic)
        locale = self._infer_locale(dic)
        target_dir = self.workspace_dir / locale
        target_dir.mkdir(parents=True, exist_ok=True)
        target_dic = target_dir / f'{locale}.dic'
        shutil.copy2(dic, target_dic)
        aff = dic.with_suffix('.aff')
        if aff.exists():
            shutil.copy2(aff, target_dir / f'{locale}.aff')
        self.scan()
        return self.get(locale) or DictionaryEntry(locale, locale_label(locale), target_dic, target_dic.with_suffix('.aff') if target_dic.with_suffix('.aff').exists() else None, 'Werkmap')

    def remove_custom(self, locale: str) -> bool:
        """Remove only a dictionary copied into QuietWriter's workspace.

        Office-suite dictionaries are discovered read-only and are never touched.
        """
        entry = self.get(locale)
        if not entry or entry.source != 'Werkmap':
            return False
        try:
            target_dir = entry.dic.parent.resolve()
            workspace = self.workspace_dir.resolve()
            if workspace not in target_dir.parents and target_dir != workspace:
                return False
            if entry.dic.exists():
                entry.dic.unlink()
            if entry.aff and entry.aff.exists():
                entry.aff.unlink()
            # Remove now-empty locale folder, but never the dictionaries root itself.
            if target_dir != workspace and target_dir.exists() and not any(target_dir.iterdir()):
                target_dir.rmdir()
            self.scan()
            return True
        except (OSError, PermissionError):
            return False
