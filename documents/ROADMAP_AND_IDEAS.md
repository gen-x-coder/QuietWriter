# QuietWriter — roadmap en ideeën

**Status:** canonieke roadmap vanaf QuietWriter 1.2.13  
**Laatste actualisatie:** 7 oktober 2026

Deze roadmap beschrijft alleen de actuele productrichting. Uitgebreide oude 1.0/v2-ontwerpen zijn bewaard in `ROADMAP_HISTORY_TO_1_2_13.md`.

## 1. Waar we nu staan

De actuele ontwikkel- en releasecandidatebron is **1.2.32**. De onafhankelijke 1.2.31-eindreview draaide de volledige PySide6-suite met 714 geslaagde tests, 0 fouten en 0 skips en beoordeelde de manuscript-/DocumentView-refactor als **A: afgerond / releasecandidate**. De aanvullende Windows-test met een echt ouder boek en de Nederlandse migratiedialoog is daarna eveneens goed verlopen.

De publieke repository `gen-x-coder/QuietWriter` heeft nog **1.1.0** als publieke releasebasis. De SignPath Foundation-aanvraag is afgewezen omdat QuietWriter nog onvoldoende publieke adoptiesignalen heeft. We wachten daarom niet langer op signing: 1.2.32 wordt als vaste unsigned Windows-releasecandidate gebouwd, exact die build wordt bij Microsoft/VirusTotal en relevante leveranciers op false positives gecontroleerd, en daarna wordt dezelfde geteste build publiek uitgebracht.

De grote manuscriptarchitectuurverbouwing is hiermee afgesloten. Nieuwe productontwikkeling kan weer voorrang krijgen; de Boekenkast met planken en privacy staat bovenaan.

## 2. Wat al gerealiseerd is

Onder andere aanwezig:

- lokale manuscripteditor met hoofdstukken en secties;
- Planning met scènes en personages;
- **In dit hoofdstuk**;
- **Darlings / Bewaarplaats**;
- **Open punten**;
- versiegeschiedenis, herstel en conflictbescherming;
- integriteitscontrole en expliciete migratiebasis;
- `.qwbook` export/import als volledig overdraagbaar boekpakket;
- DOCX import en export;
- EPUB, PDF en Markdown export;
- begeleide exportwizard;
- first-run/onboarding;
- handmatige en optionele automatische GitHub-updatecontrole;
- AI **Meelezer** met Ollama en OpenRouter;
- Schrijverspersona, Boekprofiel en Boekgeheugen;
- spelling, zoeken, focusweergave en opmaak;
- lokale media;
- vijf interfacetalen: Nederlands, Engels, Duits, Frans en Spaans;
- vijftien thema's, waaronder Lamplicht;
- Windows portable build, smoke-test en publieke Windows/Ubuntu-CI;
- GPLv3 en publieke release-/privacy-/securitydocumentatie.

Details per versie staan in `CHANGELOG.md`.

## 3. Bovenaan na de huidige hardening — Boekenkast met planken en privacy

**Prioriteit: hoog — productrichting direct na de huidige document-/importhardening.**

De huidige vlakke **Boekenplank** groeit door naar een echte **Boekenkast** met meerdere planken. Een schrijver moet boeken logisch kunnen groeperen zonder dat QuietWriter daar één vaste betekenis aan oplegt. Een plank kan bijvoorbeeld een serie, genre, pseudoniem, projectgroep of persoonlijke verzameling zijn.

### Gewenst gedrag

- één kast met meerdere horizontale planken;
- meerdere boeken per plank, met rustige coverweergave;
- planken toevoegen, hernoemen, verwijderen en ordenen;
- boeken eenvoudig tussen planken verplaatsen;
- een boek kan in eerste instantie precies één primaire plank hebben; eerst geen complexe tags/many-to-many-indeling bouwen;
- een nieuwe gebruiker houdt een eenvoudige standaardplank zodat de huidige ervaring niet ingewikkelder wordt;
- de visuele richting mag inspiratie halen uit NEO: duidelijke planknamen, covers naast elkaar, veel rust en weinig chrome.

### Verborgen / privéplanken

Voor demo's, schermdelen en gedeelde omgevingen moet een schrijver gevoelige boeken (bijvoorbeeld NSFW of werk onder een pseudoniem) elegant uit beeld kunnen houden.

Randvoorwaarden:

- een plank kan als **verborgen** worden gemarkeerd;
- verborgen planken lekken in de normale kastweergave geen titel, covers, boektitels of aantallen;
- zichtbaar maken gebeurt via een bewuste, rustige actie en niet via een opvallende permanente NSFW-indicator;
- onthoud de gewenste zichtbaarheid lokaal als UI-/werkruimtevoorkeur;
- dit is in eerste instantie **privacy tegen meekijken/demo's**, geen cryptografische beveiliging;
- zoekresultaten, recente boeken en andere globale UI mogen verborgen boeken niet per ongeluk alsnog tonen wanneer verborgen planken uit staan;
- ontwerp herstelbaarheid en bestandsopslag zo dat planken alleen organisatie toevoegen en nooit de enige vindplaats van een boek worden.

