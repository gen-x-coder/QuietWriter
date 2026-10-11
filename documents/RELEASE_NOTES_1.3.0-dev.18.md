# QuietWriter 1.3.0-dev.18

Deze tussenbuild start **Planning dichter bij het schrijven** met een eerste, bewust beperkte vorm van spookalinea's.

- In een leeg hoofdstuk toont de editor de aan dat hoofdstuk gekoppelde scènes uit Planning als zachte hulptekst.
- De hulp toont titel, synopsis, personages/locatie en compact doel, conflict en uitkomst wanneer die zijn ingevuld.
- De laag is strikt presentation-only: de Planningtekst wordt niet aan `QTextDocument` of Markdown toegevoegd en telt daarom niet mee, verschijnt niet in zoeken of spelling, gaat niet mee in export/AI-context en maakt geen Undo-stappen.
- Zodra het hoofdstuk echte tekst bevat verdwijnt de hulp. Als het hoofdstuk weer volledig leeg wordt, verschijnt de hulp opnieuw.
- Terugkeren vanuit Planning ververst de getoonde Planning direct.
- Onder **Instellingen > Uiterlijk** staat **Planninghulp in editor** met **Tonen / Verbergen**; standaard is Tonen.
- Het bestaande paneel **In dit hoofdstuk** blijft het volledige overzicht. De ghostlaag is bewust compacter en toont geen Planning-notities of status.
- `library.json`, Planning-bestanden en manuscriptbestanden krijgen door de presentatie zelf geen nieuw formaat of extra markers.

Publieke release blijft **1.2.32**. De actieve ontwikkellijn is **1.3.0-dev.18**.
