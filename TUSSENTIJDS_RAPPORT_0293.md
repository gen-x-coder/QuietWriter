# Tussentijds rapport 0.29.3

## Aanleiding
Reviewronde 16 bevestigde dat 0.29.2 corrupte UTF-8 veilig kon tonen en herstellen, maar vond twee normale UI-routes die de beschadigde bron alsnog konden vervangen: Boekgeheugen/Boekprofiel bij navigatie of AI-Onthouden, en programmatische editorbewerkingen zoals Scènebreuk.

## Kernwijziging
De bescherming zit nu niet alleen in widgets maar ook in storage. `CorruptSourceError` weigert een normale write wanneer het bestaande doelbestand niet als UTF-8 decodeert. Dit geldt voor hoofdstukken, `ai/memory.md`, `ai/boekprofiel.md` en `planning/notes.md`.

De Integriteit-backend herstelt byte-exact via zijn eigen binaire herstelroute en blijft dus bewust de enige route die zo'n beschadigd bestand mag vervangen.

## UI-laag
- Editor houdt `_chapter_corrupt` bij. Save/autosave zijn no-op, textChanged maakt niet dirty, Scènebreuk en afbeeldinginvoer worden geweigerd. AI, spelling en invoegen worden in de toolrail uitgeschakeld; zoeken blijft beschikbaar, maar vervangen wordt geweigerd.
- Boekgeheugen en Boekprofiel houden `_corrupt_source` bij. Opslaan en section-state muteren niet; AI-Onthouden weigert bij beschadigd Boekgeheugen.
- Een succesvolle reload zet de foutvlaggen weer uit.

## Tests lokaal
- Nieuwe storage-guardtests: hoofdstuk, Boekgeheugen, Boekprofiel, Planning-notities en geldig leeg bestand.
- Gerichte set: 9 passed.
- Volledige suite: 517 passed, 27 skipped, 280 subtests passed; alleen de 2 bekende fontresource-tests falen wegens ontbrekend `resources/fonts/font_manifest.json`.

## Bewuste grens
`MainWindow.adopt_active_book()` transactioneel/all-or-nothing maken blijft voor 0.30.0. Deze patch voorkomt dat corrupte bronbytes verloren gaan, maar verbreedt de adopt-architectuur niet.
