# Tussentijds rapport 0.35.1

0.35.1 is de tweede release-hardening-slice richting 1.0. De build introduceert geen nieuwe schrijf- of AI-functionaliteit.

## Opgelost

- De crashmelder kan niet meer een vensterstorm veroorzaken. Eén melding blijft actief; extra fouten worden samengevoegd, terwijl logging volledig blijft.
- Opstartfouten vóór de normale eventloop zijn zichtbaar via een modale foutmelding nadat de splash is gesloten.
- De Over-hero gebruikt altijd een licht woordmerk op zijn vaste donkere achtergrond.
- Branding en gewone SVG-iconen zijn HiDPI-bewust.
- Qt-berichten blijven voor ontwikkelaars ook op stderr zichtbaar.
- Het first-run-contract onderscheidt bestaande gebruikers onafhankelijk van het al dan niet opgeslagen `workspace`-veld.
- CI krijgt de bekende Ubuntu-runtimebibliotheken voor PySide6/Qt.

## Lokale tests

- `pytest`: 198 passed, 17 skipped.
- `pytest tests/legacy --ignore=tests/legacy/test_bundled_fonts.py`: 422 passed, 24 skipped, 280 subtests passed.
- Gerichte release-hardeningtests: 12 passed, 3 echte Qt-runtimechecks skipped in deze omgeving.
- `compileall`: groen.

De volledige echte PySide6-runs blijven verplicht bij Claude. Het fontmanifest/licentieprobleem is bewust doorgeschoven naar 0.35.2 zodat bron- en licentiegegevens in één keer correct worden vastgelegd.
