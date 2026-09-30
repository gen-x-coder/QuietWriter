from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt, QRectF
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from .themes import THEMES

ICON_DIR = Path(__file__).with_name('icons')
_current_theme = 'Helder'


def set_icon_theme(name: str) -> None:
    global _current_theme
    _current_theme = name if name in THEMES else 'Helder'


def current_icon_theme() -> str:
    return _current_theme


def _recolour_svg(svg: str, colour: str) -> str:
    """Recolour the monochrome QuietWriter SVG source.

    The repository historically contained a mix of ``currentColor`` and fixed
    grey values. QIcon does not inherit a QWidget stylesheet colour into SVG
    files on all Qt/Windows combinations, which made a few icons black in dark
    themes. The renderer now normalises every non-``none`` stroke/fill to the
    requested semantic theme colour.
    """
    svg = re.sub(r'stroke="(?:currentColor|#[0-9a-fA-F]{3,8})"', f'stroke="{colour}"', svg)
    svg = re.sub(r'fill="currentColor"', f'fill="{colour}"', svg)
    # Solid monochrome groups, e.g. drag_handle.svg.
    svg = re.sub(r'fill="#[0-9a-fA-F]{3,8}"', f'fill="{colour}"', svg)
    return svg


def _pixmap(name: str, colour: str, size: int = 24) -> QPixmap:
    path = ICON_DIR / f'{name}.svg'
    raw = path.read_text(encoding='utf-8')
    raw = _recolour_svg(raw, colour)
    renderer = QSvgRenderer(QByteArray(raw.encode('utf-8')))
    pix = QPixmap(QSize(size, size))
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


def icon(name: str, size: int = 24, theme_name: str | None = None) -> QIcon:
    """Return a theme-aware icon with normal/checked/disabled states."""
    theme = THEMES.get(theme_name or _current_theme, THEMES['Helder'])
    result = QIcon()
    result.addPixmap(_pixmap(name, theme['muted'], size), QIcon.Normal, QIcon.Off)
    result.addPixmap(_pixmap(name, theme['accent'], size), QIcon.Normal, QIcon.On)
    result.addPixmap(_pixmap(name, theme['disabled'], size), QIcon.Disabled, QIcon.Off)
    result.addPixmap(_pixmap(name, theme['disabled'], size), QIcon.Disabled, QIcon.On)
    return result


def themed_svg_pixmap(name: str, width: int, theme_name: str | None = None, colour_key: str = 'text') -> QPixmap:
    """Render a monochrome SVG at its intrinsic aspect ratio in a theme colour.

    Unlike :func:`icon`, this is intended for non-square artwork such as the
    QuietWriter wordmark used on the splash and About page.
    """
    theme = THEMES.get(theme_name or _current_theme, THEMES['Helder'])
    path = ICON_DIR / f'{name}.svg'
    raw = _recolour_svg(path.read_text(encoding='utf-8'), theme.get(colour_key, theme['text']))
    renderer = QSvgRenderer(QByteArray(raw.encode('utf-8')))
    view = renderer.viewBoxF()
    if view.width() <= 0 or view.height() <= 0:
        size = renderer.defaultSize()
        aspect = (size.height() / size.width()) if size.width() else 1.0
    else:
        aspect = view.height() / view.width()
    height = max(1, round(int(width) * aspect))
    pix = QPixmap(QSize(int(width), height))
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter, QRectF(0, 0, int(width), height))
    painter.end()
    return pix


def app_icon_path() -> Path:
    """Path to the packaged multi-size Windows application icon."""
    return Path(__file__).with_name('resources') / 'quietwriter.ico'
