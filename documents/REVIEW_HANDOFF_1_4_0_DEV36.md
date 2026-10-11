# Reviewoverdracht voor Claude — 1.4.0-dev.36

## Prioriteit

Voer alle dev.35-reproducties opnieuw uit met echte PySide6. Prioriteit: `ext35.py` voor zowel handmatige als automatische back-ups, `nohist35.py`, `trash35.py`, `partial35.py`, `daily35.py`, `savecost35.py`, de OpenTaal spellingharnassen en de volledige Qt-suite. Bevestig dat een externe wijziging van het geopende boek nooit stil wordt geaccepteerd. Test ook het geblokkeerde boek.

## Specifieke aandachtspunten

- Snapshot-checkpoints voor integriteitsherstel mogen zichtbaar blijven, maar geen ontbrekende hoofdstukken mogen terugzetten als lege tekst.
- Herstel zonder history behoudt de live history; bij `ai_chat_included=false` wordt lokale AI-chat bewaard. Controleer normale en rollback-paden met bestandslocks.
- Dagversies en handmatige versies verschijnen pas na een volledige kopie. De conflict-local-varianten schrijven eveneens in een verborgen stagingmap.
- Per-hoofdstukindexering moet identieke zoekresultaten geven na opslaan en mag na cachecorruptie veilig terugvallen op een volledige herbouw.
- `README_EN.md` zat niet in de originele dev.35-snapshot en is niet door ons gereconstrueerd.

## Nog te beoordelen

Kleine punten zoals prullenbakdatum, eerste-run woordenboekdetectie en de overige vertaalsleutelbotsingen zijn niet als afgerond geclaimd. Onderzoek eveneens of per-woordspellingtaken netjes stoppen bij afsluiten. Windows/OneDrive blijft belangrijk voor een uiteindelijke release.
