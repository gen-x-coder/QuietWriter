from __future__ import annotations
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .i18n import tr

# Dutch display names for common Hunspell locale codes. These are the Dutch
# defaults; the shown name follows the app language via ``language_name.<code>``
# and ``country_name.<CC>`` in the locale files (1.7). Unknown but valid locale
# codes are still shown; QuietWriter does not filter dictionaries by this list.
LANGUAGE_NAMES = {
    'af': 'Afrikaans', 'am': 'Amhaars', 'ar': 'Arabisch', 'az': 'Azerbeidzjaans',
    'be': 'Wit-Russisch', 'bg': 'Bulgaars', 'bn': 'Bengaals', 'br': 'Bretons',
    'bs': 'Bosnisch', 'ca': 'Catalaans', 'cs': 'Tsjechisch', 'cy': 'Welsh',
    'da': 'Deens', 'de': 'Duits', 'el': 'Grieks', 'en': 'Engels', 'eo': 'Esperanto',
    'es': 'Spaans', 'et': 'Ests', 'eu': 'Baskisch', 'fa': 'Perzisch', 'fi': 'Fins',
    'fo': 'Faeröers', 'fr': 'Frans', 'ga': 'Iers', 'gd': 'Schots-Gaelisch',
    'gl': 'Galicisch', 'gu': 'Gujarati', 'he': 'Hebreeuws', 'hi': 'Hindi',
    'hr': 'Kroatisch', 'hu': 'Hongaars', 'hy': 'Armeens', 'id': 'Indonesisch',
    'is': 'IJslands', 'it': 'Italiaans', 'ka': 'Georgisch', 'kk': 'Kazachs',
    'km': 'Khmer', 'ko': 'Koreaans', 'la': 'Latijn', 'lt': 'Litouws', 'lv': 'Lets',
    'mk': 'Macedonisch', 'mn': 'Mongools', 'ms': 'Maleis', 'nb': 'Noors Bokmål',
    'ne': 'Nepalees', 'nl': 'Nederlands', 'nn': 'Noors Nynorsk', 'oc': 'Occitaans',
    'pl': 'Pools', 'pt': 'Portugees', 'ro': 'Roemeens', 'ru': 'Russisch',
    'sk': 'Slowaaks', 'sl': 'Sloveens', 'sq': 'Albanees', 'sr': 'Servisch',
    'sv': 'Zweeds', 'sw': 'Swahili', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thais',
    'tr': 'Turks', 'uk': 'Oekraïens', 'ur': 'Urdu', 'vi': 'Vietnamees',
    'zh': 'Chinees',
}
COUNTRY_NAMES = {
    'AE': 'Verenigde Arabische Emiraten', 'AR': 'Argentinië', 'AT': 'Oostenrijk',
    'AU': 'Australië', 'BA': 'Bosnië en Herzegovina', 'BE': 'België',
    'BG': 'Bulgarije', 'BO': 'Bolivia', 'BR': 'Brazilië', 'BY': 'Belarus',
    'CA': 'Canada', 'CH': 'Zwitserland', 'CL': 'Chili', 'CN': 'China',
    'CO': 'Colombia', 'CR': 'Costa Rica', 'CY': 'Cyprus', 'CZ': 'Tsjechië',
    'DE': 'Duitsland', 'DK': 'Denemarken', 'DO': 'Dominicaanse Republiek',
    'DZ': 'Algerije', 'EC': 'Ecuador', 'EE': 'Estland', 'EG': 'Egypte',
    'ES': 'Spanje', 'FI': 'Finland', 'FR': 'Frankrijk', 'GB': 'Verenigd Koninkrijk',
    'GR': 'Griekenland', 'GT': 'Guatemala', 'HK': 'Hongkong', 'HN': 'Honduras',
    'HR': 'Kroatië', 'HU': 'Hongarije', 'ID': 'Indonesië', 'IE': 'Ierland',
    'IL': 'Israël', 'IN': 'India', 'IS': 'IJsland', 'IT': 'Italië', 'JP': 'Japan',
    'KR': 'Zuid-Korea', 'LT': 'Litouwen', 'LU': 'Luxemburg', 'LV': 'Letland',
    'MA': 'Marokko', 'MK': 'Noord-Macedonië', 'MT': 'Malta', 'MX': 'Mexico',
    'MY': 'Maleisië', 'NI': 'Nicaragua', 'NL': 'Nederland', 'NO': 'Noorwegen',
    'NZ': 'Nieuw-Zeeland', 'PA': 'Panama', 'PE': 'Peru', 'PH': 'Filipijnen',
    'PK': 'Pakistan', 'PL': 'Polen', 'PR': 'Puerto Rico', 'PT': 'Portugal',
    'PY': 'Paraguay', 'RO': 'Roemenië', 'RS': 'Servië', 'RU': 'Rusland',
    'SE': 'Zweden', 'SI': 'Slovenië', 'SK': 'Slowakije', 'TH': 'Thailand',
    'TR': 'Turkije', 'TW': 'Taiwan', 'UA': 'Oekraïne', 'US': 'Verenigde Staten',
    'UY': 'Uruguay', 'VE': 'Venezuela', 'VN': 'Vietnam', 'ZA': 'Zuid-Afrika',
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
    language = tr(f'language_name.{parts[0]}', LANGUAGE_NAMES[parts[0]]) if parts[0] in LANGUAGE_NAMES else None
    if len(parts) == 1:
        return language or locale
    country = tr(f'country_name.{parts[1]}', COUNTRY_NAMES[parts[1]]) if parts[1] in COUNTRY_NAMES else None
    if not language or not country:
        # Avoid confusing half-translated labels such as "Nederlands - XX".
        # An unknown locale is clearer when shown as one canonical code.
        return locale
    return f'{language} — {country}'


SOURCE_ORDER = {'Werkmap': 0, 'ONLYOFFICE': 2, 'LibreOffice': 3, 'OpenOffice': 4, 'Extern': 5}

# Welke woordenboektaal past bij de taal van de app (voor een voorstel).
APP_LANGUAGE_LOCALES = {'nl': 'nl_NL', 'en': 'en_GB', 'de': 'de_DE', 'fr': 'fr_FR', 'es': 'es_ES'}


def source_label(source: str) -> str:
    """Naam van een woordenboekbron zoals de gebruiker hem ziet."""
    if source == 'Werkmap':
        return tr('settings.spelling.source_workspace_170', 'QuietWriter (gedownload of toegevoegd)')
    return source


def ordered_sources(entries) -> list[str]:
    return sorted({entry.source for entry in entries}, key=lambda s: (SOURCE_ORDER.get(s, 99), s.casefold()))


def preferred_locale(app_language: str | None) -> str:
    return APP_LANGUAGE_LOCALES.get(str(app_language or 'nl')[:2].lower(), 'nl_NL')


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
    def __init__(self, workspace_dir: Path, extra_roots: list[tuple[Path, str]] | None = None, *, create: bool = True):
        self.workspace_dir = Path(workspace_dir)
        if create:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.extra_roots = extra_roots
        self._entries: list[DictionaryEntry] = []
        self.scan()

    @staticmethod
    def _infer_locale(dic: Path) -> str:
        # Prefer a specific language+country locale over a bare language code.
        # Office suites sometimes store ``nl.dic`` inside ``nl-NL/``; choosing
        # the filename first used to throw away the useful country information.
        valid: list[str] = []
        for value in (dic.stem, dic.parent.name):
            locale = normalize_locale(value)
            if re.match(r'^[a-z]{2,3}(?:_[A-Z]{2})?$', locale):
                valid.append(locale)
        for locale in valid:
            if '_' in locale:
                return locale
        if valid:
            return valid[0]
        return normalize_locale(dic.stem)

    def _add_dic(self, dic: Path, source: str):
        locale = self._infer_locale(dic)
        if not locale or locale.lower().startswith('hyph_'):
            return
        aff = dic.with_suffix('.aff')
        if not aff.exists():
            aff = None
        label = locale_label(locale)
        try:
            resolved = dic.resolve()
        except OSError:
            resolved = dic
        for current in self._entries:
            try:
                current_path = current.dic.resolve()
            except OSError:
                current_path = current.dic
            if current_path == resolved:
                return
        self._entries.append(DictionaryEntry(locale, label, dic, aff, source))

    def _scan_root(self, root: Path, source: str):
        if not root.exists():
            return
        try:
            dictionaries = root.rglob('*.dic')
            for dic in dictionaries:
                if dic.name.lower().startswith('hyph_'):
                    continue
                # Tijdelijke download- en vorige-mappen (.download-*, .vorige-*)
                # zijn nooit een bruikbaar woordenboek.
                if any(part.startswith('.') for part in dic.relative_to(root).parts[:-1]):
                    continue
                self._add_dic(dic, source)
        except (OSError, PermissionError):
            return

    def scan(self):
        self._entries.clear()
        # 1.7: QuietWriter levert geen woordenboek meer mee; je downloadt er een
        # (zie dictionary_download.py) of gebruikt dat van een Office-programma.
        self._scan_root(self.workspace_dir, 'Werkmap')

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

    def entries(self, locale: str | None = None) -> list[DictionaryEntry]:
        """Return all discovered dictionaries, optionally for one locale."""
        wanted = normalize_locale(locale) if locale else ''
        values = [entry for entry in self._entries if not wanted or entry.locale == wanted]
        priority = SOURCE_ORDER
        return sorted(
            values,
            key=lambda e: (e.label.casefold(), priority.get(e.source, 99), e.source.casefold(), str(e.dic).casefold()),
        )

    def get(self, locale: str, source: str | None = None) -> DictionaryEntry | None:
        """Resolve one dictionary and fall back safely if a saved provider is absent."""
        locale = normalize_locale(locale)
        matches = self.entries(locale)
        if source:
            for entry in matches:
                if entry.source == source:
                    return entry
        return matches[0] if matches else None

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
        entry = self.get(locale, 'Werkmap')
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
            from .dictionary_download import remove_extras
            remove_extras(target_dir, locale)
            # Remove now-empty locale folder, but never the dictionaries root itself.
            if target_dir != workspace and target_dir.exists() and not any(target_dir.iterdir()):
                target_dir.rmdir()
            self.scan()
            return True
        except (OSError, PermissionError):
            return False
