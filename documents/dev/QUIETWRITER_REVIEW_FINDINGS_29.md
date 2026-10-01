# QuietWriter: reviewronde 29 (versie 0.32.3: één bronrepresentatie voor de editor)

**Gelezen:**
- de diff van `editor_page.py` (`_editor_source_text()` via `toRawText()`, gebruikt voor baseline, dirty, save, conflict en
  zoeken/vervangen);
- `REVIEW_NOTES_0323.md` en de nieuwe test.

Daarna heb ik alle overgebleven `toPlainText()`-aanroepen op de manuscript- en notitie-editor nagelopen.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Hoofdstukbestanden heb ik met een BOM, U+00A0, U+2028 en
U+2029 op schijf gezet. `save_chapter` en `persist_notes` werden bijgehouden met een spion. Twee computers heb ik
nagebootst door bestanden direct te wijzigen.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

**Testsuite:** 598 geslaagd, 280 subtests. Alleen de 2 bekende fonttests falen. De twee nieuwe Qt-tests draaien hier echt
en slagen.

---

## REVIEW_NOTES_0323: de hoofdstuk-editor is in orde

| # | Check | Resultaat |
|---|---|---|
| 1 | Hoofdstuk met BOM, U+00A0, U+2028 en U+2029: alleen openen, `rehighlight()`, Instellingen opslaan, Negeer overal | ✅ geen enkele keer dirty, timer uit, 0× `save_chapter`, bytes identiek |
| 2 | `10 euro op p. 5` (twee harde spaties) + U+2028, dan één teken typen | ✅ beide harde spaties en U+2028 blijven staan |
| 2 | Bestaande BOM na een echte wijziging | BOM verdwijnt (Qt haalt hem weg bij `setPlainText`). Onschuldig, want UTF-8 heeft geen BOM nodig. Geen bezwaar |
| 3 | Hoofdstuk met harde spatie + externe wijziging door B + `rehighlight()` + Instellingen opslaan op A | ✅ **voor het hoofdstuk** schrijft A niets. Er kwam wel een dialoog, maar die komt uit **Planning**: zie punt 1 |
| 4 | Echte wijziging + extern conflict, "Mijn versie gebruiken" | ✅ het live bestand houdt de harde spaties, U+2028 en de nieuwe tekst; de tekst van B staat in `archive/` |
| 4 | Idem, "Versie op schijf gebruiken" | ✅ tekst van B live; de `conflict_local`-kopie in History houdt de harde spaties en U+2028 |
| 5 | De 30 proeven uit ronde 28 | ✅ 30/30 |

---

## 1. 🔴 Hetzelfde valse-dirty-probleem zit nog in Planning → Notities

**Eerdere bevinding, door mij gemist in rondes 27 en 28. Bestaat sinds 0.32.1.** In ronde 27 zag ik al dat het
notitiepaneel dirty werd, maar mijn bytecontrole zag geen wijziging. Mijn test mat op het verkeerde moment.

`settings_saved()` past lettertype en manuscriptstijl ook toe op `planning_page.notes_page.editor`. Die doet daarbij een
`rehighlight()`, en dat geeft `textChanged`. `NotesPage.changed()` zet dan **zonder vergelijking** `dirty=True` en start de
timer. De fix van 0.32.2/0.32.3 zit alleen in `EditorPage`.

**Runtime (per variant: Instellingen opslaan, daarna 4 s wachten, zonder Planning aan te raken):**

| Versie | Notities dirty | `persist_notes` aangeroepen | Bestand |
|---|---|---|---|
| 0.32.0 | nee | 0× | ongewijzigd |
| 0.32.1 – 0.32.3 | **ja** | **1×** | geen `notes.md` → er wordt een leeg `notes.md` aangemaakt; bestaat hij al, dan wordt dezelfde tekst herschreven |

**Het scenario met twee computers** (A slaat alleen Instellingen op en staat daarna gewoon in Inhoud):

| Wat B deed | Wat A 3 s later ziet | Gevolg |
|---|---|---|
| Een **hoofdstuk** gewijzigd | dialoog "Dit boek is buiten QuietWriter gewijzigd. [Mijn planning gebruiken] [Versie op schijf gebruiken]" | vals conflict midden in het schrijven. Bij elke keuze blijft het hoofdstuk van B intact |
| **`notes.md`** gewijzigd | dezelfde dialoog | "Mijn planning gebruiken" zet A's **oude** notities live over die van B. B's notities staan wel in `archive/…` |

Dit is precies het patroon van ronde-27 punt 1, alleen nu voor notities.

**Daarnaast:** `NotesPage.save()` schrijft `self.editor.toPlainText()`. Harde spaties en U+2028 in notities worden dus nog
steeds genormaliseerd, net als in ronde-28 punt 2. Gemeten: `Notitie met 10 euro.` wordt `Notitie met 10 euro.`

**Fix:** geef `NotesPage` dezelfde regel als de editor. Maak de bronfunctie gedeeld, bijvoorbeeld
`ManuscriptEditor.source_text()` (dus `toRawText().replace(' ', '\n')`), zodat editor en notities één implementatie
hebben:
- `self._clean_text = self.editor.source_text()` in `load()` en na een geslaagde save. **Niet** in `restore_pending_text`:
  dat is lokale invoer, die dirty moet blijven;
