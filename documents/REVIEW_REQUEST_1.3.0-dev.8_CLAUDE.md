# QuietWriter 1.3.0-dev.8 — reviewopdracht voor Claude

Wijzig geen code. Review en test deze snapshot als opvolging van `QUIETWRITER_REVIEW_1_3_0_DEV7_CLAUDE.md`.

## Hoofddoel

Bevestig dat W1, W2 en W3 uit de dev.7-review correct zijn opgelost zonder regressies. Beoordeel daarna of de Boekenkast functioneel klaar is voor een Windows/visuele acceptatietest richting 1.3.0.

## A. Volledige regressie

- Draai de volledige pytest-suite met PySide6.
- Draai `--smoke-test`.
- Controleer alle 5 locales en undefined names.
- Draai pyflakes en vergelijk afwijkingen met dev.7.
- Noteer opnieuw de pytest-exitcode; behandel rc 139 na alle geslaagde tests als bekende Qt/Linux teardown-observatie, tenzij het gedrag veranderd is.

## B. W1 — runtimeprofiel / settings

Test stable én dev-profiel.

- `StartPage` moet dezelfde `QSettings`-instantie gebruiken als `MainWindow`.
- Presentatiemodus aan/uit moet uitsluitend in de actieve profielopslag terechtkomen.
- Forceer een mislukt sluitpad terwijl een privéboek actief is en controleer dat knopstatus, `demo_mode_enabled()` en persistente setting allemaal **uit** zijn.
- Controleer dat stable en dev niet langer onbedoeld dezelfde Presentatiemodus-status delen.

## C. W2 — onverwachte exception

- Open een privéboek.
- Forceer tijdens het inschakelen een onverwachte exception uit `go_home()` / een onderliggend save-pad, bijvoorbeeld `PermissionError`.
- Presentatiemodus moet daarna **uit** staan en het privéboek mag open blijven; dus fail-safe zonder valse privacy-indicatie.
- Controleer dat de exception wordt gelogd zonder een nieuwe crash of recursielus.
- Herhaal de reeds bestaande bekende save-fouten (`False`, `StorageWriteError`) om regressie uit te sluiten.

## D. W3 — persistente woordtellingcache

Gebruik een geïsoleerde lokale appdatamap indien nodig.

- Eerste koude sessie: tel een realistische bibliotheek en controleer dat een lokaal cachebestand ontstaat.
- Nieuwe `StartPage` / nieuwe proces-sessie met ongewijzigde bestanden: er mogen geen hoofdstukken opnieuw door `count_words` worden gehaald.
- Wijzig één hoofdstuk: alleen dat hoofdstuk moet opnieuw worden geteld en daarna moet de cache worden bijgewerkt.
- Test twee verschillende werkmappen: ze moeten verschillende cachebestanden krijgen.
- Test corrupt JSON-cachebestand: geen crash, opnieuw tellen en weer een bruikbare cache schrijven.
- Test niet-schrijfbare/ongeldige cachelocatie: QuietWriter moet gewoon blijven werken; hoogstens valt performance terug.
- Bevestig dat de cache **niet** in de werkmap, `library.json` of `.qwbook` terechtkomt.

Meet de koude start bij 25 en indien praktisch 100 grote boeken, en vergelijk een tweede sessie met dev.7. De tweede sessie hoort de grote woordtelpiek kwijt te zijn.

## E. Presentatiemodus regressie

Herhaal de belangrijkste dev.7-scenario's:

- privéboek sluiten bij inschakelen;
- publieke boeken blijven open/bereikbaar;
- `open_book(privé)` wordt fail-closed geweigerd;
- corrupt/future `library.json` blijft fail-closed;
- geen privégegevens zichtbaar in Boekenkast, Bewaarplaats of Prullenbak.

## F. Covers / W4

Geen codewijziging gevraagd. Meet alleen nogmaals hoe groot P3 na een warme/persistente cache is. Geef aan of jij nog steeds vindt dat de beslissing terecht bij de echte Windows-test met echte covers ligt.

## G. Documentatie en packaging

- Versie moet overal waar actueel metadata betreft `1.3.0-dev.8` zijn.
- `README.md` moet byte-identiek aan dev.7 zijn.
- Als `README_EN.md` aanwezig is, moet ook die byte-identiek zijn.
- `RELEASE_NOTES_1.3.0-dev.8.md` moet de cache correct als lokaal/persistent beschrijven en `library.json` noemen.

## Rapportage

Classificeer bevindingen als:

1. blocker vóór dev.9;
2. wel doen vóór 1.3.0;
3. alleen doen als Windows/visueel dit bevestigt;
4. backlog voor 1.4.x.

Wijzig geen code.
