# QuietWriter: reviewronde 24 (versie 0.31.5, transactionele adopt)

**Gelezen:** de diffs van `main_window.py` (`adopt_active_book`, `_prepare_active_book_adoption`) en van
`book_memory_page.py`, `book_profile_page.py` en `book_details.py` (`prepare_adoption`, `adopt_*(prepared=…)`,
`show_adoption_message`), plus `REVIEW_NOTES_0315.md`.

De ZIP staat nu goed: de projectbestanden zitten direct in de root.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Failure-injection doe ik in
`create_version_with_file_overrides` met een `StorageWriteError` (een nagebootste lock). Na elke adopt controleer ik de
objectidentiteit van alle negen boekgerichte referenties: `_active_book`, editor, Planning, Boekprofiel, Boekgeheugen,
Boekdetails, Media, Integriteit en Export.

## Resultaat: groen

**Testsuite:** 574 geslaagd, 280 subtests, 0 overgeslagen. Alleen de 2 bekende fonttests falen.

### Failure-injection op de recovery-snapshots

| Geval | Snapshots | Resultaat |
|---|---|---|
| A. Boekgeheugen faalt | `ai/memory.md` ✗ | ✅ `StorageWriteError`; **alle negen referenties op het oude `Book`**; lokale tekst zichtbaar en dirty; geen conflictmelding |
| B. Boekprofiel faalt | `ai/boekprofiel.md` ✗ | ✅ idem |
| C. Boekdetails faalt | `book.json` ✗ | ✅ idem; formulier ("LOKALE SYN") ongewijzigd |
| D. Profiel slaagt, Geheugen faalt | profiel ✓, geheugen ✗ | ✅ idem; de extra herstelversie van het profiel staat in History, de UI is nergens omgebonden |
| E. Alle drie, Details faalt als laatste | profiel ✓, geheugen ✓, details ✗ | ✅ idem |

In alle vijf de gevallen geeft `verify_book_unchanged(oud)` daarna een `ExternalModificationError`. Dat klopt: de schijf
is echt veranderd. De gewone conflictflow kan dus gewoon opnieuw starten.

### Succespad (alle drie tegelijk in conflict)

| Check | Resultaat |
|---|---|
| Alle negen referenties op hetzelfde **nieuwe** `Book` | ✅ |
| Drie `conflict_local`-snapshots met de lokale invoer (geheugen, profiel, synopsis) | ✅ |
| Hetzelfde veld aan beide kanten → schijf live | ✅ ("EXTERN GEHEUGEN", "EXTERN PROFIEL", "EXTERNE SYN") |
| Veld alleen lokaal gewijzigd → blijft lokaal | ✅ ("Lokale Auteur") |
| Veld alleen op schijf gewijzigd → overgenomen | ✅ ("extern-tag") |
| Meldingen pas **na** de volledige commit | ✅ bij elke melding stonden alle pagina's al op het nieuwe object (3/3) |
| Revisiebasis na de adopt | ✅ groen |

### Regressie: alles groen

| Reeks | Resultaat |
|---|---|
| Ronde 23 (Export, twee-computersscenario, afgekapte exportinstellingen, publicatieteksten) | 12/12 |
| Ronde 22 | 12/12 |
| Spelling | 6/6 |
| **Ronde 21** | **9/9** (het adopt-punt dat tot nu toe faalde, is nu groen) |
| 0.31.0 | 18/18 |
| Corruptie rondes 16–18 | 2/2, 5/5, 3/3 |
| Integriteit | 19/19 |
| Rondes 11–13 | 36/36, 32/32, 10/10 |
| Backend 9–11 | 47/47, 15/15, 8/8 |
| Openen met corrupte JSON/UTF-8 | geen crash, geen gemengde toestand |

---

## Eén randgeval om te noteren (🟡, bestond al, geen regressie)

**Boekgeheugen dirty, en de andere computer beschadigt precies `ai/memory.md` (ongeldige UTF-8).**

`prepare_adoption` leest de schijfversie voor de merge. Dat geeft een `UnicodeDecodeError`, en de adopt breekt af.
De adopt zelf is dus netjes: er is geen gemengde toestand, en de beschadigde bytes blijven intact. Maar de conflictflow van
Boekgeheugen komt er daarna niet meer uit.

**Runtime:**

| Keuze | Navigeren | Integriteit bereiken | Sluiten | Lokale tekst in History |
|---|---|---|---|---|
| "Versie op schijf" | geweigerd | geweigerd | geweigerd | ✅ |
| "Mijn boekgeheugen" | geweigerd | geweigerd | geweigerd | ❌ alleen in het geheugen |
| Geen keuze | geweigerd | geweigerd | geweigerd | ❌ alleen in het geheugen |

In alle drie de gevallen verschijnen meldingen, maar is er geen uitweg. Voor Boekprofiel en Planning-notities verwacht ik
hetzelfde; dat heb ik niet apart gedraaid.

De trigger is zeldzaam (externe beschadiging van precies het bestand dat je op dat moment bewerkt), maar het is de laatste
route waarlangs de app vastloopt.

**Fix:** laat `prepare_adoption` bij een onleesbare schijfbron niet falen. Maak in dat geval een plan
"schijf beschadigd": de lokale invoer gaat als `conflict_local` naar History (dat kan al in de preflight), en de commit zet de
pagina in de bestaande alleen-lezen-foutstaat uit 0.29.3. Daarna zijn navigatie, sluiten en Integriteit gewoon bereikbaar.

## Conclusie

De all-or-nothing-adopt werkt zoals beschreven. Een fout in welke recovery-snapshot dan ook laat de live UI volledig op het
oude boek staan, ook als een eerdere snapshot al gelukt is. Het succespad behoudt exact de bestaande merge-regels, en de
meldingen komen pas als alles consistent is. Daarmee is het laatste bekende openstaande punt uit ronde 21 gesloten.

De hele 0.31-reeks is nu groen. Het randgeval hierboven kan mee in een volgende ronde.

**Niet kunnen testen:** echte Windows- en Dropbox-locks (nagebootst) en de visuele volgorde van de meldingen op een echt scherm.