- in `changed()`: bij gelijke tekst `dirty=False`, timer stoppen, Opslaan-knop uit, en stoppen;
- in `save()` en in de twee `toPlainText()`-aanroepen in `planning_page.py` (regels 92 en 112) en `main_window.py`
  (regel 242, `conflict_local`): dezelfde `source_text()`.

**Test:** notities met en zonder bestand → `save_settings()` → 4 s pompen → `persist_notes` 0×, geen nieuw bestand, en na een
externe hoofdstukwijziging geen dialoog.

---

## 2. 🟡 Vier bewerkingen op het hele hoofdstuk normaliseren nog steeds alle harde spaties

**Rest van ronde-28 punt 2.** Deze routes bouwen de nieuwe tekst op uit `toPlainText()` en vervangen daarna het
**volledige document** (`cursor.select(Document)` + `insertText(new_text)`):

| Route | Plek | Runtime: harde spaties / U+2028 na save |
|---|---|---|
| Scènescheiding invoegen | `editor_page.insert_scene_break` (~1427) | ❌ weg in het hele hoofdstuk |
| Afbeelding invoegen | `editor_page._insert_image_from_panel` (~1634) | ❌ weg |
| Afbeelding verwijderen | `editor_page._delete_image_block` (~1584) | ❌ weg |
| Scènescheiding verwijderen (hover-knop) | `manuscript_editor._delete_hovered_scene_break` (~994) | ❌ weg |

Eén keer een scènescheiding invoegen maakt dus alle harde spaties in dat hoofdstuk gewone spaties.

**Fix:** gebruik in deze vier functies de bronfunctie in plaats van `toPlainText()`. De offsets blijven gelijk, want
`toRawText()` heeft dezelfde lengte en posities als het document.

Niet schadelijk, alleen lezend en daarom prima zo: `update_counts`, de spellingsrijen, de AI-context in `build_ai_context`,
de statusbalk van de selectie en de slimme aanhalingstekens. De `_replace_changed_text` van de opmaakbalk vervangt alleen het
gewijzigde stuk; daarbuiten blijft alles staan.

---

## Kleine observatie (bekend, geparkeerd)

Het lege sjabloon voor Boekgeheugen en Boekprofiel bij alleen bezoeken is ongewijzigd, zoals afgesproken. Punt 1 hierboven
maakt voor notities iets vergelijkbaars, maar dat gebeurt **zonder** dat je Planning bezoekt en **met** een
conflictdialoog. Dat is dus wel een echte fout.

---

## Regressie

| Reeks | Resultaat |
|---|---|
| Ronde 28 (30 proeven) | 30/30 |
| Rondes 12–14 | 32/32, 10/10, 19/19 |
| Ronde 15 | 7/12, dezelfde 5 artefact-regels als eerder |
| Rondes 16–18 | 2/2, 5/5, 3/3 |
| 0.31.0 | 18/18 |
| Adopt / openen met corrupte JSON | geen gemengde toestand |
| Ronde 21 · spelling | 9/9 · 6/6 |
| Rondes 22–24 | 12/12, 12/12, 10/10 |
| Randgeval ronde 24 | alle drie de keuzes ok |
| Ronde 25 (met AI aan) | 25/29, de 4 bekende artefact-regels |
| Ronde 26 (start met spelling uit, spelling direct, AI en advanced, herkomst) | groen |
| Ronde 27 (live preview) | 36/37; de FAIL komt uit het testscript zelf (het geparkeerde sjabloonbestand) |
| Backend 9–11 | 47/47, 15/15, 8/8 |

De transactionele adopt en de conflictflows uit 0.31 zijn niet geraakt.

## Tips voor ChatGPT

- Zoek bij deze klasse fouten op het **patroon**, niet op de plek: `grep -n "toPlainText()"` en `textChanged.connect` in
  `ui/`. Elke editor die op schijf schrijft, heeft een baseline plus een bronfunctie nodig. Dat zijn nu de hoofdstuk-editor
  en de notities, en mogelijk later de publicatieteksten (`publication_editor.py:180` gebruikt ook `toPlainText()`).
- Voor de test van punt 1 moet de spion op `persist_notes` staan, niet op het bestand. Een herschrijving met dezelfde inhoud
  zie je niet aan de bytes, maar wel aan de revisiecontrole die de dialoog veroorzaakt.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| 1 | Planning-notities worden na elke Opslaan in Instellingen dirty en weggeschreven: leeg `notes.md` aangemaakt, vals conflict bij een externe wijziging, en "Mijn planning" kan de notities van B live overschrijven (wel in het archief) | 🔴 | Hoog voor de opzet met twee computers; bestaat sinds 0.32.1, door mij eerder gemist |
| 2 | Scènescheiding invoegen/verwijderen en afbeelding invoegen/verwijderen maken alle harde spaties gewone spaties | 🟡 | Stil verlies van typografie |

**Conclusie:** voor de hoofdstuk-editor is 0.32.3 in orde. Eén bronrepresentatie, geen valse dirty-status, harde spaties en
U+2028 blijven bewaard, ook in beide conflictroutes. Dezelfde klasse fouten zit nog op twee plekken: de notitie-editor
(punt 1, dezelfde fix als de editor) en vier bewerkingen die het hele document vervangen (punt 2, vier keer
`toPlainText()` vervangen).

**Niet kunnen testen:**
- een tweede spellingstaal;
- de echte ophaalroute van AI-modellen;
- het app-thema;
- echte Dropbox-timing (nagebootst).
