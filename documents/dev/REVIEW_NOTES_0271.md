# QuietWriter 0.27.1 — reviewnotities voor Claude

Deze release verwerkt de drie bevindingen uit reviewronde 7. De keuzes zijn bewust conservatief en sluiten aan op de bestaande data-integriteitsregels van QuietWriter.

## 1. Hoofdstukprullenbak telt als live mediagebruik

**Keuze:** `MediaManager` scant naast book-local Markdown en History ook `trash/chapters/<book-id>/*.md`. Een verwijzing daar telt mee in `reference_count` en verschijnt als `Prullenbak: <titel>`.

**Waarom:** een hoofdstuk in de prullenbak is herstelbare gebruikersinhoud. Zolang het teruggezet kan worden, mag media-cleanup geen dependency ervan verwijderen. De image-paths worden geïnterpreteerd relatief aan de *oorspronkelijke* `chapter_file`-locatie uit de trashmetadata, niet relatief aan de fysieke trashmap. Een onleesbaar trashhoofdstuk wordt toegevoegd aan `source_errors` en blokkeert cleanup conservatief.

**Te testen:** trash-only asset is `used`, `can_cleanup=False`; cleanup laat binary + manifest staan; restore van hoofdstuk levert een geldige image-reference. Corrupte trash-Markdown blokkeert cleanup.

## 2. Batch ruimt alleen expliciet `can_cleanup` op

**Keuze:** de UI roept `cleanup_unused(book, asset_ids=[...can_cleanup ids...])` aan. De manager-API zelf is niet versoepeld: een expliciet aangevraagd onveilig id blijft de hele expliciete request weigeren.

**Waarom:** de UI-belofte `opruimbaar: N` moet exact overeenkomen met de batchactie. Tegelijk blijft de lagere API fail-closed voor andere/toekomstige callers; stil overslaan van expliciet gevraagde ids zou programmeerfouten kunnen maskeren.

**Te testen:** één veilige + één history-unsafe ongebruikte asset => UI-subset verwijdert alleen veilige asset. Directe manager-call met unsafe id => `MediaCleanupError`.

## 3. ExternalModificationError verlaat de foutlus zonder lokale tekst te verliezen

**Keuze:** Media vangt `ExternalModificationError` apart af. Als de manuscripteditor/publicatiecontext schoon is, wordt de nieuwste diskversie geladen en centraal via `MainWindow.adopt_active_book(...)` geadopteerd, met `changed_files` door naar Planning. Daarna wordt Media ververst. Als manuscript of actieve publicatiecontext nog pending invoer heeft, delegeert Media eerst aan de bestaande editor-conflictafhandeling in plaats van automatisch te herladen.

**Waarom:** blind `load_book + adopt_active_book` zoals de minimale reviewfix zou de foutlus oplossen, maar kan niet-opgeslagen editorinhoud weggooien omdat `EditorPage.adopt_live_book()` zelf een no-save operatie is. De gekozen variant hergebruikt daarom de al geteste conflictflow wanneer lokale tekst risico loopt, en gebruikt de simpele automatische rebase alleen als dat veilig is.

**Te testen:** externe wijziging + schone editor => één cleanup-poging detecteert conflict, nieuwste bookstate wordt geadopteerd, tweede poging kan verder. Externe wijziging + dirty manuscript/publicatie => bestaande conflictkeuze verschijnt en lokale invoer wordt niet stil vervangen.

## Regressies

Nieuwe tests staan in `tests/test_media_manager_0270.py`; de bestaande Qt/source-test is aangepast. In de ChatGPT-omgeving: 473 tests geslaagd, 27 PySide6-skips, 280 subtests; alleen de twee bekende `test_bundled_fonts.py`-tests falen wegens de niet meegeleverde `resources/fonts/font_manifest.json`.
