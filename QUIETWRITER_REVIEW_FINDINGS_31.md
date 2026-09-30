# QuietWriter: reviewronde 30–31 (versie 0.32.4 → hotfix 0.32.5)

**Ronde 30 (0.32.4)** heb ik direct na het vinden van de startcrash gestopt. **Ronde 31 (0.32.5)** is volledig uitgevoerd.
Dit rapport dekt beide rondes.

**Gelezen:**
- de diffs van 0.32.4: `ManuscriptEditor.source_text()`, `NotesPage._clean_text`, Planning/`main_window` `conflict_local`,
  de vier bewerkingen op het hele document, `publication_editor`, en de navigatie bij een koude start;
- de hotfix-diff van 0.32.5;
- `REVIEW_NOTES_0324.md` en `REVIEW_NOTES_0325.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless) plus een echte start via `python main.py`. Met een spion
op `persist_notes` en `save_chapter`, en byte-vergelijkingen.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

---

## Ronde 30 (0.32.4): startcrash bevestigd

In 0.32.4 stond `source_text()` midden in `ManuscriptEditor.__init__`. Alles daarna was dode code na de `return`: timers,
selectiebalk, scènebreukknop, `presentation_highlighter`, typografie en marges.

- `python main.py` → `AttributeError: 'ManuscriptEditor' object has no attribute 'presentation_highlighter'`
  (vanuit `editor_page.py:116`).
- De suite in een echte PySide6-omgeving gaf **22 failures**, waaronder bijna alle Qt-runtimetests.

Deze fout is in jouw omgeving niet gevangen omdat daar 31 Qt-runtimetests worden overgeslagen. Zie de tip onderaan.

## Ronde 31 (0.32.5): hotfix correct

De methode staat nu na `__init__`. Die fix is identiek aan wat ik zelf lokaal had gepatcht om door te kunnen testen.

| Check | Resultaat |
|---|---|
| `python main.py` (koude start, offscreen) | ✅ het venster draait, geen traceback |
| `MainWindow` met spelling aan en uit | ✅ beide OK |
| Hoofdstuk-editor: `_format_timer`, `_selection_timer`, `selection_toolbar`, `scene_delete_button`, `presentation_highlighter` | ✅ aanwezig |
| Notitie-editor: dezelfde attributen | ✅ aanwezig |

---

## REVIEW_NOTES_0324/0325: alles groen

| # | Check | Resultaat |
|---|---|---|
| 1 | Koude start, rail uitgeklapt | ✅ alleen Menu, Boekenplank, Schrijverspersona, Instellingen en Prullenbak. Geen boekitems, geen HUIDIG BOEK en geen witruimte (zie `r31_coldstart.png`) |
| 1 | Boek openen | ✅ alle 8 boekitems, de kop en de witruimte direct zichtbaar |
| 1 | Terug naar Boekenplank | ✅ alles weer verborgen |
| 1 | Met boek: preview AI uit | ✅ alleen Boekgeheugen en Boekprofiel weg, de rest blijft |
| 1 | Daarna weg via Boekenplank | ✅ alle boekitems verborgen |
| 2 | Notities na Instellingen opslaan (4 varianten: met en zonder `notes.md`, Planning wel en niet bezocht) | ✅ niet dirty, timer uit, **0×** `persist_notes`, geen nieuw `notes.md`, bytes identiek |
| 2 | Twee computers: B wijzigt een hoofdstuk, A slaat Instellingen op | ✅ geen Planning-dialoog meer (was 3/3 in 0.32.3) |
| 2 | B wijzigt `notes.md`, A slaat Instellingen op | ✅ de notities van B blijven live staan (in 0.32.3 zette "Mijn planning" A's oude tekst terug) |
| 3 | Notities met twee harde spaties + U+2028, één teken typen, opslaan | ✅ alles blijft behouden |
| 3 | Teken typen en weer weghalen | ✅ weer clean, timer uit |
| 3 | Notitieconflict, "Mijn planning gebruiken" | ✅ live: harde spaties, U+2028 en de lokale tekst; tekst van B in `archive/` |
| 3 | Notitieconflict, "Versie op schijf gebruiken" | ✅ tekst van B live; de `conflict_local`-kopie houdt de harde spaties en U+2028 |
| 3 | Onvoltooide notities + centrale adopt door een hoofdstukconflict | ✅ de kopie in History houdt de lokale tekst, harde spaties en U+2028 |
| 4 | Scènescheiding invoegen, scènescheiding verwijderen, afbeelding invoegen, afbeelding verwijderen | ✅ 4/4: harde spaties en U+2028 blijven staan (alle vier ❌ in 0.32.3) |
| 5 | Voorwoord met harde spatie + U+2028, echte wijziging + opslaan | ✅ behouden |
| 5 | Voorwoord open, Instellingen opslaan (niets, thema, lettergrootte, inspringing, spelling uit) | ✅ niet dirty, niet herschreven |
| — | Hoofdstuk-editorbron (ronde 29) | ✅ 8/8 |
| — | Proeven ronde 28 | ✅ 30/30 |

---

## 1. 🟡 Nieuwe Qt-test hangt de suite in een echte PySide6-omgeving

**Alleen in de tests, niet in de app.** `tests/test_review_0324.py::test_settings_presentation_pass_does_not_dirty_or_create_planning_notes`
blijft oneindig hangen.

De `_settings()`-fixture zet geen `workspace`. De test geeft `old_root = str(window.settings.value('workspace', ''))` door,
dus `''`. In `settings_saved()` vergelijkt de app `self.settings.value('workspace')` (`None`) met `''`. Die zijn ongelijk, dus
verschijnt de modale `QMessageBox.information('Werkmap gewijzigd', …)`. In de testomgeving klikt niemand die weg.

Runtime:
- faulthandler na 25 s: `main_window.py:919 in settings_saved`;
- de rest van de suite, met deze test uitgesloten: **604 geslaagd**, 280 subtests, alleen de 2 fonttests falen;
- met `old_root = window.settings.value('workspace')` slaagt de test (3/3 in dat bestand).

**Fix:** zet in `_settings()` een `workspace`, of geef de ruwe waarde door. Lucas: draai je de suite lokaal met PySide6,
dan hangt hij hier tot je dit aanpast.

---

## 2. 🟡 (latent, geen actuele fout) `FreeTextPage` heeft nog geen baseline

Voorwoord en Nawoord slaan nu wel op via `source_text()`, maar `FreeTextPage._changed()` zet nog steeds zonder vergelijking
`dirty=True`.

Op dit moment raakt geen enkele echte route de publicatie-editor met een presentatiepass. `settings_saved()` past alleen de
hoofdstuk- en notitie-editor aan, en ik zag geen valse dirty-status bij vijf soorten instellingen. Maar een directe
`presentation_highlighter.rehighlight()` maakt het Voorwoord dirty. Als er daarna extern iets verandert en je navigeert,
verschijnt de conflictdialoog.

Wordt het publicatiescherm ooit meegenomen in `settings_saved()` (bijvoorbeeld voor dezelfde typografie), dan komt ronde 27
terug. Het is een kleine preventieve fix, met hetzelfde `_clean_text`-patroon als `NotesPage`: baseline in `set_text()` en na
een geslaagde save, en de vergelijking in `_changed()`.

---

## Regressie

| Reeks | Resultaat |
|---|---|
| Rondes 12–14 | 32/32, 10/10, 19/19 |
| Ronde 15 | 7/12, dezelfde 5 artefact-regels als eerder |
| Rondes 16–18 | 2/2, 5/5, 3/3 |
| 0.31.0 | 18/18 |
| Adopt / openen met corrupte JSON | geen gemengde toestand |
| Ronde 21 · spelling | 9/9 · 6/6 |
| Rondes 22–24 | 12/12, 12/12, 10/10 |
| Randgeval ronde 24 | alle drie de keuzes ok |
| Ronde 25 (met AI aan) | 25/29, de 4 bekende artefact-regels |
| Ronde 26 (start, spelling, AI en advanced, herkomst) | groen |
| Ronde 27 (live preview) | 36/37; de FAIL komt uit het testscript zelf (het geparkeerde sjabloonbestand, niet breder geworden) |
| Rondes 28 · 29 | 30/30 · 8/8 |
| Backend 9–11 | 47/47, 15/15, 8/8 |

De transactionele adopt en de conflictflows uit 0.31 zijn niet geraakt.

## Tips voor ChatGPT

- **Het belangrijkste:** jouw omgeving slaat de Qt-runtimetests over. Daardoor gingen zowel de startcrash van 0.32.4 als de
  hangende test van punt 1 ongemerkt mee. Twee goedkope vangnetten:
  1. Een test **zonder** PySide6-runtime die met `ast` controleert dat elke `def` binnen een klasse op klasseniveau staat,
     en dat `__init__` geen `return` vóór zijn laatste statement heeft. `python -m py_compile` vangt dit niet: het is
     geldige Python.
  2. Zet in elke Qt-test `QMessageBox.information/warning/critical` en `exec` op een stub
     (`monkeypatch.setattr(QMessageBox, 'information', lambda *a, **k: QMessageBox.Ok)`), zodat een onverwachte dialoog
     de test laat falen in plaats van laat hangen.
- Vermeld in de release-notes hoeveel Qt-tests er bij jou zijn overgeslagen. Dan weet Lucas dat die door mij of lokaal
  gedraaid moeten worden voordat hij de release gebruikt.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | 0.32.4 startte niet (`source_text()` midden in `__init__`) | 🔴 → ✅ opgelost in 0.32.5 | — |
| 1 | Nieuwe Qt-test hangt op een modale "Werkmap gewijzigd"-dialoog (fixture zonder `workspace`) | 🟡 | Alleen de suite; blokkeert een lokale testrun met PySide6 |
| 2 | `FreeTextPage` mist nog de `_clean_text`-baseline | 🟡 | Latent; geen echte route raakt het nu |

**Conclusie:** 0.32.5 is in orde. De koude start toont een schone rail. De notities hebben dezelfde echte dirty-regel als de
editor, en het vals conflict met twee computers is voor notities weg. Harde spaties en U+2028 blijven overal bewaard: in
hoofdstukken, notities, publicatieteksten, de vier bewerkingen op het hele document en alle conflictkopieën. Wat overblijft is
één testfix en één preventieve baseline.

**Niet kunnen testen:**
- een tweede spellingstaal;
- de echte ophaalroute van AI-modellen;
- het app-thema in de schermafbeeldingen;
- echte Dropbox-timing (nagebootst).
