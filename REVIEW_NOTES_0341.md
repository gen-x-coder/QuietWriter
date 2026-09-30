# Reviewnotes 0.34.1 — ronde 37

## Eerst verplicht
1. Draai eerst de actuele suite met echte PySide6 via `pytest`; geen hang. Draai daarna eenmaal `pytest tests/legacy` als historische mijlpaalcontrole.
2. Koude start en boek openen.
3. Smoke-regressie van 0.34.0: railselectie, programmatic navigation, opgeslagen/onopgeslagen Planning, AI uit, publicatie/history/corrupt chapter.

## A. Planning-structuur: boek moet open blijven
Test afzonderlijk:
- `outline.json`: `{"version":1,"scenes":5}`
- scène met `"character_ids": null`
- `characters.json`: personage met `"relations":5`
- `version: 2` voor outline en characters.

Verwacht:
- boek opent in Inhoud; geen exception in Qt-eventloop;
- **In dit hoofdstuk** toont een korte leesfout; editor blijft typen/opslaan;
- Planning opent en toont bovenaan de bronwaarschuwing; het getroffen Personages/Outline-deel is niet bewerkbaar;
- Integriteit rapporteert precies het verkeerde bestand als herstelbaar probleem;
- corrupte/structureel verkeerde bytes worden niet overschreven door een savepoging.

Controleer ook bestaande invalid-UTF8/invalid-JSON-baseline uit 0.31/0.32: tolerant lezen waar eerder afgesproken, maar nooit overschrijven.

## B. In dit hoofdstuk: volledige bestaande scènecontext
Maak een scène met titel, synopsis, status, locatie, personages, **Doel, Conflict, Uitkomst en Notities**.
- alle ingevulde velden zichtbaar; lege velden niet als lege kop tonen;
- personages afgeleid uit gekoppelde ids; verweesde ids stil overslaan;
- meerdere scènes visueel duidelijk gescheiden; subkoppen/scènetitels zichtbaar zwaarder dan gewone tekst;
- opgeslagen-vs-onopgeslagen Planning-regel blijft hetzelfde als 0.34.0.

## C. Statusbalk
- Open hoofdstuk: `Hoofdstuk n van m · x woorden` zichtbaar.
- Toon een tijdelijke statusmelding (bijv. handmatige versie of Boekdetails-save) en wacht tot die timeout verloopt: hoofdstuk-/woordentelling moet terugkomen.
- Wissel Planning → Inhoud: telling moet terugkomen.
- Voorwoord/Nawoord of Boekenplank: geen verouderde hoofdstuktelling laten staan.

## D. Ingeklapte railseparators
Met rail ingeklapt, licht én donker thema:
- zichtbare groepen hebben een subtiel maar echt zichtbaar 1px lijntje;
- geen lijn aan begin/eind of twee achter elkaar;
- uitgeklapt: geen separators, alleen groepskoppen.

## E. Lage schermen / echte Windows DPI — visuele observatie, geen blokkade voor 0.34.1
Meet 1366×768 op 100%, 125% en 150% als beschikbaar. 0.34.1 verandert de responsive policy nog niet. Noteer:
- resterende editorbreedte met Inhoud + In dit hoofdstuk open;
- of titel/tekst comfortabel leesbaar blijft;
- of een automatische collapse van linkerrail of Inhoud wenselijk voelt.

## Niet veranderd
- `quietwriter/ai/` mag functioneel niet wijzigen.
- Geen nieuw Planning-schema of migratie.
- Paneel blijft alleen-lezen en schrijft niets.


## F. Nieuwe testindeling
- `pytest` moet alleen `tests/current/` verzamelen.
- Controleer dat de actuele suite zelfstandig groen is.
- `pytest tests/legacy` moet de gearchiveerde regressies nog steeds kunnen verzamelen/uitvoeren; deze suite is niet meer release-blocking voor gewone 0.34.x-iteraties, behalve als een relevante oude foutklasse geraakt wordt.
- Controleer steekproefsgewijs dat kerngebieden in current blijven: storage/revisions, editor source, Planning/Integriteit, Settings, rail/navigatie, publicatie en chapter context.
- Geen dubbele bestanden tussen current en legacy.
