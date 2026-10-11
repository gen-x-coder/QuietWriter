# QuietWriter 1.3.0-dev.9

## Privacyvriendelijke cache en schonere tests

- De persistente woordtellingcache van de Boekenkast gebruikt voortaan een SHA-256-hash van het hoofdstukpad als sleutel. Volledige hoofdstukpaden en daarin voorkomende boektitels worden niet meer in de lokale cache opgeslagen.
- Bestaande dev.8-cachebestanden met oude pad-sleutels zijn veilig compatibel: zulke sleutels worden niet geladen. Bij de eerstvolgende Boekenkast-refresh worden de hoofdstukken opnieuw geteld en wordt het cachebestand met uitsluitend gehashte sleutels overschreven.
- De cache-invalidatie blijft hetzelfde: `mtime_ns` en bestandsgrootte bepalen of een hoofdstuk opnieuw moet worden geteld. De cache blijft lokaal in de appdatamap, buiten de werkmap.
- De testsuite schakelt Qt `QStandardPaths` testmodus in. Tijdelijke testwerkruimtes schrijven daardoor niet langer tientallen woordtellingcachebestanden naar de echte lokale appdatamap van de ontwikkelmachine.
- Ontbrekende, corrupte of onbruikbare cachebestanden blijven niet fataal: QuietWriter telt opnieuw en blijft functioneren.
- `library.json`, de plankindeling, Presentatiemodus en het `.qwbook`-formaat zijn niet gewijzigd.
- Cover-pixmapcaching blijft bewust conditioneel op de Windows-acceptatietest met echte covers.

`README.md` en `README_EN.md` worden voor 1.3.x bewust niet aangepast.
