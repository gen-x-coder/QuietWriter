# QuietWriter — projectgids

**Status:** 1.5.1. Ontwikkeling gaat in kleine patchversies (1.5.x). Werkwijze en vaste regels staan in `../AGENTS.md`; de planning in `ROADMAP_AND_IDEAS.md`.

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

Onder andere aanwezig:

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
- first-run/onboarding;
- zelf bijwerken van de portable build (Velopack, vanaf 1.5.1);
- boekback-ups (`.qwbook`, automatisch en handmatig);
- AI Meelezer, Schrijverspersona, Boekprofiel en Boekgeheugen;
- spelling, zoeken en opmaak;
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
- PyInstaller onedir voor Windows, verpakt en bijgewerkt met Velopack.

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

- `gen-x-coder/QuietWriter-dev`: private ontwikkelrepository.
- `gen-x-coder/QuietWriter`: publieke open-source- en releaserepository; de app zoekt updates alleen daar.
- Unsigned Windows-build zonder UPX of obfuscatie, met een lokaal gecompileerde PyInstaller-bootloader en gepubliceerde SHA-256-hashes. SignPath is afgeblazen.
- Versies: `x.y.z`; geen lange `-dev.N`-reeksen meer.

Zie `RELEASE_PROCESS.md`.

## Leesvolgorde voor een nieuwe ontwikkelaar of AI

1. `../AGENTS.md` — regels en werkwijze
2. `PROJECT_GUIDE.md`
3. `ARCHITECTURE_AND_DATA_SAFETY.md`
4. `PRODUCT_AND_UI_PHILOSOPHY.md`
5. `HISTORY_AND_LESSONS.md` — waarom dingen zijn zoals ze zijn
6. `ROADMAP_AND_IDEAS.md`
7. `MANUSCRIPT_SYNTAX.md`
8. `TEST_STRATEGY.md`
9. `RELEASE_PROCESS.md`
10. `DEVELOPER_REFERENCE.md` en `UI_REFERENCE.md` (naslag)
11. `design/` — ontwerp per functie (Darlings, schrijfdoelen, Planninghulp, exportwizard, paneeluitleg, back-ups)
12. `research/` — lopend onderzoek (o.a. vergelijking met NEO, oktober 2026)
13. `CHANGELOG.md`

De volledige geschiedenis (reviews, overdrachten, onderzoek, oude roadmap en changelog) staat in `archive/`, met een index in `archive/README.md`.
