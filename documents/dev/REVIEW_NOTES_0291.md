# Review notes — QuietWriter 0.29.1

Deze patch is uitsluitend de aansluiting van Integriteit & Herstel op de live workspace.

## Te verifiëren

1. Open een boek op hoofdstuk 2, verwijder dat hoofdstukbestand extern, open Integriteit en herstel het. Terug in Schrijven moet onmiddellijk de herstelde tekst staan. Eén extra zin typen mag de bestaande herstelde tekst alleen aanvullen, niet vervangen.
2. Hetzelfde scenario zonder eerst terug te gaan via de Boekenplank: de eerste herstelpoging moet direct kunnen slagen. "Opnieuw controleren" moet eveneens de actuele schijftoestand adopteren.
3. Vergelijk vóór en na alleen-controleren de volledige boekmap byte voor byte: audit/reload mag niets schrijven.
4. Verander een bestand nadat de audit al zichtbaar is maar vóór Herstel. De bestaande revision guard moet die echte race nog steeds weigeren.
5. Herstel `planning/characters.json` en controleer dat Planning daarna de herstelde data gebruikt en nieuwe data aanvult.
6. Herstel een mediafile en controleer byte/SHA-exactheid.
7. Blokkeer een boek expliciet en open/refresh Integriteit. De audit mag de blokkade niet opheffen; herstel blijft met `BookBlockedError` weigeren.
8. Future-format en een ongeldig/corrupt `book.json` moeten auditbaar blijven zonder centrale adoptie of downgrade.
9. Legacy format 1 blijft format 1 bij audit/reload; alleen de expliciete migratieknop mag naar format 2 migreren.
10. Test een boek met veel History-versies en meerdere issues: selectie mag niet bij iedere klik dezelfde recovery-scan opnieuw uitvoeren binnen één audit.

Bij voorkeur opnieuw de hele boekmap hashen bij de relevante scenario's. De belangrijkste regressie is dat een centrale reload nooit een schrijfpad mag starten.
