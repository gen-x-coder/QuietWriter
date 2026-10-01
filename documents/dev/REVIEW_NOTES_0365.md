# Review notes 0.36.5

Follow-up op Claude review 53. Deze ronde is uitsluitend release-hardening.

## Gerepareerd

1. `SettingsPage.save_settings()` berekent de genormaliseerde werkmap zelf. `refresh_models()` wijzigt het werkmapveld niet meer.
2. Oude en nieuwe werkmap worden beide genormaliseerd voordat `MainWindow.settings_saved()` ze vergelijkt. Alleen een semantische wijziging geeft de herstartmelding.
3. `--smoke-test` gebruikt een tijdelijke `QSettings.IniFormat` en tijdelijke appdata; DEV/PROD-instellingen blijven onaangeroerd.
4. Startupfouten in smoke-modus tonen geen dialoog. Ze gaan naar log/stderr en leveren exitcode 1. Onverwachte exceptions tijdens de eventloop worden door de smoke-notifier geteld en leveren eveneens exitcode 1.
5. Windows CI geeft de smoketest maximaal vijf minuten.
6. `LEESMIJ.txt` wordt buiten PyInstaller om naast `QuietWriter.exe` gekopieerd; `_internal/LEESMIJ.txt` is verboden.
7. LEESMIJ bevat nu uitpakken, SmartScreen ('Meer info' → 'Toch uitvoeren'), crashloglocatie en normale Windows-padnotatie.
8. `build_exe.cmd` installeert indien nodig `pyflakes` en voert de undefined-name checker uit vóór de release-build.

## Verplichte reviewruns

- `python tools/check_undefined_names.py`
- `python -m pytest`
- `python -m pytest -m qt`
- `python -m pytest tests/legacy`
- `python -m pytest tests/legacy -m qt`
- `python tools/prepare_release.py`

## Gerichte handmatige controle

- Sla alleen een themawijziging op met een opgeslagen werkmap die tekstueel afwijkt maar naar dezelfde map wijst (bijv. trailing slash): geen melding 'Werkmap gewijzigd'.
- Start lokaal `QuietWriter.exe --smoke-test` en controleer daarna dat DEV-instellingen exact gelijk zijn gebleven.
- Controleer in de portable map dat `LEESMIJ.txt` direct naast `QuietWriter.exe` staat.
- Forceer in een testkopie een exception in `MainWindow.__init__`: smoke moet snel met exitcode 1 eindigen zonder dialoog.
