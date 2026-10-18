"""Zelf bijwerken via Velopack.

QuietWriter bouwt geen eigen updater meer. Velopack verzorgt downloaden,
controleren (SHA-256 uit de releasefeed), vervangen van de programmamap en
herstarten. Dit bestand is de enige plek in QuietWriter die Velopack kent.

Wanneer werkt zelf bijwerken?
- alleen in een build die met ``vpk pack`` is gemaakt (portable zip of Setup);
- niet vanuit de broncode (``python main.py``) en niet in oude portable zips
  van vóór 1.5.1. Daar valt QuietWriter terug op ``update_checker``: alleen
  melden en de GitHub-pagina openen.

Boeken, instellingen en logs staan buiten de programmamap (werkmap, register,
%LOCALAPPDATA%). Velopack vervangt alleen de programmamap, dus een update raakt
nooit gebruikersdata.

Eerst zelf testen, daarna pas voor iedereen (zie
``documents/research/UPDATE_UITROL_ONDERZOEK.md``):
- een gewone kopie leest alleen ``releases.win.json`` uit stabiele releases;
- een *testkopie* (leeg bestand ``.quietwriter-update-pilot`` naast
  ``QuietWriter.exe`` / ``Update.exe``) leest ``releases.pilot.json`` en ziet
  ook pre-releases. Velopack vervangt alleen de map ``current``, dus het bestandje
  blijft na elke update staan.
Of gebruikers met één klik kunnen bijwerken, beslist Lucas dus op GitHub (wel
of geen ``releases.win.json`` bij de release), niet de geïnstalleerde versie.

Testen zonder GitHub: zet de omgevingsvariabele ``QUIETWRITER_UPDATE_SOURCE``
op een map met een ``vpk pack``-uitvoer (bijv. ``release\\velopack``). Zie
``documents/RELEASE_PROCESS.md``. Wie omgevingsvariabelen van een gebruiker kan
zetten, heeft die computer al in handen; dit opent dus geen nieuwe aanvalsroute.
"""
from __future__ import annotations

import os
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal

REPO_URL = 'https://github.com/gen-x-coder/QuietWriter'
SOURCE_OVERRIDE_ENV = 'QUIETWRITER_UPDATE_SOURCE'


@dataclass(frozen=True)
class AvailableUpdate:
    version: str
    notes: str
    info: object  # velopack.UpdateInfo; bewust ondoorzichtig voor de UI


PILOT_MARKER = '.quietwriter-update-pilot'
PILOT_CHANNEL = 'pilot'


def update_source_override() -> str:
    return str(os.environ.get(SOURCE_OVERRIDE_ENV, '') or '').strip()


def pilot_marker_candidates(executable: str | os.PathLike | None = None) -> list[Path]:
    """De enige plek waar het pilotbestand telt.

    In een Velopack-kopie draait ``<map>\\current\\QuietWriter.exe``; de map
    die de gebruiker ziet (met ``QuietWriter.exe`` en ``Update.exe``) is de
    ouder daarvan. Alleen daar blijft het bestand na een update staan
    (Velopack vervangt ``current``). Een kopie zonder die indeling kan zichzelf
    niet bijwerken, en vanuit de broncode bestaat geen testkopie.
    """
    if executable is None:
        if not getattr(sys, 'frozen', False):
            return []
        executable = sys.executable
    exe_dir = Path(executable).resolve().parent
    root = exe_dir.parent
    if exe_dir.name.lower() != 'current' or not (root / 'Update.exe').is_file():
        return []
    return [root / PILOT_MARKER]


def is_pilot_copy(executable: str | os.PathLike | None = None) -> bool:
    return any(path.is_file() for path in pilot_marker_candidates(executable))


def build_source_and_options(velopack, *, override: str, pilot: bool):
    """Kies bron en kanaal. Los van ``SelfUpdater`` zodat het testbaar is.

    - gewone kopie: GitHub, alleen stabiele releases, kanaal ``win``;
    - testkopie: GitHub inclusief pre-releases, kanaal ``pilot``;
    - testbron (map of URL): die bron, met het kanaal dat bij de kopie hoort.
    Terugzetten naar een lagere versie staat altijd uit.
    """
    channel = PILOT_CHANNEL if pilot else None
    options = velopack.UpdateOptions(False, 0, channel)
    if override:
        if override.lower().startswith('https://github.com/'):
            source = velopack.GithubSource(override, None, bool(pilot))
        else:
            source = override  # lokale map of eigen webadres met de feed
    else:
        source = velopack.GithubSource(REPO_URL, None, bool(pilot))
    return source, options


