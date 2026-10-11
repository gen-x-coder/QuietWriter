# QuietWriter 1.3.0-dev.1

Eerste ontwikkeliteratie van de 1.3-lijn. Deze build legt bewust alleen het fundament voor meerdere boekenplanken; de volledige Neo-interface en Demo-modus zijn nog niet af.

## Wat is gebouwd

- `<werkmap>/library.json` bevat de canonieke `book_id -> shelf_id`-mapping.
- Eén publieke standaardplank: **Werk in uitvoering**.
- Stabiele plank-ID's, hernoemen, verplaatsen, privéstatus en veilig verwijderen.
- Migratie vanaf 1.2.x zonder bestaande `book.json`-bestanden aan te passen.
- `.qwbook` blijft onafhankelijk van lokale plankindeling.
- Boeken in de prullenbak behouden hun plank.
- Atomaire opslag, revision-check/replay en een last-good herstelkopie.
- Basis voor centrale zichtbaarheid en fail-closed Demo-filtering.

## Nog niet in deze dev-build

- De nieuwe horizontale Neo-boekenplank-UI.
- Inline hernoemen in de zichtbare boekenkast.
- De Demo-modus-schakelaar en filters in alle UI-oppervlakken.

Deze onderdelen volgen nadat het opslagfundament is gevalideerd.
