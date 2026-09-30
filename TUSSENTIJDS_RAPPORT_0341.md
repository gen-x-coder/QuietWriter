# Tussentijds rapport 0.34.1

## Aanleiding
Reviewronde 36 was functioneel groen voor 0.34.0, maar liet drie relevante punten zien: Planning-JSON met een verkeerde structuur kon het hele boek stil blokkeren, het contextpaneel miste visuele hiërarchie en een rechterpaneel maakt lage/DPI-schermen krap. Lucas meldde daarnaast een ontbrekende/verdwijnende woordtelling, nauwelijks zichtbare separators in de ingeklapte rail en het ontbreken van scènevelden zoals Notities.

## Uitgevoerd
- PlanningStore valideert versie en lijststructuren fail-closed met `CorruptSourceError`.
- MainWindow-preflight accepteert die fout als ondersteunde read-only Planning-state in plaats van boek-open te blokkeren.
- Personages/Outline tonen de bronwaarschuwing en worden voor het beschadigde onderdeel niet bewerkbaar.
- Integriteit valideert nu ook Planning-structuur.
- ChapterContext toont Doel, Conflict, Uitkomst en Notities en gebruikt compacte scènekaarten.
- Statusbalk bewaart de documentstatus en herstelt deze na tijdelijke berichten.
- Collapsed-rail separators zijn visueel versterkt.

## Lokaal getest
- Gerichte 0.34.1-tests: groen.
- Volledige lokale suite: 589 passed + 280 subtests; 34 Qt-runtimetests overgeslagen; alleen de 2 bekende ontbrekende fontresource-tests falen.

## Bewust nog niet gedaan
- Geen automatische Planning → AI-context.
- Geen schemawijzigingen.
- Geen automatische rail-/Inhoud-collapse op kleine schermen; dit blijft een expliciete UX-keuze na echte Windows-DPI-observatie.

## Testorganisatie
Vanaf 0.34.1 is de historisch gegroeide suite opgesplitst. `tests/current/` bevat de compacte standaardset en `tests/legacy/` bewaart oude reviewtests. `pytest.ini` laat een gewone `pytest` alleen de actuele suite draaien. De legacy-suite blijft expliciet uitvoerbaar voor mijlpaal- en regressieonderzoek.

Lokale controle in deze omgeving:
- actuele suite: 135 geslaagd, 8 overgeslagen;
- legacy zonder de twee bekende fonttests: 452 geslaagd, 27 overgeslagen, 280 subtests;
- current + legacy zonder de bekende fonttests: 587 geslaagd, 35 overgeslagen, 280 subtests.
