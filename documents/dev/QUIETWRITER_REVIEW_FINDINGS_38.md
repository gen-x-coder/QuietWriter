# QuietWriter: reviewronde 38 (versie 0.34.2: nieuwere Planning-versie, gecombineerde statusbalk, testindeling)

**Gelezen:**
- `planning_validation.py`;
- de diffs van `planning_storage.py`, `integrity.py`, de Planning-pagina's, `chapter_context_panel.py`, `editor_page.py`
  en `main_window.py`;
- `REVIEW_NOTES_0342.md`.

Daarnaast heb ik alle plekken nagelopen die `load_scenes` en `load_characters` aanroepen.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless) met het echte stylesheet, een echte start via `main.py`,
en een vergelijking met 0.34.0 en 0.34.1 waar dat nodig was.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

**Kleine correctie op de toelichting:** het punt over de woordentelling kwam niet van mij. Dat was jouw eigen observatie,
Lucas.

## Suites: allebei groen

| Suite | Resultaat |
|---|---|
| `pytest` (current, 44 bestanden) | ✅ **196 geslaagd**, 0 failures (inclusief de separatortest die in ronde 37 faalde) |
| `pytest tests/legacy` | ✅ 449 geslaagd, 280 subtests; alleen de 2 fonttests falen (de Planning-nepobjecten werken weer) |
| Een bestand in zowel `current` als `legacy` | geen ✅ |
| Beleid voor minor-releases in `tests/README.md` | ✅ ("bij elke nieuwe minor-release … volledige legacy-suite groen") |
| Koude start via `main.py` | ✅ |

---

## Productgedrag

### B. Planning: corrupt versus nieuwer (voor `outline.json` en `characters.json`)

Opzet: eerst een geldige v1 met een handmatige History-versie, daarna schrijft "de andere computer" een nieuwer of kapot
bestand.

| Geval | Boek opent | In dit hoofdstuk | Planning | Integriteit | Herstel | Live bytes |
|---|---|---|---|---|---|---|
| v1 `scenes: 5`, `character_ids: null`, `relations: 5` | ✅ | "kan niet betrouwbaar worden gelezen" | alleen-lezen | `aux_json_invalid`, herstelbaar | ✅ zet v1 terug (bedoeld) | pas na bewust herstel gewijzigd |
| **v2** outline | ✅ | "gemaakt met een nieuwere QuietWriter. Werk QuietWriter bij" | "…alleen-lezen. Werk QuietWriter bij; herstel het bestand niet naar een oudere versie." | `aux_json_newer`, `recoverable=False` | ✅ **knop uit**, ook met een geldige v1 in History | ✅ byte-identiek |
| **v2** characters | ✅ | idem | idem | idem | ✅ knop uit | ✅ byte-identiek |

✅ Opslag en Integriteit gebruiken nu allebei `validate_planning_payload()`; de dubbele implementatie is weg.

### A. Statusbalk

| Check | Resultaat |
|---|---|
| Twee hoofdstukken (5 en 1.234 woorden) | ✅ `Boek: 1.239 woorden · Hoofdstuk 1 van 2: 5 woorden` |
| Geen losse "Boek bevat …" meer onder de boom | ✅ (het widget is weg) |
| Typen | ✅ allebei +1 (1.240 / 6) |
| Wisselen van hoofdstuk | ✅ `Hoofdstuk 2 van 2: 1.234 woorden`, boektotaal klopt |
| Tijdelijke melding | ✅ de telling komt terug |
| Planning, Boekenplank, Voorwoord | ✅ geen verouderde hoofdstukstatus (bij Voorwoord blijft de balk leeg) |

**Klein tekstpunt:** bij precies één woord staat er `Hoofdstuk 1 van 2: 1 woorden`. Maak daar `1 woord` van, en ook voor
het boektotaal.

### D. Visueel

- **Uitlijning in "In dit hoofdstuk":** de labels zelf beginnen allemaal op x=11. Toch staan de vetgedrukte koppen
  ("Aankomst", "Doel", "Conflict", "Personages", "Scènes") zichtbaar **ongeveer 4 px verder naar rechts** dan de tekst
  eronder (zie `r38_context_zoom.png`, 2× vergroot).

  De oorzaak is een bekende eigenaardigheid van Qt. Zodra een QSS-regel een box-eigenschap zet, zoals `margin-top: 3px` bij
  `subsectionTitle` en `contextFieldLabel`, krijgt het QLabel een frame. Met de standaard `indent=-1` rekent Qt dan een
  inspringing van ongeveer een halve "x"-breedte.

  **Fix:** voeg `qproperty-indent: 0;` toe aan beide QSS-regels, of roep `label.setIndent(0)` aan.
- **Separators:** de code en de kleuren zijn niet gewijzigd, dus mijn metingen uit ronde 37 gelden nog: echt 1 px en
  subtiel, met een contrast van ongeveer 1,15–1,35:1. Of dat genoeg is, is aan jou.

### Smoke-regressie

