"""Interfacegrootte: de hele interface groter of kleiner (1.7).

Qt legt de schaalfactor vast bij het opstarten (``QT_SCALE_FACTOR``); daarom
geldt een nieuwe keuze na een herstart, net als de programmataal. Windows-
schaal (125%, 150%) blijft gewoon werken; deze factor komt erbovenop.
"""
from __future__ import annotations

import os

SETTING_KEY = 'interface_scale'
DEFAULT_SCALE = 100
SCALES = (80, 90, 100, 110, 125, 150, 175)


def normalize_scale(value) -> int:
    """Een opgeslagen waarde naar de dichtstbijzijnde toegestane stap (onzin = 100%)."""
    try:
        number = int(float(str(value).strip().rstrip('%')))
    except (TypeError, ValueError):
        return DEFAULT_SCALE
    if not 50 <= number <= 300:
        return DEFAULT_SCALE
    return min(SCALES, key=lambda step: (abs(step - number), step))


def apply_interface_scale(settings, environ=None) -> float | None:
    """Zet ``QT_SCALE_FACTOR`` vóór ``QApplication`` wordt gemaakt.

    Een factor die de gebruiker zelf in de omgeving zette, gaat voor.
    Geeft de toegepaste factor terug, of None als er niets veranderde.
    """
    env = os.environ if environ is None else environ
    if env.get('QT_SCALE_FACTOR'):
        return None
    try:
        scale = normalize_scale(settings.value(SETTING_KEY, DEFAULT_SCALE))
    except Exception:
        return None
    if scale == DEFAULT_SCALE:
        return None
    factor = scale / 100.0
    env['QT_SCALE_FACTOR'] = f'{factor:g}'
    return factor
