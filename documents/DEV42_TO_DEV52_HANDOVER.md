# QuietWriter 1.5.0 — Overdracht dev.42 t/m dev.52

## Ontwikkelafspraken

Werk incrementeel op de laatste **gecontroleerde** bron-ZIP. Lever een volledige project-ZIP voor Windows-testen, met correcte interne `quietwriter/__init__.py`-versie. Controleer de meegeleverde functionaliteit en ZIP-integriteit. Eerst eigen inspectie, tests en gebruikersacceptatie; Claude pas na een groter afgerond werkblok voor onafhankelijke review, niet voor elke build. Respecteer de bestaande ontwerpprincipes en vertaalde UI. Git synchronisatie/release hoort afzonderlijk te worden afgestemd; een bron-ZIP is geen Git-push of Windows-EXE.

## Chronologie

- **dev.42**: basis Meelezer/pop-out, probleemrapport met knoppen en archieven.
- **dev.43**: compacte bovenste knoppen, pop-out en terugplaatsen van rechterpaneel, lege archiefstaten.
- **dev.44**: Nederlandstalige Bewaren-dialoog.
- **dev.45**: begrijpelijke meldingen bij Bewaren zonder gesprek of tijdens antwoord; verificatie van geheugenopslag.
- **dev.46**: OpenRouter PKCE-browserautorisatie en opslag in Windows Credential Manager; handmatige sleutel als alternatief. Initiële pakketversie was niet meegewerkt; gecorrigeerd.
- **dev.47**: expliciete keuze **browserlogin / handmatige API-sleutel**; geen impliciete fallback tussen credentials.
- **dev.48**: providerafhankelijke instellingen en visuele verbindingsstatus.
- **dev.49**: eerste schrijfmodel-filter; te agressief gebleken door brede beschrijvingsmatch.
- **dev.50**: gecorrigeerde filter op expliciete programmeerfamilies en tekstuitvoer; `openrouter/free` altijd in de selectie. Gebruiker heeft OpenRouter goedgekeurd.
- **dev.51**: tolerantere gestructureerde geheugenvoorstellen en afscherming van half ontvangen streamingmarkers. Testgesprek toonde dat modellen soms *beweren* geheugen te schrijven zonder een daadwerkelijke actie.
- **dev.52**: expliciete knop **Onthouden**, bewerkbare tekst, categorie en gecontroleerde lokale opslag, onafhankelijk van het AI-model.

## Architectuur en grenzen

- Meelezer: `quietwriter/ai/ui.py`, prompting/parser in `quietwriter/ai/`; AI-providers in `quietwriter/ai/providers.py` en gerelateerde modules.
- Boekgeheugen: `quietwriter/ui/book_memory_page.py`, `quietwriter/book_memory.py`; per boek `ai/memory.md`. Schrijver autoriseert elke toevoeging.
- OpenRouter heeft twee **afzonderlijke** verbindingsmethoden. De gekozen methode wordt gebruikt en na herstart behouden; de andere mag niet ongemerkt als fallback dienen.
- `openrouter/free` is belangrijk voor goedkope stresstests, maar routes kunnen verschillende modellen en inconsistent gedrag leveren.
- Fouten en beweringen van modellen zijn niet gelijk aan lokaal bevestigde acties. Meldingen over opgeslagen geheugen mogen uitsluitend uit QuietWriter komen, na schijfcontrole.

## Openstaand

- Windows-test van de nieuwe dev.52-geheugendialoog en behoud na herstart.
- Meelezer-prompt: expliciet voorkomen dat een model namens QuietWriter claimt iets al te hebben opgeslagen. Verder testen met wisselende Free-modellen.
- Later gebruikershandleiding voor OpenRouter-account aanmaken, browserkoppeling en kosten/limieten.
- Na afronden van de totale geheugenworkflow een grotere onafhankelijke Claude-review en daarop gebaseerde regressietests.

## Aanvulling dev.53 (14 oktober 2026)
- `quietwriter/ai/prompting.py`: auteurscanon expliciet, beknopte antwoorden op nieuwe feiten, onderscheid manuscript/canon, geen AI-opslagclaims.
- `quietwriter/ai/response_guard.py`: beperkt vangnet tegen onterecht geclaimde opslag in een AI-antwoord; alleen het definitieve antwoord wordt bijgewerkt.
- `tests/current/test_ai_reader_memory_dev53.py`: gedragstests plus opstartconstanten. Bekijk `documents/DEV53_READER_BEHAVIOR.md` voor acceptatietests en beperkingen.
- Dev.52 is door de gebruiker geaccepteerd: de knop Onthouden werkt en gegevens blijven bewaard. Dev.53 is nog niet op Windows getest.
