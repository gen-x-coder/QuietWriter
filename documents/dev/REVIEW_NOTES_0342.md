# Reviewnotes 0.34.2 — ronde 38

## Eerst verplicht
1. Draai `pytest` met echte PySide6.
2. Draai daarna `pytest tests/legacy`; afgezien van de twee bekende fontresource-tests moet legacy groen zijn.
3. Koude start en smoke-regressie van 0.34.1.

## A. Statusbalk
- Open een boek met minstens twee hoofdstukken en tekst in beide.
- Onder de hoofdstukboom staat **geen** losse `Boek bevat … woorden` meer.
- Statusbalk toont: `Boek: <totaal> woorden · Hoofdstuk <n> van <m>: <hoofdstuk> woorden`.
- Typ in het actieve hoofdstuk: hoofdstuk- én boektotaal lopen mee.
- Wissel hoofdstuk: index en hoofdstuktelling wijzigen, boektotaal blijft correct.
- Tijdelijke statusmelding: na timeout komt de gecombineerde telling terug.
- Planning/Boekenplank/Voorwoord: geen verouderde hoofdstukstatus laten staan.

## B. Planning: corrupt versus nieuwere versie
Test voor `outline.json` én `characters.json`:
1. structureel fout v1 (bijv. `scenes: 5`) → `CorruptSourceError`, boek opent, onderdeel read-only, Integriteit `aux_json_invalid`, herstelbaar indien History-kopie bestaat.
2. geldige `version: 2` → `FuturePlanningFormatError`, boek opent, onderdeel read-only.
3. Bij v2:
   - Chapter Context meldt dat Planning met een nieuwere QuietWriter is gemaakt;
   - Planning meldt **Werk QuietWriter bij**;
   - Integriteit rapporteert `aux_json_newer`;
   - `recoverable == False`;
   - herstelknop uit, ook als History een geldige v1 bevat;
   - live v2-bytes blijven byte-identiek.
4. Controleer dat opslag en Integriteit dezelfde `validate_planning_payload()` gebruiken.

## C. Testorganisatie
- `pytest` verzamelt de zeven teruggeplaatste kernregressiebestanden in `tests/current`.
- Geen duplicaten tussen current en legacy.
- De bijgewerkte legacy Planning-character-tests draaien weer.
- Minor-releasebeleid staat in `tests/README.md`.

## D. Visueel
- Controleer `In dit hoofdstuk`: scènetitels en veldlabels links uitgelijnd met de waarden eronder.
- Controleer ingeklapte railseparators in minstens één licht en één donker thema; noteer of ze voldoende zichtbaar zijn.

## Niet gewijzigd
- Geen nieuwe AI-context.
- Geen Planning-schemawijziging.
- Geen responsive auto-collapse.
