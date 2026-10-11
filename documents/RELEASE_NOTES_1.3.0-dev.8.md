# QuietWriter 1.3.0-dev.8

## Presentatiemodus robuuster en koude Boekenkast sneller

- Presentatiemodus gebruikt nu exact dezelfde `QSettings`-opslag als het actieve runtimeprofiel. Dev en productie delen daardoor niet langer onbedoeld dezelfde `bookshelf_demo_mode`-status.
- Als het veilig sluiten van een privéboek onverwacht een exception oplevert, logt QuietWriter die fout en zet Presentatiemodus zichzelf terug naar **uit**. De interface kan daardoor niet "aan" blijven tonen terwijl privé-inhoud nog open staat.
- De woordtellingcache van de Boekenkast wordt nu lokaal tussen sessies bewaard. De cache staat in Qt's lokale appdatamap en dus **niet** in de gesynchroniseerde werkmap.
- Iedere werkmap krijgt een eigen cachebestand op basis van een SHA-256-hash van het werkmappad. De cache bewaart alleen hoofdstukpad, `mtime_ns`, bestandsgrootte en woordenaantal.
- Ontbrekende, corrupte of niet-schrijfbare cachebestanden zijn niet fataal: QuietWriter valt automatisch terug op opnieuw tellen. De cache is uitsluitend een performance-optimalisatie.
- De bestaande `library.json`-structuur, plankmigratie, privacyfiltering en boekformaatlogica zijn niet gewijzigd.
- Cover-pixmapcaching is bewust nog niet toegevoegd. Eerst wordt op Windows met echte covers beoordeeld of de resterende circa kwart seconde merkbaar stoort.
- De bekende Linux `pytest`-exitcode 139 na een volledig geslaagde suite is geen regressie van deze build en wordt apart gevolgd.

`README.md` en `README_EN.md` worden voor 1.3.x bewust niet aangepast.
