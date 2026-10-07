# QuietWriter 1.2.22

Deze ontwikkelversie introduceert een neutrale importlaag tussen DOCX en de QuietWriter-manuscriptbron.

## Gewijzigd

- DOCX wordt eerst gelezen als `ImportDocument` met semantische secties, hoofdstukken, blocks en inline-opmaak.
- QuietWriter-syntax en escaping worden pas daarna door één centrale serializer opgebouwd.
- De bestaande importinterface voor opslag en UI blijft compatibel.
- Geen bestaande boeken worden gemigreerd of herschreven.

## Validatie

- 555 tests geslaagd, 45 overgeslagen, 304 subtests geslaagd.
