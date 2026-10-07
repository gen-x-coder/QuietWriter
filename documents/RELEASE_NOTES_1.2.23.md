# QuietWriter 1.2.23

Deze ontwikkelversie maakt DOCX-import transactioneel.

## Gewijzigd

- Een Word-import wordt volledig voorbereid in een verborgen stagingmap.
- Hoofdstukken, media-structuur en `book.json` moeten compleet zijn voordat het boek zichtbaar wordt.
- Publicatie gebeurt met één directory-rename binnen dezelfde `books`-map.
- Bij een schrijf- of publicatiefout wordt de stagingmap opgeruimd en verschijnt geen half geïmporteerd boek.
- Voor publicatie valideert QuietWriter het manifest en controleert het of alle hoofdstukbestanden bestaan.
- Bestaande boeken en manuscriptbestanden worden niet gemigreerd of herschreven.

## Validatie

- 558 tests geslaagd, 45 overgeslagen, 304 subtests geslaagd.
