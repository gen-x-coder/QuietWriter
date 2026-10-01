# Translation audit 0.35.3

- `nl.json` en `en.json`: 1091 identieke sleutels.
- Altijd zichtbare statusbalk is gelokaliseerd, inclusief enkelvoud/meervoud en duizendtalscheiding.
- Editor-contextmenu, AI-label, spellingstatus en Replace all zijn gelokaliseerd.
- Zeldzame conflict-/corruptie-/boekenplankmeldingen uit reviewronde 49 zijn gelokaliseerd.
- Planning-scènestatus en relatietypen: vertaalde displaytekst, canonieke bestaande opslagwaarde blijft intact.
- Nieuwe hoofdstuktitels worden in de actieve UI-taal aangemaakt.
- CI voert `pyflakes` uit om undefined names zoals de 0.35.2 `tr`-fout te blokkeren.

Runtimecontrole in het Engels blijft verplicht omdat statische tests geen afkapping of slechte formulering kunnen aantonen.
