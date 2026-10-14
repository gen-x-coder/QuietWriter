# QuietWriter dev.40 — leesbare herstelvergelijking

## Opgeleverd

- Op **Integriteit & herstel**: **Tekst vergelijken** bij een geselecteerde herstelmap.
- Bewaarde tekst links, huidig hoofdstuk rechts; ontbrekende hoofdstukken worden expliciet aangegeven.
- Alleen-lezen, geen automatische terugzetactie, verwijdering of bestandswijziging.
- Begrensde tekstgrootte (1 MB per bestand), maximaal 20 hoofdstukken in één vergelijking.
- Journal-schema, boek-id, herstelhash, padveiligheid en symlinks worden gecontroleerd.
- Teksten in vijf talen toegevoegd.

## Getest in deze omgeving

`python -m pytest -q tests/current/test_recovery_compare_dev40.py tests/current/test_recovery_overview_dev39.py tests/current/test_replace_batch_dev37.py tests/current/test_replace_crash_journal_dev38.py tests/current/test_sync_conflicts_dev36.py tests/current/test_bookshelf_sync_dev35.py` → **24 geslaagd, 1 overgeslagen**.

`python tools/check_locales.py` → **1744 keys in vijf talen**.

`python tools/check_source_assets.py` → **negen brandingbestanden intact**.

De volledige testsuite is niet uitgevoerd. De nieuwe dialoog is niet visueel op Windows gecontroleerd.

## Belangrijke beperkingen

- Deze iteratie maakt de vergelijking zichtbaar; geen automatische herstelactie in de interface. Bij twijfel blijft het herstelproces handmatig.
- De harde Windows-crashtest en de live Dropbox-proef op twee computers blijven op de acceptatielijst.
- Het nieuwe programmaupdatesysteem blijft uitgeschakeld. Het openbare 1.4.0-project en de lokale ontwikkelrepo zijn niet gewijzigd.
- Bronversie-identiteit van oude reviewsnapshots moet later worden rechtgetrokken voor een echte release; deze bron-ZIP is geen productiebuild.

## Volgende functionele mijlpaal

Meer aandacht voor de schrijfflow (editor, Planning, AI Meelezer). Geen nieuwe uitgebreide technische updater-iteratie voordat die productfunctionaliteit prioriteit heeft of een releaseacceptatie nodig is.
