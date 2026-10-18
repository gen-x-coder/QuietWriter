"""Rustige omslag per boek, afgeleid van een seed (de boek-ID).

Alleen weergave: er wordt niets opgeslagen en niets geëxporteerd. Een boek
zonder eigen omslag krijgt in de Boekenkast (en als voorbeeld in Boekdetails)
een eigen kleur en patroon, zodat de kast niet uit gelijke, lege ruggen
bestaat. Dezelfde seed geeft op elke computer en in elke versie hetzelfde
beeld: de waarden komen rechtstreeks uit SHA-256, niet uit ``random``.
"""
from __future__ import annotations

import colorsys
import hashlib
import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap


PATTERNS = ('bands', 'rings', 'diagonals', 'dots', 'waves', 'hills', 'arches')


class _Stream:
    """Deterministische getallen 0..1 uit SHA-256 (seed + teller)."""

    def __init__(self, seed: str):
        self._seed = seed.encode('utf-8')
        self._counter = 0
        self._buffer = b''

    def _byte_pairs(self) -> int:
        if len(self._buffer) < 2:
            block = hashlib.sha256(self._seed + b':' + str(self._counter).encode('ascii')).digest()
            self._counter += 1
            self._buffer += block
        value = int.from_bytes(self._buffer[:2], 'big')
        self._buffer = self._buffer[2:]
        return value

    def unit(self) -> float:
        return self._byte_pairs() / 65535.0

    def between(self, low: float, high: float) -> float:
        return low + (high - low) * self.unit()

    def integer(self, low: int, high: int) -> int:
        """Geheel getal van low tot en met high."""
        return min(high, low + int(self.unit() * (high - low + 1)))


def _hsl(hue: float, saturation: float, lightness: float) -> str:
    r, g, b = colorsys.hls_to_rgb((hue % 360.0) / 360.0, max(0.0, min(1.0, lightness)), max(0.0, min(1.0, saturation)))
    return '#{:02x}{:02x}{:02x}'.format(round(r * 255), round(g * 255), round(b * 255))


@dataclass(frozen=True)
class CoverSpec:
    seed: str
    pattern: str
    base: str        # achtergrond: gedempt en vrij donker, zodat lichte tekst leesbaar blijft
    shade: str       # dezelfde kleurfamilie, iets lichter: hoofdvorm van het patroon
    accent: str      # één rustige tegenkleur, spaarzaam gebruikt
    ink: str         # lichte tekstkleur voor titel en auteur
    params: tuple    # patroonafhankelijke getallen 0..1


def cover_seed(book) -> str:
    """De boek-ID; zonder ID (oude of kapotte metadata) valt hij terug op de titel."""
    seed = str(getattr(book, 'id', '') or '').strip()
    if seed:
        return seed
    return 'title:' + str(getattr(book, 'title', '') or '').strip().casefold()


def cover_spec(seed: str) -> CoverSpec:
    stream = _Stream(str(seed))
    pattern = PATTERNS[stream.integer(0, len(PATTERNS) - 1)]
    hue = stream.between(0.0, 360.0)
    saturation = stream.between(0.18, 0.38)
    lightness = stream.between(0.26, 0.38)
    shade_shift = stream.between(-28.0, 28.0)
    accent_hue = hue + stream.between(140.0, 220.0)
    base = _hsl(hue, saturation, lightness)
    shade = _hsl(hue + shade_shift, saturation * 0.9, lightness + stream.between(0.09, 0.16))
    accent = _hsl(accent_hue, stream.between(0.25, 0.45), stream.between(0.58, 0.70))
    ink = _hsl(hue, 0.25, 0.94)
    params = tuple(round(stream.unit(), 4) for _ in range(8))
    return CoverSpec(str(seed), pattern, base, shade, accent, ink, params)


# --------------------------------------------------------------------------- tekenen

def _color(value: str, alpha: int = 255) -> QColor:
    color = QColor(value)
    color.setAlpha(alpha)
    return color


def _paint_bands(p: QPainter, area: QRectF, spec: CoverSpec):
    count = 3 + int(spec.params[0] * 4)
    weights = [0.5 + spec.params[(i + 1) % 8] * ((i % 3) + 1) for i in range(count)]
    total = sum(weights)
    y = area.top()
    for index, weight in enumerate(weights):
        height = area.height() * weight / total
        if index % 2 == 0:
            color = _color(spec.shade, 210 - 25 * (index % 3))
        elif index == count // 2:
            color = _color(spec.accent, 150)
        else:
            color = None
        if color is not None:
            p.fillRect(QRectF(area.left(), y, area.width(), max(1.0, height - 2)), color)
        y += height


