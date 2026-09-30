# Tussentijds rapport 0.34.2

## Aanleiding
Lucas vond de losse boektelling onder de hoofdstukboom onlogisch en wilde boek- en hoofdstuktelling samen in de statusbalk. Reviewronde 37 wees daarnaast op het risico dat een Planning-bestand van een nieuwere QuietWriter als herstelbare corruptie werd behandeld, plus enkele gaten in de nieuwe current/legacy-testindeling.

## Uitgevoerd
- Losse `book_words`-label uit Inhoud verwijderd.
- Statusbalk combineert boektotaal en actief hoofdstuk.
- Centrale `validate_planning_payload()` toegevoegd.
- `FuturePlanningFormatError` onderscheidt nieuwere Planning-data van corruptie.
- Integriteit meldt nieuwere Planning als `aux_json_newer`, niet-herstelbaar.
- Planning en Chapter Context tonen een update-instructie voor nieuwere data.
- Zeven kernregressiebestanden terug naar `tests/current`.
- Legacy Planning-fakes en de separator-Qt-test bijgewerkt.
- Minor-releasebeleid voor een volledige legacy-run vastgelegd.

## Lokaal getest
- `pytest`: 167 geslaagd, 11 overgeslagen.
- `pytest tests/legacy`: 424 geslaagd, 24 overgeslagen, 280 subtests; alleen de 2 bekende fontresource-tests falen.
- `pytest tests/current tests/legacy --ignore=tests/legacy/test_bundled_fonts.py`: 589 geslaagd, 35 overgeslagen, 280 subtests.
- `compileall`: groen.

## Bewust nog niet gedaan
- Geen Planning → AI-context.
- Geen nieuw Planning-schema.
- Geen automatische paneel-collapse op smalle/DPI-schermen.