✅ "In dit hoofdstuk" en de railselectie 20/20, railmatrix 26/26, editorbron 8/8, publicatie 18/18, notities,
scène/afbeelding, de rondes 12–24 op hun basislijn, randgeval ronde 24, herkomst, backend 47/15/8.

Mijn oude script uit ronde 19 leest nog het verwijderde `book_words`-label; dat is een artefact van mijn script, want de
productcode verwijst er nergens meer naar.

---

## 1. 🟡 De AI-functie "Planning-context" vangt corrupte of nieuwere Planning niet af

Er zijn twee aanroepers van `load_scenes` en `load_characters` die geen van beide uitzonderingen afvangen:
`ai/planning_context.options_for_book` en `ai/planning_context.build_planning_context`. Die worden gebruikt door de
bestaande AI-functie waarin je zelf personages of scènes als context kiest (de dialoog "Planning-context" en de
samenvattingsregel in het AI-paneel).

**Runtime:** stel dat er al een Planning-selectie is gekozen en Dropbox brengt daarna een kapot of nieuwer `outline.json`
binnen:

| Aanroep | 0.34.0 | 0.34.1 | 0.34.2 |
|---|---|---|---|
| samenvatting verversen (`_refresh_idle_context_summary`) | v1-structuurfout: `TypeError`; v2: OK (werd genegeerd) | beide: `CorruptSourceError` | v1: `CorruptSourceError`, v2: **`FuturePlanningFormatError`** |
| Planning-context voor een AI-vraag (`_planning_context`) | idem | idem | idem |
| de dialoog "Planning-context" openen | idem | idem | idem |

Al die aanroepen lopen via slots van knoppen of events. De exceptie verdwijnt dus in de Qt-eventloop:
- de dialoog opent niet;
- de samenvatting ververst niet;
- een AI-vraag met een Planning-selectie gaat stil niet door.

De v1-structuurfout bestond al. Het v2-geval is nieuw sinds 0.34.1: in 0.34.0 werd de versie gewoon genegeerd.

**Fix:** laat `options_for_book` en `build_planning_context` allebei `CorruptSourceError` en `FuturePlanningFormatError`
afvangen. Geef dan lege opties terug met een korte melding ("Planning-context niet beschikbaar: …"), zodat de AI-vraag
zonder Planning doorgaat en de gebruiker ziet waarom. Voeg een test toe aan `current` met een actieve selectie en de v1- en
v2-bestanden.

## 2. 🟡 Het herstellen van een volledige versie uit History draait een nieuwere Planning alsnog terug

Integriteit weigert nu terecht om een v2-Planning terug te zetten. Maar de andere herstelroute doet het wel: **Versiegeschiedenis → "Deze versie
herstellen"**.

**Runtime:** eerst v1 "OUD" met een handmatige versie, daarna schrijft de andere computer v2 "NIEUW V2", daarna
geschiedenis → herstellen. Daarna is `outline.json` **weer v1**. Er komt geen extra melding; alleen de gewone bevestiging
"Wil je deze versie herstellen?".

Het is een bewuste actie van de gebruiker, en de huidige stand wordt eerst veiliggesteld, dus het is terug te halen. Maar
de gebruiker weet op dat moment niet dat de Planning uit een nieuwere versie komt. Het effect is hetzelfde als de fout die
0.34.2 voor Integriteit oplost, en Dropbox verspreidt de terugzetting.

**Fix (klein):** laat `restore_version` Planning-bestanden overslaan waarvan de live versie
`FuturePlanningFormatError` geeft, en meld dat ("Planning is gemaakt met een nieuwere QuietWriter en is niet
teruggezet"). Of weiger het herstel met dezelfde tekst. Voeg ook hiervoor een test toe aan `current`.

---

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | Nieuwere Planning alleen-lezen en niet herstelbaar via Integriteit; één centrale validatie; gecombineerde statusbalk; beide suites groen | ✅ | — |
| 1 | De AI-functie "Planning-context" vangt corrupte of nieuwere Planning niet af: dialoog, samenvatting en AI-vraag falen stil | 🟡 | Alleen met een gekozen Planning-selectie; v2-geval nieuw sinds 0.34.1 |
| 2 | Het herstellen van een versie uit History zet een nieuwere Planning terug naar v1 | 🟡 | Bewuste actie, wel terug te halen; zelfde klasse als de Integriteit-fix |
| — | Koppen in "In dit hoofdstuk" staan 4 px ingesprongen (Qt-`indent`); `1 woorden` | tekst en visueel | één QSS-regel en één meervoudsvorm |

**Conclusie:** 0.34.2 lost het hoofdpunt uit ronde 37 correct op. Beide testsuites zijn voor het eerst echt groen met
PySide6. Met punt 1 en 2 is de klasse "nieuwere Planning wordt nooit teruggedraaid en blokkeert niets" langs álle routes
dicht: Integriteit, History, AI en het paneel. Daarna kan het Planning-schema veilig worden uitgebreid.

**Niet kunnen testen:**
- echte Windows DPI-schaling;
- de ophaalroute van AI-modellen;
- echte Dropbox-timing.
