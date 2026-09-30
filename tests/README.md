# Tests in QuietWriter

De tests zijn vanaf 0.34.1 opgesplitst in een actuele en een historische suite.

## Actuele suite

`tests/current/` bevat de tests die bij iedere build horen te draaien. Deze suite bewaakt de huidige architectuur en de belangrijkste regressierisico's: opslag/revisies, editorbron, Planning en Integriteit, Settings, rail/navigatie, publicatie en de actuele 0.34-functies.

Draai vanaf de projectroot:

```bash
pytest
```

`pytest.ini` wijst standaard alleen naar `tests/current`.

## Historische regressies

`tests/legacy/` bevat oude review- en releasegerichte tests. Ze zijn niet verwijderd; ze worden alleen niet meer standaard uitgevoerd. Gebruik ze bij grote refactors, mijlpaalreleases of als een oude foutklasse opnieuw verdacht wordt.

```bash
pytest tests/legacy
```

De twee bekende gebundelde-fonttests kunnen in omgevingen zonder de fonts nog steeds falen.

## Volledige historische controle

```bash
pytest tests/current tests/legacy
```

Gebruik deze volledige run vooral voor mijlpaalreleases of wanneer Claude/lokaal met een complete PySide6-installatie controleert.

## Regels

- Nieuwe productfuncties en nieuwe regressies krijgen eerst een test in `tests/current/`.
- Een actuele test mag pas naar `tests/legacy/` wanneer een nieuwere, algemenere test dezelfde foutklasse afdekt of wanneer de test alleen een vervallen implementatiedetail bewaakt.
- Tests worden niet verwijderd alleen omdat ze oud zijn.
- `tests/conftest.py` blijft gedeeld door beide suites en bewaakt onder meer onverwachte modale dialogen.


## Releasebeleid

- `pytest` draait de actuele suite in `tests/current`.
- `pytest tests/legacy` draait historische regressies.
- Bij elke nieuwe minor-release (bijvoorbeeld 0.35.0, 0.36.0) moet ook de volledige legacy-suite groen zijn, afgezien van expliciet gedocumenteerde externe resourceproblemen.
- Kernrisico's blijven in `current`: transactionele adoptie, onleesbare bronnen met lokale invoer, Planning-notities zonder false-dirty, exportconflicten, History-preview en exportcorrectheid.
## Qt-runtimecontrole

Tests die echte PySide6/Qt-runtime gebruiken worden automatisch gemarkeerd met `qt`. De marker wordt tijdens collectie toegevoegd wanneer de testmodule PySide6 importeert of de `app`-fixture gebruikt. Bestandsnamen zijn dus niet bepalend.

Snelle Qt-deelcontrole:

```bash
pytest -m qt
pytest tests/legacy -m qt
```

Voor externe review met echte PySide6 blijven de volledige runs verplicht:

```bash
pytest
pytest tests/legacy
```

`-m qt` is alleen de snelle Qt-deelcontrole; het vervangt de volledige suites niet. Gebruik niet langer `-k qt` als maatstaf voor Qt-dekking.

