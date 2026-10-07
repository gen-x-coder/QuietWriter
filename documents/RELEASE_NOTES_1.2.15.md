# QuietWriter 1.2.15 — DocumentView crashfix

Deze ontwikkelbuild herstelt een fout uit 1.2.14 in de nieuwe centrale manuscriptinterpretatielaag.

## Opgelost

- Een lege manuscriptbron maakte een `DocumentView` zonder verplichte `blocks`-waarde aan.
- Daardoor kon woordtelling tijdens opstarten en exporteren een `TypeError` veroorzaken.
- De lege documentweergave is nu een geldige, expliciet lege structuur.
- Er is een regressietest toegevoegd voor dit scenario.

## Teststatus

- 523 tests geslaagd
- 45 overgeslagen
- 304 subtests geslaagd

Er zijn geen bestaande manuscriptbytes of boekformaten gewijzigd.