def _paint_rings(p: QPainter, area: QRectF, spec: CoverSpec):
    radius = area.width() * (0.45 + spec.params[0] * 0.35)
    center = QPointF(area.left() + area.width() * (0.25 + spec.params[1] * 0.6),
                     area.top() + area.height() * (0.35 + spec.params[2] * 0.5))
    p.setPen(Qt.NoPen)
    p.setBrush(_color(spec.shade, 200))
    p.drawEllipse(center, radius, radius)
    rings = 2 + int(spec.params[3] * 3)
    p.setBrush(Qt.NoBrush)
    for index in range(rings):
        r = radius * (0.32 + 0.6 * (index + 1) / (rings + 1))
        p.setPen(QPen(_color(spec.accent if index == 0 else spec.base, 170), 1.6))
        p.drawEllipse(center, r, r)


def _paint_diagonals(p: QPainter, area: QRectF, spec: CoverSpec):
    angle = math.radians(25 + spec.params[0] * 40) * (1 if spec.params[1] > 0.5 else -1)
    gap = 9 + spec.params[2] * 12
    dx = math.tan(angle) * area.height()
    start = area.left() - abs(dx) - gap
    x = start
    index = 0
    while x < area.right() + abs(dx) + gap:
        accent = index % (4 + int(spec.params[3] * 4)) == 0
        p.setPen(QPen(_color(spec.accent if accent else spec.shade, 190 if accent else 220), 2.2 if accent else 1.4))
        p.drawLine(QPointF(x, area.bottom()), QPointF(x + dx, area.top()))
        x += gap
        index += 1


def _paint_dots(p: QPainter, area: QRectF, spec: CoverSpec):
    step = 15 + spec.params[0] * 10
    radius = step * (0.16 + spec.params[1] * 0.16)
    p.setPen(Qt.NoPen)
    columns = int(area.width() / step) + 1
    rows = int(area.height() / step) + 1
    offset_x = (area.width() - (columns - 1) * step) / 2
    for row in range(rows):
        for column in range(columns):
            fade = 1.0 - row / max(1, rows) * spec.params[2] * 0.8
            highlight = (row * 7 + column * 3 + int(spec.params[3] * 11)) % 13 == 0
            p.setBrush(_color(spec.accent if highlight else spec.shade, int(235 * fade)))
            stagger = step / 2 if (spec.params[4] > 0.5 and row % 2) else 0.0
            p.drawEllipse(QPointF(area.left() + offset_x + column * step + stagger, area.top() + step / 2 + row * step), radius, radius)


def _paint_waves(p: QPainter, area: QRectF, spec: CoverSpec):
    lines = 5 + int(spec.params[0] * 6)
    amplitude = 4 + spec.params[1] * 10
    wavelength = area.width() * (0.45 + spec.params[2] * 0.6)
    phase = spec.params[3] * math.tau
    p.setBrush(Qt.NoBrush)
    for index in range(lines):
        y0 = area.top() + area.height() * (index + 0.5) / lines
        path = QPainterPath(QPointF(area.left(), y0))
        steps = 32
        for step in range(1, steps + 1):
            x = area.left() + area.width() * step / steps
            y = y0 + amplitude * math.sin(phase + index * 0.6 + (x - area.left()) / wavelength * math.tau)
            path.lineTo(QPointF(x, y))
        accent = index == int(spec.params[4] * lines)
        p.setPen(QPen(_color(spec.accent if accent else spec.shade, 210), 2.4 if accent else 1.6))
        p.drawPath(path)


def _paint_hills(p: QPainter, area: QRectF, spec: CoverSpec):
    layers = 3
    p.setPen(Qt.NoPen)
    for layer in range(layers):
        top = area.top() + area.height() * (0.15 + layer * 0.25)
        path = QPainterPath(QPointF(area.left(), area.bottom()))
        peaks = 2 + int(spec.params[layer] * 3)
        path.lineTo(QPointF(area.left(), top + area.height() * 0.12 * spec.params[layer + 3]))
        for peak in range(peaks):
            x = area.left() + area.width() * (peak + 0.5) / peaks
            height = area.height() * 0.18 * (0.4 + spec.params[(layer + peak) % 8])
            path.lineTo(QPointF(x, top - height + area.height() * 0.1))
            path.lineTo(QPointF(area.left() + area.width() * (peak + 1) / peaks, top + area.height() * 0.08))
        path.lineTo(QPointF(area.right(), area.bottom()))
        path.closeSubpath()
        color = spec.accent if layer == 0 else spec.shade
        p.setBrush(_color(color, (110, 170, 235)[layer]))
        p.drawPath(path)


