# Tussentijds rapport QuietWriter 0.32.7

## Doel

Reviewronde 32 verklaarde 0.32.6 applicatief groen. 0.32.7 bevat daarom uitsluitend test-hardening.

## Wijzigingen

- Pakketbrede AST-regressietest voor onbereikbare statements na een onvoorwaardelijke `return` of `raise`.
- De exacte tekstpositiecontrole rond `ManuscriptEditor.source_text()` verwijderd.
- Suitebrede QMessageBox-guard toegevoegd via `tests/conftest.py`, inclusief instance-`exec()`.
- Lokale dialogenfixture uit reviewtest 0.32.4 verwijderd.
- Versie verhoogd naar 0.32.7.

## Lokale testbasis

- 569 tests geslaagd.
- 280 subtests geslaagd.
- 32 Qt-runtime-tests overgeslagen in deze omgeving.
- Alleen de twee bekende fontresource-tests falen.

## Productgedrag

Geen productcode gewijzigd behalve het versienummer.
