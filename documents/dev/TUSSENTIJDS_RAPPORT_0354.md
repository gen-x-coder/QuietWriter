# Tussentijds rapport 0.35.4

0.35.4 is een release-hardeningcorrectie. De bewerkbare Planning-combo's bewaren custom waarden weer exact; bekende vertaalde labels worden naar canonieke opslagwaarden gemapt. De undefined-name CI-check filtert pyflakes gericht. Python 3.12+ is expliciet het ondersteunde runtimecontract.

## Lokale verificatie
- current: 219 geslaagd, 17 Qt-skips
- legacy: 426 geslaagd, 24 Qt-skips, 284 subtests
- compileall: groen
- pyflakes-tool niet lokaal uitvoerbaar omdat pyflakes niet in deze runtime is geïnstalleerd; CI installeert pyflakes expliciet.
