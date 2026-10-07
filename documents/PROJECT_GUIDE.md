# QuietWriter — projectgids

**Status:** QuietWriter-dev staat op **1.2.32** en is de actuele releasecandidate-bron. De manuscript-/DocumentView-refactor is onafhankelijk beoordeeld als afgerond/releasecandidate. De publieke repository heeft nog 1.1.0 als releasebasis; 1.2.32 wordt eerst als vaste unsigned Windows-RC gebouwd en op false positives/reputatie gecontroleerd voordat dezelfde bron en dezelfde geteste portable ZIP publiek worden uitgebracht.

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

In 1.2.32 zijn onder andere aanwezig:

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
- vóór publicatie wordt één vaste releasecandidate gebouwd en exact die EXE/ZIP op false positives en reputatie gecontroleerd;
- na die controle wordt dezelfde bron naar de publieke repository gepromoveerd en dezelfde geteste portable ZIP gepubliceerd.

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
