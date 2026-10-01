# Tussentijds rapport QuietWriter 0.33.0

## Doel

0.33.0 maakt de informatiearchitectuur expliciet zonder opslag- of AI-logica te wijzigen. De centrale ontwerpregel is:

**effectieve toestand → railmodel → weergave**

## Implementatie

- Nieuw puur Python-model `quietwriter/ui/rail_model.py` met groepen, itemvoorwaarden, `RailState`, `RailViewModel` en centrale fallback.
- Vier groepen: BIBLIOTHEEK, HUIDIG BOEK, AI-CONTEXT, PROGRAMMA.
- Linkerrail wordt uitsluitend gerenderd vanuit het model. Losse feature-specifieke `setVisible()`-regels voor boek/AI/Integriteit zijn uit de navigatieflows verwijderd.
- `_render_rail()` doet alleen zichtbaarheid.
- `_apply_committed_navigation_effects()` bevat de blijvende side-effects: verborgen rechterpaneel sluiten en verborgen actieve/terugkeerpagina via de model-fallback omleiden.
- Settings-preview gebruikt dezelfde effectieve state, maar roept de commitstap nooit aan.
- QScrollArea rond de navigatie voorkomt dat de rail de hoofdvensterhoogte afdwingt; Menu blijft vast boven het scrollgebied.
- Bestaande railbreedtes blijven 64/218 px; navigatieknoppen gebruiken 48/194 px zodat ruimte voor de smalle verticale scrollbar overblijft.
- Uitlegteksten Persona/Profiel/Geheugen afgestemd op globaal versus boekspecifieke AI-context.
- Oude contextloze melding `Structuuractie niet uitgevoerd` generiek gemaakt.

## Testhardening ronde 33

- Suitebrede dialoogguard registreert onverwachte QMessageBox/QDialog/QInputDialog/QFileDialog-aanroepen en controleert ook na Qt event-loop callbacks.
- Code-health test gebruikt een absoluut bronpad vanaf `__file__`, vereist minimaal één gevonden Pythonbestand en doorloopt ook geneste statementlijsten voor unreachable code na return/raise.

## Nieuwe tests

- Handmatige railreferenties voor drie kernstaten.
- Invarianten over alle 8 inhoudelijke toestanden.
- Centrale fallbacktests.
- Source-contract: renderer heeft geen navigatie/QSettings/paneel-side-effects.
- Qt-runtime: 16 combinaties incl. rail open/dicht.
- Qt-runtime: 700/720/768 px hoogte en scrollbarbreedte.
- Qt-runtime: preview versus commit voor Boekgeheugen/AI en Integriteit/Advanced.

## Lokale teststand

`PYTHONPATH=. pytest -q`:

- 576 geslaagd;
- 280 subtests geslaagd;
- 33 Qt-runtime-tests overgeslagen in deze omgeving;
- alleen de 2 bekende fontresource-tests falen wegens ontbrekende `resources/fonts/font_manifest.json`.

Claude moet de nieuwe Qt-matrix, overgangstests en lage-schermmetingen uitvoeren met echte PySide6.
