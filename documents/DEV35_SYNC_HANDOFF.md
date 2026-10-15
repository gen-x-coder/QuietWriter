# QuietWriter dev.35 — synchronisatie en boekenkast

## Oplevering
Volledige bronbasis afkomstig uit `QuietWriter-1.5.0-dev.34-source-review.zip`. Geen GitHub-mutaties. Het interne versienummer is bewust niet geforceerd verhoogd (de bestaande bron noemt dev.28); pas versieadministratie aan bij acceptatie van de ontwikkelbranch.

## Wijzigingen
- Boekenkast: handmatige knop **Vernieuwen** en F5 (alleen wanneer de boekenkast actief is).
- Iedere acht seconden wordt **alleen bij zichtbare boekenkast** een metadatahandtekening van `books/*/book.json` vergeleken. Verandering leidt tot een gewone `StartPage.refresh()`. Geen Dropbox-API of netwerkstatusclaims.
- Rustige niet-modale aanduiding voor boekmap zonder `book.json` en aangetroffen bestandsnamen met `conflicted copy`/`conflictkopie`. Er worden geen conflictkopieën verwijderd of overschreven.
- `create_version_from_state` controleert ontbrekende hoofdstukbestanden vóór het aanmaken van een tijdelijke versiegeschiedenismap; resterende I/O-fouten tijdens het schrijven vragen nog een afzonderlijke transactietest.
- Vier vertaalde UI-sleutels voor vijf talen; nieuwe Qt-tests voor het verschijnen van metadata en read-only conflictdetectie.

## Tests in deze omgeving
- 29 geslaagd, 2 overgeslagen (gerichte sync/boekenkasttests).
- 32 geslaagd, 2 overgeslagen (bestaande boekenkast-/manuscripttests).
- Volledige suite gestart, zonder gerapporteerde testfail tot ~86%, maar tijdslimiet bereikt. **Geen GO voor volledige suite**.

## Beperkingen / veiligheidsgrenzen
- Metadata-polling toont binnengekomen boeken pas nadat `book.json` daadwerkelijk lokaal beschikbaar is. Synchronisatievoortgang van Dropbox/OneDrive is generiek niet betrouwbaar detecteerbaar.
- Conflictkopieën alleen gesignaleerd; detailweergave met map-/Verkennerlink staat nog op de backlog.
- `Alles vervangen` over meerdere hoofdstukken is nog niet één atomische schrijfactie als externe wijzigingen midden in de operatie optreden; **niet als opgelost beschouwen**.
- De oude automatische updater blijft uit, de handmatige GitHub-route blijft ongemoeid.
- Test op Windows met een echte Dropbox-laptop: ontbrekende metadata, vertraagd hoofdstuk, nieuw boek terwijl de boekenkast openstaat, F5, conflictkopie, online-only placeholder.
