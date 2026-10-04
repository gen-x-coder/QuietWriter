# QuietWriter — projectgids

**Status:** 1.0.0, eerste stabiele release. De 1.0-functieset is bevroren; nieuwe functionaliteit volgt via de v2-roadmap.

## Wat QuietWriter is
QuietWriter is een lokale desktop-schrijfomgeving voor boeken en langere teksten. De applicatie combineert een rustige manuscripteditor, hoofdstuk- en sectiebeheer, Planning, revisiegeschiedenis/herstel, spelling, publicatie/export, media en een optionele **AI Meelezer**.

De kernwaarden zijn: lokale controle, voorspelbaar gedrag, dataveiligheid, een rustige interface en AI die ondersteunt zonder het auteurschap over te nemen.

## Wat QuietWriter niet wil zijn
- geen DTP-pakket;
- geen cloud-samenwerkingsplatform;
- geen autonome AI-schrijver;
- geen allesomvattende worldbuildingdatabase;
- geen systeem dat stil bestanden repareert, migreert of herschrijft;
- geen applicatie met meerdere concurrerende bronnen van waarheid voor dezelfde structuur.

## Technische basis
- Python 3.12+;
- PySide6/Qt;
- Markdown voor manuscriptachtige inhoud;
- JSON voor gestructureerde boekdata;
- lokale bestandssystemen, geen verplichte cloudbackend;
- History/revisions voor conflict- en herstelgedrag;
- EPUB, PDF en Markdown export;
- Ollama en OpenRouter als optionele AI-providers;
- PyInstaller onedir voor Windows.

## Belangrijkste codegebieden
- `quietwriter/storage.py`, `revisions.py`, `integrity.py`, `migrations.py`: opslag en veiligheid.
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
5. Presentatie is geen inhoud: highlighting, spelling en typografie mogen geen manuscriptwrite veroorzaken.
6. Eén autoritatieve bron per concept.
7. AI is Meelezer, niet schrijver/co-auteur.
8. Externe AI krijgt pas context na een bewuste gebruikersactie.
9. Geen autonome writes naar Boekgeheugen.
10. Onzekere media worden niet automatisch weggegooid.

## Leesvolgorde voor een nieuwe ontwikkelaar of AI
1. `PROJECT_GUIDE.md`
2. `ARCHITECTURE_AND_DATA_SAFETY.md`
3. `PRODUCT_AND_UI_PHILOSOPHY.md`
4. `HISTORY_AND_LESSONS.md`
5. `TEST_STRATEGY.md`
6. `ROADMAP_AND_IDEAS.md`
7. `RELEASE_BRANDING_AND_OPERATIONS.md`
8. `CHANGELOG.md`

## Richting 1.0
RC2 is technisch groen op basis van de releasecyclus én de lokale overdraagbaarheidsreview van 2 oktober 2026 (Python 3.12.3 / PySide6 6.11.2). Zie `VALIDATION.md` voor de concrete testruns. Wat nog vooral praktijkvalidatie is:
- clean Windows zonder Python;
- SmartScreen;
- 100/125/150% schaal;
- echte Ollama/OpenRouter-runs;
- oudere echte boeken;
- groot boek (~150.000 woorden / 40 hoofdstukken);
- een langere periode echt schrijven zonder data-incident.

Tot de stabiele 1.0 geldt feature freeze: alleen regressie-, data- en releasefixes.
