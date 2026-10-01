# QuietWriter: reviewronde 23 (versie 0.31.4)

**Gelezen:**
- de diffs van `exporting/settings.py` (`validate_source`) en `integrity.py` (`publication/texts/*.md`);
- de diff van `ui/export_page.py` (`_persist_settings`, `_resolve_external_change`);
- `REVIEW_NOTES_0314.md`.

Let op: de ZIP had deze keer een extra bovenliggende map `qw0314/`. Voor mij maakt dat niet uit, maar voor jouw
build-script misschien wel.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless), met klikken via de echte knoppen.

## Resultaat: groen, geen nieuwe bevindingen

**Testsuite:** 571 geslaagd, 280 subtests, 0 overgeslagen. Alleen de 2 bekende fonttests falen.

### De drie punten uit ronde 22

| Check (REVIEW_NOTES_0314) | Resultaat |
|---|---|
| **1.** Hoofdstuk extern gewijzigd → Exporteren → PDF | ✅ geen excepthook; melding "Boek extern gewijzigd"; `export/settings.json` byte-identiek; **alle acht pagina's** op hetzelfde nieuwe `Book`-object; de editor toont de externe hoofdstuktekst |
| 1. Daarna opnieuw PDF kiezen | ✅ opgeslagen, `verify_book_unchanged` groen |
| **2.** `export/settings.json` extern gewijzigd → EPUB aanklikken | ✅ externe bytes onaangeroerd, melding, de UI toont daarna de externe keuze (Markdown) |
| 2. Tweede keuze | ✅ normaal opgeslagen, baseline groen |
| **3.** Dirty editor + exportconflict, "Mijn versie" | ✅ lokale tekst op schijf |
| 3. Idem, "Versie op schijf" | ✅ externe tekst live, lokale tekst in History |
| 3. Idem, dialoog gesloten zonder keuze | ✅ lokale tekst blijft in de editor; niets overschreven |
| 3b. Openstaande Voorwoordtekst + exportconflict | ✅ tekst behouden, geen excepthook (zie de opmerking onderaan) |
| **4.** Afgekapte `export/settings.json` | ✅ pagina direct uitgeschakeld, klikken geven geen exceptie, bytes identiek, Integriteit toont hem als herstelbaar |
| **5.** Beschadigd Voorwoord en Nawoord | ✅ alleen-lezen; Integriteit toont exact dat pad als `aux_text_invalid` / error / herstelbaar; herstel is byte-exact; daarna bewerkbaar en opslaanbaar |
| **6.** Normale export zonder externe wijzigingen | ✅ geen vals conflict; openen, `set_book` en adopt schrijven niets |

### Regressie

| Reeks | Resultaat |
|---|---|
| Ronde 22 | ✅ 12/12 |
| Spelling katt/matt en eerste klik | ✅ 6/6 |
| 0.31.0 | ✅ 18/18 |
| Corruptie rondes 16–18 | ✅ 2/2, 5/5, 3/3 |
| Integriteit | ✅ 19/19 |
| Rondes 11–13 | ✅ 36/36, 32/32, 10/10 |
| Backend 9–11 | ✅ 47/47, 15/15, 8/8 |
| Openen met corrupte JSON (alle vier) | ✅ geen crash, geen gemengde toestand |
| Ronde 21 | ✅ 8/9; de enige FAIL is het bekende adopt-commitpunt |

## Bekend open (baseline voor 0.31.5)

**Adopt-commit (ronde 21 #6):** ongewijzigd. Een lock tijdens de conflict-snapshot van Boekgeheugen laat de editor en
Planning op het nieuwe object staan, en de overige pagina's plus `_active_book` op het oude. Zoals afgesproken voor 0.31.5.

## Kleine opmerking (geen bug)

In geval 3b, met openstaande publicatietekst tijdens het exportconflict, heet de melding **"Structuuractie niet
uitgevoerd"**. De Exportpagina hergebruikt de conflictroute van de editor, en die heeft deze titel voor
structuuracties. Het gedrag klopt: de tekst is veilig en er is niets overschreven. Alleen de woordkeus past niet bij
een exportinstelling. Voor een latere UI-ronde.

## Conclusie

0.31.4 doet precies wat hij belooft. De Exportpagina gaat nu met externe wijzigingen om zoals Media en Integriteit dat
doen, afgekapte exportinstellingen worden direct herkend, en beschadigde publicatieteksten zijn via Integriteit
herstelbaar. Er is een schone basislijn voor de transactionele adopt-commit in 0.31.5.

**Niet kunnen testen:** echte Dropbox-timing tussen twee computers (nagebootst door bestanden direct te wijzigen), en de
visuele kant van de meldingen.