def _paint_arches(p: QPainter, area: QRectF, spec: CoverSpec):
    count = 1 + int(spec.params[0] * 3)
    width = area.width() / count
    p.setBrush(Qt.NoBrush)
    for index in range(count):
        outer = min(area.height() * 0.92, width * (0.55 + spec.params[(index + 2) % 8] * 0.35) * (1.6 if count == 1 else 1.0))
        rings = 4 + int(spec.params[(index + 1) % 8] * 4)
        cx = area.left() + width * (index + 0.5)
        for ring in range(rings):
            r = outer * (ring + 1) / rings
            rect = QRectF(cx - r, area.bottom() - r, 2 * r, 2 * r)
            accent = ring == rings - 1 and index == int(spec.params[5] * count)
            p.setPen(QPen(_color(spec.accent if accent else spec.shade, 220), 2.2 if accent else 1.8))
            p.drawArc(rect, 0, 180 * 16)


_PAINTERS = {
    'bands': _paint_bands,
    'rings': _paint_rings,
    'diagonals': _paint_diagonals,
    'dots': _paint_dots,
    'waves': _paint_waves,
    'hills': _paint_hills,
    'arches': _paint_arches,
}


def paint_generated_cover(painter: QPainter, rect: QRectF, spec: CoverSpec, title: str = '', author: str = '', font=None):
    """Teken achtergrond, patroon (onderste deel) en titel/auteur (bovenste deel)."""
    rect = QRectF(rect)
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setClipRect(rect)
    painter.fillRect(rect, _color(spec.base))
    pattern_area = QRectF(rect.left(), rect.top() + rect.height() * 0.42, rect.width(), rect.height() * 0.58)
    painter.save()
    painter.setClipRect(pattern_area)
    _PAINTERS.get(spec.pattern, _paint_bands)(painter, pattern_area, spec)
    painter.restore()
    # Dun lijntje tussen titelvlak en patroon, zoals op een klassieke omslag.
    margin = max(8.0, rect.width() * 0.08)
    painter.setPen(QPen(_color(spec.ink, 120), 1.0))
    painter.drawLine(QPointF(rect.left() + margin, pattern_area.top() - 8), QPointF(rect.right() - margin, pattern_area.top() - 8))
    if title or author:
        _paint_title(painter, QRectF(rect.left() + margin, rect.top() + margin,
                                     rect.width() - 2 * margin, pattern_area.top() - rect.top() - margin - 16),
                     rect.height() / 307.0, spec, title, author, font)
    painter.restore()


def _paint_title(painter: QPainter, text_rect: QRectF, scale: float, spec: CoverSpec, title: str, author: str, font):
    """Titel en auteur in het titelvlak; een lange titel wordt kleiner en zo nodig afgekapt."""
    flags = int(Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap)
    author_font = QFont(font if font is not None else painter.font())
    author_font.setBold(False)
    author_font.setPointSizeF(max(5.0, scale * 9.0))
    painter.setFont(author_font)
    author_height = (painter.fontMetrics().height() + 4) if author else 0
    title_room = QRectF(text_rect.left(), text_rect.top(), text_rect.width(), max(1.0, text_rect.height() - author_height))

    title_font = QFont(font if font is not None else painter.font())
    title_font.setBold(True)
    size = max(6.0, scale * 12.5)
    minimum = max(5.0, size * 0.72)
    bounds = QRectF()
    while True:
        title_font.setPointSizeF(size)
        painter.setFont(title_font)
        bounds = painter.boundingRect(QRectF(title_room.left(), title_room.top(), title_room.width(), 10000), flags, title)
        if bounds.height() <= title_room.height() or size <= minimum:
            break
        size = max(minimum, size - 0.5)
    painter.setPen(_color(spec.ink))
    painter.drawText(title_room, flags, title)
    if author:
        painter.setFont(author_font)
        author_top = min(bounds.bottom(), title_room.bottom()) + 4
        painter.setPen(_color(spec.ink, 200))
        painter.drawText(QRectF(text_rect.left(), author_top, text_rect.width(), painter.fontMetrics().height() + 2),
                         int(Qt.AlignLeft | Qt.AlignTop | Qt.TextSingleLine),
                         painter.fontMetrics().elidedText(author, Qt.ElideRight, int(text_rect.width())))


def generated_cover_pixmap(spec: CoverSpec, width: int, height: int, *, title: str = '', author: str = '', font=None, device_pixel_ratio: float = 1.0) -> QPixmap:
    ratio = max(1.0, float(device_pixel_ratio or 1.0))
    pixmap = QPixmap(max(1, round(width * ratio)), max(1, round(height * ratio)))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(QColor(spec.base))
    painter = QPainter(pixmap)
    try:
        paint_generated_cover(painter, QRectF(0, 0, width, height), spec, title, author, font)
    finally:
        painter.end()
    return pixmap
