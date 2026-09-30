# Review 0.34.4 — transparante hoofdstukplanning in AI-context

## Doel
Deze release verandert **niet** welke Planning automatisch naar AI wordt gestuurd. Hij maakt eerst zichtbaar welke opgeslagen Planning van het actieve hoofdstuk beschikbaar is en welke tekst QuietWriter later eventueel zou kunnen meesturen.

## Verplicht testen met echte PySide6
1. Volledige `tests/current`-suite.
2. Koude start en normale boek/open-hoofdstuk smoke.
3. Open AI → Context bij een hoofdstuk met 2 scènes/personages. Verwacht:
   - `Altijd meegestuurd: Schrijverspersona · Boekprofiel · Boekgeheugen`;
   - `Planning van dit hoofdstuk: ... · nog niet automatisch meegestuurd`;
   - hoofdstukwissel ververst deze samenvatting.
4. **Context bekijken**:
   - toont de vaste context en manuscriptcontext;
   - toont de bestaande expliciet geselecteerde Planning-context apart;
   - toont daarna `Planning van huidig hoofdstuk — voorbeeld, nog niet automatisch meegestuurd`;
   - de preview bevat exact de opgeslagen scenevelden/personages van het hoofdstuk.
5. Bewijs dat een normale AI-vraag de hoofdstukpreview nog **niet** verstuurt. Gebruik liefst een nep-provider en inspecteer de systeemprompt. Alleen handmatig geselecteerde `Planning-context…` mag in `GESELECTEERDE PLANNINGCONTEXT` staan.
6. Corrupte v1 en nieuwere v2 Planning:
   - Contextknop en dialoog blijven bruikbaar;
   - geen dubbele tekst `Planning: Planning-context niet beschikbaar`;
   - AI-vraag gaat verder zonder Planning zoals in 0.34.3.
7. BOM-matrix: `outline.json`/`characters.json` met UTF-8-BOM en `version:2` moet nog steeds als **nieuwere QuietWriter** worden herkend door PlanningStore, Integriteit en History-guard.

## Regressie
- 0.34.3 AI Planning fail-safe en History-guard.
- `In dit hoofdstuk` blijft alleen opgeslagen Planning tonen.
- Geen nieuwe writes/schemafields.
- `tests/legacy` hoeft bij deze patchrelease niet verplicht volledig te draaien, maar is lokaal zonder fonttest opnieuw groen gehouden.

## Visueel voor Lucas
- Open AI → Context bij een hoofdstuk met Planning en beoordeel of de twee regels `Altijd meegestuurd...` en `Planning van dit hoofdstuk...` duidelijk maar niet te druk zijn.
- Open **Context bekijken** en beoordeel of het onderscheid tussen **geselecteerde Planning-context** en de **hoofdstukplanning-preview** begrijpelijk is.
