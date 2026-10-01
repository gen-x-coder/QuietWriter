# QuietWriter: reviewronde 37 (versie 0.34.1: Planning fail-closed, statusbalk, separators, scènedetails, nieuwe testindeling)

**Gelezen:**
- de diffs van `planning_storage.py` (`_require_list`, versiecontrole), `integrity.py` (structuurcontrole),
  `main_window.py` (statusbalk, separators, preflight) en `chapter_context_panel.py` (scènekaarten, velden,
  `hide()` vóór `deleteLater()`);
- `pytest.ini`, `tests/README.md` en `REVIEW_NOTES_0341.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless) met het echte stylesheet. Voor de separators heb ik alle
14 thema's gemeten, en ik heb een echte start via `python main.py` gedaan.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Suites

| Suite | Resultaat |
|---|---|
| `pytest` (alleen `tests/current`) | **157 geslaagd, 1 failure**: `test_review_0341_qt.py::test_collapsed_rail_has_visible_group_separators` (zie punt 2) |
| `pytest tests/legacy` | 482 geslaagd, 280 subtests. Failures: de 2 fonttests plus **3 nieuwe** in `test_planning_characters_ui.py` (zie punt 3) |
| Een bestand in zowel `current` als `legacy` | geen ✅ |
| `pytest` verzamelt alleen `current` | ✅ |
| Geen hang | ✅ |

---

## Productgedrag: groen

### Eerst: koude start en smoke-regressie van 0.34.0

✅ `main.py` start. De smoke-set van 0.34.0 (railselectie, navigatie via code, opgeslagen versus onopgeslagen Planning,
AI uit, publicatie, geschiedenis, beschadigd hoofdstuk) haalt **20/20**. In 0.34.0 blokkeerden 3 van die gevallen het
openen van het boek; nu slagen ze.

### A. Planning met een verkeerde structuur: het boek blijft open

| Geval | Boek opent | Paneel | Typen en opslaan | Planning | Save op het kapotte deel | Integriteit |
|---|---|---|---|---|---|---|
| `outline.json` `scenes: 5` | ✅ Inhoud | ✅ leesfout | ✅ | ✅ foutstaat `scenes` | ✅ bytes intact | ✅ `aux_json_invalid` op precies dat pad |
| scène met `character_ids: null` | ✅ | ✅ | ✅ | ✅ `scenes` | ✅ | ✅ |
| personage met `relations: 5` | ✅ | ✅ | ✅ | ✅ `characters` | ✅ | ✅ |
| `outline.json` versie 2 | ✅ | ✅ | ✅ | ✅ `scenes` | ✅ | ✅, maar zie punt 1 |
| `characters.json` versie 2 | ✅ | ✅ | ✅ | ✅ `characters` | ✅ | ✅, maar zie punt 1 |

Nergens een exceptie in de Qt-eventloop. De bestaande basislijn voor ongeldige UTF-8 en ongeldige JSON (rondes 16–18 en
ronde 29) blijft groen.

### B. Scènedetails in "In dit hoofdstuk"

| Check | Resultaat |
|---|---|
| Alle ingevulde velden zichtbaar: titel, status en locatie, synopsis, **Doel, Conflict, Uitkomst, Notities**, personages | ✅ |
| Lege velden krijgen geen lege kop (scène met alleen Conflict toont alleen Conflict) | ✅ |
| Verweesd personage-id overgeslagen | ✅ |
| Elke scène in een eigen kaart; de titel is zwaarder dan de gewone tekst | ✅ (zie `r37_context.png`) |

**Kleine visuele noot:** in de schermafbeelding staan de scènetitel en de veldlabels ("Doel", "Conflict") een paar pixels
verder naar rechts dan de gewone tekst eronder. Dat komt vermoedelijk door de marge in de QSS van `subsectionTitle` en
`contextFieldLabel`. Kijk even of je dat op je eigen scherm ook ziet.

### C. Statusbalk

| Check | Resultaat |
|---|---|
| Hoofdstuk open | ✅ `Hoofdstuk 1 van 2 · 5 woorden` |
| Tijdelijke melding van 100 ms | ✅ daarna komt de telling terug |
| Tijdens typen | ✅ telling loopt mee (5 → 6 woorden) |
| Wisselen van hoofdstuk | ✅ `Hoofdstuk 2 van 2 · 0 woorden` |
| Planning | ✅ geen hoofdstuktelling; terug naar Inhoud → telling terug |
| Voorwoord (via `open_publication_item`) | ✅ leeg, geen oude telling, ook niet na een tijdelijke melding |
| Boekenplank | ✅ leeg, ook na een tijdelijke melding |

### D. Separators in de ingeklapte rail

✅ Geen lijn aan begin of eind, geen twee achter elkaar, niets in de uitgeklapte rail (de railmatrix haalt 26/26). De lijn
van 1 px heeft in alle 14 thema's echt de randkleur (pixel gemeten).

Het contrast is wel laag. Zie `r37_separators.png`: links Helder, rechts Nacht, beide 2× vergroot.

| Thema | Lijnkleur | Rail | Contrast |
|---|---|---|---|
| Helder | `#dce1e6` | `#eef1f4` | ~1.15:1 |
| Nacht | `#353a42` | `#292d33` | ~1.2:1 |
| Aurora | `#4c566a` | `#3b4252` | ~1.35:1 |

