# QuietWriter 1.2.16 — DocumentView voor zoeken, spelling en Meelezer

Deze ontwikkelversie trekt de centrale manuscriptinterpretatie verder door. Zoeken, spelling en de AI Meelezer gebruiken nu dezelfde semantische laag als editor/export in plaats van losse interpretaties van de bron.

Belangrijk: bestaande boekbestanden worden niet gemigreerd en er is nog geen nieuwe manuscriptsyntaxis ingevoerd.

## Technisch

- Centrale offset-stabiele tekstweergave voor zoeken en spelling.
- Technische markers en structurele prefixes worden niet als proza behandeld.
- AI-context wordt uit `DocumentView` opgebouwd.
- Letterlijke ongepaarde Markdowntekens blijven gewone tekst.
- Regressietests uitgebreid.

Geautomatiseerde suite: 526 passed, 45 skipped, 304 subtests passed.
