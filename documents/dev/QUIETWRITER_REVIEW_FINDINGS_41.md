# QuietWriter: reviewronde 41 (versie 0.34.5: knop "Planning-context", foutteksten, compacte preview, responsieve divider)

**Gelezen:**
- de diffs van `ai/ui.py` (`has_book` via `self.store`, `_compact_planning_display`), `ai/planning_context.py`
  (foutteksten zonder prefix) en `main_window.py` (`_program_separator_needed`, koppeling aan `rangeChanged`);
- `REVIEW_NOTES_0345.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless) met het echte stylesheet. Een nep-provider onderschept
de systeemprompt. Voor de divider heb ik de vensterhoogte stapsgewijs van 1000 naar 430 px laten zakken.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Suites

| Suite | Resultaat |
|---|---|
| `pytest` (current) met PySide6 | **209 geslaagd, 1 failure**: `test_review_0345_qt.py::test_planning_context_button_enabled_after_real_open_book_route` (zie punt 1) |
| `pytest tests/legacy` | ✅ 449 geslaagd, 280 subtests; alleen de 2 fonttests falen |
| Koude start | ✅ |

---

## Productgedrag: groen

### A. Knop "Planning-context…" via de echte route

| Stap | Knop actief |
|---|---|
| Boek openen via de boekenplank-signaal, AI-paneel open | ✅ |
| Klikken → de dialoog opent echt, met Anna en "Aankomst" als opties | ✅ |
| Wisselen van hoofdstuk | ✅ |
| AI-paneel dicht en weer open | ✅ |
| Nieuw gesprek | ✅ |
| Boekenplank → opnieuw openen | ✅ |
| Planning → Inhoud | ✅ |

### B. Foutstatus bij een kapotte v1 en een nieuwere v2

| Plek | v1 kapot | v2 nieuwer |
|---|---|---|
| Contextknop | `Context · Planning niet beschikbaar` | idem |
| Tooltip | `Huidig hoofdstuk · Planning kan niet betrouwbaar worden gelezen.` | `… · Gemaakt met een nieuwere QuietWriter. Werk QuietWriter bij.` |
| Hoofdstukregel | `Planning van dit hoofdstuk: niet beschikbaar — Planning kan niet betrouwbaar worden gelezen.` | idem, met de v2-tekst |
| Dialoog | de reden staat er één keer | idem |
| Dubbele "niet beschikbaar: … niet beschikbaar" | ✅ nergens | ✅ nergens |
| AI-vraag | ✅ gaat door, `planning_text=''` | ✅ |
| Selectie blijft staan | ✅ | ✅ |

### C. "Context bekijken"

- ✅ Binnen één scène staan `- Status`, `- Synopsis`, `- Doel`, `- Conflict`, `- Uitkomst`, `- Notities` en
  `- Personages` direct onder elkaar. Tussen scènes en secties blijft er lucht.
- ✅ Het compacter maken geldt **alleen voor de weergave**: de `planning_text` voor de prompt heeft nog het oude format.
- ✅ Met de nep-provider komt geen van de vijf unieke preview-markeringen in de systeemprompt. De handmatige selectie
  (Ruzie, D2) staat er wel in.

### D. Divider vóór PROGRAMMA (ingeklapte rail, stapjes van 2 px van 1000 naar 430 px hoog)

| Situatie | Resultaat |
|---|---|
| Helder, AI en Geavanceerd aan | ✅ geen lijn op 1000 px; de lijn verschijnt precies bij **768 px**, wanneer het middendeel gaat scrollen (max 18); daarna stabiel |
| Helder, AI en Geavanceerd uit | ✅ de lijn verschijnt pas bij 536 px (minder items) |
| Nacht | ✅ exact hetzelfde gedrag |
| Knipperen of heen-en-weer springen rond de grens | ✅ geen enkele keer; de lijn volgt steeds het scrollgedrag |
| Alle 16 toestanden × 2 hoogtes | ✅ HUIDIG BOEK en AI-CONTEXT kloppen, de PROGRAMMA-lijn alleen bij scrollen |
| Uitgeklapte rail | ✅ geen separators |

Een terugkoppeling tussen de lijn en het scrollgebied kan ook niet ontstaan. De lijn zit buiten het scrollgebied, dus als
hij verschijnt, wordt het scrollgebied alleen maar kleiner. Daardoor blijft de toestand stabiel. (Zie
`r41_rail_700_dicht.png`, 2× vergroot.)

**Voor Lucas:** op **1366×768** met de rail ingeklapt en alles aan zit je precies op de grens: daar staat de lijn er net
wel. Kijk op je eigen laptop of dat natuurlijk voelt.

### E. Regressie

✅ Transparantie uit 0.34.4 (6/6), AI- en History-failsafe uit 0.34.3 (7/7), Planning corrupt/nieuwer/BOM, hoofdstukcontext
en railselectie 20/20, statusbalk inclusief enkelvoud, editorbron, publicatie, rondes 12–24, backend 47/15/8.

(Mijn oude railmatrix verwachtte altijd een PROGRAMMA-lijn in de ingeklapte rail. Die verwachting heb ik vervangen door de
nieuwe regel hierboven.)

---

## 1. 🟡 De nieuwe Qt-test in `current` faalt met echte PySide6

`test_planning_context_button_enabled_after_real_open_book_route` verwacht dat de knop **vóór** het openen van een boek
uit staat. In werkelijkheid staat hij bij een koude start aan: `store=None`, maar `isEnabled()=True`.

`_update_busy_buttons()` wordt in `AIPanel.__init__` namelijk nooit aangeroepen, dus de knop houdt de standaardwaarde van
Qt. Dat was in 0.34.4 ook al zo; ik had toen alleen de toestand na het openen gemeten.

In de echte UI maakt het niets uit: zonder boek is het AI-paneel niet te zien, en `_choose_planning_context()` stopt meteen
als er geen boek is. Maar de actuele suite is hierdoor rood, en het is weer een Qt-test die in jouw omgeving wordt
overgeslagen.

**Fix (één regel, in de app):** roep aan het eind van `AIPanel.__init__` `self._update_busy_buttons()` aan, of zet de knop
daar op `setEnabled(False)`. Dan is ook de begintoestand consistent en slaagt de test zoals hij geschreven is.

## Kleine opmerking

- **Contextstukken in het gesprek:** bij een Planning-fout staat daar nu alleen de kale reden, bijvoorbeeld "Gemaakt met
  een nieuwere QuietWriter. Werk QuietWriter bij.", zonder dat erbij staat dat het om Planning gaat. In de knop, de tooltip
  en de hoofdstukregel is de context wel duidelijk. Voor het gesprek zou "Planning niet beschikbaar — …" iets duidelijker
  zijn. Dit is puur cosmetisch.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | Knop "Planning-context" via de echte route, foutteksten zonder dubbeling, compacte preview (alleen weergave), preview niet in de prompt, responsieve divider zonder knipperen | ✅ | — |
| 1 | Nieuwe Qt-test faalt: de knop staat bij een koude start aan, omdat `_update_busy_buttons` niet in `__init__` wordt aangeroepen | 🟡 | Alleen de suite en de begintoestand; geen zichtbaar effect |

**Conclusie:** 0.34.5 lost het punt uit ronde 40 op. De handmatige Planning-context is weer bereikbaar via de echte route
en blijft dat ook. De UX-restpunten zijn netjes afgerond en de responsieve divider werkt stabiel. Alleen de nieuwe
Qt-test is rood, en dat lost één regel in `AIPanel.__init__` op.

**Niet kunnen testen:**
- een echte AI-provider (nagebootst);
- echte Windows DPI-schaling;
- echte Dropbox-timing.
