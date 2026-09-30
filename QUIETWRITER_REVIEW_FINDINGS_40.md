# QuietWriter: reviewronde 40 (versie 0.34.4: transparante hoofdstukplanning in de AI-context)

**Gelezen:**
- de diffs van `ai/planning_context.py` (`PlanningContextResult`, `chapter_planning_preview`) en `ai/ui.py`
  (samenvatting, "Context bekijken", `send`);
- de overstap naar `utf-8-sig` in `planning_storage.py`, `integrity.py`, `storage.py` en `chapter_context_panel.py`;
- `REVIEW_NOTES_0344.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Een nep-provider met onderschepte `build_system_prompt`
laat zien wat er echt naar de AI gaat. In de Planning-velden staan unieke markeringen (`SYNOPSIS_UNIEK_1`,
`DOEL_UNIEK_1` enzovoort), zodat ik kan zien waar welke tekst terechtkomt.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Suites

| Suite | Resultaat |
|---|---|
| `pytest` (current) met PySide6 | ✅ **204 geslaagd** |
| `pytest tests/legacy` | ✅ 449 geslaagd, 280 subtests; alleen de 2 fonttests falen |
| Koude start | ✅ |

---

## REVIEW_NOTES_0344: alles groen

| # | Check | Resultaat |
|---|---|---|
| 3 | Samenvatting bij 2 scènes / 2 personages | ✅ `Altijd meegestuurd: Schrijverspersona · Boekprofiel · Boekgeheugen` en `Planning van dit hoofdstuk: 2 scènes · 2 personages · nog niet automatisch meegestuurd` |
| 3 | Wisselen van hoofdstuk | ✅ `1 scène · 1 personage` (enkelvoud correct) |
| 4 | "Context bekijken" | ✅ vaste context, manuscriptcontext, de **apart** getoonde geselecteerde Planning-context (Cees, "Elders" uit een ander hoofdstuk), daarna de preview met status, locatie, synopsis, doel, conflict, uitkomst, notities en personages; het verweesde id `zz` is weg |
| 5 | **Nep-provider, normale AI-vraag met een handmatige selectie** | ✅ **geen van de vijf unieke preview-markeringen in de systeemprompt**; de handmatige selectie (Cees, `DOEL_ELDERS`) staat wel onder `GESELECTEERDE PLANNINGCONTEXT` |
| 5 | Nep-provider zonder selectie | ✅ geen Planning in de prompt; `[geen Planning-context geselecteerd]` |
| 6 | v1 kapot en v2 nieuwer | ✅ knop `Context · Planning niet beschikbaar`, de dialoog werkt, de AI-vraag gaat door met `planning_text=''`, geen exceptie |
| 6 | Dubbele tekst "Planning: Planning-context …" | ✅ weg |
| 7 | BOM plus v2 `outline.json` | ✅ PlanningStore geeft `FuturePlanningFormatError`, Integriteit `aux_json_newer` (niet herstelbaar), History-guard blokkeert |
| 7 | BOM plus v2 `characters.json` | ✅ idem |
| 7 | BOM plus **geldige v1** | ✅ gewoon leesbaar, geen melding in Integriteit, de guard laat door |
| 12 | Geen writes of schemawijzigingen | ✅ `planning/` byte-identiek na alle AI- en preview-acties |
| — | Regressie: AI-failsafe en History-guard 0.34.3 (7/7), Planning corrupt of nieuwer (5 vormen), In dit hoofdstuk en railselectie 20/20, railmatrix 26/26, editorbron, publicatie, rondes 12–24, backend | ✅ |

---

## 1. 🟡 De knop "Planning-context…" staat sinds 0.31.2 altijd uit na het openen van een boek

**Eerdere bevinding, door mij gemist sinds ronde 21.** In mijn eerdere tests zette ik de selectie rechtstreeks in de code,
en niet via de knop. Pas in de schermafbeelding van deze ronde zag ik dat de knop grijs is (`r40_ai_context.png`).

**Runtime:** boek openen → AI-paneel → `planning_context_button.isEnabled()` is **False**. Hij blijft ook uit na:
- opnieuw openen;
- een hoofdstukwissel;
- het AI-paneel dicht en weer open doen;
- "Nieuw gesprek";
- de contextknop.

| Versie | Knop aan na het openen |
|---|---|
| 0.31.0, 0.31.1 | ✅ True |
| 0.31.2 t/m 0.34.4 | ❌ False |

**Oorzaak:** `EditorPage.load_book()` roept `ai.set_book(book)` aan, en dat roept `_update_busy_buttons()` aan. Die
functie gebruikt `bool(self.main.active_book())`. Sinds de centrale adopt uit 0.31.2 wordt `_active_book` pas als
**laatste** gezet, dus op dat moment is hij nog `None`. Daarna wordt de knop nooit meer ververst.

**Gevolg:** de bestaande functie om bewust Planning mee te sturen (personages en scènes aanvinken) is al sinds 0.31.2
onbereikbaar. Dat is precies de functie waar 0.34.4 transparantie omheen bouwt, en waarop de volgende 0.34-slice verder
gaat.

**Fix (één regel):** laat `_update_busy_buttons` het boek gebruiken dat `set_book` meekrijgt (`self.store` of een
`self._book`), in plaats van `self.main.active_book()`. Of roep na de commit van de adopt `editor_page.ai._update_busy_buttons()`
aan.

**Test voor `current`:** `MainWindow` → `open_book` → `planning_context_button.isEnabled()` is True, via de echte UI-route
en niet door de selectie rechtstreeks in de code te zetten.

---

## Kleine opmerkingen (geen actie nodig)

- **Dubbele formulering in de hoofdstukregel** bij een kapotte of nieuwere Planning: "Planning van dit hoofdstuk: niet
  beschikbaar. **Planning-context niet beschikbaar:** Planning kan niet betrouwbaar worden gelezen." Het tweede deel kan
  zonder de prefix, bijvoorbeeld "…: niet beschikbaar — Planning kan niet betrouwbaar worden gelezen."
- **Luchtige preview:** de preview en de geselecteerde Planning-context worden samengevoegd met `'\n\n'`. Tussen elke
  "- Doel: …"-regel staat daardoor een lege regel, en de dialoog wordt al snel lang. Met `'\n'` binnen een scène blijft het
  compact. Het gaat alleen om de weergave; de prompttekst mag zo blijven.
- **"Altijd meegestuurd":** dat klopt met `ai/prompting.py`. Alleen als er geen hoofdstuk open is, stuurt
  `ContextBuilder` alleen de persona mee. Het AI-paneel is dan niet te zien, dus in de praktijk speelt het niet.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | Samenvatting, "Context bekijken", preview **niet** in de prompt (bewezen met een nep-provider), fail-safe, BOM-matrix, geen writes | ✅ | — |
| 1 | De knop "Planning-context…" staat sinds 0.31.2 uit na het openen van een boek; handmatige Planning-context is onbereikbaar | 🟡 | De bestaande functie werkt niet; oplossen vóór de volgende AI-slice |

**Conclusie:** 0.34.4 doet precies wat hij belooft. Het maakt zichtbaar welke hoofdstukplanning er is, en stuurt die
aantoonbaar niet mee. Wel kwam er een oude fout boven: juist de knop om bewust Planning mee te sturen, staat al sinds
0.31.2 uit. Die fix is één regel en hoort in 0.34.5, vóór de hoofdstukplanning eventueel automatisch mee gaat.

**Niet kunnen testen:**
- een echte AI-provider (nagebootst);
- echte Windows DPI-schaling;
- echte Dropbox-timing.