class SelfUpdater:
    """Dunne laag rond ``velopack.UpdateManager``.

    ``available`` is False als Velopack ontbreekt of als deze kopie niet via
    Velopack is verpakt. Alle andere methodes mogen dan niet aangeroepen worden.
    """

    def __init__(self, manager_factory=None):
        self._manager = None
        self.reason = ''
        self.source_label = 'github'
        self.pilot = False
        try:
            if manager_factory is None:
                import velopack
                override = update_source_override()
                self.pilot = is_pilot_copy()
                if override:
                    self.source_label = 'override'
                source, options = build_source_and_options(velopack, override=override, pilot=self.pilot)
                self._manager = velopack.UpdateManager(source, options)
            else:
                self._manager = manager_factory()
        except ImportError:
            self.reason = 'velopack-missing'
        except Exception:
            # Velopack meldt "not properly installed" bij een bron- of oude build.
            self.reason = 'not-installed'
            self._manager = None

    @property
    def available(self) -> bool:
        return self._manager is not None

    @property
    def is_portable(self) -> bool:
        return bool(self._manager is not None and self._manager.get_is_portable())

    def current_version(self) -> str:
        return str(self._manager.get_current_version()) if self._manager is not None else ''

    def check(self) -> AvailableUpdate | None:
        info = self._manager.check_for_updates()
        if not info:
            return None
        target = info.TargetFullRelease
        return AvailableUpdate(
            version=str(target.Version),
            notes=str(getattr(target, 'NotesMarkdown', '') or '')[:2000],
            info=info,
        )

    def download(self, update: AvailableUpdate, progress=None) -> None:
        self._manager.download_updates(update.info, progress)

    def apply_when_closed(self, update: AvailableUpdate) -> None:
        """Laat Velopack wachten tot dit proces is beëindigd.

        Aanroepen pas nádat het hoofdvenster via het normale afsluitpad dicht
        is (alles opgeslagen). Daarna vervangt Velopack de programmamap en
        start QuietWriter opnieuw.
        """
        self._manager.wait_exit_then_apply_updates(update.info, False, True, None)


class SelfUpdateWorker(QObject):
    """Voert één netwerkstap uit buiten de UI-thread: 'check' of 'download'.

    Bewust een Python-*daemon*thread en geen QThread: wordt QuietWriter
    afgesloten terwijl een controle of download loopt, dan stopt het proces
    gewoon. Een QThread zou dan Qt laten afbreken ("Destroyed while thread is
    still running"). Een half gedownload pakket wordt door Velopack nooit
    toegepast: het controleert de SHA-256 uit de feed.

    ``silent`` hoort bij déze bewerking: een automatische controle meldt
    niets bij "geen update" of een fout; een handmatige wel.
    """

    found = Signal(object)        # AvailableUpdate | None
    progress = Signal(int)        # 0-100
    downloaded = Signal(object)   # AvailableUpdate
    failed = Signal(str)
    finished = Signal()

    def __init__(self, updater: SelfUpdater, mode: str, update: AvailableUpdate | None = None,
                 parent=None, *, silent: bool = False):
        super().__init__(parent)
        self.updater = updater
        self.mode = mode
        self.pending = update
        self.silent = bool(silent)
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self.run, name=f'quietwriter-update-{self.mode}', daemon=True)
        self._thread.start()

    def isRunning(self) -> bool:  # noqa: N802 (Qt-achtige naam, gelijk aan de vorige QThread-API)
        return bool(self._thread is not None and self._thread.is_alive())

    def _emit(self, signal, *args) -> None:
        # Na afsluiten kan het Qt-object al weg zijn; dan is er niemand meer
        # om iets te melden en hoort de thread stil te stoppen.
        try:
            signal.emit(*args)
        except RuntimeError:
            pass

    def run(self):
        try:
            if self.mode == 'check':
                self._emit(self.found, self.updater.check())
            elif self.mode == 'download' and self.pending is not None:
                def _progress(value=0, *_):
                    try:
                        self._emit(self.progress, max(0, min(100, int(value))))
                    except (TypeError, ValueError):
                        pass
                self.updater.download(self.pending, _progress)
                self._emit(self.downloaded, self.pending)
            else:
                raise ValueError(f'Onbekende updatestap: {self.mode}')
        except Exception as exc:  # netwerk, GitHub, schijf: altijd netjes melden
            self._emit(self.failed, str(exc) or type(exc).__name__)
        finally:
            self._emit(self.finished)
