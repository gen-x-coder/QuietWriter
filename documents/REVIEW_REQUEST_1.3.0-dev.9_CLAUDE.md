# QuietWriter 1.3.0-dev.9 — reviewopdracht voor Claude

Review deze snapshot zonder code te wijzigen.

## Doel
Dev.9 sluit de twee kleine punten uit de dev.8-review af:

1. N1: Qt-tests mogen de echte lokale appdatamap niet vervuilen met woordtellingcachebestanden.
2. N2: de persistente woordtellingcache mag geen volledige hoofdstukpaden of boektitels bewaren.

De covercache (W4/P3) is bewust nog niet gebouwd; die beslissing volgt uit de Windows-acceptatietest met echte covers.

## Controleer regressie
- Volledige pytest-suite met PySide6.
- `python main.py --smoke-test`.
- locales: exact dezelfde 1551 sleutels in 5 talen.
- undefined-names en pyflakes; vergelijk meldingen met dev.8.
- Noteer opnieuw of de bekende Linux pytest-exitcode 139 na een volledig geslaagde suite blijft bestaan.

## N1 — testisolatie
Controleer dat `tests/conftest.py` `QStandardPaths.setTestModeEnabled(True)` activeert zodra PySide6 beschikbaar is.

Meet bij voorkeur vóór/na een volledige suiterun hoeveel nieuwe `bookshelf-word-counts-*.json` bestanden in de echte lokale appdatamap zijn ontstaan. Verwachting: geen nieuwe testcachebestanden daar.

Controleer ook dat deze testmodus uitsluitend de tests beïnvloedt en niet de normale app-runtime.

## N2 — gehashte cachekeys
Controleer met een werkmap met duidelijk herkenbare private boektitels, bijvoorbeeld `GEHEIMTITEL`:

- cachebestand blijft in lokale appdata en buiten de werkmap;
- keys zijn 64 hextekens (SHA-256);
- cachetekst bevat geen boektitel en geen volledig hoofdstukpad;
- tweede proces/sessie telt ongewijzigde hoofdstukken 0 keer opnieuw;
- wijziging van één hoofdstuk telt precies dat hoofdstuk opnieuw;
- twee werkmappen krijgen aparte cachebestanden;
- corrupte/onbruikbare cache blijft niet fataal.

### Migratie vanaf dev.8
Maak expliciet een cachebestand in het dev.8-formaat met een volledig hoofdstukpad als key. Start dev.9.

Verwachting:
- oude pad-key wordt niet als geldige hit gebruikt;
- hoofdstuk wordt opnieuw geteld;
- na refresh bevat het bestand uitsluitend SHA-256-keys;
- de oude privétitel/padtekst is uit het bestand verdwenen.

Pas `cache138.py` gerust lokaal aan of maak een nieuw harnas; wijzig geen projectcode.

## Presentatiemodus
Draai minimaal de relevante dev.7/dev.8 privacy- en foutpadharnassen opnieuw om te bevestigen dat N1/N2 daar niets aan veranderen.

## Performance
Vergelijk warme tweede sessie met dev.8. Hashing mag geen betekenisvolle regressie veroorzaken. Coverkosten hoeven niet opnieuw diep onderzocht te worden tenzij iets verandert.

## Packaging/documentatie
- actuele versie: `1.3.0-dev.9`;
- `RELEASE_NOTES_1.3.0-dev.9.md` beschrijft gehashte hoofdstukpaden en `library.json` als ongewijzigd;
- `.pytest_cache` hoort niet in de aangeleverde dev.9-ZIP;
- `README.md` moet byte-identiek blijven aan dev.8;
- `README_EN.md` niet aanmaken of wijzigen wanneer die niet aanwezig is.

Rapporteer bevindingen als blocker / vóór 1.3.0 / backlog en geef aan of de Boekenkast daarna functioneel releaseklaar is, behoudens de Windows-visuele acceptatietest.
