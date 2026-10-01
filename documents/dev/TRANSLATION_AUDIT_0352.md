# Vertaalcontrole 0.35.2

## Resultaat

- `nl.json`: 1045 sleutels.
- `en.json`: 1045 sleutels.
- De sleutelsets zijn identiek.
- Alle letterlijk gebruikte `tr()`-sleutels in `quietwriter/**/*.py` bestaan in beide bestanden.
- Dynamisch opgebouwde sleutels voor Schrijverspersona, Boekprofiel, Boekgeheugen en AI-snelacties zijn apart afgedekt door een regressietest.
- Een AST-test bewaakt zichtbare letterlijke tekst in QLabel/QPushButton/QCheckBox/QRadioButton/QGroupBox en de belangrijkste `setText`/tooltip/placeholder/window-title-routes. Technische symbolen en formaatvoorbeelden staan op een kleine expliciete allowlist.

## Belangrijke implementatiedetails

De drie AI-manuscriptbereiken gebruiken nu stabiele interne ids `chapter`, `section` en `book`. De zichtbare labels mogen daardoor Nederlands of Engels zijn zonder de contextlogica te veranderen. Hetzelfde principe geldt voor dynamische sectienamen in Persona, Boekprofiel en Boekgeheugen: de opgeslagen Markdown-structuur blijft compatibel, alleen de UI-labels worden vertaald.

## Nog door een echte gebruiker/runtime te controleren

De statische gates bewijzen dat sleutels bestaan, maar niet dat elke Engelse formulering prettig leest of dat een vertaald label nergens wordt afgekapt. Claude moet daarom in de review een volledige Engelse schermrondgang doen, met extra aandacht voor het rechtermenu, Boekdetails, Boekprofiel, Boekgeheugen, Schrijverspersona, Planning, AI-context en dialoogteksten.
