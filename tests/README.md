# Tests in QuietWriter

QuietWriter gebruikt na de RC2-opschoning één actieve suite: `tests/current/`. Relevante historische regressies zijn hierin opgenomen; de oude `tests/legacy/`-verzameling is verwijderd. Git/history of de oorspronkelijke bron-ZIP blijft het archief, niet de dagelijkse testsuite.

## Standaard
```bash
pytest
```

`pytest.ini` wijst naar `tests/current`.

## Qt-runtime
```bash
pytest -m qt
```

De `qt` marker wordt tijdens collectie toegevoegd aan tests die echte PySide6/runtime nodig hebben. Gebruik `-m qt`, niet bestandsnaamfilters.

## Static gate
```bash
python tools/check_undefined_names.py
```

## Regels
- Nieuwe regressies krijgen een test in de actieve suite.
- Test op product-/veiligheidscontract, niet op een reviewnummer wanneer een domeinnaam duidelijker is.
- Source/AST-tests zijn aanvullend; Qt-runtimegedrag krijgt een runtime-test.
- Windows-handle-, future-format-, corruptie-, conflict-, History- en stale-AI-worker scenario's blijven actieve dekking.
- Een test wordt verwijderd als een sterker equivalent hetzelfde contract bewaakt, de feature niet meer bestaat of hij alleen een vervallen implementatiedetail controleert.

Zie `documents/TEST_STRATEGY.md` voor de volledige aanpak.
