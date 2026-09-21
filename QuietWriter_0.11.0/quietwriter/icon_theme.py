from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
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
