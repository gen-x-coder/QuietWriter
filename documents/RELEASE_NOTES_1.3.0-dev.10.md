# QuietWriter 1.3.0-dev.10

Deze snapshot is de laatste releasepolish na de Windows-acceptatietest van de Boekenkast en Presentatiemodus.

## Wijzigingen

- De kopteksten van `packaging/requirements-runtime.lock` en `packaging/requirements-build.lock` verwijzen nu naar QuietWriter 1.3.0 in plaats van de oude 1.2.32 Windows RC.
- Versie-, snapshot- en testmetadata zijn bijgewerkt naar `1.3.0-dev.10`.
- Er zijn geen functionele wijzigingen aan de Boekenkast, Presentatiemodus, woordtellingcache, `library.json`, boekformaten of planklogica.
- Cover-pixmapcaching is bewust niet toegevoegd: de Windows-acceptatietest met echte gegevens gaf geen merkbaar probleem.

## Bewust ongewijzigd

- `README.md` en `README_EN.md`.
- De vijf locales en hun 1551 sleutels.
- De dependency-versies in beide lockfiles; alleen de verouderde koptekst is aangepast.

## Richting 1.3.0

Als deze snapshot de regressie-, smoke- en packagingcontroles doorstaat, is de 1.3-lijn inhoudelijk klaar om als 1.3.0-releasekandidaat te worden vastgezet.
