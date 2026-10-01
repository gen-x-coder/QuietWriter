# Tussentijds rapport — QuietWriter 0.32.5

## Aanleiding

Lucas meldde direct na 0.32.4 een startup-crash. Inspectie van de ZIP liet zien dat `ManuscriptEditor.source_text()` per ongeluk vóór het einde van `__init__` was ingevoegd. Hierdoor was het grootste deel van de constructor onbereikbaar.

## Correctie

`source_text()` is verplaatst tot na de volledige constructor. De oorspronkelijke editorinitialisatie uit 0.32.3/0.32.4 is daarmee hersteld zonder andere functionele wijziging.

## Tests lokaal

- gerichte bron/contracttests: 6 geslaagd, 2 Qt-tests overgeslagen;
- volledige suite: 568 geslaagd, 31 overgeslagen, 280 subtests geslaagd;
- alleen de 2 bekende fontresource-tests falen wegens ontbrekend `resources/fonts/font_manifest.json`;
- `python -m compileall quietwriter`: groen.

PySide6 is niet geïnstalleerd in deze omgeving, daarom moet Claude de echte startup-runtime als eerste controleren.
