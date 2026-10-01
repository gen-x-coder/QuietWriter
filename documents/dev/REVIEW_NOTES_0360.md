# Review notes 0.36.0 — clean release staging / Windows packaging foundation

0.36.0 verandert nog geen first-run-gedrag. De kern van deze build is dat de ontwikkelmap bewust rommelig mag zijn, terwijl de build altijd uit een schone allowlist-staging komt.

## Standaard

Draai onder Python 3.12 met echte PySide6:

1. `pytest`
2. `pytest -m qt`
3. `pytest tests/legacy`
4. `pytest tests/legacy -m qt`
5. `python main.py`
6. `python tools/check_undefined_names.py`

## Nieuwe release-staging

1. Maak expres een map `ppm/` met willekeurige bestanden, een `REVIEW_NOTES_TEST.md`, een `.log` en ander afval in de ontwikkelroot.
2. Draai `python tools/prepare_release.py`.
3. Controleer dat `release/stage` wél `main.py`, `quietwriter/`, `packaging/`, de twee fetch-tools, fontmanifest/OFL's en licenties bevat.
4. Controleer dat `release/stage` géén `ppm`, `tests`, `.git`, `.github`, review-notes, tussenrapporten, caches of gedownloade TTF's bevat.
5. Draai `python tools/prepare_release.py --check`.
6. Controleer `release/stage/STAGE_MANIFEST.json`: versie 0.36.0 en SHA-256 per opgenomen bestand.

## Windows lokale build — belangrijk voor Lucas

Op Lucas' Windows-machine vanuit de normale, vervuilde projectmap:

`build_exe.cmd`

Verwacht:
- build begint met het opnieuw maken van `release/stage`;
- fonts en nl_NL-woordenboek worden binnen de stage opgehaald;
- `release/QuietWriter-0.36.0/QuietWriter.exe` bestaat;
- `release/QuietWriter-0.36.0-windows-portable.zip` en `.sha256` bestaan;
- in de uiteindelijke map/ZIP staan geen `.py` bronbestanden uit de ontwikkelroot, geen tests, PPM of reviewrapporten;
- QuietWriter.exe start zonder Python-installatie uit de portable map;
- Over → Licenties opent QuietWriter-, third-party- en fontlicenties;
- het meegeleverde Nederlandse woordenboek verschijnt als `Meegeleverd`.

Controleer tevens Windows Eigenschappen → Details van QuietWriter.exe: productnaam/versie 0.36.0 en copyright.

## Claude-bestanden

De aangeleverde `quietwriter-exe-build.zip` is als basis gebruikt. Controleer vooral de PyInstaller-datastructuur: `quietwriter/icons`, `quietwriter/locales`, `quietwriter/resources`, `resources/fonts`, `dictionaries`, `LICENSE` en `THIRD_PARTY_LICENSES.md` moeten in de onedir-layout terechtkomen waar de bestaande `__file__`-paden ze verwachten.
