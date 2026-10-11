# QuietWriter 1.3.0-dev.26: brede code-, runtime- en visuele review

**Reviewer:** Claude · **Datum:** 8 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.26.zip`, SHA-256 `1f86d20114bfaed1b78472d0955dedbdc71dba58d9db3f44b8e6b8ccc789f676`
**Opdracht:** `documents/REVIEW_REQUEST_1.3.0-dev.26_CLAUDE.md`. Er is geen productcode gewijzigd.
**Vergelijkingsbasis:** dev.9, mijn vorige brede review.

**Reikwijdte van de code-review:** de volledige diff dev.9 → dev.26. Gelezen zijn:
- `editor_page.py`, `manuscript_editor.py` en `search_panel.py`;
- de Planning-UI (`planning_page.py`, `outline_page.py`, `characters_page.py`, `chapter_context_panel.py`);
- `planning_models.py`, `settings_page.py`, `book_details.py`, `writing_progress.py`, `storage.py` (diff),
  `bookshelf.py` (diff), `main_window.py` (diff) en `themes.py` (diff).

Legenda: **[test]** = in Qt gereproduceerd · **[meting]** = gemeten · **[inspectie]** = code gelezen ·
**[visueel]** = screenshot bekeken.

---

## 0. Conclusie

De drie productlijnen werken functioneel en zijn netjes presentation-only gebouwd:
- **schrijfdoelen**;
- **Planninghulp en de Planning-flyout**;
- **zoeken/vervangen en kopiëren/plakken**.

De ghosttekst komt nergens in document, bestand, zoekresultaten of undo terecht. Planninghulp blijft presentation-only.

Er zijn **twee blockers**. Beide zijn klein:
1. **De suite is rood.** Twee Qt-tests zijn niet bijgewerkt na bewuste UI-wijzigingen.
2. **De opt-in voor "Vandaag geschreven bijhouden" wordt stil overschreven** zodra je Boekdetails opslaat. In één
   richting zet dat het bijhouden **zonder toestemming aan**.

Daarnaast vier punten die vóór 1.3.0 moeten. Daarvan is het scrollwiel op instellingen het belangrijkste. Het
lijstje backlogpunten is klein.

---

## 1. Blockers vóór verdere ontwikkeling

### B1. De Qt-suite is rood: 2 tests zijn achtergebleven bij bewuste wijzigingen [test]

| Test | Verwacht | Werkelijk | Oorzaak |
|---|---|---|---|
| `test_planning_ghosts_130_dev19_qt.py::test_ghost_detail_lines_keep_location_and_characters_separate` | `'Status: ○ idee'` | `'Status: ○ Idee'` | In dev.24/25 zijn de statussen bewust met hoofdletter weergegeven |
| `test_writing_goals_130_dev12_qt.py::test_goal_date_is_explicit_compact_and_defaults_to_today` | `maximumWidth() <= 170` | `180` | Het datumveld is bewust breder gemaakt |

Beide falen ook geïsoleerd, dus het ligt niet aan de testvolgorde. De productcode is in beide gevallen de bedoelde
versie; **de tests moeten worden bijgewerkt**.

**Waarom dit een blocker is:** een rode suite maskeert de volgende echte regressie. Het laat ook zien dat de volledige
Qt-suite vóór oplevering niet is gedraaid.

### B2. Boekdetails overschrijft de globale opt-in "Vandaag geschreven bijhouden" [test, inspectie]

**Waar:**
- `book_details.py` legt bij de constructie `self._baseline_progress_enabled = settings.value('writing_progress_enabled')`
  vast en vult daarmee de combo `progress_tracking`;
- `save()` schrijft die combo **altijd** terug naar `QSettings`;
- de pagina wordt per boek één keer gebouwd en bij het tonen niet ververst (`main_window.open_current_book_details`).

**Reproductie** (`rt1326b.py` §A):

| Stappen | Resultaat |
|---|---|
| Boek openen (Boekdetails wordt gebouwd met "Niet bijhouden"), dan Instellingen → **Bijhouden** → Opslaan, dan Boekdetails → woorddoel wijzigen → Opslaan | De instelling staat weer op **Niet bijhouden**. Er wordt stil niet meer geteld. |
| Boekdetails gebouwd terwijl "Bijhouden" aan stond, dan Instellingen → **Niet bijhouden** → Opslaan, dan Boekdetails → Opslaan | De instelling staat weer op **Bijhouden**. Het meten is **zonder toestemming hervat**. |

Het tweede geval breekt de expliciete productbelofte: "opt-in, standaard uit; uitzetten stopt het bijhouden".

**Simpelste fix (aanbevolen): haal het veld uit Boekdetails.**
- Het is een apparaatinstelling, geen boekgegeven.
- De intro van Boekdetails zegt zelf "Deze gegevens horen bij het boek".
- Eén plek, in Instellingen, is ook anti-bloat.

**Alternatief:** ververs de combo bij elke `open_current_book_details()` uit `settings`, en schrijf hem alleen als de
gebruiker hem in dit formulier zelf heeft veranderd.

**Test:** beide volgordes hierboven.

---

## 2. Moet vóór 1.3.0

### M1. Het scrollwiel wijzigt instellingen ongemerkt [test]

Sinds dev.16 zijn negen aan/uit-instellingen `SettingsBooleanChoice` (een `QComboBox`). Qt laat een combobox op het
wiel reageren **zonder focus**, alleen omdat de muis erboven hangt.

**Gemeten** (`wheel1326.py`): één wielstap boven "AI Meelezer gebruiken", "Geavanceerde opties", "Slimme
aanhalingstekens" en "Vandaag geschreven bijhouden". **Alle vier wisselen van waarde**, en "Opslaan" wordt actief.

Bij "AI Meelezer gebruiken" en "Geavanceerde opties" is het effect bovendien **direct zichtbaar** via
`_preview_feature_switches`: de rail verandert terwijl je alleen door de pagina scrolt. Wie daarna om een andere reden
op Opslaan klikt, legt de onbedoelde wijziging vast.

Dezelfde Qt-eigenschap geldt voor `QSpinBox`, `QDateEdit` en `QComboBox` in Boekdetails, bijvoorbeeld het woorddoel
(stappen van 1000). Dat heb ik niet apart gemeten.

**Fix (klein, centraal):** in `SettingsBooleanChoice`, en via een kleine `eventFilter`- of mixinklasse voor de overige
formuliervelden:
- `setFocusPolicy(Qt.StrongFocus)`;
- in `wheelEvent`: `event.ignore()` als `not self.hasFocus()`.

Het wiel scrollt dan gewoon de pagina.

### M2. Ghost- en editorkleuren lezen het thema uit het verkeerde profiel [test, visueel]

`ManuscriptEditor` gebruikt hardcoded `QSettings('QuietWriter','QuietWriter')`, zowel voor `_theme()` als voor de
typografie. De ghostlaag tekent met `theme['muted']` en `theme['accent']` uit die opslag.

- In het **dev-profiel** met thema Nacht tekent de ghost daardoor met de kleuren van Helder op een donkere achtergrond.
  Zie `09_ghost_Nacht.png`: grijsblauwe hulptekst, lager contrast dan bedoeld.
- Voor eindgebruikers met het stable-profiel zijn beide opslagen gelijk, dus daar treedt het niet op.
- **Waarom toch vóór 1.3.0:** de visuele acceptatie (licht/donker, contrast) gebeurt in het dev-profiel en meet daar dus
  de verkeerde kleuren.

Dit is dezelfde klasse fout als W1 en backlogpunt B5 uit dev.8. Ze is nu zichtbaar geworden door de nieuwe paintlaag.

**Fix:** geef `settings` mee aan `ManuscriptEditor`. Neem in dezelfde pass ook mee:
- `BookCover`;
- `manuscript_tree` (themakleur);
- `editor_page` (regel 273, typografie).

### M3. De lege Planning-flyout toont een groot grijs blok [visueel]

dev.26 zet titel, uitleg en "Geen planning voor dit hoofdstuk." correct bovenaan:
- titel op y=14, uitleg op y=37, lege melding op y=90–119;
- de overlay is 330×636.

Daaronder wordt `empty_filler` echter als **grijs, omkaderd vlak** getekend over bijna de volledige hoogte (zie
`01_flyout_leeg.png`). Het oogt als een lege lijst of een ladende container in plaats van "hier is niets".

**Fix:** geef de filler een transparante achtergrond (`setObjectName` plus een QSS-regel) of vervang hem door
`root.addStretch()`.

### M4. Tweede klik op de Planning-knop: op Windows controleren [inspectie]

**Offscreen gedrag** [test]:
- de tweede klik op de knop sluit de flyout correct, zowel met press → eventloop → release als met een directe klik;
- Escape sluit, en de volgende klik opent één keer;
- **een klik buiten de flyout sloot offscreen niet**. Dat is een beperking van het offscreen-platform: de
  popuprouting van Qt wordt daar niet nagebootst. Het is geen bewijs van een fout.

**Mogelijk risico op Windows** (op basis van mijn kennis van het standaardgedrag van Qt, niet gemeten):
1. Qt sluit een `Qt.Popup` bij een muisdruk erbuiten en **speelt die druk opnieuw af** op de widget eronder (standaard
   `ReplayMousePressOutsidePopup`). Die widget is hier de Planning-knop.
2. `_planning_overlay_closed` zet via `QTimer.singleShot(0)` de knop op "niet gecheckt".
3. Op Windows zit er tijd tussen press en release, dus die timer loopt vóór de release.
4. De release maakt er dan een klik van: `toggled(True)`, en de flyout **gaat weer open**.

De singleShot is bedoeld om het tegenovergestelde te voorkomen, maar kan juist dit veroorzaken.

**Controleer op Windows:** flyout open, één klik op "Planning". Hij moet dicht blijven.

**Robuuste, kleine fix**, ongeacht de uitkomst: `self.planning_overlay.setAttribute(Qt.WA_NoMouseReplay)`. Dat is
dezelfde aanpak die Qt zelf gebruikt voor combobox-popups. Een klik op de knop sluit dan alleen de popup, en de
timer houdt de knopstatus gelijk.

---

## 3. Backlog / polish

| # | Punt | Bron |
|---|---|---|
| P1 | **Scènebreuk en opmaak gaan verloren bij intern kopiëren en plakken** van een fragment met `***`. Het interne klembord bevat de juiste bron (`…\n\n***\n\n…`), maar `prepare_markdown_insertion` weigert met `UnsafeMarkdownInsertionError`. De fallback plakt dan de zichtbare platte tekst: de scènebreuk wordt een lege regel en vet/cursief verdwijnt. **Bestaand gedrag**, identiek in dev.9. Stil verlies van structuur, dus hoog op de backlog. | [test] |
| P2 | **Undo werkt per teken.** "Woord" typen en één Ctrl+Z geeft "Woor". Ook in dev.9 en mogelijk een offscreen-artefact van `QTest.keyClicks`; even controleren op Windows. Voor Planninghulp geen probleem: zodra undo het document volledig leegmaakt, komt de hulp terug [test]. | [test] |
| P3 | **Telling bij een afgekapte ghostlijst.** "… nog N meer" telt een gedeeltelijk getekende scène als niet getoond. Bij 14 scènes staat de titel "Veel 3" er wel, met "nog 12 meer" eronder. Kies tussen geen halve scène tekenen, of die scène meetellen als getoond. | [visueel] |
| P4 | **Hulptekst klopt niet met het gedrag.** De Outline-uitleg zegt "**Open** scènes kunnen in een leeg hoofdstuk als planninghulp verschijnen", maar de ghostlaag toont ook scènes met status Geschreven (met ✓). Pas óf de tekst aan, óf filter de geschreven scènes. | [inspectie, visueel] |
| P5 | **Tempo kan "ongeveer 0 per dag" zijn**, bijvoorbeeld bij nog 12 woorden over 30 dagen (`round(0,4)`). Gebruik `max(1, …)`. | [meting] |
| P6 | **`WritingProgressStore`** leest het bestand één keer en schrijft het geheel terug. Twee QuietWriter-processen op dezelfde werkmap overschrijven elkaars dagtelling (last-writer-wins). Eén proces is de normale situatie. | [inspectie] |
| P7 | **Update-check voor dev-builds.** `is_newer_version('1.3.0', '1.3.0-dev.26')` geeft `False`, dus dev-testers krijgen geen melding van de definitieve 1.3.0. Ook krijgt elke dev-build Windows-bestandsversie 1.3.0.0. | [test] |
| P8 | **Achtergebleven exportlabels** met de titel van het laatst geopende boek. Bekend punt L1 uit dev.7, ongewijzigd. | [test] |
| P9 | **Testvervuiling:** 52 cachebestanden per suiterun in `~/.qttest/share/…`. Bekend punt uit dev.9, ongewijzigd. | [test] |
| P10 | **Meervoud:** de plankkop toont "1 boeken" (`bookshelf.shelf.book_count` heeft geen enkelvoud). | [visueel] |
| P11 | **Instelling Thinking:** het label "Thinking uitschakelen" met als waarde ook "Thinking uitschakelen" is dubbelop. Bijvoorbeeld label "Thinking" met waarden "Modelstandaard" en "Uitgeschakeld". | [inspectie] |
| P12 | **`PROJECT_GUIDE.md`, statusregel:** de opsomming loopt tot dev.25; dev.26 (de compacte lege flyout) ontbreekt. | [inspectie] |

---

## 4. Testresultaten en performance

### 4.1 Regressie

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 (Linux, Python 3.13, PySide6 6.11.2) | ❌ **790 geslaagd, 2 gefaald** (B1), 304 subtests, 107 s |
| Exitcode | **139** na de suite: de bekende segfault bij Qt-teardown, ongewijzigd ten opzichte van dev.6–dev.9 en dus **geen regressie**. Let op: rc 139 maskeert de rc 1 van de twee gefaalde tests. Lees de samenvattingsregel, niet alleen de exitcode. |
| `python main.py --smoke-test` | ✅ rc 0 |
| locales | ✅ `OK: 1614 keys in 5 locales` (63 nieuwe sleutels sinds dev.9, alle 5 talen compleet) |
| undefined-names | ✅ OK |
| pyflakes | ✅ 32 meldingen, **identiek aan dev.9**; de nieuwe code levert geen meldingen op |

### 4.2 Bestaande harnassen

| Harnas | Resultaat |
|---|---|
| `demo137.py`, stable en dev-profiel | 36/37 in beide. De enige FAIL is P8 (verborgen exportlabels). |
| `demo138.py` (Presentatiemodus-foutpaden, profielscheiding) | 26/26 |
| `cache139.py` (gehashte woordtellingcache) | 25/25; tweede sessie 42 ms |

### 4.3 Nieuwe runtime-harnassen

`rt1326.py`: **49/52**. De 3 resterende punten zijn verklaard:

| Scenario | Waarom geen productfout |
|---|---|
| 5 (buiten klikken) | beperking van offscreen; zie M4 |
| 12 (undo) | undo per teken, ook in dev.9; de hulp komt terug zodra het document leeg is |
| 27 (scènebreuk plakken) | P1, ook in dev.9 |

`rt1326b.py`: bevestigt B2, M4 en P1/P2. `wheel1326.py`: bevestigt M1. `pos1326.py`: positie van de flyout.

### 4.4 Performance [meting]

| Meting | Resultaat |
|---|---|
| Viewport opnieuw tekenen, leeg hoofdstuk, 40 scènes, ghost aan | 5,9 ms |
| Idem met ghost uit | 2,1 ms |
| `refresh_chapter_context` (leest de planning van schijf) | 21,5 ms per aanroep; alleen bij hoofdstukwissel, editor tonen en opslaan van instellingen |
| Flyout openen en sluiten met 40 scènes | 111 ms |
| Woordtelling Boekenkast, tweede sessie | 42 ms |

**Geen event-loop- of paintproblemen gezien.** De ghost wordt alleen getekend bij een leeg document en hangt dus nooit
aan typen.

---

## 5. Visuele bevindingen

De screenshots zijn gemaakt in het dev-profiel, offscreen, op een gesimuleerd scherm van 1920×1080 en een venster van
1400×860.

| # | Scenario | Bevinding | Bestand |
|---|---|---|---|
| 1 | Lege flyout | ✅ titel, uitleg en melding compact bovenaan; ❌ groot grijs leeg vlak eronder (M3) | `01_flyout_leeg` |
| 2 | 1, 3 en 14 scènes | ✅ smal en hoog: 330×636, rechts onder de knop, bedekt ongeveer 35 % van de editor-viewport aan de rechterkant. Bij 14 scènes scrollbaar; bij 1 en 3 geen scrollbalk. Statusbadges en "✓ Klaar" duidelijk. | `02a/b/c_flyout_*` |
| 3–5 | Tweede klik, Escape, buiten klikken | ✅ tweede klik en Escape; buiten klikken niet offscreen te toetsen (M4) | – |
| 6–7 | Instelling Verbergen/Tonen en hoofdstuk zonder planning | ✅ knop en ghost verdwijnen en komen terug, ook via Instellingen → Opslaan. Bij een hoofdstuk zonder scènes blijft de knop staan. | – |
| 8 | Klaar/Geschreven | ✅ alleen `planning/scenes.json` wijzigt (status "geschreven"); het manuscript is byte-identiek. De Outline-badge toont "✓ Geschreven", ghost en context ook. Het werkt ook als de Planning-pagina nooit geopend is. | `08_outline_badges` |
| 9 | Licht/donker | flyout in Nacht: goed contrast, kaarten herkenbaar. Ghost in Nacht (dev-profiel): kleuren van Helder (M2). | `09_*` |
| 10, 16 | Veel scènes | ✅ "… nog 12 meer in Planning" zichtbaar; zie P3 voor de telling | `10_ghost_veel_licht` |
| 15 | Eén scène | ✅ "Locatie:" en "Personages:" op aparte regels, daarna Doel, Conflict en Uitkomst | `15_ghost_een_scene` |
| 17–18 | Personages | ✅ eerste personage automatisch geselecteerd; lijst toont alleen namen, ook bij lange rollen | `17_personages` |
| 19–20 | Status en uitleg | ✅ `SceneDialog.status` niet bewerkbaar, met "Idee / Uitgewerkt / Geschreven". De uitleg in Planning, Personages en Outline is helder; alleen P4 spreekt het gedrag tegen. | `19_outline` |
| 21–24 | Zoeken | ✅ bij 0 treffers één melding, geen "0 resultaten"; resultaatzone en "Vervangen door" blijven op exact dezelfde geometrie bij 0, 1 en weer 0 treffers, en bij vensters van 1280×700, 1000×620 en 1600×1000. Lege zone in `panel`-kleur. | `21_zoek_0`, `22_*`, `24_*` |
| 33 | Boekenkast | ✅ dunne balk en "91 van 2.500 woorden"; rustig | `33_boekenkast` |

---

## 6. Functionele scenario's uit de opdracht

| # | Scenario | Resultaat |
|---|---|---|
| 10 | Leeg hoofdstuk met scènes | ✅ toont hulp; woordtelling 0 |
| 11 | Echte tekst typen | ✅ hulp verdwijnt |
| 12 | Backspace terug naar volledig leeg | ✅ hulp komt terug |
| 12 | Undo terug naar leeg | ✅ hulp komt terug (zie P2) |
| 13 | Uniek woord dat alleen in de ghost staat | ✅ geen zoekresultaat, ook niet in scope Hele boek; het woord staat niet in `QTextDocument` of de bron |
| 14 | Opslaan, heropenen | ✅ hoofdstukbestand leeg, geen enkel `.md`-bestand bevat ghosttekst; na heropenen leeg, hulp zichtbaar, niet dirty |
| 25 | Ctrl+C/V met platte tekst | ✅ geen selectie, cursor aan het eind |
| 28 | Daarna typen | ✅ voegt toe |
| 26 | Vet en cursief | ✅ opmaak behouden, geen selectie, cursor direct achter de invoeging; aan het eind én midden in de tekst |
| 25 | Extern klembord | ✅ sterretjes ge-escaped, cursor aan het eind |
| 27 | Meerdere regels | ✅ |
| 27 | Met scènebreuk | ❌ P1 (bestaand) |
| 29 | Opt-in bij een schoon profiel | ✅ standaard uit |
| 30 | +10 opslaan, −2 opslaan, +5 opslaan | ✅ vandaag 15; de statusregel toont "Boek: 30 van 1.000 woorden · vandaag 15 · …" |
| 30 | Extern via sync binnengekomen +50 woorden (conflictdialoog → "Versie op schijf"), daarna lokaal +1 | ✅ +0: externe tekst telt niet mee. In mijn test bleef vandaag op 16; de ene lokale toegevoegde woord telde niet mee, waarschijnlijk omdat de conflictafhandeling die opslag overnam. |
| 31 | Uit, +10, aan, +1 | ✅ 16: de +10 wordt niet ingehaald |
| 32 | Versieherstel | ✅ woorddoel 2.500 en datum 2027-06-01 blijven staan (ook de suitetest) |
| 33 | Boekenkast-balk | ✅ |

**Planninghulp blijft presentation-only [inspectie]:**
- de ghost is een pure paintlaag in `paintEvent` (`_paint_planning_ghosts`) en gebruikt geen `QTextDocument`-API;
- woordtelling, zoeken (`collect_search_matches` op bron en bestand), spelling, export (leest hoofdstukbestanden),
  AI-context (leest bron en bestanden) en undo kunnen er dus structureel niet bij;
- de statusactie in de flyout schrijft uitsluitend via `planning.persist_scenes`, met de bestaande conflictafhandeling.

---

## 7. Versie-audit

| Plek | Waarde | Oordeel |
|---|---|---|
| `quietwriter/__init__.py` | `1.3.0-dev.26` | ✅ |
| `SNAPSHOT_INFO.txt` | app `1.3.0-dev.26`, stable `1.2.32` | ✅ |
| `README.md` | "Status: 1.2.32" | ✅ bewust ongewijzigd en ook inhoudelijk juist (publieke release); `README_EN.md` is niet aanwezig |
| `documents/PROJECT_GUIDE.md` | 1.2.32 publiek, dev-lijn 1.3.0-dev.26 | ✅, met de kanttekening van P12 |
| `documents/ROADMAP_AND_IDEAS.md` | 1.2.32 publiek, dev-lijn 1.3.0-dev.26 | ✅ |
| `packaging/requirements-*.lock` | "QuietWriter 1.3.0 … lock" | ✅ (de B6-kanttekening uit dev.8 is opgelost) |
| `packaging/make_version_info.py` | leidt de versie af van `__version__` | ✅ (zie P7 voor de numerieke bestandsversie) |
| Release notes, changelog en reviews | historische nummers | buiten scope, correct |

**Geen verouderde actuele verwijzingen gevonden**, behalve P12.

---

## 8. Niet getest / beperkingen

- **Popuprouting van Qt.Popup:** een klik buiten de flyout, en het opnieuw afspelen van een muisdruk op de knop. Het
  offscreen-platform bootst dit niet na (M4).
- **Plakken vanuit Word of de browser** (HTML-klembord). Alleen het interne QuietWriter-formaat en platte tekst zijn
  getest.
- **AI-context met een echt model en exportbestanden** (PDF/EPUB/DOCX) met een leeg hoofdstuk. Beide zijn alleen
  structureel beoordeeld (export en AI lezen hoofdstukbestanden of bron; de ghost zit daar aantoonbaar niet in), niet
  end-to-end gedraaid.
- **Spellingsonderstreping onder de ghostlaag.** Er is geen documenttekst om te controleren; alleen structureel
  beoordeeld.
- **Schermlezer**: wat er bij Planninghulp wordt voorgelezen (verwachting: niets, want het is een paintlaag).
- **Twee QuietWriter-processen** die tegelijk de dagtelling bijwerken (P6). Alleen geïnspecteerd.

---

### Bijlage: harnassen en screenshots

| Bestand | Inhoud |
|---|---|
| `rt1326.py` | Alle 33 scenario's plus een extra controle op het scrollwiel, met screenshots. Aanroep: `python3 rt1326.py <zip-pad> <uitvoermap>`. Voor de juiste flyoutpositie offscreen: `QT_QPA_PLATFORM="offscreen:configfile=screen1080.json"` met een scherm van 1920×1080. |
| `rt1326b.py` | B2 in beide richtingen, popuprouting op vensterniveau, scènebreuk-plakken, undo |
| `wheel1326.py` | M1 |
| `pos1326.py` | Flyoutgeometrie per venstergrootte |
| `perf1326.py` | Metingen van §4.4 |
| `shots26/*.png` | Screenshots uit §5 |
