# QuietWriter: reviewronde 28 (versie 0.32.2: echte dirty-status, consistente preview, rollback bij mislukte save)

**Gelezen:**
- de diffs van `editor_page.py` (`_clean_text`, `on_text_changed`);
- de diffs van `main_window.py` (`_feature_visibility_preview`, `_apply_nav_width(ai_enabled=…, advanced=…)`, `hidden_right`
  alleen bij de commit);
- de diffs van `settings_page.py` (rollback);
- `REVIEW_NOTES_0322.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Het venster was getoond en de rail uitgeklapt.
`save_chapter` werd bijgehouden met een spion, en de boekmap byte voor byte vergeleken.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

**Testsuite:** 596 geslaagd, 280 subtests. Alleen de 2 bekende fonttests falen.

---

## Resultaat REVIEW_NOTES_0322: 30/30 groen

| # | Check | Resultaat |
|---|---|---|
| 1 | Opslaan zonder wijziging, en met thema, lettergrootte, AI, spelling of inspringing gewijzigd (6 varianten) | ✅ `dirty=False`, status "● Opgeslagen", timer uit; na 4 s en naar Planning: **0×** `save_chapter`, bytes identiek |
| 1 | Twee computers: Instellingen opslaan, daarna extern hetzelfde hoofdstuk wijzigen, navigeren | ✅ geen conflictdialoog, de tekst van de andere computer blijft staan, niets geschreven |
| 2 | Negeer overal, Toevoegen aan woordenboek, Altijd negeren | ✅ alle drie niet dirty, geen autosave, bytes identiek |
| 2 | Eén teken typen | ✅ dirty, en de autosave-timer loopt |
| 2 | Undo exact terug naar de opgeslagen tekst | ✅ niet meer dirty, timer gestopt |
| 2 | Undo **voorbij** een save (tekst wijkt nu af van de schijf) | ✅ wel dirty. Dat is correct: de baseline is de opgeslagen tekst, niet de laadtekst |
| 3 | Preview AI uit en Geavanceerd uit | ✅ AI-items, kop SCHRIJVEN, Integriteit en witruimte direct weg |
| 3 | Rail in- en uitklappen tijdens de preview | ✅ de previewtoestand blijft staan |
| 3 | Beide weer aan | ✅ alles direct terug |
| 3 | Weg zonder Opslaan via Inhoud, Planning, Boekdetails of Boekenplank | ✅ de opgeslagen stand komt terug; `_feature_visibility_preview` is weer `None` |
| 4 | AI-paneel open met halve invoer → preview uit/aan → weg | ✅ paneel open, invoer "mijn halve vraag" intact |
| 4 | AI uit met Opslaan | ✅ paneel dicht |
| 5 | Mislukte `sync()` (AI, Geavanceerd, thema, spelling, provider en lettergrootte gewijzigd) | ✅ `QSettings` in het geheugen exact terug; `settings_saved()` niet aangeroepen; rail en thema op de oude stand; formulier houdt de nieuwe keuzes; Opslaan blijft actief |
| 5 | Opnieuw proberen | ✅ slaagt en wordt toegepast |

**Andere herlaadroutes (baseline `_clean_text` goed bijgewerkt):** na conflict "Mijn versie", na conflict "Versie op
schijf", na wisselen van hoofdstuk, na een voorbeeld uit de geschiedenis plus afsluiten, na herstel uit de geschiedenis en
na een centrale adopt. In al die gevallen geeft een `rehighlight()` daarna **geen** dirty-status. ✅

---

## 1. 🟡 De dirty-fix werkt niet voor hoofdstukken met harde spaties, U+2028/U+2029 of een BOM

**Rest van ronde-27 punt 1.** `_clean_text` is de tekst **zoals geladen**. De vergelijking gebeurt met
`editor.toPlainText()`, en Qt past bij `toPlainText()` een paar tekens aan:

| Teken in het bestand | Wat `toPlainText()` ervan maakt |
|---|---|
| U+00A0 (harde spatie) | gewone spatie |
| U+2028 / U+2029 | `\n` |
| U+FEFF (BOM aan het begin) | valt weg |

Zo'n hoofdstuk is daardoor **nooit** gelijk aan `_clean_text`. Elke `rehighlight()` maakt het weer dirty, precies zoals in
ronde 27.

**Runtime (12 varianten, alleen openen → `rehighlight()` → Instellingen opslaan → 3,5 s):**

| Inhoud | Dirty? | Bestand herschreven |
|---|---|---|
| Gewoon LF, CRLF, losse CR, smalle harde spatie (U+202F), tab of spaties aan het eind, geen slot-newline, zero-width tekens, form feed | nee ✅ | nee |
| `10 euro` | **ja** | `10\xc2\xa0euro` → `10 euro` |
| `Een Twee` of `Een Twee` | **ja** | → `Een\nTwee` |
| BOM + tekst | **ja** | BOM verwijderd |

Hoe vaak komt dat voor? Harde spaties zitten vaak in tekst die uit Word, Scrivener of een webpagina geplakt of
geïmporteerd is ("p. 5", "10 euro", Franse aanhalingstekens). U+2028 komt uit Pages en Word. De BOM komt van oudere
Windows-editors. Voor zulke hoofdstukken blijven de gevolgen uit ronde 27 bestaan:
- Instellingen opslaan of een spellingsactie herschrijft het hoofdstuk;
- in de situatie met twee computers kan een vals conflict ontstaan;
- de schrijfactie verandert daarbij stil **de inhoud**: de harde spaties worden gewone spaties.

**Fix (één regel per laadplek):** zet de baseline op wat Qt zelf teruggeeft, niet op de ruwe bestandstekst.

```python
self.editor.setPlainText(text)
self._clean_text = self.editor.toPlainText()   # was: = text
```

Doe dit op beide plekken in de laadroutine (de normale en de corrupte tak). Daarna vergelijk je altijd Qt met Qt.

**Test:** een hoofdstuk met ` `, ` ` en een BOM openen → `rehighlight()` → `dirty is False` en bytes identiek.

---

## 2. 🟡 (bestond al) Elke gewone save vervangt alle harde spaties in het hoofdstuk door gewone spaties

`save()` schrijft `self.editor.toPlainText()`. Daardoor verliest het **hele** hoofdstuk zijn harde spaties, U+2028 wordt
een regeleinde en de BOM verdwijnt, zodra je ergens in dat hoofdstuk één teken typt.

**Runtime:** een bestand met `Hij betaalde 10 euro op p. 5.\nEen regel.` → één `x` aan het eind typen →
na autosave: `b'Hij betaalde 10 euro op p. 5.\nEen\nregel.\nx'`.

Dit is geen regressie. Het is wel stil verlies van typografische bedoeling. Een harde spatie voorkomt dat "10" en "euro"
over twee regels worden gesplitst in de export.

**Fix:** sla op met `document().toRawText()`, waarbij ` ` (Qt's alinea-scheiding) wordt omgezet naar `\n`. De harde
spaties en U+2028 blijven dan staan. Controleer wel of jullie beeldblokken tijdens het bewerken als `U+FFFC`-object in het
document staan. Zo ja, dan geldt dezelfde behandeling als nu, want dat teken zit ook in `toPlainText()`.

Doe je dit samen met punt 1, gebruik dan dezelfde functie voor de baseline, bijvoorbeeld een `_editor_source_text()` die op
beide plekken wordt gebruikt. Dan kunnen baseline en save nooit uit elkaar lopen.

---

## Kleine observatie (geen bug, ter info)

Bij een boek zonder `ai/memory.md` of `ai/boekprofiel.md` maakt alleen al het bezoeken en weer verlaten van Boekgeheugen
of Boekprofiel het sjabloonbestand aan op schijf. De inhoud is het lege sjabloon. Dat is onschuldig, maar het wijkt af van
het principe dat openen niets schrijft. Het levert ook één extra Dropbox-bestand op per boek. Voor als je het ooit
opschoont: pas schrijven bij de eerste echte wijziging.

---

## Regressie

| Reeks | Resultaat |
|---|---|
| Rondes 12–14 | 32/32, 10/10, 19/19 |
| Ronde 15 | 7/12, dezelfde 5 artefact-regels als in 0.32.0 en 0.32.1 |
| Rondes 16–18 | 2/2, 5/5, 3/3 |
| 0.31.0 | 18/18 |
| Adopt / openen met corrupte JSON | geen gemengde toestand; open → ok → Integriteit toont het probleem |
| Ronde 21 · spelling | 9/9 · 6/6 |
| Rondes 22–24 | 12/12, 12/12, 10/10 |
| Randgeval ronde 24 | alle drie de keuzes ok |
| Ronde 25 (met AI aan) | 25/29, de 4 bekende artefact-regels |
| Ronde 26 (start met spelling uit, spelling uit direct, AI en advanced, herkomst) | groen |
| Ronde 27 (live preview) | 36/37; de ene FAIL komt uit het testscript zelf, door het sjabloonbestand uit de observatie hierboven |
| Backend 9–11 | 47/47, 15/15, 8/8 |

De transactionele adopt en de conflictflows uit 0.31 zijn niet geraakt.

## Tips voor ChatGPT

- Gebruik in tests voor tekstbaselines altijd een fixture met ` `, ` ` en een BOM. Die drie tekens verschillen
  tussen de bestandstekst en wat Qt teruggeeft, en vangen dit soort fouten direct.
- Maak één functie voor "de brontekst van de editor" en gebruik die voor de baseline, voor `save()` en voor de
  dirty-vergelijking.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| 1 | De baseline `_clean_text` gebruikt de ruwe bestandstekst. Hoofdstukken met een harde spatie, U+2028/2029 of een BOM blijven vals dirty (herschrijving, mogelijk vals conflict) | 🟡 | Middel: alleen bij zulke hoofdstukken, maar dan dezelfde gevolgen als in ronde 27. De fix is één regel |
| 2 | Een gewone save zet harde spaties om naar gewone spaties (en U+2028 → `\n`, BOM weg) | 🟡 | Stil verlies van typografie; bestond al |

**Conclusie:** alle vijf de verplichte proeven zijn groen (30/30). De dirty-status volgt nu echte tekstwijzigingen, de
preview is volledig consistent, en een mislukte save rolt netjes terug. Er blijft één randgeval over: de baseline moet de
tekst zijn zoals Qt hem teruggeeft, niet zoals hij van schijf kwam (punt 1). Als je daarbij punt 2 meeneemt, blijven harde
spaties ook bij gewoon typen behouden.

**Niet kunnen testen:**
- een tweede spellingstaal;
- de echte ophaalroute van AI-modellen (geen netwerk);
- het app-thema in de schermafbeeldingen;
- echte Dropbox-timing (nagebootst).