### Nog uit te werken

- opslagmodel voor plankmetadata (bij voorkeur op bibliotheek-/werkruimteniveau, niet in ieder boek);
- drag-and-drop versus expliciet menu voor verplaatsen;
- standaardplank en gedrag bij verwijderen van een plank;
- optionele snelle **Demo-modus** die alle verborgen planken met één actie uitschakelt;
- toetsenbord- en toegankelijkheidsbediening;
- migratie van de huidige vlakke boekenplank zonder boekbestanden te verplaatsen.

## 4. Huidige technische prioriteit — documentmodel hardenen

### Afgeronde onderzoeksbeslissing

Het formaatonderzoek en de Claude-review bevestigen de richting: open platte tekst met Markdownconventies blijft de canonieke manuscriptopslag, met een formeel QuietWriter-profiel en een centrale DocumentView/serializer. Strikte CommonMark-compatibiliteit is geen doel.

### Status

De kernimplementatie en hardening zijn afgerond. De afsluitende onafhankelijke review geeft advies **A: refactor afgerond / releasecandidate**. Nieuwe syntaxfeatures zoals links mogen vanaf hier als normale productontwikkeling worden behandeld.

## 5. Achtergrond — intern boek- en manuscriptformaat onderzoeken

**Prioriteit: zeer hoog — eerst onderzoeken, nog niets migreren.**

QuietWriter gebruikt nu Markdown als canonieke manuscriptbron omdat dat historisch zo is gegroeid. Dat heeft belangrijke voordelen: leesbaarheid, openheid, diffbaarheid, eenvoudige recovery en onafhankelijkheid van QuietWriter.

Maar het product krijgt steeds meer semantiek rond tekst: afbeeldingen, Open punten, publicatiestructuur, planningkoppelingen, toekomstige boektypografie en mogelijk andere structurele elementen. Daarom mag Markdown niet alleen uit gewoonte de permanente keuze blijven.

### Centrale vraag

**Wat is voor QuietWriter op langere termijn het beste interne boek- en manuscriptmodel, nu er echte gebruikers en bestaande boeken zijn?**

Het doel is nadrukkelijk **geen DOCX-roundtrip**. Een geïmporteerd Word-document wordt een QuietWriter-boek. We hoeven onbekende Word-opmaak niet later weer exact naar Word terug te kunnen schrijven.

Wel moet het onderzoek de basis van DOCX/OOXML goed begrijpen, zodat een normale roman betrouwbaar kan worden geïmporteerd zonder stille vervorming. De primaire praktijkcase is proza met hoofdstukken/scènes, gebruikelijke inline-opmaak en hooguit enkele afbeeldingen en tabellen.

Dit onderzoek moet minimaal vergelijken:

1. huidige Markdown per hoofdstuk;
2. Markdown met een explicietere semantische laag/sidecar-data;
3. een gestructureerd documentmodel met eigen schema;
4. HTML/XHTML-achtige opslag;
5. JSON/AST-achtige opslag;
6. hybride modellen waarbij een open tekstformaat de bron blijft maar QuietWriter een formeel structureel model onderhoudt.

Andere kandidaten mogen worden toegevoegd als daar een sterke reden voor is.

### Beoordelingscriteria

Niet alleen kijken naar wat technisch elegant is. Beoordeel minimaal:

- menselijk leesbare en herstelbare bestanden;
- open formaat en vendor lock-in;
- backward en forward compatibility;
- veilige migratie van bestaande boeken;
- externe wijzigingen / Dropbox / twee computers;
- atomische writes en conflictgedrag;
- History en byte-/semantisch herstel;
- source fidelity;
- Undo/Redo;
- hoofdstukken en scènegrenzen;
- inline opmaak;
- afbeeldingen en andere media;
- Open punten en toekomstige semantische annotaties;
- voetnoten, poëzie, gecentreerde tekst, kleinkapitalen en andere boektypografie;
- zoeken en vervangen;
- spelling;
- woordtelling en statistiek;
- AI-context;
- DOCX/EPUB/PDF/export;
- prestaties bij grote boeken;
- inspecteerbaarheid bij bugs;
- testbaarheid;
- mogelijkheid voor gebruikers om hun werk buiten QuietWriter terug te krijgen.

### DOCX-import als expliciet hoofdcriterium

Onderzoek DOCX niet als generiek rich-textformaat, maar vanuit wat romanschrijvers waarschijnlijk daadwerkelijk aanleveren.

Minimale importmatrix:

- gewone alinea's;
- Heading 1/2/3 en hoofdstuktitels;
- bold, italic, underline en strike waar relevant;
- scènebreuken;
- harde regeleinden;
- page breaks;
- lijsten voor uitzonderlijke gevallen;
- hyperlinks;
- afbeeldingen;
- afbeeldingsonderschriften waar herkenbaar;
- eenvoudige tabellen;
- documenttaal en basismetadata;
- Word-stijlen en style inheritance.

