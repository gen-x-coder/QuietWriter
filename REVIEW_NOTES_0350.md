# Review QuietWriter 0.35.0 — releasefundament: branding, crashvangnet en CI

## Scope

Deze build start de 1.0-lijn. Geen nieuwe schrijf- of AI-feature. De functionele wijzigingen zijn beperkt tot branding, crashdiagnostiek en testinfrastructuur.

## Verplicht door Claude te draaien met echte PySide6

1. `pytest`
2. `pytest -m qt`
3. `pytest tests/legacy`
4. `pytest tests/legacy -m qt`
5. `python main.py`

Omdat ChatGPT in deze omgeving geen PySide6-runtime heeft, zijn juist deze Qt-runs expliciet onderdeel van de review.

## A. Branding

- Windows/taskbar-icoon gebruikt `quietwriter/resources/quietwriter.ico`, niet meer het boekenicoon/Python-icoon.
- Op Windows wordt vóór `QApplication` AppUserModelID `LucasBonsel.QuietWriter` gezet.
- Splash blijft bestaan en toont het thema-gekleurde woordmerk.
- Over toont hetzelfde woordmerk; wisselen van thema ververst het woordmerk.
- Controleer Helder, Nacht en Aurora.
- Controleer 16/24/32 px taskbar/window-icon indien Windows beschikbaar is.

## B. Crashvangnet

- `crash.log` staat niet meer in de werkmap maar onder `QStandardPaths.AppLocalDataLocation/logs/crash.log`.
- Forceer één exception vanuit een Qt-slot. Verwachting:
  - fout komt in `crash.log`;
  - QuietWriter blijft niet stil;
  - er verschijnt een niet-modale melding met `Logbestand openen`;
  - de melding beweert niet dat data gegarandeerd is opgeslagen, maar vraagt de laatste wijziging te controleren.
- Forceer een exception in een Python-thread: log + zichtbare melding via de Qt-signal bridge.
- Trigger een `qWarning`: het bericht staat in hetzelfde logbestand maar opent géén foutdialoog.
- Start met werkmap in Dropbox/OneDrive: het log blijft buiten die werkmap.
- Test rotatie rond 2 MiB en tempfallback bij onschrijfbare lokale logmap.
- Controleer dat een startup-/workspacefoutdialoog niet door de splash wordt verborgen.

## C. CI

`.github/workflows/tests.yml` draait dezelfde vier suites op Ubuntu én Windows met `QT_QPA_PLATFORM=offscreen`. Controleer de workflowsyntaxis en of `requests`, `spylls` en `PyYAML` voldoende testdependencies zijn.

## D. First-run

Nog niet gebouwd. `FIRST_RUN_DESIGN_035.md` legt alleen het contract voor 0.36 vast: maximaal vier stappen, bestaande gebruikers nooit automatisch, AI standaard uit.

## Niet in 0.35.0

- vertaalgaten oplossen;
- licentie-inventaris afronden;
- first-run bouwen;
- portable Windows-build.

Die volgen in volgende 0.35.x/0.36 builds; 0.35.0 is bewust een afgebakende eerste release-hardening slice.
