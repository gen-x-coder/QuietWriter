# QuietWriter 1.3.0-dev.7

## Presentatiemodus en snelle Boekenkast

- **Demo-modus** heet in de gebruikersinterface voortaan **Presentatiemodus**. De interne instelling `bookshelf_demo_mode` blijft bewust ongewijzigd voor compatibiliteit.
- Het bestaande plankmodel en `library.json`-formaat zijn niet gewijzigd; deze iteratie verandert alleen gedrag en performance bovenop hetzelfde 1.3-fundament.
- Als Presentatiemodus wordt ingeschakeld terwijl een boek op een privéplank open staat, probeert QuietWriter eerst alle actuele boekgegevens veilig op te slaan en sluit daarna het boek. De app keert terug naar de Boekenkast en maakt de boekgebonden pagina’s leeg.
- Als dat veilig sluiten niet lukt, wordt Presentatiemodus automatisch weer uitgezet zodat de interface nooit privacy suggereert terwijl privétekst zichtbaar blijft.
- Ook andere routes naar `open_book()` blokkeren een privéboek zolang Presentatiemodus actief is.
- Woordtellingen op boekkaarten gebruiken nu een cache per hoofdstuk op basis van pad, `mtime_ns` en bestandsgrootte. Ongewijzigde hoofdstukken worden bij een Boekenkast-refresh niet opnieuw gelezen en geparsed.
- Het zoekveld vernieuwt de Boekenkast pas 200 ms na de laatste toetsaanslag, zodat typen geen volledige refresh per toets veroorzaakt.
- Tooltipteksten maken expliciet dat Presentatiemodus een presentatiefilter is en **geen beveiligingsfunctie**.
- Geen covercache, schaduwoptimalisatie, virtualisatie of incrementele widgetherbouw in deze iteratie; die blijven bewust buiten de noodzakelijke performancefix.

`README.md` is in deze dev-build bewust niet gewijzigd.
