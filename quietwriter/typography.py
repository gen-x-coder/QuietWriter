from __future__ import annotations

from dataclasses import dataclass
import sys

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QFontDatabase


DEFAULT_WRITING_FONT = 'Merriweather'
FALLBACK_WRITING_FONTS = ('Merriweather', 'Georgia')
DEFAULT_WRITING_SIZE = 15
MIN_WRITING_SIZE = 11
MAX_WRITING_SIZE = 24


@dataclass(frozen=True)
class WritingTypography:
    """Independent writing typography settings.

    The font family and point size are intentionally separate. Selecting another
    family never changes the size, and changing the size never changes the family.
    """

    family: str = DEFAULT_WRITING_FONT
    point_size: int = DEFAULT_WRITING_SIZE

    @classmethod
    def from_settings(cls, settings: QSettings) -> 'WritingTypography':
        family = str(settings.value('editor_font', DEFAULT_WRITING_FONT) or DEFAULT_WRITING_FONT)
        size = _safe_size(settings.value('editor_font_size', DEFAULT_WRITING_SIZE, int))
        return cls(resolve_family(family), size)

    def body_font(self) -> QFont:
        font = QFont(self.family)
        font.setPointSize(self.point_size)
        font.setWeight(QFont.Weight.Light)
        return tune_writing_font(font)

    def title_font(self) -> QFont:
        font = QFont(self.family)
        font.setPointSize(max(18, self.point_size + 5))
        font.setWeight(QFont.Weight.DemiBold)
        return tune_writing_font(font)


def tune_writing_font(font: QFont) -> QFont:
    """Tune manuscript text for crisp, colour-neutral rendering on Windows.

    ClearType/subpixel antialiasing can produce visible red/cyan fringes when
    light serif text is rendered on a dark editor background.  For the writing
    surface we prefer grayscale antialiasing with full hinting instead.  The
    rest of the application keeps the platform default rendering.
    """
    if sys.platform.startswith('win'):
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias
            | QFont.StyleStrategy.NoSubpixelAntialias
        )
    return font


def _safe_size(value) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = DEFAULT_WRITING_SIZE
    return max(MIN_WRITING_SIZE, min(MAX_WRITING_SIZE, value))


def available_families() -> list[str]:
    """Return all installed font families, suitable for a dynamic settings list."""
    families = sorted({str(f).strip() for f in QFontDatabase.families() if str(f).strip()}, key=str.casefold)
    return families


def resolve_family(preferred: str | None = None) -> str:
    preferred = (preferred or DEFAULT_WRITING_FONT).strip() or DEFAULT_WRITING_FONT
    available = {f.casefold(): f for f in available_families()}
    if preferred.casefold() in available:
        return available[preferred.casefold()]
    for fallback in FALLBACK_WRITING_FONTS:
        if fallback.casefold() in available:
            return available[fallback.casefold()]
    # QApplication has an explicit valid point size in run(); here we only need
    # its family name as a last-resort writing family.
    return QFontDatabase.systemFont(QFontDatabase.GeneralFont).family() or 'Segoe UI'


def typography_from_values(family: str | None, point_size) -> WritingTypography:
    return WritingTypography(resolve_family(family), _safe_size(point_size))