"Subtiel" klopt dus. Of het "werkelijk zichtbaar" is, hangt af van je scherm. Vind je hem te zwak, gebruik dan `muted` met
een lage alfa in plaats van `border`.

---

## 1. 🟡 Een **nieuwere** Planning-versie wordt als "beschadigd en herstelbaar" gemeld, en herstel draait het terug

`version != 1` wordt nu behandeld als corrupt. Dat is goed voor het openen: fail-closed, alleen-lezen en geen overschrijving.
Maar Integriteit meldt het als `aux_json_invalid` en markeert het als **herstelbaar**. Herstellen zet dan de laatste v1 uit
History terug.

**Runtime:** `outline.json` v1 ("OUD") → handmatige versie → andere computer schrijft v2 ("NIEUW V2") → Integriteit
→ Herstellen → het live bestand is weer **v1 "OUD"**. Hetzelfde gebeurt met `characters.json`.

De v2-bytes staan volgens het 0.29-ontwerp nog in `pre_integrity_repair`, maar live zijn ze weg. Dropbox synchroniseert die
terugzetting daarna naar de computer met de nieuwere versie.

Dit is nu nog theoretisch, want er bestaat geen v2. Maar het is precies de situatie die ontstaat zodra 0.34 of 0.35 het
Planning-schema uitbreidt en je twee computers niet tegelijk bijwerkt.

Voor `book.json` is dit in 0.28 al goed geregeld met `FutureBookFormatError` en de melding "Werk QuietWriter bij".

**Fix (vóór de eerste schemawijziging):**
- In `planning_storage._read_json` en `integrity.py`: `version > 1` krijgt een eigen code, bijvoorbeeld
  `aux_json_newer`, met `recoverable=False` en de tekst "Gemaakt met een nieuwere QuietWriter. Werk QuietWriter bij;
  herstellen zou nieuwere Planning-gegevens terugdraaien."
- Planning blijft alleen-lezen, precies zoals nu.

**Daarnaast:** de structuurregels staan nu twee keer in de code, in `planning_storage.py` en in `integrity.py`. Die gaan
uit elkaar lopen zodra het schema verandert. Maak er één `validate_planning_payload(kind, value)` van die beide gebruiken.
Dat is dezelfde aanpak als `validate_manifest_structure` voor `book.json`.

## 2. 🟡 De nieuwe separatortest in `tests/current` faalt met echte PySide6

