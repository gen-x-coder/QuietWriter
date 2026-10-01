# Review QuietWriter 0.35.1 — crashhardening, startup, branding en HiDPI

## Verplicht door Claude met echte PySide6

Draai:

- `pytest`
- `pytest -m qt`
- `pytest tests/legacy`
- `pytest tests/legacy -m qt`
- koude start via `python main.py`

## Runtimechecks

1. **Crashstorm:** laat een QTimer-slot 50 keer dezelfde exception geven. Verwachting: precies één zichtbaar foutvenster; daarin staat dat er extra fouten waren. Het log bevat alle 50 exceptions. Sluit het venster en laat dezelfde fout direct opnieuw optreden: geen nieuw venster binnen de cooldown.
2. **Andere fout terwijl venster open is:** ook die wordt in hetzelfde venster meegeteld; geen tweede dialoog.
3. **Startup-crash:** injecteer een exception in `MainWindow(...)` vóór `app.exec()`. De splash sluit en een modale foutmelding blijft zichtbaar met knop `Logbestand openen`.
4. **Qt-waarschuwing:** staat in `crash.log` én op stderr als er geen eerdere Qt-message-handler is; geen crashdialoog.
5. **Over-pagina:** controleer in Helder, Nacht en Aurora dat het woordmerk op de donkere hero altijd licht en leesbaar is. Dit is bewust anders dan de thematische splash.
6. **HiDPI:** controleer splash, Over en rail-/werkbalkiconen met 100%, 125% en 150% schaal. Ze moeten scherp blijven en logisch dezelfde visuele maat houden.
7. **First-run-design:** alleen documentcontrole in 0.35.1: `workspace` is niet langer de trigger; bestaande gebruikers moeten in 0.36 worden herkend via `first_run_done`/bestaande state.
8. **CI YAML:** Ubuntu bevat `libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3`. Het fontmanifest is bewust nog niet in deze build opgelost; dat gaat samen met de licentie-inventaris in 0.35.2.

## Bekend / nog niet in 0.35.1

- Vertaalgaten en hardgecodeerde Nederlandse UI-teksten volgen in 0.35.2.
- `LICENSE`, `THIRD_PARTY_LICENSES.md`, fontmanifest en fontlicenties volgen in 0.35.2.
- De first-run wizard zelf wordt pas in 0.36 gebouwd.
