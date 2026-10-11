# QuietWriter 1.4.0 — integrale reviewopdracht voor Claude

**Basis:** 1.4.0-dev.33 (oorspronkelijk opgesteld voor dev.30). **Rol:** onafhankelijk beoordelen en testen, geen productcode wijzigen. Een groen statisch testresultaat vervangt geen echte Windows-test.

## Prioriteit 1: gegevensveiligheid

- Automatische en handmatige `.qwbook`-back-ups: schrijfbare fsync-handle op Windows, eerst verifiëren dan publiceren, gedeeltelijke bestanden en terugkerende Windows-/OneDrive-locks.
- History: geen halfgeschreven versies; ook volledige oudere versiemappen uit eerdere versies meenemen.
- Bewaarbeleid: handmatige back-ups en veiligheidskopieën na een herstel mogen nooit automatisch worden verwijderd. Controleer de volgorde: pas retentie na geslaagde, gevalideerde back-up.
- Herstel naar bestaand boek: twee bevestigingen, veiligheidskopie vóór wissel, behoud van huidige plank, rollback bij injectie van fouten in iedere stap. Test ook falen tijdens opruimen en stroom-/procesuitval waar gesimuleerd mogelijk.
- Beschermde/privéboeken in Presentatiemodus: geen titel- of statuslek via back-upkeuzelijsten.
- Boeken met veel media en history: de bestaande 2-GB-grens van de import is een expliciet bekend aandachtspunt; maak geen claim dat grote back-ups herstelbaar zijn zonder test.

## Prioriteit 2: Qt en UI

- Start de hele app op Windows en Linux; draai `python -m quietwriter.app --smoke-test` en de volledige PySide6-suite.
- De nieuwe `test_qt_startup_gate_140_dev30.py` moet met echte PySide6 draaien; let op platformafhankelijke crashes na een volledig groene suite.
- Notities: 1/2/3 kolommen bij resizing, lange titels, bewerken, corrupt/brontekstbescherming en bewaren na herstart; controleer ook codeblokken met `##`-kopjes en verdwijnende kaartrijen.
- Planning: hoofdstukken inklappen, scènevolgorde, personages, dialogen en kleine schermen.
- Vertaalde knoppen in vijf talen; meldingen mogen geen standaard Engelstalige OK/Cancel tonen.

## Prioriteit 3: spelling en overige controles

- 1.3.1-woordenboekbronnen en woordbudget semantisch geïntegreerd, geen regressie ten opzichte van publiek 1.3.1.
- Asynchrone spelling: snel wisselen van woorden/taal, afsluiten tijdens werk, geen suggesties voor inmiddels vervangen woorden.
- Diagnostisch overzicht: nooit boektitels, manuscripten, bestandslocaties of AI-sleutels verzamelen.

Extra observaties dev.33: controleer vooral dat de eerste-runwizard nu nog `nl_NL` kan tonen wanneer geen echte `.dic` aanwezig is; de gewone woordenboekscanner werkt anders en scant ook de werkmap. Controleer bovendien of het suggestiebudget van één seconde onder alle omstandigheden de totale achtergrondtaak begrenst: de huidige code stopt pas bepaalde edit-kandidaten, niet noodzakelijk alle ngramwerk. Concurrente `suggest()`-taken delen mutable Hunspell- en cachedata en vragen een stress-test met woordenboekwissel. Let op het verschil tussen bron-ZIP (geen meegeleverd OpenTaal-bestand) en portable Windows-build (haalt OpenTaal tijdens build op).

## Rapportage

Rapporteer per punt: **blocker**, **must-fix**, **klein punt**, **niet getest**, met concrete reproductiestappen. Review zonder codewijzigingen. Vermeld Qt-/OS-versie en of de test offscreen of op echte Windows-hardware is uitgevoerd.


## Update voor dev.35 (na Claude’s dev.33-review)

Gerichte wijzigingen: onafhankelijke deadlines en cachegeneratie bij spelling, eigen seriële QThreadPool, herstel met best-effort rollback en duurzame unieke reddingslocatie, metadata voor versiegeschiedenis, stille retry bij typ-races van back-ups, vier bijgewerkte Qt-tests, vertaalde dialogen en labels.

**Nog onafhankelijk te bevestigen:** de vier Qt-tests onder echte PySide6; de 30 herstelcases inclusief bestaande reddingsmap (de oorspronkelijke harnasverwachting controleert slechts één vaste locatie), de volledige spellingsstresstest met echte OpenTaal, automatische back-up tijdens continu typen met media en alle Windows-bestandslocks. M3 heeft nog een open risico als een externe spylls-iterator lang bezig is vóór zijn volgende yield. Ook K5, K7, K9 en K12 blijven open.
