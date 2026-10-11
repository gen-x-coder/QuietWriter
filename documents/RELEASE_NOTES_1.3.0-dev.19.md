# QuietWriter 1.3.0-dev.19

Deze build polijst uitsluitend de eerste Planninghulp uit dev.18.

## Gewijzigd

- Locatie en Personages staan nu op afzonderlijke regels.
- De editor reserveert ruimte voor een afsluitende regel wanneer niet alle gekoppelde scènes passen.
- Die regel meldt hoeveel scènes nog in Planning staan, zodat afkapping nooit stil gebeurt.

## Bewust niet gewijzigd

Tijdens de Windows-test is een bestaand layoutprobleem in Zoeken en vervangen gevonden: de paneelverdeling stort in bij zoeken, de lege-resultaatmelding is dubbel en `Vervangen door` springt naar boven. Dit staat hoog op de UI-backlog en wordt in een eigen iteratie aangepakt.

De Planninghulp blijft een pure paintlaag buiten `QTextDocument`. Manuscriptbestanden, `library.json`, woordtelling, zoeken, spelling, export, AI-context en Undo blijven ongewijzigd.
