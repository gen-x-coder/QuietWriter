# QuietWriter reviewnotities 0.32.5 — ronde 31

0.32.5 is een pure startup-hotfix op 0.32.4.

## Oorzaak

In `quietwriter/ui/manuscript_editor.py` stond `source_text()` per ongeluk midden in `ManuscriptEditor.__init__`. De code voor timers, signalen, selection toolbar, scènebreukknop, `presentation_highlighter`, typografie en margins stond daardoor na de `return` van `source_text()` en werd nooit uitgevoerd.

## Verplicht eerst testen

1. Start QuietWriter normaal vanaf een koude start. Het hoofdvenster moet zonder exceptie verschijnen.
2. Bouw een echte `MainWindow` in PySide6 en controleer dat `editor_page.editor` ten minste `_format_timer`, `_selection_timer`, `selection_toolbar`, `scene_delete_button` en `presentation_highlighter` heeft.
3. Herhaal daarna de 0.32.4-proeven: koude-startnavigatie, Planning-notities na Settings-save, Unicode-behoud in notities, scènescheiding/afbeelding invoegen/verwijderen en Voorwoord/Nawoord-smoketest.
4. Draai de volledige suite en regressiereeksen.

## Verwachting

Er zijn geen functionele wijzigingen ten opzichte van de bedoelde 0.32.4. Alleen de constructorindeling is hersteld.
