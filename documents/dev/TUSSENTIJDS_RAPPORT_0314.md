# Tussentijds rapport 0.31.4

## Aanleiding

Reviewronde 22 bevestigde dat de twee rode punten uit ronde 21 waren gesloten, maar vond één nieuwe rode Export-regressie en twee kleinere herstelgaten.

## Opgelost

- Export bewaart instellingen via één afgeschermde `_persist_settings()`-route.
- `ExternalModificationError` ontsnapt niet meer uit formaat-/optiesignalen. Bij een schone editor wordt de nieuwste disk-state centraal geadopteerd en krijgt de gebruiker een zichtbare melding om de keuze opnieuw te doen; bij pending tekst wordt de bestaande editor-conflictflow gebruikt.
- `ExportSettingsStore.validate_source()` gebruikt dezelfde JSON-guard als de save-laag, zodat afgekapt `export/settings.json` al bij `set_book()` fail-closed wordt herkend.
- `BookIntegrityChecker` controleert alle bestaande `publication/texts/*.md` en markeert ongeldige UTF-8 als herstelbare `aux_text_invalid`. De bestaande generieke History-recovery kan deze bestanden vervolgens herstellen.

## Tests in deze buildomgeving

- Gerichte 0.31.4 + 0.31.3 + Integriteit-tests: 27 geslaagd.
- Volledige suite: 543 geslaagd, 27 overgeslagen, 280 subtests geslaagd.
- Enige twee failures: de bekende gebundelde-fonttests omdat `resources/fonts/font_manifest.json` en de fonts in deze distributieomgeving ontbreken.
- De overgeslagen tests zijn Qt-runtimepaden; daarom moet Claude de echte PySide6/QTest-conflictflow opnieuw testen.

## Bewust nog open

De transactionele/all-or-nothing commit van `adopt_active_book()` blijft voor 0.31.5. Dat is een grotere architectuurwijziging en wordt niet vermengd met deze export/herstel-hotfix.
