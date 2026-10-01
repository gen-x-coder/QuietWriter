# QuietWriter: reviewronde 43 (versie 0.34.7: hoofdstukplanning expliciet naar de AI)

**Gelezen:**
- de diffs van `ai/prompting.py` (de sectie `PLANNING VAN HET HUIDIGE HOOFDSTUK` en de nieuwe instructie) en `ai/ui.py`
  (checkbox, instelling `ai_use_chapter_planning`, `_active_chapter_planning_text`, `send`);
- `REVIEW_NOTES_0347.md`.

Er is maar één aanroeper van `_continue_send`, dus snelacties en andere routes gaan allemaal via dezelfde `send()`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Een nep-provider onderschept de echte `build_system_prompt`.
Unieke markeringen in de Planning (`AUTO_SYNOPSIS_0347`, `AUTO_DOEL_0347`, `AUTO_DOEL_CH2`, `MANUAL_DOEL`) laten zien in
welke sectie van de prompt welke tekst terechtkomt. Herstarts heb ik nagebootst met een nieuw `MainWindow` op hetzelfde
ini-bestand.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Suites

| Suite | Resultaat |
|---|---|
| `pytest` (current) met PySide6 | ✅ **215 geslaagd** |
| `pytest tests/legacy` | ✅ 449 geslaagd, 280 subtests; alleen de 2 fonttests falen |
| Koude start | ✅ |

## Runtime: 18/18 groen

| # | Check | Resultaat |
|---|---|---|
| 1 | Hoofdstuk met scènes: checkbox actief en standaard aangevinkt | ✅ |
| 1 | Samenvatting | ✅ `… · wordt meegestuurd` |
| 2 | "Context bekijken" | ✅ `Planning van huidig hoofdstuk — wordt meegestuurd:`, met de markeringen van dit hoofdstuk en niet die van hoofdstuk 2 |
| 3 | **Aan, nep-provider** | ✅ `AUTO_SYNOPSIS_0347` en `AUTO_DOEL_0347` staan onder **PLANNING VAN HET HUIDIGE HOOFDSTUK**; de handmatige scène (`MANUAL_DOEL`) staat alleen onder **GESELECTEERDE PLANNINGCONTEXT**; de twee bronnen lopen niet door elkaar |
| 4 | **Uit**, nieuwe vraag | ✅ **geen enkele `AUTO_`-markering** in de prompt, de sectie toont `[niet meegestuurd]`, de handmatige selectie staat er nog |
| 4 | Samenvatting en dialoog bij uit | ✅ `niet meegestuurd` / `wordt niet meegestuurd` |
| 5 | Uit blijft uit na hoofdstukwissel, paneel dicht/open en **herstart** | ✅ |
| 5 | Weer aan → herstart | ✅ blijft aan |
| 6 | Wisselen van hoofdstuk | ✅ de prompt bevat nu de planning van hoofdstuk 2 en niet meer die van hoofdstuk 1 |
| 7 | Hoofdstuk zonder scènes | ✅ checkbox uitgeschakeld (blijft wel aangevinkt), AI-vraag gaat door met `[niet meegestuurd]` |
| 8 | v1 kapot, v2 nieuwer, **BOM plus v2** | ✅ checkbox uit, reden zichtbaar, voorkeur blijft "aan", AI-vraag gaat door, bytes identiek |
| 8 | Planning hersteld | ✅ checkbox meteen weer actief en nog steeds aangevinkt |
| 9 | Boekenplank | ✅ "Planning-context…" en de checkbox staan uit; de voorkeur is niet overschreven (het punt uit ronde 42 is opgelost) |
| 10 | Geen writes | ✅ `planning/` byte-identiek na alle previews, toggles en AI-vragen |

**Regressie:** AI- en History-failsafe (7/7), hoofdstukcontext en railselectie 20/20, separator-regel, editorbron,
publicatie, rondes 12–24, backend 47/15/8 ✅.

Mijn oude scripts uit rondes 40 en 41 controleerden "de preview staat **niet** in de prompt". Die falen nu, maar dat is
precies de bedoelde verandering: bij "aan" moet de preview er juist wel in staan. De controle van ronde 42 op dubbele tekst
reageert op het woord "Planning" in "Planning niet beschikbaar — Planning kan niet…". Dat is correcte tekst; mijn controle
was te streng.

---

## Twee ontwerpkeuzes om bewust te bevestigen (geen bugs)

### 1. Standaard aan betekent dat na de update ongemerkt meer gegevens meegaan

Bestaande gebruikers hebben de instelling `ai_use_chapter_planning` nog niet. De standaardwaarde is `True`, dus direct na de
update gaat bij elke AI-vraag de volledige opgeslagen hoofdstukplanning mee: synopsis, doel, conflict, uitkomst, notities
en personages.

De samenvatting in het AI-paneel zegt dat wel ("wordt meegestuurd"). Maar in rondes 34 en 35 hebben we bij persona,
profiel en geheugen bewust expliciet gemaakt dat die gegevens bij een externe provider de computer verlaten. Hier gaat het
om een nieuwe categorie gegevens die standaard mee gaat.

Twee lichte opties, afhankelijk van wat Lucas wil:
- Standaard aan laten, maar bij de **eerste** keer (instelling nog niet gezet) een eenmalige, rustige melding tonen in het
  AI-paneel: "Nieuw: de Planning van dit hoofdstuk wordt nu meegestuurd. Uitzetten kan hier."
- Of standaard aan alleen bij een lokale provider (Ollama), en standaard uit bij een externe provider (OpenRouter).

### 2. Geen lengtegrens op de hoofdstukplanning

De hoofdstukplanning gaat onbegrensd mee. Notities of synopses bij scènes kunnen lang worden, zeker als iemand Planning als
kladblok gebruikt. Bij kleine lokale modellen gaat dat ten koste van de ruimte voor de manuscripttekst.

Een ruime grens (bijvoorbeeld een paar duizend tekens), met in de preview een melding als de tekst is ingekort, voorkomt
dat. Nu niet nodig, wel iets voor een latere slice.

## Conclusie

0.34.7 is groen. De schakelaar doet precies wat hij belooft: bij aan staat de hoofdstukplanning aantoonbaar in een eigen
sectie van de prompt, bij uit aantoonbaar niet. De handmatige Planning-context blijft daar apart van. De voorkeur blijft
bewaard over wissels en herstarts, en wordt niet overschreven als de Planning tijdelijk onbeschikbaar is. Er wordt niets
naar Planning geschreven.

Wat overblijft zijn twee keuzes voor Lucas: moet "standaard aan" ook gelden voor bestaande gebruikers en voor externe
providers, en wil je later een lengtegrens?

**Niet kunnen testen:** een echte AI-provider (nagebootst met een nep-provider), echte Windows DPI-schaling en echte
Dropbox-timing.
