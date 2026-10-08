# QuietWriter — projectgids

**Status:** QuietWriter **1.2.32** is de publieke stabiele release. De 1.3-lijn is bevroren op **1.3.0-rc1** voor de Windows releasecandidate. De 1.3-lijn bevat inmiddels de nieuwe Boekenkast met planken en Presentatiemodus; dev.11 introduceerde opt-in schrijfdoelen en lokale dagvoortgang; dev.18 startte Planning dichter bij het schrijven met presentation-only Planninghulp in lege hoofdstukken; dev.19 polijst de sceneweergave en maakt afgekapt gebleven scènes expliciet zichtbaar; dev.20 maakte Planning zelf duidelijker en trok context-subnavigatie visueel gelijk; dev.21 verduidelijkte de Planningworkflow en maakte scènestatus zichtbaar; dev.22 voegde de on-demand Planning-overlay in de editor toe, maakte Status een vaste dropdown en liet scènes bewust als Geschreven markeren; dev.23 polijstte die workflow; dev.24 maakt de overlay smaller/hoger, koppelt de Planning-knop aan de Planninghulp-instelling en repareert de losse zoek/vervang- en plakselectiebugs; dev.25 laat de Planning-knop ook zonder gekoppelde scènes beschikbaar en trekt de lege zoekstatus visueel gelijk. dev.26 maakte de lege flyout compact en vormde de basis voor een brede review; dev.27 verwerkte de review-hardening rond tests, opt-in, scrollwiel, profielinstellingen en popupgedrag; dev.28 rondt de kerneditor af met natuurlijke undo, veilige scènebreuk-plakacties, de updatecheck en een kleine polishbundel. dev.29 richt zich op echt Windows-/laptopgebruik: betrouwbare undo bij menselijke typesnelheid, zichtbare boeklaadfeedback, kleine-schermgedrag, thema-accenten en expliciete Integriteit.

## Wat QuietWriter is

QuietWriter is een lokale desktop-schrijfomgeving voor boeken en langere teksten. De applicatie combineert een rustige manuscripteditor, hoofdstuk- en sectiebeheer, Planning, versiegeschiedenis/herstel, spelling, publicatie/export, media en een optionele **AI Meelezer**.

De kernwaarden zijn:

- **Blijf schrijven**;
- lokale controle;
- voorspelbaar gedrag;
- dataveiligheid;
- rust boven feature density;
- AI die ondersteunt zonder het auteurschap over te nemen.

## Wat QuietWriter niet wil zijn

- geen DTP-pakket;
- geen cloud-samenwerkingsplatform;
- geen autonome AI-schrijver;
- geen allesomvattende worldbuildingdatabase;
- geen systeem dat stil bestanden repareert, migreert of herschrijft;
- geen applicatie met meerdere concurrerende bronnen van waarheid voor dezelfde structuur.

## Huidige productstaat

In de stabiele 1.2.32 zijn onder andere aanwezig:

- manuscript en hoofdstukstructuur;
- Planning, scènes en personages;
- In dit hoofdstuk;
- Darlings/Bewaarplaats;
- Open punten;
- versiegeschiedenis en herstel;
- conflict- en integriteitsbeveiliging;
- `.qwbook` import/export;
- DOCX import/export;
- EPUB/PDF/Markdown-export;
- begeleid exporteren;
- first-run/onboarding en updatecontrole;
- AI Meelezer, Schrijverspersona, Boekprofiel en Boekgeheugen;
- spelling, zoeken, focusweergave en opmaak;
- lokale media;
- vijf interfacetalen;
- vijftien thema's.

Zie `CHANGELOG.md` voor exacte versiedetails.

## Technische basis

- Python 3.12+;
- PySide6/Qt;
- momenteel Markdown als canonieke manuscriptbron;
- JSON voor diverse gestructureerde boekdata;
- lokale bestandssystemen, geen verplichte cloudbackend;
- History/revisions en optimistic concurrency;
- EPUB, PDF, DOCX en Markdown export;
- Ollama en OpenRouter als optionele AI-providers;
- PyInstaller onedir voor Windows.

### Manuscriptarchitectuur: besluit afgerond

QuietWriter houdt open, leesbare platte tekst met Markdownconventies als canonieke manuscriptopslag. De bron gebruikt een formeel en geversioneerd QuietWriter-profiel; strikte CommonMark-compatibiliteit is geen doel. `DocumentView` is de centrale read-only interpretatielaag en gegenereerde manuscriptsyntax loopt via de centrale serializer.

Oudere boeken worden niet stil aangepast. Wanneer een syntaxmigratie nodig is, vraagt QuietWriter expliciet toestemming en maakt eerst een herstelpunt. De onafhankelijke 1.2.31-review beoordeelde deze architectuur als **A: afgerond / releasecandidate**.

## Belangrijkste codegebieden

