# Tussentijds rapport 0.35.2

## Samenvatting

0.35.2 maakt de releasefundamenten controleerbaar in plaats van adviserend. Vertaling heeft nu regressiegates, fontbronnen/licenties hebben een manifest, de eigen en derde-partijlicenties zijn zichtbaar vanuit Over en de crash-cooldown is ongevoelig voor wisselende exceptiontekst.

## Crashmelding

De signature voor een terugkerende exception bestaat uit het exceptiontype en het laatste tracebackframe (`bestand:regel`). De exceptiontekst zelf is geen onderdeel meer van de signature. Hierdoor worden bijvoorbeeld `RuntimeError("hoofdstuk 17")` en `RuntimeError("hoofdstuk 18")` vanaf dezelfde defecte refreshregel als dezelfde foutbron behandeld. Alle exemplaren blijven afzonderlijk in `crash.log` staan.

## Vertaling

De locales hebben elk 1045 sleutels en dezelfde sleutelset. Een nieuwe current-test verzamelt alle letterlijke `tr()`-calls via AST en faalt als een sleutel ontbreekt. Een tweede AST-gate voorkomt nieuwe zichtbare widgetteksten buiten `tr()`. Dynamische profiel-/geheugen-/snelactiesleutels zijn apart benoemd in de test.

Bij vertaalde comboboxen gebruikt de applicatie stabiele ids in `Qt.UserRole/currentData()` in plaats van de zichtbare Nederlandse tekst. Daardoor verandert Engelse weergave de contextselectie niet.

## Fonts en licenties

`resources/fonts/font_manifest.json` beschrijft Merriweather, Literata, Source Serif 4 en EB Garamond met twee variable TTF-faces per familie. Elk font heeft lokaal een `OFL.txt`. De binaries zelf hoeven niet in de bronzip te staan: CI haalt ze op met `tools/fetch_bundled_fonts.py`; de portable build in 0.36 moet ze wel daadwerkelijk bundelen.

`LICENSE` legt de huidige eigen copyrightstatus vast. `THIRD_PARTY_LICENSES.md` inventariseert Python, PySide6/Qt, Requests, spylls en de vier fonts. Hunspell-dictionaries worden op dit moment niet als data meegeleverd; zodra 0.36 woordenboeken bundelt, is hun exacte licentie een verplichte packaging-gate.

## First-run

Het ontwerp gebruikt `first_run_done`. Bij een upgrade geldt bestaande QuietWriter-state óf het bestaan van de standaardwerkmap al als bewijs van bestaand gebruik. Een lege bestaande standaardwerkmap veroorzaakt dus geen onboarding na een update.
