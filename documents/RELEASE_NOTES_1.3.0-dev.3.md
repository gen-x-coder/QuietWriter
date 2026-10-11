# QuietWriter 1.3.0-dev.3

Deze ontwikkelversie maakt de nieuwe boekenplanken voor het eerst zichtbaar. De boekenkast is nu opgebouwd uit horizontale planken in de Neo-richting.

## Wat je kunt testen

- Nieuwe boeken komen op **Werk in uitvoering**.
- Maak één of meer nieuwe planken aan.
- Klik op een planknaam en hernoem hem inline.
- Gebruik `⋯` bij een boek om het naar een andere plank te verplaatsen.
- Gebruik `⋯` bij een plank om hem privé te maken of te verwijderen.
- De standaardplank mag worden hernoemd, maar niet privé worden gemaakt of verwijderd.
- Verwijder een niet-standaardplank met boeken: de boeken moeten naar de standaardplank teruggaan en mogen niet verdwijnen.
- Controleer zoeken en sorteren met meerdere planken.

## Onder de motorkap

De migratie naar `library.json` schrijft niet meer tijdens een query. Daardoor kan een tweede computer met een nog onvolledig gesynchroniseerde werkmap niet per ongeluk een nieuwe openbare indeling publiceren. Locks zijn lokaal en een nieuwere schemaversie kan niet door de herstelknoppen worden overschreven.

## Nog niet in deze versie

De Demo-modus-schakelaar en het verbergen van privéplanken in de volledige UI volgen in een volgende dev-iteratie. Privé markeren is nu al beschikbaar zodat de normale boekenplank en het gegevensmodel visueel getest kunnen worden.
