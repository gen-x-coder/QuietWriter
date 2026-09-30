# QuietWriter 0.32.6 — reviewronde 32

0.32.5 is door Claude functioneel groen verklaard. Deze release sluit alleen twee gele punten uit reviewronde 31 en hardt de tests af.

## Verplicht eerst

1. Draai de volledige suite met echte PySide6. `tests/test_review_0324.py::test_settings_presentation_pass_does_not_dirty_or_create_planning_notes` mag niet hangen.
2. Controleer dat een onverwachte `QMessageBox.information/warning/critical` in `test_review_0324.py` een test failure geeft in plaats van een wachtende modal.
3. Start `python main.py` koud en open daarna een boek. Geen startupregressie; rail blijft conform 0.32.5.

## Vrije publicatietekst

Test Voorwoord en Nawoord minimaal zo:

- Open bestaande tekst met harde spatie (U+00A0) en U+2028. Direct na laden: `dirty=False`.
- Roep `presentation_highlighter.rehighlight()` aan: `dirty=False`, timer uit, bestand byte-identiek.
- Typ één teken: `dirty=True`; undo exact terug naar de opgeslagen bron: `dirty=False`, timer uit.
- Typ opnieuw en sla op: `dirty=False`, `_clean_text == editor.source_text()`, harde spatie en U+2028 behouden.
- Herhaal een disk-conflict voor een vrije publicatietekst; na mine/disk moet de baseline corresponderen met de live tekst en mag een latere rehighlight niet dirty maken.

## Startupvangnet

- `tests/test_manuscript_editor_init_0325.py` moet ook zonder Qt-runtime groen zijn.
- Verifieer dat de AST-test de 0.32.4-vorm (een geneste `source_text()`/return midden in `__init__`) zou afkeuren.

## Regressie

- Herhaal ronde 31 cold-start/notities/Unicode-proeven.
- Herhaal ronde 28: 30/30.
- Let erop dat de transactionele adopt- en conflictflows uit 0.31 onaangeraakt blijven.

## Bekende omgeving

In ChatGPT's huidige omgeving worden 32 Qt-runtime-tests overgeslagen en ontbreken de gebundelde fontresources; daarom moeten de bovenstaande Qt-proeven bij Claude/lokaal echt draaien.
