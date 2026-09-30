# Tussentijds rapport — QuietWriter 0.32.4

## Doel

Ronde 29 wees op dezelfde bron-/dirtyklasse in Planning-notities en vier documentbrede manuscriptbewerkingen. Lucas meldde daarnaast dat bij koude start boekfuncties zichtbaar waren zonder actief boek.

## Wijzigingen

- Boeknavigatie is gecentraliseerd in `_set_feature_visibility`: zonder `active_book()` zijn alle boekknoppen en **HUIDIG BOEK** verborgen.
- `ManuscriptEditor.source_text()` is de gedeelde Unicode-veilige persistentielaag. `EditorPage._editor_source_text()` delegeert hiernaar.
- Planning-notities houden `_clean_text` bij, vergelijken echte broninhoud vóór dirty/autosave en gebruiken `source_text()` voor save en recovery-snapshots.
- Scènescheiding invoegen/verwijderen en afbeelding invoegen/verwijderen gebruiken de gedeelde bronrepresentatie.
- Vrije publicatietekst gebruikt dezelfde bron bij save.

## Lokale tests

Volledige suite in deze omgeving: **567 geslaagd, 31 overgeslagen, 280 subtests geslaagd**. Alleen de 2 bekende fontresource-tests falen omdat `resources/fonts/font_manifest.json` hier ontbreekt. De echte PySide6-runtimetests voor 0.32.4 worden hier overgeslagen en staan daarom expliciet in `REVIEW_NOTES_0324.md` voor Claude.

## Niet meegenomen

Het alleen bezoeken van Boekgeheugen/Boekprofiel kan nog een leeg sjabloonbestand aanmaken. Dit blijft een afzonderlijk polishpunt.
