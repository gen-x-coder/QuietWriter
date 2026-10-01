# QuietWriter: reviewronde 39 (versie 0.34.3: AI Planning-context, History-guard, divider, uitlijning, enkelvoud)

**Gelezen:**
- de diffs van `ai/planning_context.py`, `ai/ui.py`, `planning_context_dialog.py`,
  `storage.py` (`_guard_future_planning_before_restore`), `editor_page.py` en `themes.py`;
- `REVIEW_NOTES_0343.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless) met het echte stylesheet. Pixels heb ik gemeten voor de
separators en de uitlijning. Verder heb ik de echte AI-verzendroute nagebootst met een nep-provider, zodat ik de
systeemprompt kon onderscheppen.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Resultaat: groen, geen nieuwe bevindingen

### Verplicht eerst

| Check | Resultaat |
|---|---|
| `pytest` (current) met PySide6 | ✅ **200 geslaagd**, 0 failures |
| `pytest tests/legacy` | ✅ 449 geslaagd, 280 subtests; alleen de 2 fonttests falen |
| Koude start via `python main.py` | ✅ |

### A. AI Planning-context bij een onbetrouwbare Planning

Opzet: eerst een Planning-selectie kiezen (Anna, scène s1), daarna vervangt "Dropbox" een Planning-bestand.

| Check | v1-structuurfout outline | v2 outline | v2 characters |
|---|---|---|---|
| Samenvatting ververst zonder exceptie | ✅ | ✅ | ✅ |
| Contextknop | ✅ `Context · aangepast` → `Context · Planning niet beschikbaar` | ✅ | ✅ |
| Reden | ✅ "kan niet betrouwbaar worden gelezen" | ✅ "gemaakt met een nieuwere QuietWriter. Werk QuietWriter bij." | ✅ idem |
| Dialoog opent en toont de reden; Opslaan staat uit | ✅ | ✅ | ✅ |
| Bestaande selectie blijft staan (`['c1'], ['s1']`) | ✅ | ✅ | ✅ |
| Manuscriptcontext intact | ✅ | ✅ | ✅ |
| Planning-bytes identiek | ✅ | ✅ | ✅ |

**De echte `send()`** (met een nep-provider, v2 outline en een actieve selectie): de systeemprompt wordt opgebouwd met
`planning_text=''` en de manuscripttekst zit er gewoon in. Er is geen exceptie. De AI-vraag gaat dus door zonder
Planning-context. ✅

### B. History en een nieuwere Planning

| Check | v2 `outline.json` | v2 `characters.json` |
|---|---|---|
| "Deze versie herstellen" | ✅ geweigerd: "Versie niet hersteld … Werk QuietWriter bij" | ✅ |
| Wijzigingen in de hele boekmap (hoofdstukken, manifest, Planning, publicatie, AI, assets) | ✅ **0 bestanden** | ✅ 0 |
| Aantal versies (geen onnodige `pre_restore`) | ✅ 1 → 1 | ✅ 1 → 1 |
| Editor | ✅ blijft "Versie B"; het voorbeeld is netjes afgesloten | ✅ |
| Kapotte v1-Planning via History terugzetten | ✅ nog steeds mogelijk ("OUD" teruggezet) | — |

De guard staat vóór `verify_book_unchanged` en vóór `create_version('pre_restore')`. Dat is de juiste volgorde.

### C. Visueel

**Separators in de ingeklapte rail** (pixels op het midden van de lijn, zie `r39_separators.png`: Helder, Nacht en
Aurora, 2× vergroot):

| Thema | Inhoud | Pixel erboven · 2 lijnpixels · pixel eronder |
|---|---|---|
| Helder | ✅ 2 px | `#eef1f4` · **`#dce1e6` `#dce1e6`** · `#eef1f4` |
| Nacht | ✅ 2 px | `#292d33` · **`#353a42` `#353a42`** · `#292d33` |
| Aurora | ✅ 2 px | `#3b4252` · **`#4c566a` `#4c566a`** · `#3b4252` |

- In de uitgeklapte rail zijn er geen separators (railmatrix 26/26).
- Het kleurcontrast is hetzelfde gebleven (1,15–1,35:1), maar de lijn is twee keer zo dik. Of dat nu "duidelijk genoeg"
  is, beoordeel jij op je eigen scherm.

**Uitlijning in "In dit hoofdstuk"**: de eerste zichtbare pixel per label, binnen een scènekaart:

| Label | x |
|---|---|
| Aankomst · Anna arriveert. · Alles is vol · Ze slaapt bij Bram | 1045 |
| concept · Station · Doel · Een kamer vinden · Conflict · Uitkomst · Notities · Regen · Personages: Anna | 1046 |

Het verschil van 1 px komt alleen van de vorm van de letters (de beginstreep van "A" tegenover "D", "E" of "c"). De
inspringing van 4 px is weg (zie `r39_context_zoom.png`). ✅

**Enkelvoud en meervoud:**

| Tekst | Statusbalk |
|---|---|
| leeg | ✅ `Boek: 0 woorden · Hoofdstuk 1 van 1: 0 woorden` |
| "Een" | ✅ `Boek: 1 woord · Hoofdstuk 1 van 1: 1 woord` |
| "Een twee" | ✅ `Boek: 2 woorden · Hoofdstuk 1 van 1: 2 woorden` |

### D. Regressie

✅ Nieuwere en kapotte Planning met Integriteit (5 vormen, zoals in ronde 38), hoofdstukcontext en railselectie 20/20,
railmatrix 26/26, editorbron 8/8, publicatie 18/18, notities, scène/afbeelding, History-voorbeeld, transactionele adopt
(ronde 24: 10/10), rondes 12–24 op hun basislijn, randgeval ronde 24, herkomst, backend 47/15/8.

---

## Kleine opmerkingen (geen actie nodig)

- **Label in de gespreksgegevens:** bij een AI-vraag zonder beschikbare Planning komt er in de contextstukken van dat
  bericht "Planning: Planning-context niet beschikbaar: …" te staan. Dat woord staat er dubbel, maar het is wel transparant.
  Oppoetsen kan later.
- **Tekstvergelijking:** `planning_unavailable` wordt bepaald met `labels[0].startswith('Planning-context niet
  beschikbaar:')`. Zodra die tekst vertaald wordt (`en.json`), werkt die controle niet meer. Een expliciet veld, zoals
  `PlanningOptions.error` dat al is, is robuuster. Voor later.
- **BOM in een v2-Planning:** een v2-bestand dat met een UTF-8-BOM is opgeslagen, wordt door de History-guard als "kapot"
  gelezen en niet als "nieuwer". Herstel wordt dan niet tegengehouden. QuietWriter schrijft zelf nooit een BOM, dus dit
  speelt alleen als een ander programma het bestand heeft bewerkt. `encoding='utf-8-sig'` in de guard, in `_read_json`
  en in Integriteit sluit het af.

## Conclusie

0.34.3 is groen. De regel "een nieuwere Planning wordt nooit teruggedraaid en blokkeert niets" geldt nu langs alle vier
de routes: Integriteit, History, AI Planning-context en "In dit hoofdstuk". Daarmee is het Planning-schema klaar om
uitgebreid te worden. De visuele punten uit rondes 37 en 38 zijn opgelost. Wat mij betreft kan 0.34 door naar de volgende
slice.

**Niet kunnen testen:**
- echte Windows DPI-schaling;
- een echte AI-provider (nagebootst met een nep-provider om de systeemprompt te controleren);
- echte Dropbox-timing.
