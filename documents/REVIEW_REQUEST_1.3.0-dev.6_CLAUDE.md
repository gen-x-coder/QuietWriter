# QuietWriter 1.3.0-dev.6 — reviewopdracht voor Claude

## Instructie

Review deze ZIP als opvolger van je dev.2-review en de inmiddels gebouwde Neo-Boekenkast/Demo-laag. **Wijzig geen code.** We willen eerst metingen en een onafhankelijk oordeel.

Draai de volledige testsuite met PySide6, smoke-test, locales en undefined-name checks zoals eerder. Controleer daarnaast de Demo-modus functioneel op de zichtbare Qt-laag.

## 1. Performance: eerst meten, dan adviseren

De gebruiker ervaart de Boekenkast als merkbaar traag. Profileer dit gericht. Meet bij voorkeur een werkmap met ongeveer 25 boeken, meerdere planken en enkele echte covers. Vergelijk minimaal:

- eerste openen van de Boekenkast;
- `refresh()` zonder inhoudswijziging;
- Demo-modus aan/uit;
- sorteren op laatst gebruikt, titel en aantal woorden;
- zoeken tijdens typen;
- vensterbreedte wijzigen / card reflow.

Onderzoek expliciet, maar neem niet vooraf aan dat dit de oorzaak is:

- volledige afbraak en herbouw van alle Qt-widgets in `StartPage.refresh()`;
- woordtelling die hoofdstukbestanden opnieuw leest;
- coverbestanden / `QPixmap` opnieuw laden en schalen;
- `Library.list_books()` en shelf-snapshot loading;
- sorteren op `book_activity`;
- `textChanged -> refresh()` bij iedere toetsaanslag;
- `_WrappingCardHost` reflow;
- schaduweffecten / grote aantallen `QGraphicsDropShadowEffect`;
- Demo-filters in Bewaarplaats/Prullenbak.

Geef per gevonden bottleneck:
1. gemeten bijdrage;
2. ernst voor 25 / 100 / 500 boeken voor zover zinvol;
3. de **eenvoudigste** veilige optimalisatie;
4. risico op stale UI, cachebugs of extra complexiteit;
5. jouw aanbevolen volgorde.

QuietWriter-principe blijft: **simpel en schrijven; geen bloat**. We accepteren liever een kleine gerichte cache of debounce dan een complex UI-framework.

## 2. Demo-modus functioneel / privacy als presentatie

De functie is **geen beveiliging**. Doel: tijdens een demo, screenshot of schermdeling privéplanken en eraan gekoppelde informatie niet in QuietWriter tonen. Geen encryptie, secure deletion of bescherming tegen filesystem-/forensisch onderzoek.

Controleer minimaal:

- privéplank en boeken verdwijnen uit Boekenkast;
- zoeken en aantallen lekken ze niet;
- Bewaarplaats en Prullenbak tonen geen aan privéboeken gekoppelde informatie;
- aan/uit schakelen geeft alles direct correct terug;
- niet-canonieke/future shelf-data blijft fail-closed in Demo-modus;
- de nieuwe knopstatus (`Demo-modus: aan/uit`) blijft correct na herstart en taalwisseling;
- een open privéboek bij inschakelen: controleer wat de huidige code werkelijk doet en of dit productmatig veilig/duidelijk genoeg is.

Meld blockers apart van polish.

## 3. Naamgevingsvraag — geef een onafhankelijk productadvies

We twijfelen over **Demo-modus**. De naam is functioneel, maar misschien technisch. Beoordeel minimaal:

- **Demo-modus**
- **Presentatiemodus**
- **Privémodus**
- **Presenteren**
- eventueel één betere eigen suggestie

Context:
- de functie verbergt privéplanken tijdens meekijken, demo's, screenshots en schermdelen;
- het is nadrukkelijk **geen security/privacy-beveiliging**;
- de naam moet voor een schrijver direct begrijpelijk zijn;
- hij moet niet zwaarder klinken dan de functie is;
- hij moet redelijk natuurlijk vertaalbaar zijn naar Engels, Duits, Frans en Spaans.

Geef één duidelijke voorkeursnaam en leg kort uit waarom. Geef ook aan welke naam je juist zou vermijden vanwege verkeerde verwachtingen.

## 4. Gewenste uitkomst

Lever een compact rapport met:

1. testresultaten;
2. blockers;
3. performanceprofiel met concrete metingen;
4. aanbevolen optimalisaties in prioriteitsvolgorde;
5. oordeel over Demo-modus;
6. naamgevingsadvies;
7. wat vóór de volgende dev-build moet en wat veilig op backlog kan.

**Geen code wijzigen in deze review.**