Daarnaast inventariseren wat we bewust **niet** willen ondersteunen of alleen met waarschuwing importeren, bijvoorbeeld track changes, comments, complexe velden, tekstvakken, zwevende objecten en exotische lay-out.

Een import mag normaliseren naar QuietWriter-semantiek. De gebruiker moet vooraf of achteraf duidelijk kunnen zien wat niet is overgenomen. Perfecte DOCX→QuietWriter→DOCX-reconstructie is geen doel.

### Open-source vergelijkingsonderzoek

Bestudeer minimaal:

- NEO;
- novelWriter;
- Manuskript;
- bibisco;
- één of meer aanvullende open-source schrijfapps wanneer hun opslag-/importarchitectuur relevant is.

Kijk per project naar:

- canoniek intern opslagformaat;
- scheiding tussen tekst en metadata;
- hoe hoofdstukken/scènes worden gemodelleerd;
- hoe DOCX wordt geïmporteerd;
- welke DOCX-features bewust worden genegeerd;
- hoe export wordt opgebouwd;
- hoe recovery/sync/backups worden opgelost;
- welke lessen bruikbaar zijn voor QuietWriter en welke niet.

### Harde randvoorwaarden

Tot dit onderzoek is afgerond:

- Markdown blijft de canonieke manuscriptbron;
- bestaande boeken worden niet gemigreerd;
- geen nieuw opslagformaat alleen voor een nieuwe feature introduceren;
- geen stille migratie;
- een toekomstige overgang moet expliciet, herstelbaar en terugwaarts doordacht zijn;
- gebruikersdata gaat vóór architectonische elegantie.

### Onderzoeksdocument

Het werkdocument staat in:

`documents/BOOK_FORMAT_ARCHITECTURE_RESEARCH.md`

Dit document bevat de huidige QuietWriter-analyse, open-source vergelijkingen, DOCX-scope, kandidaatarchitecturen en een expliciete reviewopdracht voor Claude/andere reviewers.

## 6. Productontwikkeling na/naast het formaatonderzoek

### 6.1 Schrijfdoelen en rustige voortgang
Hoge productwaarde. Geen streak-shaming, badges of motiverende popups.

### 6.2 Planning dichter bij het schrijven
Onderzoek naar spookalinea's / ghost paragraphs, altijd presentation-only.

### 6.3 Planning-polish op basis van echt gebruik
Scènes verplaatsen, inklapbare hoofdstukgroepen, compactere scènebewerking, eerste verschijning personages, locaties, relaties en aliassen.

### 6.4 Automatische `.qwbook`-back-ups
Dagelijks, handmatig, instelbare locatie en retention; back-up blijft output en geen tweede live bron.

## 7. Latere inhoudelijke ideeën

### Boektypografie
Voetnoten, poëzie/verzen, gecentreerde tekst, kleinkapitalen, harde spaties en bijzondere literaire opmaak.

### Export/publicatie
Echte exportpreview, half-title/schutblad, blanco pagina, meer TOC-niveaus, extra front/back matter en verdere afbeeldingsoptimalisatie.

### AI
Contextbudget, providercompatibiliteit, eenvoudigere Ollama-setup, voorstellen voor feiten/Open punten en aliasherkenning.

### Diagnostiek
Veilige diagnoseweergave zonder manuscriptinhoud, API-sleutels of gevoelige boekdata.

## 8. Distributie en platforms

### Nu
- 1.2.32 als vaste Windows-releasecandidate bevriezen;
- exacte buildomgeving en SHA-256 van EXE/portable ZIP vastleggen;
- exact dezelfde EXE controleren via Microsoft Security Intelligence en VirusTotal;
- alleen bij daadwerkelijke false positives de betreffende AV-leveranciers benaderen;
- daarna 1.2.32-bron naar de publieke repository promoveren en exact dezelfde geteste portable ZIP publiceren.

### Later
- Microsoft Store/MSIX onderzoeken als aanvullend distributiekanaal;
- SignPath Foundation eventueel opnieuw aanvragen wanneer QuietWriter aantoonbaar meer publieke adoptie/zichtbaarheid heeft;
- commerciële signing alleen overwegen als gebruik en kosten dat later rechtvaardigen.

## 9. Bewust niet bouwen

- AI als ghostwriter;
- Herschrijf selectie;
- autonome Boekgeheugenwrites;
- stille reparatie/migratie;
- future-format downgraden;
- agressieve media-cleanup;
- tweede onafhankelijke hoofdstukvolgorde;
- volwaardige coverdesigner;
- complexe DTP-editor;
- volledige Scrivener/Obsidian/worldbuilding-featurepariteit.

## 10. Beslisregels voor nieuwe features

Voor substantiële wijzigingen eerst vastleggen welk probleem wordt opgelost, welke persistente data verandert, hoe conflict/recovery/history werken, wat zoeken/spelling/export/AI zien en welke tests het contract bewaken.

De roadmap is een beslisdocument, geen verzamelbak voor iedere mogelijke feature.
