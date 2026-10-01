# Tussentijds rapport 0.34.10

0.34.10 is een afrondende test-/UX-build. De privacy-opt-intekst is ingekort zonder betekenisverlies. De testinfrastructuur gebruikt nu een automatische pytest-marker `qt` in plaats van naamfiltering met `-k qt`. Hierdoor worden ook Qt-runtimebestanden zonder `qt` in de bestandsnaam meegenomen.

Lokaal: actuele suite 188 geslaagd en 14 overgeslagen. Legacy: 424 geslaagd, 280 subtests, 24 overgeslagen; alleen de twee bekende fontresource-tests falen. Echte PySide6-runs moeten door Claude worden uitgevoerd zoals vastgelegd in `REVIEW_NOTES_03410.md`.
