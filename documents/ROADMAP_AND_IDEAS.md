# QuietWriter — roadmap en ideeën

**Status:** canonieke roadmap vanaf QuietWriter 1.2.13  
**Laatste actualisatie:** 15 oktober 2026 (1.5.1)

Deze roadmap beschrijft alleen de actuele productrichting. Uitgebreide oude 1.0/v2-ontwerpen zijn bewaard in `archive/research/ROADMAP_HISTORY_TO_1_2_13.md`.

## 1. Waar we nu staan en wat er komt

**1.5.1** is de basis. De eigen updater is vervangen door Velopack: de portable build werkt zichzelf bij. De projectmap is opgeschoond; de geschiedenis staat in `archive/`. Werkwijze vanaf nu: Claude bouwt, ChatGPT reviewt, Lucas test op Windows (`../AGENTS.md`).

Het plan hieronder volgt uit de vergelijking met NEO (`research/NEO_VERGELIJKING_QW_1_6_CLAUDE.md`, §6). Het gekozen tempo: kleine patchversies binnen 1.5.x. De vroegere voorstellen "1.7" en "1.8" uit dat document heten hier 1.6 en 1.7 (nummering nog door Lucas te bevestigen).

### 1.5.x — kleine winst, weinig risico
- [x] **1.5.1** Updater vervangen door Velopack (portable); documentatie opgeschoond; `AGENTS.md`.
- [x] **1.5.2** Reviewbevindingen updater verwerkt; melding "nieuwere versie dan GitHub".
- [x] **1.5.2** Boektitel in de venstertitel, behalve voor boeken op een verborgen plank.
- [x] **1.5.2** Sneltoetsenoverzicht (Ctrl+/ of F1), met de tip dat andere software een sneltoets kan afpakken.
- [x] **1.5.2** Typografie tijdens het typen, per taal: `’` als apostrof, `‘…’`, gedachtestreepje (`--`), `…` (`...`). Met tests voor dialoog na een streep. Geen automatische hoofdletters (breekt op *'s avonds*).
- [x] **1.5.2** Boek dupliceren en exporteren vanaf de boekenkast (menu Boekacties).
- [x] **1.5.2** Schrijftest en een begrijpelijke melding bij Windows *Controlled Folder Access* bij het kiezen van de werkmap.
- [x] Echte bijwerkproef op Windows, lokaal via `QUIETWRITER_UPDATE_SOURCE` (15 oktober 2026, Lucas).
- [x] **1.6.1** Bijwerken eerst zelf testen: testkopie met pilotbestand, drie standen per release op GitHub (`research/UPDATE_UITROL_ONDERZOEK.md`).
- [ ] Echte bijwerkproef via GitHub met een pre-release (stand 1). **Vóór de 1.7-functies.**

### 1.6 — data en rust
- [x] **1.6.0** Retentie voor dagversies (instelbaar). *Geen* delta-opslag: alle lezers (Geschiedenis, herstel, `.qwbook`, Integriteit) verwachten complete versiemappen, en hardlinks zijn onbetrouwbaar in Dropbox/OneDrive. De retentie lost de onbegrensde groei op.
- [x] **1.6.0** Conflicten per hoofdstuk en niet-modaal; beide versies bewaren bij een echte botsing; open hoofdstuk herladen bij terugkeer.
- [x] **1.6.0** "Ongedaan maken" na hoofdstuk verwijderen. (Verplaatsen niet: dat zie je direct en sleep je terug.)
- [x] ~~Spellingsuggesties in een apart proces~~: vervallen na meting (zie backlog punt 6).
- [x] Praktijkproef met twee computers via Dropbox: Lucas, 18 oktober 2026 (1.7.0-dev16), geen Dropbox-fouten.

### 1.7 — planning dichter bij het verhaal
- [x] **1.7.0** Scènes in de tekst: besluit *geen* scène-ID in het manuscript; scène *n* = stuk na scènebreuk *n* (`design/SCENES_IN_TEXT_DESIGN.md`).
- [x] **1.7.0** Meelopende scènehulp (regel onder de tekst + "Volgende in Planning" na de laatste breuk); "ongeplande scènes" met **Toevoegen aan Planning** (omgekeerd plannen).
- [x] **1.7.0** Personages per hoofdstuk herkennen (naam, voornaam, *Ook bekend als*), met "voor het eerst"; niets hernoemen.
- [x] **1.7.0** Exportdoel "Inzenden" (standaard manuscriptopmaak, ook anoniem).
- [ ] Na praktijkgebruik: is de volgorde-koppeling genoeg, of is een anker in Planning nodig (optie B in het ontwerp)?

- [x] **1.7.0** Zoekresultaten leesbaar: stukje rond de treffer binnen de alinea, treffer vet, hoofdstuk alleen bij een nieuw hoofdstuk, geen horizontale balk.

### Backlog, in de volgorde van Lucas (15 oktober 2026)
Nieuw werk hangt onder 1.7.0 tot Lucas vindt dat 1.7.0 genoeg bevat. Pas dan volgen de bijwerkproef via GitHub (pre-release) en de proef met twee computers.
1. ~~Hulp voor vertalers.~~ **1.7.0:** Instellingen → Vertalingen (vergelijken, invullen, opslaan, exporteren en importeren) + `tools/merge_translation.py` + `TRANSLATING.md`. Meervoudsvormen bewust nog niet.
2. ~~Woordenboeken installeren zonder handwerk.~~ **1.7.0:** vaste, gecontroleerde lijst (12 talen, LibreOffice-woordenboeken op één commit, SHA-256 per bestand), downloaden vanuit Instellingen en de eerste start. **dev14:** 35 talen en bijwerken (vergelijking met de controlesom, nooit online kijken).
3. ~~Voetnoten.~~ **1.7.0:** `^[tekst]` op de plek in de tekst, Ctrl+Alt+F; echte Word-voetnoten in DOCX en Inzenden, noten per hoofdstuk in EPUB en PDF, DOCX-import leest Word-voetnoten. Zie `documents/design/FOOTNOTES_DESIGN.md`.
4. ~~Omslagen op basis van een seed.~~ **1.7.0:** boeken zonder eigen omslag krijgen in de Boekenkast een rustig patroon en kleur uit de boek-ID, met titel en auteur. Alleen weergave, niets opgeslagen of geëxporteerd.
5. ~~Een rustige grafiek van de afgelopen 30 dagen.~~ **1.7.0 (dev13):** Boekdetails → Schrijfdoel → *Laatste 30 dagen*, alleen bij de opt-in dagtelling. Ontwerp: `design/RUSTIGE_GRAFIEK_VOORSTEL.md`.
6. ~~Spellingsuggesties in een apart proces.~~ **Vervallen (Lucas, 16 oktober 2026):** gemeten in dev12, de interface haperde hooguit ±30 ms; een apart proces kost ±230 MB extra en maakt de voorstellen niet beter.
7. ~~In- en uitzoomen van de hele interface.~~ **1.7.0:** Instellingen → Uiterlijk → Interfacegrootte (80–175%), na herstart. Live zoomen (Ctrl +/−) kan Qt niet voor de hele interface.
8. ~~Paperback-PDF met woordafbreking~~, 9. ~~`inbox.md`~~, 10. ~~Voorlezen~~: **voorlopig niet** (Lucas, 16 oktober 2026). Paperback: opmaken kan na export in Word of een ander programma; QuietWriter wordt geen publicatieprogramma. `inbox.md`: past niet in de filosofie. Voorlezen: offline stemmen klinken blikkerig, en online stemmen willen we niet.

### Volgorde vanaf dev14 (Lucas, 16 oktober 2026)
1. ~~Spellingcontrole in de notenstrook.~~ **dev14.**
2. ~~Woordenboeken bijwerken en meer talen in de downloadlijst.~~ **dev14.**
3. ~~De opmaak van oudere formulieren gelijktrekken (6.2).~~ **dev15:** `ui/page_layout.py`, zie `UI_REFERENCE.md` → Eén paginavorm.
4. ~~Planning bijschaven: scènes verplaatsen, hoofdstukgroepen inklappen (6.4).~~ **dev15:** slepen (ook naar een ander hoofdstuk), *Verplaatsen naar*, ↑/↓, ingeklapte groepen per boek onthouden, *Alles in-/uitklappen*.
5. ~~Controle per pagina en paneel op designtaal en foutjes.~~ **dev15** (zie CHANGELOG). Tagline: "Rustig schrijven. Heldere boeken." (besluit Lucas; documenten gelijkgetrokken).

Daarna, ter afsluiting van 1.7.0: ~~ChatGPT-review van deel E en F~~ (verwerkt in dev16, herreview akkoord), ~~de proef met twee computers via Dropbox~~ (18 oktober, geen fouten), en als laatste **de bijwerkproef via GitHub met een pre-release** (stand 1).

### Naar voren gehaald uit 1.8.0 (Lucas, 18 oktober 2026)
- ~~Een echt voorbeeld van de export vóór je exporteert.~~ **1.7.0 (dev18):** *Voorbeeld bekijken* op de exportpagina en in de wizard; tijdelijke map, niets onthouden.
- ~~De Ollama-installatie eenvoudiger maken.~~ **1.7.0 (dev18):** *Ollama instellen* in Instellingen → AI Meelezer: zoeken, downloadlink, korte modellenlijst naar werkgeheugen, downloaden via Ollama. De modellenlijst staat in `ai/ollama_setup.py` (`RECOMMENDED_MODELS`) en moet bij een release nagekeken worden.

### 1.8.0
- Nog leeg.

### Historische status (tot 1.5.0-dev.63)
QuietWriter 1.3.x en 1.4.0 zijn publiek uitgebracht. De 1.5.0-ontwikkellijn (dev.1–dev.63) bracht synchronisatieveiligheid en de vernieuwde Meelezer, maar is niet als 1.5.0 uitgebracht; 1.5.1 is de eerste release van die lijn. Zie `CHANGELOG.md`.

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
- updatecontrole en zelf bijwerken (Velopack, vanaf 1.5.1);
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

`documents/archive/research/BOOK_FORMAT_ARCHITECTURE_RESEARCH.md`

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
- geen dagdoel, streaks, badges, sprints, rood/achterstandstaal of meldingen in v1 (een rustige 30-dagengrafiek in Boekdetails kwam in 1.7.0);
- woorddoel/deadline zijn actuele intentie en blijven daarom behouden bij versieherstel.

Canoniek ontwerp: `documents/design/SCHRIJFDOELEN_DESIGN.md`.

### 6.2 UI-consistentie van Instellingen en formulieren
**Prioriteit: hoog; eerste Instellingen-pass uitgevoerd in 1.3.0-dev.16.** De vaste regel is nu: links naam + uitleg, rechts één controlzone; aan/uit-waarden gebruiken dezelfde afgeronde keuzevelden als andere instellingen en acties gebruiken de secundaire knopstijl.

Nog te doen in de bredere componentaudit:
- ~~dezelfde regel nalopen op overige formulierpagina's naast Instellingen en Boekdetails~~ (1.7.0-dev15);
- witte achtergronden alleen waar een invoer/control dat functioneel nodig heeft;
- spacing, veldbreedtes en hulpteksthiërarchie tussen oudere pagina's verder harmoniseren;
- previews en samengestelde controls alleen als uitzondering gebruiken wanneer ze functioneel echt iets toevoegen.
- **Opgelost (dev.24, gecontroleerd in 1.7.0):** Zoeken/vervangen-paneel stabiliseren. Bij een actieve zoekterm stort de verticale layout nu in, `0 resultaten` en `Geen resultaten gevonden` zijn dubbelop en `Vervangen door` springt naar boven. Dit is een losstaand UI-probleem en moet in een eigen iteratie worden opgelost.
- **Opgelost (dev.24, gecontroleerd in 1.7.0):** kopiëren/plakken in de manuscripteditor mag uitsluitend tekst en opmaak meenemen. Na Ctrl+C/Ctrl+V mag de nieuw geplakte tekst niet geselecteerd blijven alsof de bronselectie is meegekopieerd.
- **Polish:** context-subnavigatie gebruikt één visuele regel: dezelfde achtergrond als de pagina, met selectie als lokaal accentvlak. Planning en hoofdstuknavigatie zijn in dev.20 als eerste gelijkgetrokken; overige contextmenu’s later nalopen.

### 6.3 Planning dichter bij het schrijven
**Fase 1 uitgevoerd in 1.3.0-dev.18 en uitgebouwd t/m dev.23.** Gekoppelde scènes verschijnen als presentation-only Planninghulp in een leeg hoofdstuk. De hulp wordt buiten het QTextDocument geschilderd en kan dus niet in manuscript, woordtelling, zoeken, spelling, export, AI-context of Undo terechtkomen. Instellingen > Uiterlijk kan de laag volledig verbergen.

De bestaande scènestatus vormt inmiddels de eenvoudige workflow **Idee / Uitgewerkt / Geschreven**. Dev.22 voegde naast Tekstbreedte een subtiele knop **Planning** toe waarmee de schrijver ook tijdens bestaand manuscript gekoppelde scènes en hun status kan bekijken en een scène bewust als Geschreven kan markeren. Dev.23 maakt die overlay een betrouwbare toggle, schaalt hem mee met de editor en trekt statuslabels en hoofdstukscrollbar visueel gelijk. Geen automatische detectie: de schrijver bepaalt zelf wanneer een scène klaar is. *(1.7.0: de knop en de popup zijn weggehaald, want dubbelop met In dit hoofdstuk; **✓ Klaar** staat daar nu bij elke scène.)*

Vervolg pas na praktijkgebruik: scènegerichte plaatsing na echte scènebreuken en nog niet geschreven scènes onder het laatste geschreven segment.

### 6.4 Planning-polish op basis van echt gebruik
~~Scènes verplaatsen, inklapbare hoofdstukgroepen~~ (1.7.0-dev15), compactere scènebewerking, eerste verschijning personages, locaties, relaties en aliassen.

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
- volledige Scrivener/Obsidian/worldbuilding-featurepariteit;
- een eigen updater of installer (Velopack doet dit sinds 1.5.1);
- Enter-Enter-Enter als structuurcommando;
- AI-gegenereerde omslagen;
- een mobiele app.

## 10. Beslisregels voor nieuwe features

Voor substantiële wijzigingen eerst vastleggen welk probleem wordt opgelost, welke persistente data verandert, hoe conflict/recovery/history werken, wat zoeken/spelling/export/AI zien en welke tests het contract bewaken.

De roadmap is een beslisdocument, geen verzamelbak voor iedere mogelijke feature.

## Talen en vertalingen — polish

**Dev.16:** gewone informatie-, waarschuwing- en foutmeldingen in de UI zijn centraal gelokaliseerd. De vijf bestaande taallijsten blijven intact. Vervolg: vraagdialogen (Ja/Nee/Annuleren), dubbelingen en langlopende UI-teksten analyseren vóór sleutels verwijderd worden.

- Controleer alle dialoogknoppen op standaardteksten uit Qt (OK/Cancel/Yes/No) in de vijf talen.
- Inventariseer dubbele, ongebruikte en verouderde vertaalsleutels; hergebruik bestaande woorden waar de betekenis gelijk is.
- Controleer langere vertalingen bij kleine vensters en hoge DPI, zonder tekst stil af te kappen.
- Houd de gebruikersgerichte teksten begrijpelijk, kort en zonder technische termen.

### Spelling: suggesties zonder wachten (1.4 vervolg)

- Suggesties vanuit het spellingpaneel in een achtergrondwerker zoeken zodat het venster direct reageert.
- Alleen het resultaat van het nieuwste woord tonen; oudere resultaten negeren.
- Het suggestiebudget behouden, ook als het zoekwerk naar een worker verhuist.
- Voor vrijgave Windows- en Qt-test met lange woorden en meerdere woordenboekbronnen.

### Spelling: woordenboeken zonder handwerk (backlog na Claude-review)

**Doel:** de gebruiker hoeft Hunspell-bestanden nooit zelf te zoeken, te downloaden of te kopiëren. Dit is nog niet geïmplementeerd.

1. Tijdens eerste gebruik alle werkelijk beschikbare woordenboeken scannen: OpenTaal in de distributie, bestaande Office-installaties en woordenboeken in de gekozen werkmap. Geen niet-bestaand `nl_NL` als gevonden presenteren.
2. Per taal tonen: officiële woordenboeknaam, herkomst, versie (indien beschikbaar), licentie en beschikbaarheidsstatus. Noem het Nederlandse bundelwoordenboek **OpenTaal (meegeleverd)**, niet een eigen QuietWriter-woordenboek.
3. Geen woordenboek? Bied indien beschikbaar het meegeleverde OpenTaal aan; ontbreekt ook dat, geef een heldere keuze: later instellen of een beschikbaar woordenboek via een vertrouwde catalogus installeren. Verberg de ontbrekende afhankelijkheid niet.
4. In Instellingen een ingebouwde catalogus met installeren, voortgang, annuleren, verwijderen en optionele updates. Alleen geverifieerde bronnen; `.dic` én `.aff` en licentie/attributie controleren.
5. Download in tijdelijke stagingmap met limiet, checksum/integriteitscontrole en veilige atomische publicatie; nooit bestaande woordenlijsten beschadigen bij netwerkfout. Geen willekeurige archiefpaden uitpakken.
6. Wijzig geen Office-installaties. Eigen downloads in de QuietWriter-werkmap, met duidelijke keuze van taal, bron en persoonlijke woordenlijst. Geen stille download of verbinding zonder toestemming.
7. Bij wisselen van woordenboek tijdens achtergrond-suggesties oude resultaten veilig negeren. Test op Windows met grote woordenboeken, snelle wisselingen en ontbrekende `.aff`-bestanden.
8. Voeg expliciete herstel-/foutmeldingen toe voor ontbrekend woordenboek, onbereikbare catalogus en onvoldoende schijfruimte, in vijf talen.


## Synchronisatie en meerdere computers (review dev.32, 13 oktober 2026)

Gebaseerd op Claude’s `sync532.py`: een nieuwe Dropbox/OneDrive-boekenmap kan gedeeltelijk binnenkomen. Deze bevindingen zijn vastgesteld met een nagebootste synchronisatie, niet met een echte Dropbox-installatie.

1. **HOOG — ontbrekend hoofdstuk nooit als leeg interpreteren.** Een wel ontvangen `book.json` met nog ontbrekend Markdown-bestand toonde voorheen een lege editor en liet opslaan toe. In de dev.33-reviewbron is een eerste fail-closed correctie aangebracht: expliciete fout, editor alleen-lezen, opslaan blokkeren. Nog op Windows/Qt en echte cloudsynchronisatie testen.
2. **MIDDEN — boekenkast verversen.** Dev.35 bevat een handmatige knop, F5 en een periodieke lichte metadatawijzigingscontrole (8 seconden zolang de boekenkast zichtbaar is). Praktijkproef op Windows en Dropbox blijft nodig; geen claim dat de clouddienst klaar is.
3. **MIDDEN — rustige synchronisatiestatus.** Als `book.json` ontbreekt of een online-only placeholder nog niet lokaal beschikbaar is, toon een neutrale hint in plaats van een enge leesfout. Geen claim dat Dropbox klaar is: generieke synchronisatiestatus is niet betrouwbaar beschikbaar.
4. **MIDDEN — conflictkopieën zichtbaar maken.** In dev.36 is een begrensde alleen-lezen zoekfunctie op Integriteit & herstel toegevoegd, met ‘Openen in Verkenner’. Geen automatische wijzigingen. Nog open: herkenning van meer OneDrive-naamconventies en Windows-visuele acceptatie.
5. **LAAG — praktische gebruikershulp.** Leg uit waarom twee computers niet tegelijk in hetzelfde boek moeten schrijven, waarom de boekenmap het beste lokaal beschikbaar blijft en hoe je controleert of synchronisatie is afgerond.

**Acceptatie:** geen stille lege hoofdstukken, geen verlies van bronbestanden, geen automatische creatie van een ontbrekend gesynchroniseerd manuscript; rustige, vertaalde meldingen; Qt- en Windows-test, plus handmatige proef op twee echte computers.

### Dev.35 vervolgaandachtspunten
- Conflictkopieën worden op de boekenkast gesignaleerd, maar een gericht overzicht met bestandslocaties en “Openen in Verkenner” bij Integriteit & herstel blijft op de backlog (midden).
- Zoeken en vervangen: ontbrekende hoofdstukken blokkeren de operatie; volledige meerhoofdstuk-atomiciteit bij gelijktijdige externe wijzigingen vereist apart transactioneel ontwerp (hoog voor toekomstige iteratie).
- Synchronisatiestatus is heuristisch en kan niet aangeven of Dropbox/OneDrive volledig klaar is.

### Openstaande praktijkacceptatie — twee computers (dev.36)

De echte Dropbox/OneDrive-proef op desktop en laptop is bewust uitgesteld: momenteel is testen met twee computers niet mogelijk. Zodra het kan: boek A maken, op laptop gedeeltelijke synchronisatie afwachten, controleren dat ontbrekende hoofdstukken niet als leeg geopend of opgeslagen worden, wachten op volledige synchronisatie en controleren dat de boekenkast automatisch of via F5 ververst. Ook online-only placeholders en conflictkopieën beoordelen. Deze acceptatietest is **niet uitgevoerd** en blijft open.

**Hoog open:** alles vervangen over meerdere hoofdstukken is nog niet transactioneel bij externe wijzigingen tussen de afzonderlijke saves. Geen volledige atomariteit claimen voordat een transactie- of preconditioneel batchprotocol is gebouwd en getest.