`assert all(sep.height() == 1 …)` faalt, want de widget is **9 px** hoog: 1 px lijn plus `margin: 4px` boven en onder
uit de QSS. De lijn zelf is 1 px en zichtbaar (zie D). Dit is dus alleen een fout in de test.

**Fix:** test op `sep.contentsRect().height() == 1`, of lees een pixel uit `grab()`.

## 3. 🟡 Drie tests in `legacy` zijn door deze release stukgegaan, en niemand ziet het

`tests/legacy/test_planning_characters_ui.py` gebruikt een nep-`_Owner` zonder de nieuwe `clear_source_error()`.
`CharactersPage.load()` roept die nu aan, wat een `AttributeError` geeft. Dit is geen productfout; het nep-object is gewoon
verouderd.

Het laat wel het risico van de nieuwe indeling zien. `legacy` draait niet meer standaard, dus tests gaan daar ongemerkt
kapot. Zodra je een oude foutklasse wél wilt controleren, blijkt de test dan zelf al stuk.

## 4. 🟡 (voorstel) Een paar kernrisico's staan alleen in `legacy`

Het idee van `current` en `legacy` vind ik goed, want 600+ historische tests per iteratie is te veel. Maar deze foutklassen
zijn de afgelopen twintig rondes juist het vaakst teruggekomen, en ze staan nu **alleen** in `legacy`:

| Bestand | Bewaakt |
|---|---|
| `test_review_0315.py` | de transactionele adopt (alles of niets bij een fout in de snapshot) |
| `test_review_0316.py` | een onleesbare eigen bron met onopgeslagen invoer |
| `test_review_0324.py` | Planning-notities: geen valse dirty-status na Instellingen en geen `notes.md` |
| `test_review_0313.py` en `test_review_0314.py` | het conflict tussen Export en een extern gewijzigd boek |
| `test_review_history_preview_qt_0222.py` | het voorbeeld uit de geschiedenis schrijft nooit naar het archief |
| `test_review_export_correctness_0224.py` | de correctheid van de export |

**Voorstel:** verplaats die zeven naar `current`. Het gaat om ongeveer 35 tests. Leg daarnaast vast dat `legacy` bij elke
**minor-release** (0.35.0, 0.36.0) volledig groen moet zijn. Dan kan hij niet stilletjes wegrotten.

---

## Wat Lucas zelf kan checken

Je vier punten zijn goed. Ik zou er twee dingen aan toevoegen:
- **Separators:** kijk ook met een donker thema. Het contrast is daar iets hoger, maar nog steeds laag.
- **Uitlijning in "In dit hoofdstuk":** staan scènetitels en veldlabels ("Doel", "Conflict") op dezelfde linkerkant als de
  tekst eronder?

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | Planning fail-closed (5 vormen), boek blijft open, geen overschrijving, Integriteit wijst het juiste pad aan; scènedetails; statusbalk; separators; regressie | ✅ | — |
| 1 | Een nieuwere Planning-versie is "herstelbaar" en herstel draait hem terug naar v1 | 🟡 | Latent; oplossen vóór de eerste Planning-schemawijziging |
| 2 | De separatortest in `current` faalt met echte Qt (widget 9 px, lijn 1 px) | 🟡 | Alleen de test |
| 3 | Drie `legacy`-tests stuk door een verouderd nep-object; niemand ziet het | 🟡 | Alleen de tests |
| 4 | Zeven tests voor kernrisico's staan alleen in `legacy` | 🟡 | Voorstel |

**Conclusie:** productmatig is 0.34.1 groen. Planning met een verkeerde structuur blokkeert het boek niet meer, en de
paneel- en statusbalkverbeteringen werken. Het enige inhoudelijke punt is hoe een **nieuwere** Planning-versie wordt
behandeld. Leg dat vast vóór je aan het Planning-schema begint.

**Niet kunnen testen:**
- echte Windows DPI-schaling (punt E uit de notes; zie mijn metingen in ronde 36);
- de ophaalroute van AI-modellen;
- echte Dropbox-timing.
