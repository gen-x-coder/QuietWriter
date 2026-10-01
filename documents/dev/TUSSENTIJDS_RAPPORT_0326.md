# Tussentijds rapport 0.32.6

## Aanleiding

Reviewronde 31 verklaarde 0.32.5 functioneel groen en vond twee gele punten: één Qt-test kon op een modale Werkmap gewijzigd-melding blijven hangen, en `FreeTextPage` had nog geen echte dirty-baseline.

## Wijzigingen

- `FreeTextPage` houdt `_clean_text` bij via `ManuscriptEditor.source_text()`.
- `_changed()` zet alleen dirty wanneer de persistente bron werkelijk afwijkt. Bij gelijkheid stopt de timer en wordt Opslaan uitgeschakeld.
- `set_text()` zet de baseline na het laden; een succesvolle `save_pending()` verplaatst de baseline naar de opgeslagen bron.
- `test_review_0324.py` zet `workspace` expliciet en faalt op onverwachte modale messageboxes.
- `test_manuscript_editor_init_0325.py` bevat nu naast de bestaande bronvolgordecheck een AST-check tegen geneste methodedefinities/returns in `ManuscriptEditor.__init__`.
- Nieuwe Qt-tests dekken publicatie-rehighlight, edit→undo en save/baseline met harde spaties.

## Lokale tests

- Volledige suite: 569 geslaagd, 32 overgeslagen, 280 subtests geslaagd.
- Alleen de twee bekende fontresource-tests falen doordat `resources/fonts/font_manifest.json` in deze werkomgeving ontbreekt.
- De nieuwe publicatie-runtimetests behoren tot de Qt-tests die hier worden overgeslagen en moeten bij Claude/lokaal draaien.

## Scope

Geen nieuwe productfunctie. De release maakt de drie persistente teksteditors (hoofdstuk, Planning-notities en vrije publicatietekst) conceptueel consistent en verbetert de betrouwbaarheid van de reviewtests.
