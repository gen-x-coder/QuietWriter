# Review notes 0.31.0

Graag runtime beoordelen in de echte MainWindow. Focus op regressies door always-on autosave en de nieuwe navigatiegroepen.

- Controleer dat nergens in de editor nog runtimegedrag afhangt van `settings['autosave']`.
- Controleer normale autosave, retry na lock, drag/reorder pause/resume en Ctrl+S.
- Controleer dat corrupte hoofdstukken/geheugen/profiel/notities ondanks always-on autosave byte-identiek blijven.
- Controleer de zichtbaarheid van HUIDIG BOEK bij openen/sluiten/verwijderen/future-format detach en na terugkeer naar Boekenplank.
- Controleer rail collapsed/expanded en tabvolgorde; de labels zijn decoratief en mogen geen extra focusstop vormen.
- Controleer de woordtelling na typen, hoofdstukwissel, nieuw/verwijderd hoofdstuk en herstel vanuit Integriteit.
- Spellingscontrole en `adopt_active_book()` zijn inhoudelijk niet gewijzigd; eventuele nieuwe regressie daar is dus verdacht.
