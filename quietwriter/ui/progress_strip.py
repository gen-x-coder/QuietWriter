"""Rustige grafiek van de laatste 30 dagen in Boekdetails (1.7).

Alleen weergave van de opt-in dagtelling (``writing_progress.py``). Geen as,
geen gemiddelde, geen doellijn, geen reeks: per dag een staafje, een dag
zonder schrijven is een dun grijs streepje. Ontwerp:
``documents/design/RUSTIGE_GRAFIEK_VOORSTEL.md``.
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QLocale, QRectF, QSettings, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QToolTip, QWidget

from ..i18n import current_locale, tr
from ..themes import THEMES

BAR_GAP = 3
MAX_BAR_WIDTH = 12
STRIP_HEIGHT = 54


def format_words(count: int) -> str:
    return f'{int(count):,}'.replace(',', '.')


def day_label(day: date) -> str:
    """Bijvoorbeeld "di 14 okt" in de taal van de app."""
    locale = QLocale(current_locale() or 'nl')
    return locale.toString(QDate(day.year, day.month, day.day), 'ddd d MMM')


def strip_summary(days: list[tuple[date, int]]) -> str:
    total = sum(count for _day, count in days)
    written = sum(1 for _day, count in days if count > 0)
    return tr('writing_progress.strip_summary', '{count} woorden op {days} van de {total_days} dagen · alleen op deze computer',
              count=format_words(total), days=written, total_days=len(days))


class ProgressStrip(QWidget):
    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings or QSettings('QuietWriter', 'QuietWriter')
        self._days: list[tuple[date, int]] = []
        self.setFixedHeight(STRIP_HEIGHT)
        self.setMinimumWidth(200)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)  # geen bediening; de regel eronder zegt hetzelfde

    def set_days(self, days: list[tuple[date, int]]):
        self._days = list(days)
        self.setAccessibleName(strip_summary(self._days) if self._days else '')
        self.update()

    def days(self) -> list[tuple[date, int]]:
        return list(self._days)

    def _bar_width(self) -> float:
        count = max(1, len(self._days))
        return max(2.0, min(MAX_BAR_WIDTH, (self.width() - BAR_GAP * (count - 1)) / count))

    def bar_rect(self, index: int) -> QRectF:
        """Volle kolom van een dag (ook voor de tooltip)."""
        width = self._bar_width()
        return QRectF(index * (width + BAR_GAP), 0, width, self.height())

    def index_at(self, x: float) -> int | None:
        width = self._bar_width()
        index = int(x // (width + BAR_GAP))
        if 0 <= index < len(self._days) and x - index * (width + BAR_GAP) <= width:
            return index
        return None

    def _theme(self):
        return THEMES.get(str(self.settings.value('theme', 'Helder')), THEMES['Helder'])

    def paintEvent(self, event):
        if not self._days:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        theme = self._theme()
        peak = max(count for _day, count in self._days) or 1
        usable = self.height() - 6
        last = len(self._days) - 1
        for index, (_day, count) in enumerate(self._days):
            column = self.bar_rect(index)
            if count > 0:
                height = max(3.0, usable * count / peak)
                color = QColor(theme['accent'])
                color.setAlpha(255 if index == last else 170)
                painter.setBrush(color)
                painter.drawRoundedRect(QRectF(column.left(), usable - height, column.width(), height), 2, 2)
            else:
                painter.setBrush(QColor(theme['border']))
                painter.drawRoundedRect(QRectF(column.left(), usable - 2, column.width(), 2), 1, 1)

    def tooltip_text(self, index: int) -> str:
        day, count = self._days[index]
        if count <= 0:
            return tr('writing_progress.strip_day_none', '{day} · niet geschreven', day=day_label(day))
        return tr('writing_progress.strip_day', '{day} · {count} woorden', day=day_label(day), count=format_words(count))

    def mouseMoveEvent(self, event):
        index = self.index_at(event.position().x())
        if index is None:
            QToolTip.hideText()
        else:
            QToolTip.showText(event.globalPosition().toPoint(), self.tooltip_text(index), self)
        super().mouseMoveEvent(event)
