"""Ollama eenvoudiger instellen (1.7): kijken of Ollama draait en een model binnenhalen.

Geen Qt hier. De UI (``ui/ollama_setup.py``) roept deze functies in een thread aan.
QuietWriter installeert Ollama nooit zelf: het wijst naar de officiële downloadpagina.
Een model binnenhalen gaat via Ollama's eigen ``/api/pull``; QuietWriter downloadt
zelf niets en schrijft niets in de werkmap of de instellingen.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

import requests

OLLAMA_DOWNLOAD_URL = 'https://ollama.com/download'

# Status
MISSING = 'missing'        # niets bereikbaar op het adres
NO_MODELS = 'no_models'    # Ollama draait, maar er is nog geen model
READY = 'ready'            # Ollama draait en heeft minstens één model


@dataclass(frozen=True)
class RecommendedModel:
    name: str          # precies de naam voor ``ollama pull``
    size_gb: float     # ongeveer, voor de uitleg
    level: str         # 'light' | 'medium' | 'strong'
    min_ram_gb: int


# Een korte, vaste lijst (gecontroleerd 18 oktober 2026 op ollama.com/library).
# Bewust klein: een schrijver moet kunnen kiezen zonder modellen te kennen.
# Bijwerken bij een nieuwe release; een verdwenen naam geeft een nette foutmelding.
RECOMMENDED_MODELS: tuple[RecommendedModel, ...] = (
    RecommendedModel('qwen3.5:4b', 3.4, 'light', 8),
    RecommendedModel('gemma4:12b', 7.6, 'medium', 16),
    RecommendedModel('qwen3.5:9b', 6.6, 'medium', 16),
    RecommendedModel('gemma4:26b', 18.0, 'strong', 32),
)


def total_ram_gb() -> float | None:
    """Werkgeheugen van deze computer in GB, of None als dat niet te zien is."""
    try:
        if sys.platform.startswith('win'):
            import ctypes

            class _Status(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
            status = _Status()
            status.dwLength = ctypes.sizeof(_Status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return None
            return status.ullTotalPhys / 1024 ** 3
        return os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1024 ** 3
    except (AttributeError, ValueError, OSError):
        return None


def suggested_level(ram_gb: float | None) -> str:
    """Welk niveau past bij dit geheugen. Bij twijfel het lichte model."""
    if ram_gb is None or ram_gb < 14:
        return 'light'
    if ram_gb < 28:
        return 'medium'
    return 'strong'


def suggested_model(ram_gb: float | None) -> RecommendedModel:
    level = suggested_level(ram_gb)
    return next(model for model in RECOMMENDED_MODELS if model.level == level)


def check_ollama(base_url: str, timeout: float = 2.0) -> tuple[str, list[str]]:
    """Geef (status, modelnamen). Gooit nooit: elke fout betekent 'niet gevonden'."""
    try:
        response = requests.get(f'{base_url.rstrip("/")}/api/tags', timeout=timeout)
        response.raise_for_status()
        names = [str(row.get('name') or '') for row in response.json().get('models', [])]
    except Exception:
        return MISSING, []
    names = [name for name in names if name]
    return (READY if names else NO_MODELS), names


class PullCancelled(Exception):
    pass


def pull_model(base_url: str, name: str, on_progress=None, should_stop=None, timeout: float = 30.0) -> None:
    """Laat Ollama *name* downloaden. ``on_progress(fractie|None, status)`` tijdens het werk.

    Ollama stuurt per regel JSON met ``status`` en (tijdens downloaden) ``total`` en
    ``completed``. Een regel met ``error`` wordt een RuntimeError met die tekst.
    ``should_stop()`` wordt tussen regels gevraagd; dan stopt het met PullCancelled.
    Ollama bewaart wat al binnen is, dus opnieuw beginnen gaat verder waar het was.
    """
    with requests.post(f'{base_url.rstrip("/")}/api/pull', json={'model': name, 'stream': True},
                       stream=True, timeout=timeout) as response:
        if not response.ok:
            try:
                detail = response.json().get('error')
            except Exception:
                detail = None
            raise RuntimeError(detail or f'HTTP {response.status_code}')
        for raw in response.iter_lines():
            if should_stop and should_stop():
                raise PullCancelled()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            if row.get('error'):
                raise RuntimeError(str(row['error']))
            status = str(row.get('status') or '')
            total, completed = row.get('total'), row.get('completed')
            fraction = (completed / total) if total and completed is not None else None
            if on_progress:
                on_progress(fraction, status)
            if status == 'success':
                return
    raise RuntimeError('Ollama stopte voordat het model binnen was.')