- `quietwriter/storage.py`, `revisions.py`, `integrity.py`, `migrations.py`: opslag en veiligheid.
- `quietwriter/library_shelves.py`: werkmap-brede boekenkasten, planktoewijzing, herstel en toekomstige Demo-zichtbaarheid.
- `quietwriter/document_view.py`: centrale read-only interpretatie van manuscriptsyntaxis en bronranges.
- `quietwriter/import_document.py`: neutraal importmodel tussen externe formaten en QuietWriter-bron.
- `quietwriter/ui/editor_page.py`, `manuscript_editor.py`, `manuscript_markup.py`: manuscript/editor.
- `quietwriter/planning_*` en `ui/planning/`: scènes, personages en notities.
- `quietwriter/publication_*`, `ui/publication/`, `exporting/`: publicatie en export.
- `quietwriter/media/`: media en afbeeldingen.
- `quietwriter/ai/`: Meelezer, providers en context.
- `quietwriter/ui/main_window.py`, `rail_model.py`, `current_page_stack.py`: navigatie en hoofd-UI.

## Dataconcepten

**Manuscript** = wat werkelijk geschreven is.  
**Planning** = wat bedoeld/gepland is.  
**Boekprofiel** = regels en karakter van dit specifieke boek.  
**Boekgeheugen** = duurzame feiten, afspraken en besluiten.  
**Schrijverspersona** = globale stijl/voorkeuren van de schrijver.
**Boekenkast** = lokale werkmaporganisatie; geen onderdeel van het manuscript of een losse `.qwbook`-export.

Deze lagen mogen niet stil in elkaar overlopen.

## Harde productregels

1. Externe wijzigingen nooit stil overschrijven.
2. Geen stille reparatie/migratie bij openen.
3. Nieuwere bestandsformaten zijn incompatibel, niet corrupt.
4. Lokale dirty invoer blijft zichtbaar of wordt eerst herstelbaar vastgelegd.
5. Presentatie is geen inhoud.
6. Eén autoritatieve bron per concept.
7. AI is Meelezer, niet schrijver/co-auteur.
8. Externe AI krijgt pas context na een bewuste gebruikersactie.
9. Geen autonome writes naar Boekgeheugen.
10. Onzekere media worden niet automatisch weggegooid.
11. Een opslagformaat wordt niet vervangen zonder expliciete migratie- en herstelstrategie.

## Repository- en releasemodel

- `gen-x-coder/QuietWriter-dev`: private ontwikkelrepository en actuele ontwikkelbaseline.
- `gen-x-coder/QuietWriter`: publieke open-source- en releaserepository.
- de SignPath Foundation-aanvraag is afgewezen wegens nog onvoldoende publieke adoptiesignalen; dit blokkeert de release niet;
- de Windows-release wordt voorlopig unsigned gebouwd zonder UPX/obfuscatie, met lokaal gecompileerde PyInstaller-bootloader en gepubliceerde SHA-256-hashes;
- stabiele releases worden als vaste Windows-build bevroren, gecontroleerd en met SHA-256 gepubliceerd;
- actieve featureontwikkeling gebruikt oplopende prereleaseversies op de komende minor-lijn (nu `1.3.0-dev.X`). Na publicatie van 1.3.0 gaan eventuele gebruikersfixes naar `1.3.1`, terwijl nieuwe featureontwikkeling dan op `1.4.0-dev.X` doorgaat.

Zie `RELEASE_PROCESS.md`.

## Leesvolgorde voor een nieuwe ontwikkelaar of AI

1. `PROJECT_GUIDE.md`
2. `ARCHITECTURE_AND_DATA_SAFETY.md`
3. `PRODUCT_AND_UI_PHILOSOPHY.md`
4. `ROADMAP_AND_IDEAS.md`
5. `MANUSCRIPT_SYNTAX.md` — feitelijke 1.2.13-manuscriptsyntaxis en richting naar gangbare Markdownconventies
6. `BOOK_FORMAT_ARCHITECTURE_RESEARCH.md` — actief onderzoek naar manuscriptopslag, intern documentmodel en DOCX-import
7. `BOOK_FORMAT_ARCHITECTURE_REVIEW_CLAUDE.md` — eerste onafhankelijke architectuurreview
8. `BOOK_FORMAT_ARCHITECTURE_REVIEW_1_2_24_CLAUDE.md` — onafhankelijke hardeningreview na de eerste DocumentView-implementatie
9. `QUIETWRITER_REVIEW_1_2_30_CLAUDE.md` — finale audit die nog één hardeningblok vereiste
10. `QUIETWRITER_REVIEW_1_2_31_CLAUDE.md` — afsluitende PySide6-review: A, refactor afgerond/releasecandidate
11. `TEST_STRATEGY.md`
12. `HISTORY_AND_LESSONS.md`
13. `RELEASE_PROCESS.md`
14. `RELEASE_BRANDING_AND_OPERATIONS.md`
15. `PUBLIC_PRESENTATION.md`
16. `CHANGELOG.md`

Historische roadmapdetails staan in `ROADMAP_HISTORY_TO_1_2_13.md`.
