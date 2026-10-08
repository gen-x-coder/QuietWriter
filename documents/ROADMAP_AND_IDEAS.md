# QuietWriter — roadmap en ideeën

**Status:** canonieke roadmap vanaf QuietWriter 1.2.13  
**Laatste actualisatie:** 8 oktober 2026

Deze roadmap beschrijft alleen de actuele productrichting. Uitgebreide oude 1.0/v2-ontwerpen zijn bewaard in `ROADMAP_HISTORY_TO_1_2_13.md`.

## 1. Waar we nu staan

**QuietWriter 1.2.32** is de huidige publieke stabiele release. De 1.3-lijn is bevroren op **1.3.0-rc1**. Deze releasecandidate wordt als Windows portable build getest; bij groen wordt exact dezelfde binary de definitieve 1.3.0. Nieuwe features gaan daarna naar 1.4.0-dev.1.

**dev.24–dev.28:** Planning, schrijfdoelen en kerneditor zijn afgerond en breed gereviewd. **dev.29:** Windows- en kleine-scherm-hardening op basis van echte laptoptests: boeklaadfeedback, undo bij menselijke typesnelheid, responsieve geometrie, expliciete Integriteit en rustigere technische UI.

De grote manuscriptarchitectuurverbouwing is afgerond. Daarna is in 1.3 de **Boekenkast** gebouwd met meerdere planken, privéplanken, Presentatiemodus, snelle woordtellingcache en uitgebreide privacy-/recovery-hardening. De Windows-acceptatietest van de Boekenkast is afgerond zonder resterende blocker.

Vanaf **1.3.0-dev.11** zijn **schrijfdoelen en rustige voortgang** toegevoegd. Dagactiviteit is volledig opt-in; zonder expliciete keuze wordt niets bijgehouden. In **1.3.0-dev.18** startte de volgende productlaag: Planning dichter bij het schrijven, met strikt presentation-only Planninghulp in lege hoofdstukken. **dev.19** polijst de sceneweergave en meldt expliciet wanneer niet alle scènes in de beschikbare editorruimte passen.

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

## 3. Gerealiseerd in 1.3 — Boekenkast met planken en privacy

**Status: functioneel afgerond en Windows-geaccepteerd in 1.3.0-dev.10.**

De **Boekenkast** ondersteunt meerdere planken zodat een schrijver boeken logisch kan groeperen zonder dat QuietWriter daar één vaste betekenis aan oplegt. Een plank kan bijvoorbeeld een serie, genre, pseudoniem, projectgroep of persoonlijke verzameling zijn.

### Gerealiseerd gedrag

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

### Resterende Boekenkast-backlog

- eventueel per plank een subtiele **Nieuw boek**-actie als aanmaken-en-verplaatsen in de praktijk te omslachtig blijkt;
- cover-pixmapcache alleen als echte Windows-profielen daar later aanleiding toe geven;
- oude kaartwidgets vóór `deleteLater()` verbergen als er ooit zichtbare flikkering optreedt;
- incrementeel kaart-hergebruik/virtualisatie pas bij aantoonbaar zeer grote bibliotheken;
- overige polish en technische schuld staan in de dev-reviewdocumenten, maar sturen de productroadmap niet.

## 4. Afgeronde technische basis — documentmodel hardenen

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
**Actief in 1.3.0-dev.11.** Hoge productwaarde, maar volledig opt-in en zonder gamification.

V1-contract:
- woorddoel per boek en optionele gewenste einddatum in Boekdetails;
- rustige voortgang op de Boekenkast en in de bestaande woordtelling;
- lokale teller **vandaag geschreven** alleen als de gebruiker dit expliciet inschakelt;
- alleen positieve groei tussen geslaagde editor-opslagen telt mee; schrappen verlaagt het dagtotaal niet;
- uitzetten pauzeert het bijhouden maar wist de lokale historie niet en haalt later niets retroactief in;
- daggrens is lokale middernacht;
- geen dagdoel, streaks, badges, sprints, grafiek, rood/achterstandstaal of meldingen in v1;
- woorddoel/deadline zijn actuele intentie en blijven daarom behouden bij versieherstel.

Canoniek ontwerp: `documents/SCHRIJFDOELEN_DESIGN.md`.

### 6.2 UI-consistentie van Instellingen en formulieren
**Prioriteit: hoog; eerste Instellingen-pass uitgevoerd in 1.3.0-dev.16.** De vaste regel is nu: links naam + uitleg, rechts één controlzone; aan/uit-waarden gebruiken dezelfde afgeronde keuzevelden als andere instellingen en acties gebruiken de secundaire knopstijl.

Nog te doen in de bredere componentaudit:
- dezelfde regel nalopen op overige formulierpagina's naast Instellingen en Boekdetails;
- witte achtergronden alleen waar een invoer/control dat functioneel nodig heeft;
- spacing, veldbreedtes en hulpteksthiërarchie tussen oudere pagina's verder harmoniseren;
- previews en samengestelde controls alleen als uitzondering gebruiken wanneer ze functioneel echt iets toevoegen.
- **Hoog:** Zoeken/vervangen-paneel stabiliseren. Bij een actieve zoekterm stort de verticale layout nu in, `0 resultaten` en `Geen resultaten gevonden` zijn dubbelop en `Vervangen door` springt naar boven. Dit is een losstaand UI-probleem en moet in een eigen iteratie worden opgelost.
- **Polish:** kopiëren/plakken in de manuscripteditor mag uitsluitend tekst en opmaak meenemen. Na Ctrl+C/Ctrl+V mag de nieuw geplakte tekst niet geselecteerd blijven alsof de bronselectie is meegekopieerd.
- **Polish:** context-subnavigatie gebruikt één visuele regel: dezelfde achtergrond als de pagina, met selectie als lokaal accentvlak. Planning en hoofdstuknavigatie zijn in dev.20 als eerste gelijkgetrokken; overige contextmenu’s later nalopen.

### 6.3 Planning dichter bij het schrijven
**Fase 1 uitgevoerd in 1.3.0-dev.18 en uitgebouwd t/m dev.23.** Gekoppelde scènes verschijnen als presentation-only Planninghulp in een leeg hoofdstuk. De hulp wordt buiten het QTextDocument geschilderd en kan dus niet in manuscript, woordtelling, zoeken, spelling, export, AI-context of Undo terechtkomen. Instellingen > Uiterlijk kan de laag volledig verbergen.

De bestaande scènestatus vormt inmiddels de eenvoudige workflow **Idee / Uitgewerkt / Geschreven**. Dev.22 voegde naast Tekstbreedte een subtiele knop **Planning** toe waarmee de schrijver ook tijdens bestaand manuscript gekoppelde scènes en hun status kan bekijken en een scène bewust als Geschreven kan markeren. Dev.23 maakt die overlay een betrouwbare toggle, schaalt hem mee met de editor en trekt statuslabels en hoofdstukscrollbar visueel gelijk. Geen automatische detectie: de schrijver bepaalt zelf wanneer een scène klaar is.

Vervolg pas na praktijkgebruik: scènegerichte plaatsing na echte scènebreuken en nog niet geschreven scènes onder het laatste geschreven segment.

### 6.4 Planning-polish op basis van echt gebruik
Scènes verplaatsen, inklapbare hoofdstukgroepen, compactere scènebewerking, eerste verschijning personages, locaties, relaties en aliassen.

### 6.5 Automatische `.qwbook`-back-ups
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
- 1.2.32 is de huidige publieke stabiele Windows-release;
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
