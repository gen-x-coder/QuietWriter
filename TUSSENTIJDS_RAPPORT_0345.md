# Tussentijds rapport 0.34.5

## Aanleiding
Reviewronde 40 bevestigde dat 0.34.4 zijn preview-only contract hield, maar vond dat de al bestaande knop **Planning-context…** sinds 0.31.2 na het openen van een boek uitgeschakeld bleef. Daarnaast waren de fouttekst en previewweergave nog wat onrustig. Lucas gaf aan dat de divider boven het vaste PROGRAMMA-blok op ruime schermen weg mag, zolang kleine schermen voldoende oriëntatie houden.

## Implementatie
- AI-panel `_update_busy_buttons()` beschouwt een geladen `ConversationStore` als geldig boek tijdens de open/adopt-volgorde.
- Planning-foutresultaten bevatten alleen een reden; UI-labels worden lokaal samengesteld.
- Alleen de dialoogweergave comprimeert lege regels vóór bulletvelden; prompttekst blijft onaangetast.
- PROGRAMMA-divider is gekoppeld aan echte overflow van de middenrail.
- Nieuwe actuele tests dekken broncontracten; echte Qt-tests dekken de open-book-knoproute en responsieve divider voor Claude/lokaal.

## Lokale tests
- `tests/current`: 179 geslaagd, 12 overgeslagen.
- `tests/legacy`: 424 geslaagd + 280 subtests, 24 overgeslagen; alleen de twee bekende fontresource-tests falen.
- current + legacy zonder fonttestbestand: 601 geslaagd + 280 subtests, 36 overgeslagen.
