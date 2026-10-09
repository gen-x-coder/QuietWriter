## 1.3.1-dev.1 — woordenboekbron kiezen voor spellingscontrole

- start een aparte 1.3.1-hotfixlijn vanaf de stabiele 1.3.0-code, los van de doorlopende 1.4-ontwikkeling;
- Instellingen > Spelling laat naast de taal nu ook de gevonden woordenboekbron kiezen;
- meerdere woordenboeken voor hetzelfde locale blijven tegelijk beschikbaar in plaats van vooraf te worden weggefilterd;
- ondersteunde bronnen: Meegeleverd, ONLYOFFICE, LibreOffice, OpenOffice en zelf toegevoegde compatibele Hunspell-bestanden;
- de gekozen bron wordt lokaal bewaard in `spell_dictionary_source` en valt veilig terug wanneer die bron later ontbreekt;
- regressietests en een expliciete 1.4-overdrachtsnotitie voorkomen dat de hotfix bij verdere ontwikkeling verloren gaat;
- de gemelde crash met het meegeleverde Nederlandse woordenboek is hiermee nog niet als root cause verklaard: deze devbuild maakt gericht vergelijken en reproduceren mogelijk.

## 1.3.0 — releasecandidate freeze voor de definitieve release

- bevriest de inhoud van 1.3.0 na de Windows-/laptopacceptatie van dev.29;
- bevat Boekenkast met planken, Presentatiemodus, schrijfdoelen, Planninghulp en de Planning-overlay;
- bevat de afgeronde editorfixes voor undo en veilig intern plakken met scènebreuken;
- bevat de kleine-scherm-, laadfeedback-, thema- en Integriteitspolish uit dev.29;
- bedoeld voor de Windows portable releasecandidate; bij groen wordt exact dezelfde binary gepromoveerd naar 1.3.0.

## 1.3.0-dev.29 — Windows- en kleine-scherm-hardening

- toont een echte `Boek laden…`-popup rond de bestaande boek-inleesfase; geen cloud- of netwerkdetectie;
- maakt undo bij menselijk typen platformonafhankelijk door woorden/pauzes als expliciete undo-grenzen te gebruiken;
- maakt het hoofdvenster responsiever op kleinere Windows-schermen en laat instellingenrijen verder krimpen;
- gebruikt voor de hoofdstukselectie de actieve themakleur in plaats van de Windows-highlightkleur;
- laat de synchronisatiewaarschuwing in Instellingen zijn hoogte aanpassen aan de werkelijke breedte;
- voert Integriteit alleen nog uit na `Integriteit controleren`; tijdens de controle staat de knop op `Controleren…` en is hij uitgeschakeld;
- verwijdert gewone bronpad-/bestandsmeldingen uit Schrijverspersona, Boekprofiel en Boekgeheugen;
- maakt de Thinking-keuze volledig `Modelstandaard / Uitgeschakeld`;
- verwijdert `~/.qttest` alleen wanneer QuietWriter die testmap zelf voor de suite heeft aangemaakt.

## 1.3.0-dev.28 — Kerneditor afronden en kleine polish

- Ctrl+Z behandelt ononderbroken typen weer als een natuurlijke bewerking in plaats van één letter per stap.
- Intern kopiëren/plakken bewaart nu ook scènebreuken samen met vet/cursief-opmaak.
- Updatecontrole herkent de definitieve 1.3.0 als nieuwer dan een 1.3.0-dev-build.
- Opstartscherm toont tijdens de echte boekinleesfase `Boeken laden…`; er is geen Dropbox/OneDrive/netwerkdetectie toegevoegd.
- Kleine polish gebundeld: enkelvoud `1 boek`, minimaal `ongeveer 1 per dag`, duidelijker Thinking-label, alleen open scènes in automatische Planninghulp, nooit halve ghostscènes, compacte lege Planning-flyout en testartefact-opruiming.
- `library.json` is ongewijzigd.

## 1.3.0-dev.27 — Hardening na brede dev.26-review

- Hardening na de brede dev.26-review: Qt-testverwachtingen bijgewerkt naar de bedoelde UI.
- "Vandaag geschreven bijhouden" is alleen nog een apparaatinstelling in Instellingen; Boekdetails kan deze opt-in niet meer stil overschrijven.
- Keuze-, getal- en datumvelden wijzigen niet meer door scrollen zolang ze geen focus hebben.
- Editor, hoofdstukboom en boekomslagen gebruiken de actieve profielinstellingen voor thema/typografie.
- Lege Planning-flyout heeft geen grijs filler-vlak meer en blokkeert Qt-mouse-replay bij sluiten.
- `library.json` is ongewijzigd.

## 1.3.0-dev.26 — Acceptatiecorrectie en Claude-reviewbasis

- Planning-flyout zonder gekoppelde scènes lijnt titel, uitleg en lege melding nu compact bovenaan uit.
- Geen functionele wijziging aan Planning, zoeken/vervangen, plakken of schrijfdoelen ten opzichte van dev.25.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.26.
- Gerichte Claude-reviewopdracht toegevoegd voor code-, runtime- en visuele regressietests over de recente 1.3-iteraties.

## 1.3.0-dev.25 — Laatste acceptatiepolish vóór Claude-review

- Planning-knop blijft zichtbaar bij een gewoon hoofdstuk zolang Planninghulp aan staat, ook als nog geen scènes aan dat hoofdstuk gekoppeld zijn.
- Planning-flyout toont in dat geval neutraal: `Geen planning voor dit hoofdstuk.`
- De lege resultatenzone van Zoeken en vervangen gebruikt dezelfde paneelachtergrond als de normale resultatenlijst.
- Geen wijzigingen aan manuscriptdata, Planningdata of `library.json`.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.25.

## 1.3.0-dev.24 — Editor-polish vóór review

- Planning-overlay is smaller en hoger zodat hij minder manuscript bedekt.
- Planning-knop is volledig verborgen wanneer Planninghulp in editor is uitgeschakeld.
- Zoek/vervang-paneel houdt een vaste resultatenzone; nul treffers laat de vervangsectie niet meer omhoog springen.
- Bij nul treffers wordt niet langer zowel `0 resultaten` als `Geen resultaten gevonden` getoond.
- Intern Ctrl+C/Ctrl+V behoudt tekst/opmaak maar laat de geplakte tekst niet geselecteerd achter.
- De bestaande Planning-toggle wordt niet verder gepatcht vóór gerichte Claude-review.
- Geen wijziging aan Planning-opslag, manuscriptopslag of `library.json`.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.24.

## 1.3.0-dev.23 — Planning-overlay polish

- Planning-knop is nu een echte toggle: nogmaals klikken sluit de overlay betrouwbaar.
- De Planning-overlay schaalt mee met de editor en gebruikt maximaal ongeveer de helft van de editorbreedte.
- Zichtbare scènestatussen gebruiken consequent hoofdletters: Idee, Uitgewerkt en Geschreven.
- De hoofdstukscrollbar kleurt nu ook de groove en lege track met de pagina-achtergrond.
- Geen wijziging aan Planning-opslagformaat, manuscriptopslag of `library.json`.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.23.

## 1.3.0-dev.22 — Planning tijdens het schrijven

- Subtiele Planning-knop naast Tekstbreedte opent een tijdelijke overlay voor het huidige hoofdstuk.
- Overlay toont alle gekoppelde scènes met status; open scènes kunnen bewust als Geschreven worden gemarkeerd.
- Ghosttekst toont voortaan ook scènestatus.
- Scènestatus is een vaste dropdown en geen vrije tekst.
- Bij Personages wordt het eerste opgeslagen personage standaard geselecteerd.
- Scrollbar-track van de hoofdstukkenlijst volgt de pagina-achtergrond.
- Geen automatische scene-herkenning; Planning blijft los van manuscript, zoeken, export, AI-context en Undo.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.22.

## 1.3.0-dev.21 — Planningworkflow verduidelijkt

- Het Inhoud-lipje gebruikt nu dezelfde pagina-achtergrond als de editor en voelt niet langer als een los paneel.
- De uitleg boven Planning, Personages en Outline beschrijft nu ook hoe Planning samenwerkt met de planninghulp in lege hoofdstukken.
- Bestaande scène-status (idee / uitgewerkt / geschreven) wordt in Outline duidelijk zichtbaar als rustige statusbadge; geschreven scènes krijgen een vinkje.
- Dit is alleen voorbereiding op de volgende workflowstap: status is nog niet via één klik afvinkbaar en er is nog geen Planning-overlay in de editor.
- Geen wijziging aan Planning-opslagformaat, manuscriptopslag, `library.json` of ghostdata.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.21.

## 1.3.0-dev.20 — Planningduidelijkheid en contextnavigatie

- Personages en Outline hebben nu direct onder de paginatitel een korte uitleg van hun doel.
- De personageselectie toont alleen namen, is ruimer en volgt visueel dezelfde rustige selectiegrammatica als Instellingen.
- Planning-subnavigatie en de hoofdstuknavigatie gebruiken nu de pagina-achtergrond; selectie blijft lokaal zichtbaar.
- De losstaande Ctrl+C/Ctrl+V-selectiebug is op de polish-backlog gezet en bewust niet in deze iteratie gewijzigd.
- Geen wijziging aan Planning-opslag, manuscriptopslag, `library.json` of ghostlogica.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.20.

## 1.3.0-dev.19 — Planninghulp polish

- `Locatie` en `Personages` staan in de Planninghulp voortaan ieder op een eigen regel.
- De ghostlaag reserveert ruimte voor een afsluitende melding als niet alle gekoppelde scènes in het zichtbare editorvlak passen; scènes verdwijnen daardoor niet meer stilletjes.
- De melding verwijst expliciet naar Planning en toont hoeveel scènes nog niet zichtbaar zijn.
- Het zoek/vervangpaneel heeft een losstaand layoutprobleem dat tijdens Windows-testen is gevonden; dit is hoog op de UI-backlog gezet en bewust niet in deze ghost-polishbuild gewijzigd.
- Geen wijziging aan manuscriptopslag, `library.json`, woordtelling, export, AI-context of Undo.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.19.

## 1.3.0-dev.18 — Planninghulp in lege hoofdstukken

- Eerste fase van "Planning dichter bij het schrijven": gekoppelde scènes uit Planning verschijnen als zachte hulptekst in een leeg hoofdstuk.
- De hulp is strikt presentation-only: niets wordt aan het QTextDocument of Markdown toegevoegd en de tekst telt niet mee, verschijnt niet in zoeken/spelling/export/AI-context en raakt Undo niet.
- Zodra echte tekst in het hoofdstuk staat verdwijnt de Planninghulp; bij terugkeer naar een leeg hoofdstuk verschijnt hij weer.
- Instellingen > Uiterlijk bevat Planninghulp in editor: Tonen/Verbergen; standaard staat de hulp aan.
- Terugkeren vanuit Planning ververst de hulp direct.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.18.
- `library.json` en manuscriptbestanden zijn door deze functie ongewijzigd.

## 1.3.0-dev.17 — Rustigere lettertypepreview

- De preview van het schrijflettertype is hoger en heeft meer binnenruimte.
- De preview toont alleen nog voorbeeldtekst; de dubbele vermelding van lettertype en puntgrootte is verwijderd.
- Geen functionele wijzigingen aan schrijftypografie, schrijfdoelen of `library.json`.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.17.

## 1.3.0-dev.16 — Consistente Instellingen-formulieren

- Losse aan/uit-checkboxes in Instellingen zijn vervangen door rustige, afgeronde keuzevelden binnen dezelfde controlkolom als taal, thema en andere waarden.
- De keuzes gebruiken per instelling natuurlijke tekst zonder de onderliggende instellingen of defaults te veranderen.
- Actieknoppen zoals Nu controleren, Map kiezen, Modellen ophalen en woordenboekacties gebruiken consequent de secundaire knopstijl.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.16.
- `library.json` is ongewijzigd.

## 1.3.0-dev.15 — Datum- en omslagpolish

- De einddatumkiezer volgt nu dezelfde QuietWriter-veldopmaak als andere invoercontrols.
- Boekomslag toont zonder eigen afbeelding een duidelijk previewvak met `Geen omslag`.
- Omslag verwijderen is alleen actief wanneer er daadwerkelijk een eigen omslag aanwezig of nieuw gekozen is.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.15.
- `library.json` en de functionele schrijfdoelenlogica zijn ongewijzigd.

## 1.3.0-dev.14 — Rustigere schrijfdoelbediening

- De losse systeemcheckboxes bij Gewenst klaar op en Vandaag geschreven zijn vervangen door gewone keuzelijsten die aansluiten bij de rest van Boekdetails.
- Einddatum gebruikt nu de keuze Geen einddatum / Einddatum gebruiken; de datumkiezer verschijnt als dezelfde rustige formulierbediening.
- Vandaag geschreven gebruikt Niet bijhouden / Bijhouden; de opt-in, bewaargedrag en dagtelling zijn functioneel ongewijzigd.
- De knoppen bij Boekomslag gebruiken nu de bestaande secundaire knopstijl.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.14.
- `library.json` is ongewijzigd.

## 1.3.0-dev.13 — Boekdetails-formulierpolish

- Schrijfdoel en Boekomslag gebruiken nu hetzelfde label→control-formulierpatroon als de rest van Boekdetails; de kleine losse witte panelen zijn verwijderd.
- De zichtbare term "lokaal" is uit de optie voor Vandaag geschreven gehaald; de checkbox heet kortweg "Bijhouden".
- De uitleg van Schrijfdoel beschrijft alleen wat wordt bijgehouden en dat de bestaande telling bij uitschakelen behouden blijft.
- UI-consistentie van Instellingen en andere formulierpagina's staat nu expliciet hoog op de roadmap voor een aparte systematische polishronde.
- Publieke release blijft 1.2.32; actieve ontwikkellijn is 1.3.0-dev.13.
- `library.json` en de functionele schrijfdoelen-/dagtel-logica zijn ongewijzigd.

## 1.3.0-dev.12 — Boekdetails- en datum-UX voor schrijfdoelen

- Schrijfdoel en Boekomslag volgen nu het visuele tweekolomspatroon van Instellingen.
- Gewenste einddatum heeft een expliciete aan/uit-keuze en compacte datumkiezer.
- Een nieuwe datum begint op vandaag in plaats van 01-01-1900.
- Schrijfdoelen, dagtelling en opt-in-logica zijn functioneel ongewijzigd.
- Versie- en testmetadata bijgewerkt naar 1.3.0-dev.12.

## 1.3.0-dev.11 — Opt-in schrijfdoelen en rustige dagvoortgang

- Per boek een optioneel Woorddoel en gewenste einddatum toegevoegd aan Boekdetails.
- Boekenkast en editor tonen rustige doelvoortgang zonder meldingen of gamification.
- Lokale teller `vandaag geschreven` toegevoegd als expliciete opt-in; uitzetten bewaart historie maar stopt verzamelen en telt later niets retroactief in.
- Dagvoortgang telt alleen positieve groei tussen geslaagde editor-opslagen en blijft buiten de werkmap.
- Woorddoel en deadline blijven staan bij versieherstel.
- Canoniek ontwerp vastgelegd in `documents/SCHRIJFDOELEN_DESIGN.md`; roadmap/status bijgewerkt.
- Versie- en testmetadata bijgewerkt naar 1.3.0-dev.11.

## 1.3.0-dev.10 — Laatste releasepolish na Windows-acceptatie
- Boekenkast en Presentatiemodus zijn op Windows visueel en functioneel geaccepteerd; er zijn geen aanvullende functionele wijzigingen nodig.
- Cover-pixmapcaching blijft bewust op de backlog: de gemeten synthetische vertraging was in de echte Windows-test niet hinderlijk.
- De kopteksten van de Windows dependency-lockfiles verwijzen nu naar QuietWriter 1.3.0 in plaats van de oude 1.2.32 RC.
- Snapshot- en release-metadata bijgewerkt naar 1.3.0-dev.10.
- `README.md` en `README_EN.md` blijven bewust ongewijzigd.

## 1.3.0-dev.9 — Privacyvriendelijke woordtellingcache en testisolatie
- Persistente woordtellingcache gebruikt voortaan SHA-256-hashes van hoofdstukpaden als sleutels; boektitels en volledige paden worden niet meer in het cachebestand opgeslagen.
- Oude dev.8-cachekeys met volledige paden worden bij laden genegeerd en bij de eerstvolgende refresh vervangen door gehashte sleutels.
- Qt-tests draaien met `QStandardPaths` testmodus zodat testruns de echte lokale appdatamap niet langer vervuilen met tijdelijke cachebestanden.
- Geen wijzigingen aan Presentatiemodus, `library.json`, boekformaten of planklogica.

## 1.3.0-dev.8 — Robuuste Presentatiemodus en persistente woordtellingcache
- Presentatiemodus gebruikt nu de `QSettings`-opslag van het actieve runtimeprofiel; dev en productie houden hun status gescheiden.
- Ook onverwachte exceptions tijdens het sluiten van een privéboek zetten Presentatiemodus veilig terug naar **uit** en worden gelogd.
- De woordtellingcache wordt per werkmap lokaal in de appdatamap bewaard, zodat een nieuwe sessie ongewijzigde hoofdstukken niet opnieuw hoeft te tellen.
- Een ontbrekend, corrupt of niet-schrijfbaar cachebestand is niet fataal en leidt alleen tot opnieuw tellen.
- Covercaching blijft voorlopig buiten scope en wordt pas toegevoegd als de Windows-test met echte covers daar aanleiding toe geeft.

## 1.3.0-dev.7 — Presentatiemodus en snelle Boekenkast
- Demo-modus heet in de gebruikersinterface voortaan **Presentatiemodus**; de bestaande interne instellingssleutel blijft compatibel.
- Een open privéboek wordt bij inschakelen veilig opgeslagen en gesloten; de app keert terug naar de Boekenkast. Als sluiten mislukt, wordt Presentatiemodus weer uitgezet.
- `open_book()` weigert privéboeken zolang Presentatiemodus actief is, zodat ook toekomstige alternatieve open-routes fail-closed blijven.
- Woordtellingen van boekkaarten worden per hoofdstuk gecachet op bestandssignatuur (`mtime_ns` + grootte), waardoor ongewijzigde hoofdstukken niet bij iedere refresh opnieuw worden geparsed.
- Zoeken in de Boekenkast gebruikt een debounce van 200 ms.
- De Presentatiemodus-tooltip zegt expliciet dat de functie geen beveiliging is.

## 1.3.0-dev.6 — Duidelijke Demo-status en reviewmoment
- De Demo-modusknop toont nu expliciet **aan** of **uit** en heeft een zichtbare ingeschakelde stijl.
- De term **Demo-modus** blijft voorlopig staan; de volgende onafhankelijke review beoordeelt ook de productnaam en vertaalbaarheid.
- Performance is bewust nog niet op gevoel geoptimaliseerd. De Boekenkast wordt eerst gemeten/geprofileerd zodat alleen de echte bottlenecks worden aangepakt.
- Een gerichte Claude-reviewopdracht is opgenomen voor PySide6, Demo-modus, performance en naamgeving.

## 1.3.0-dev.5 — Boekenkast en Demo-modus
- De hoofdweergave heet voortaan **Boekenkast** in plaats van Boekenplank.
- Demo-modus toegevoegd als lokale presentatie-instelling; privéplanken en gekoppelde boeken verdwijnen uit de Boekenkast.
- Bewaarplaats en Prullenbak filteren in Demo-modus inhoud die aan een privéboek gekoppeld is.
- Boekenkast-search, aantallen en plank-actiemenu’s lekken in Demo-modus geen privéplanknamen of privéboeken.
- Onleesbare boekkaarten worden in Demo-modus niet getoond, omdat hun boek-id niet betrouwbaar kan worden vastgesteld.
- Backlog aangevuld met optioneel direct een nieuw boek op een gekozen plank aanmaken.

## 1.3.0-dev.4 — Boekenplank visuele polish

- Horizontale scrollbars binnen planken verwijderd. Boekkaarten lopen nu automatisch door naar een volgende rij, in dezelfde rustige richting als het Neo-ontwerp.
- De kleine `⋯`-knop naast **Openen** is vervangen door een duidelijke, volledige knop **Boekacties** onder **Openen**. Het verplaatsmenu blijft via die knop beschikbaar.
- Bevestigingsvensters voor het verwijderen/resetten van een plank gebruiken nu de QuietWriter-vertalingen voor **Ja** en **Nee** in plaats van de Engelstalige Qt-knoppen.
- Kaarten zijn iets hoger gemaakt zodat de twee duidelijke actieknoppen zonder visuele drukte passen.
- Geen wijzigingen aan het shelf-datamodel of de privacylogica in deze iteratie.

## 1.3.0-dev.3 — Neo-boekenplanken en sync-veilige migratie

- De laatste blocker vóór de boekenplank-UI is opgelost: ontbrekende `library.json`-metadata blijft bij queries alleen in het geheugen (`pending_migration`) en wordt pas bij een expliciete plank-/boekactie opgeslagen. Een half gesynchroniseerde tweede computer kan daardoor niet stil alle boeken openbaar maken.
- Demo-zichtbaarheid blijft fail-closed zolang de plankindeling nog niet canoniek is.
- Herstelacties weigeren een `library.json` van een nieuwere schemaversie te overschrijven.
- De lokale proceslock staat niet langer in de gesynchroniseerde werkmap, maar in de lokale tijdelijke map met een werkmapgebonden sleutel.
- De boekenplank is omgebouwd naar horizontale planken in de Neo-richting. Iedere plank heeft een vaste ID en een inline hernoembare naam.
- Nieuwe planken kunnen vanuit de boekenkast worden aangemaakt; planken kunnen privé worden gemaakt en niet-standaardplanken kunnen worden verwijderd. Boeken van een verwijderde plank gaan veilig terug naar de standaardplank.
- Elk boek heeft een compact actiemenu om het naar een andere plank te verplaatsen. Nieuwe en geïmporteerde boeken komen standaard op **Werk in uitvoering**.
- De standaardplank kan wel worden hernoemd, maar niet privé worden gemaakt of verwijderd.
- De boekenkast gebruikt per render één geladen shelf-snapshot, zodat plank- en boekzichtbaarheid uit dezelfde consistente toestand komen.
- Herstelmeldingen voor last-good, noodindeling en future-schema zijn in de boekenkast zichtbaar; metadatawaarschuwingen worden centraal getoond.
- Nieuwe regressietests dekken pending migration, expliciete eerste write, bescherming van future-schema en de lokale locklocatie.
- Demo-modus zelf is nog niet als UI-schakelaar toegevoegd; deze dev-versie richt zich op de normale Neo-boekenkast en het daarvoor vereiste fundament.

## 1.3.0-dev.2 — Plankfundament hardening

- Twee blockers uit de onafhankelijke dev.1-review opgelost vóór de UI-laag.
- Een verdwenen `library.json` migreert niet langer stil opnieuw wanneer een last-good-kopie bestaat; Demo-modus blijft dan fail-closed.
- Boekaanmaak, DOCX/Markdown-import, QWBOOK-import en prullenbakacties blijven succesvol als alleen de plankmetadata niet kan worden bijgewerkt; de plankfout wordt als niet-blokkerende waarschuwing bewaard.
- De standaardplank krijgt een deterministische ID zodat onafhankelijke 1.2→1.3-migraties dezelfde basis produceren.
- Lokale gelijktijdige plankbewerkingen worden met een lock geserialiseerd en na schrijven opnieuw gecontroleerd; geen stille verloren operaties meer in de race-test.
- Nieuwere `library.json`-schema's geven voor queries een veilige read-only/fail-closed toestand in plaats van een exception.
- Ongeldige boek→plankverwijzingen blijven leesbaar voor veilige fallback, maar blokkeren writes tot herstel.
- Expliciete herstel-API toegevoegd: last-good terugzetten of de indeling bewust resetten naar de standaardplank.
- Queries kunnen één geladen snapshot hergebruiken zodat een UI-render consistent kan blijven.
- Regressietests uitgebreid met privacyherstel, half-succesvolle boekoperaties, deterministische migratie, future-schema, recovery en multiprocessing-concurrency.

## 1.3.0-dev.1 — Fundament voor meerdere boekenplanken

- Nieuwe werkmap-brede `library.json` als enige bron van waarheid voor de relatie `book_id -> shelf_id`; `book.json` en `.qwbook` blijven vrij van lokale plankmetadata.
- Iedere werkmap krijgt één publieke standaardplank **Werk in uitvoering**; bestaande live boeken en boeken in de prullenbak worden bij de eenmalige migratie aan die plank gekoppeld zonder hun boekbestanden te wijzigen.
- Planken hebben vaste interne UUID's en hernoembare namen. Een boek hoort structureel bij precies één plank.
- De standaardplank kan niet privé worden gemaakt of verwijderd.
- Verplaatsen, hernoemen, privéstatus en verwijderen van planken worden als kleine operaties op de nieuwste schijfversie toegepast en atomair opgeslagen; een last-good-kopie biedt herstel bij beschadigde bibliotheekmetadata.
- Boeken in de prullenbak behouden hun planktoewijzing; definitief verwijderen ruimt de mapping op.
- De eerste centrale zichtbaarheidregels zijn aanwezig: privéplanken kunnen in Demo-modus worden gefilterd en ontbrekende/ongeldige relaties worden daar fail-closed behandeld. De Demo-UI zelf volgt in een volgende 1.3-dev iteratie.
- Nieuwe regressietests dekken migratie, export/import, prullenbak, corruptieherstel, synchronisatiegedrag en de kerninvarianten van het plankmodel.

## 1.2.32 — Migratiedialoog en releasepolish

- De Windows-RC-build gebruikt nu Python 3.12.10 met vastgepinde runtime- en PyInstaller-dependencies; stille dependency-upgrades zijn uit de buildroute verwijderd.
- Het buildscript initialiseert een aanwezige Visual Studio C++-toolchain automatisch via `vswhere` wanneer `cl.exe` nog niet in PATH staat.
- Iedere definitieve Windows-build schrijft een extern buildmanifest met broncommit, exacte packageversies en SHA-256 van EXE en portable ZIP.
- De dev-repo blijft bronopslag; GitHub Actions in de dev-repo zijn niet vereist voor deze RC.
- SignPath Foundation-aanvraag is afgewezen wegens nog onvoldoende publieke adoptiesignalen; de releasekoers is aangepast naar een vaste unsigned Windows-RC met false-positive/reputatiecontrole vóór publicatie.
- Projectdocumentatie en snapshotstatus bijgewerkt naar de afgeronde 1.2.32 releasecandidate; de finale onafhankelijke 1.2.31-review is opgenomen als ontwikkelreferentie.

- De eenmalige manuscriptsyntaxmigratie gebruikt nu volledig vertaalde QuietWriter-knoppen in plaats van Qt-standaardknoppen `Yes` en `Cancel`.
- De acties zijn expliciet: **Boek bijwerken** voert de veilige migratie uit en opent daarna het boek; **Niet openen** laat het boek volledig ongewijzigd en opent het niet.
- Ook de dialoog voor dubbelzinnige legacy-backslashes gebruikt de vertaalde knop **Niet openen**.
- Geen wijziging aan manuscriptsyntaxis, opslag of migratie-algoritme ten opzichte van 1.2.31.

## 1.2.31 — Finale hardening van manuscriptsyntax

- Onversioneerde boeken uit het 1.2.19–1.2.29 escape-tijdperk worden herkend aan veilige escapevingerafdrukken en krijgen alleen het syntaxprofiel; hun bronbytes worden niet opnieuw gemigreerd.
- Echte pre-escape-boeken wijzigen alleen backslashes die de huidige lezer anders zou verbergen; bij uitsluitend dubbelzinnige backslashparen vraagt QuietWriter expliciet welke weergave behouden moet blijven.
- Publicatieteksten onder `publication/texts/` gaan mee in dezelfde expliciete syntaxmigratie en herstelcheckpoint.
- Structurele escapes aan het begin van een regel blijven atomair en onzichtbaar wanneer de afsluitende spatie wordt verwijderd.
- Plakken en vervangen midden in een regel maken geen onnodige lijst-/kop-/nummer-escapes meer.
- Shift+Enter schrijft weer een echte U+2028 soft break binnen dezelfde manuscriptalinea.
- Zoek-en-vervang slaat matches over die slechts één kant van een inline-opmaakspan zouden verwijderen, zodat geen losse `**`/`*`-markers achterblijven.
- Selecties die precies binnen een escape eindigen nemen het volgende zichtbare teken niet meer onbedoeld mee.
- Escape-cursorcontrole werkt per Qt-tekstblok in plaats van over het hele hoofdstuk.
- Blok-SDT-tekst uit DOCX wordt in documentvolgorde behouden; eindnoten worden expliciet gemeld als nog niet ondersteund.
- Nieuwe regressietests toegevoegd voor escape-era migratie, dubbelzinnige backslashes, contextgevoelig plakken en opmaakgrensvervanging.

## 1.2.30 — Legacy syntax veilig migreerbaar en laatste architectuuropruiming

- Oude boeken zonder `manuscript_syntax` krijgen bij openen een expliciete eenmalige updatevraag; annuleren laat het boek volledig ongemoeid.
- Voor de syntaxupdate wordt automatisch een volledige herstelversie gemaakt. Legacy backslashes worden conservatief verdubbeld zodat de zichtbare tekst onder `escape-v1` gelijk blijft.
- Mislukt de cross-file syntaxmigratie, dan probeert QuietWriter het live boek direct uit de vooraf gemaakte checkpoint te herstellen.
- Nieuwe golden regressietests dekken UNC-paden, Windows-paden, regex-backslashes, `\#tag` en andere legacy brongevallen.
- De editor gebruikt Qt's clean/modified-state voor dirty-detectie en hoeft daardoor niet meer bij elke toetsaanslag de volledige hoofdstukbron te kopiëren en vergelijken.
- De pure read-side grammatica (`manuscript_syntax.py`) is losgetrokken van editor-/serializerbewerkingen; `DocumentView` hangt voor inline parsing en escaping niet meer af van `manuscript_markup.py`.
- Woordtelling, zoekprojectie en AI-context hebben een eigen `manuscript_text.py`-grens in plaats van als algemeen manuscriptgedrag in de mediamodule te leven.
- DOCX-runopmaak leest de Word run- en paragraph-styleketen nog maar één keer per run, zodat grote imports minder herhaalde `python-docx`-stijlopzoekingen doen.
- Geen automatische migratie bij alleen `load_book()`/opslaan: de conversie blijft een expliciete gebruikersactie met checkpoint.

## 1.2.29 — Markdown via het neutrale documentmodel

- Markdown-import bouwt nu eerst een neutraal `ImportDocument` en gebruikt daarna dezelfde centrale serializer als DOCX-import.
- Markdown-import wordt volledig in een stagingmap opgebouwd en pas na succesvolle validatie atomair gepubliceerd.
- Gewone externe Markdown volgt weer de normale Markdown-alinearegel: bronregels zonder lege regel ertussen vormen één alinea.
- CommonMark hard breaks worden als QuietWriter soft break (U+2028) geïmporteerd.
- Publieke Markdown-export serializeert QuietWriter-alinea's met echte lege regels, zodat CommonMark/websites alineagrenzen behouden.
- QuietWriter soft breaks worden bij Markdown-export als geldige CommonMark hard break geschreven.
- Onbekende frontmattervelden blijven bij Markdown-import behouden.
- Nieuwe regressietests bewaken de neutrale importgrens, alinea's, hard breaks en transactionele import.
- Volledige lokale suite: 587 passed, 46 skipped, 304 subtests passed.

## 1.2.28 — DOCX-import behoudt zichtbare tekst beter

- Zachte Word-regeleinden worden als U+2028 soft break behouden in plaats van onbedoeld nieuwe QuietWriter-alinea’s te maken.
- Een pagina-einde midden in een alinea wordt als regeleinde behouden en expliciet gemeld, zodat omliggende tekst niet aan elkaar plakt.
- Tabelrijen worden op hun positie als leesbare platte tekst geïmporteerd (`cel · cel`) in plaats van alle tabeltekst weg te gooien.
- Zichtbare veldresultaten, tracked insertions, inline content controls en tekst uit Word-tekstvakken worden via descendant-runs zoveel mogelijk als gewone tekst behouden; beperkingen worden gemeld.
- Beschadigde ingebedde afbeeldingen worden overgeslagen met een waarschuwing in plaats van de volledige boekimport te laten mislukken.
- Afbeeldingstype wordt op de daadwerkelijke bytes gevalideerd in plaats van alleen op de OOXML content-type/extensie te vertrouwen.
- Achtergelaten `.import-*`-stagingmappen ouder dan 24 uur worden bij bibliotheekstart best-effort opgeruimd; verse stagingmappen blijven ongemoeid.
- Nieuwe regressietests dekken soft/page breaks, tabellen, velden/track changes/tekstvakken, corrupte afbeeldingen en staging-cleanup.

## 1.2.27 — Manuscriptsyntax geversioneerd

- Nieuwe boeken en nieuwe DOCX-imports krijgen een expliciet `manuscript_syntax`-profiel met versie en featureflags.
- Bestaande boeken zonder profiel blijven ongewijzigd; openen en normaal opslaan voegt geen stille syntaxmigratie toe.
- Onbekende toekomstige syntaxversies/features worden fail-closed geweigerd en Integriteit onderscheidt onversioneerd, ongeldig en toekomstig.
- `inline_runs` is herschreven als lineaire sweep over stijlgrenzen, zodat zwaar opgemaakte lange tekst niet meer per teken alle spans scant.
- Regressietests toegevoegd voor profielbehoud, future-featureveiligheid en zwaar opgemaakte inline-runs.
- Nog geen expliciete conversie van oudere boeken uitgevoerd; die blijft een afzonderlijke zichtbare/omkeerbare stap.

## 1.2.26 — Zichtbare tekst centraal en sneller typen

- De schrijver-zichtbare tekstprojectie is verder gecentraliseerd en wordt nu ook gebruikt voor full-text search-indexering en Bewaarplaats-preview/filtering.
- Woordtelling gebruikt rechtstreeks dezelfde centrale DocumentView-semantiek in plaats van een tweede zichtbaarheidspad.
- Genummerde lijsten behouden in AI-context hun echte nummer in plaats van alles als `1.` te tonen.
- Woordtelling tijdens typen is 400 ms gedebounced; lange hoofdstukken worden daardoor niet meer bij iedere toets volledig opnieuw geparset.
- De productroadmap zet **Boekenkast met meerdere planken en verborgen/privéplanken** bovenaan na de huidige hardeningfase, met NEO als visuele referentierichting.
- Geen manuscriptmigratie of nieuwe manuscriptsyntaxis in deze versie.

## 1.2.25 — Escaping gehard na onafhankelijke review

- Verborgen escapes zijn editor-atomair gemaakt voor cursorbeweging, Backspace en Delete.
- Niet-expliciete edits mogen niet stil nieuwe blockstructuur maken; Enter/Delete/Backspace en gewone invoer worden na de bewerking semantisch bewaakt.
- Kopiëren naar het systeemklembord levert zichtbare tekst; QuietWriter-naar-QuietWriter plakken kan opmaak behouden via een intern MIME-type.
- Zoekresultaten gebruiken een zichtbare projectie met bron-offsetmapping, waardoor `5*3`, `**literal**` en tekst over vet/cursief-grenzen vindbaar zijn.
- Zoek-en-vervang serializeert vervangtekst als letterlijke schrijverstekst.
- `DocumentView` splitst alleen op `\n`; U+2028 van Shift+Enter is geen nieuwe alinea meer.
- Expliciete opmaak leest de persistente bron via `source_text()` en behoudt daardoor NBSP.
- Structurele escapes worden alleen op geldige prefixposities gelezen; getypte escaped Open-puntmarkers blijven gewone tekst.
- Qt-regressietests uit de onafhankelijke 1.2.24-review zijn als gedragstests opgenomen.
- Geen bestaande boeken gemigreerd of herschreven.

## 1.2.24 — DOCX-afbeeldingen via de mediastore

- DOCX-import leest PNG- en JPEG-afbeeldingen nu als neutrale import-assets in plaats van ze te negeren.
- Afbeeldingen worden tijdens de transactionele stagingfase in de boeklokale mediastore geplaatst en pas daarna als normale QuietWriter-afbeeldingsblokken in hoofdstukken geserialiseerd.
- Alt-tekst uit Word wordt waar beschikbaar behouden.
- Dezelfde afbeelding die meerdere keren in Word voorkomt wordt binair één keer opgeslagen, terwijl alle plaatsingen in het manuscript behouden blijven.
- Een afbeelding midden in een Word-alinea wordt veilig als los afbeeldingsblok geïmporteerd en levert een expliciete waarschuwing op.
- Niet-ondersteunde Word-afbeeldingstypen worden expliciet gemeld; PNG en JPEG zijn de ondersteunde importformaten.
- De volledige import blijft transactioneel: een fout tijdens media-import kan geen half boek publiceren.
- Geen bestaande boeken gemigreerd of herschreven.

## 1.2.23 — Transactionele DOCX-import

- DOCX-import wordt eerst volledig opgebouwd in een verborgen stagingmap onder `books/`; pas wanneer hoofdstukken, assetsmanifest en `book.json` compleet en valide zijn, wordt de complete map in één directory-rename gepubliceerd.
- Een schrijf- of syncfout tijdens import laat daardoor geen half zichtbaar boek meer achter in de boekenplank.
- Mislukte stagingimports worden opgeruimd; een succesvol gepubliceerde map wordt nooit door de foutafhandeling verwijderd.
- Voor publicatie wordt gecontroleerd of alle door `book.json` genoemde hoofdstukbestanden daadwerkelijk bestaan.
- Nieuwe regressietests simuleren een schijffout tijdens het tweede hoofdstuk en een mislukte directory-publicatie en controleren dat de bibliotheek leeg en schoon blijft.
- Geen bestaande boeken gemigreerd of herschreven.
- Volledige geautomatiseerde suite: 558 passed, 45 skipped, 304 subtests passed.

## 1.2.22 — Neutraal importdocument

- DOCX-import leest Word nu eerst naar een formaat-onafhankelijk `ImportDocument` met secties, hoofdstukken, blocks en semantische inline-runs.
- De DOCX-reader bouwt geen QuietWriter-markup meer rechtstreeks; pas aan de opslaggrens serializeert één centrale writer de importsemantiek naar veilige QuietWriter-tekst.
- Letterlijke Markdownachtige Word-tekst en echte Word-opmaak blijven daardoor technisch van elkaar gescheiden tot het laatste moment.
- De bestaande `parse_docx_book()`-interface blijft behouden als compatibiliteitsgrens voor de huidige opslagworkflow.
- Nieuwe regressietests controleren expliciet dat het neutrale model geen QuietWriter-markup bevat en dat serialisatie pas daarna escaping/opmaak toevoegt.
- Geen bestaande boeken gemigreerd of herschreven.
- Volledige geautomatiseerde suite: 555 passed, 45 skipped, 304 subtests passed.

## 1.2.21 — Centrale bronopbouw en veiligere DOCX-import

- Naast de centrale `DocumentView` is nu ook de **schrijfkant van de manuscriptsyntaxis** gecentraliseerd: gegenereerde inline-opmaak en blockstructuur worden via gedeelde serializers opgebouwd in plaats van met losse `*`, `**`, `> ` en lijstprefixen in verschillende modules.
- DOCX-import encodeert letterlijke Markdownachtige tekens eerst als schrijverstekst en voegt daarna pas semantische opmaak toe. Een Word-zin als `- Kom je? *316 5*3 **letterlijk**` verandert daardoor niet stil in een lijst of opmaak.
- Hard line breaks in een opgemaakte Word-run worden per fysieke QuietWriter-alinea geserialiseerd, zodat vet/cursief niet meer met een open marker over de volgende regel kan lekken.
- QuietWriter-DOCX gebruikt voortaan een eigen `QuietWriter Scene Break`-stijl voor scènebreuken. Daardoor blijft `***` bij roundtrip structureel, terwijl een letterlijk `***` uit een gewoon extern Word-document gewone tekst kan blijven.
- DOCX-import volgt nu ook character styles en `basedOn`-overerving, waardoor onder andere Word **Strong**, *Emphasis* en opmaak uit een paragraph style worden meegenomen. Expliciete run-opmaak blijft leidend.
- Eigen Word-paragraafstijlen die van Heading 1/2 erven worden nu als hoofdstuk-/sectiestructuur herkend.
- De page-oriented fallback gebruikt een korte eerste gewone zin niet meer automatisch als titel; dit voorkomt dat tekst zoals `Nee.` stil uit de body verdwijnt.
- DOCX-import meldt nu expliciet wanneer track changes, content controls, Word-velden, hyperlinkdoelen of voetnoten niet volledig kunnen worden behouden. Hyperlinktekst zelf blijft behouden.
- Nieuwe importwaarschuwingen toegevoegd aan alle vijf interfacetalen.
- Geen bestaande QuietWriter-boeken gemigreerd of herschreven.
- Volledige geautomatiseerde suite: 553 passed, 45 skipped, 304 subtests passed.

## 1.2.20 — Escaping editor crashfix

- Crash bij iedere gewone toetsaanslag in 1.2.19 opgelost: de editor importeert nu alle vier gebruikte escapinghelpers expliciet.
- Ook de plak-/kopieerroutes zijn meegenomen, zodat `escape_literal_text` en `unescape_literal_text` niet pas later als NameError opduiken.
- Regressietest toegevoegd die de editor-module importeert en controleert dat alle escapinghelpers beschikbaar zijn.
- Geen wijziging in boekformaat of bestaande manuscriptbytes.

## 1.2.19 — Letterlijke invoer en escaping-basis

- Nieuwe letterlijke-invoerlaag: direct getypte markuptekens zoals `*`, `~`, backticks, `<` en backslashes worden veilig escaped in de bron maar blijven normaal zichtbaar in de editor.
- Regels die door een spatie anders stil een lijst, citaat, tussenkop of genummerde lijst zouden worden (`- `, `> `, `## `, `1944. `) worden bij gewone invoer als proza opgeslagen.
- Expliciete opmaak via Ctrl+B/Ctrl+I/Ctrl+U, de opmaakbalk en blockacties blijft echte QuietWriter/Markdown-syntax maken.
- Gewone plakacties behandelen geplakte inhoud als schrijverstekst en escapen syntaxachtige tekens; technische Open-puntmarkers worden zoals voorheen verwijderd.
- `DocumentView`, inline-runs, export, zoeken, spelling en AI-context begrijpen dezelfde escapes en tonen/exporteren alleen de bedoelde zichtbare tekst.
- Gekopieerde letterlijke tekst bevat de verborgen escape-backslashes niet.
- Bestaande hoofdstukken worden niet herschreven of gemigreerd; escaping ontstaat alleen bij nieuwe letterlijke invoer/plakacties of wanneer bron al escapes bevat.
- Regressietests toegevoegd voor `*31623455`, `5*3`, dialoog met `- `, jaartallen zoals `1944.`, expliciete opmaak en export van escaped proza.

## 1.2.18 — Centrale semantische inline-laag

- `DocumentView` levert nu naast blocks ook semantische inline-runs met zichtbare tekst en stijlen; consumers hoeven `*`, `**`, `~~`, backticks en `<u>` niet opnieuw te parsen.
- DOCX-export gebruikt de centrale inline-runs voor vet, cursief, onderstrepen, doorhalen en code.
- XHTML/EPUB- en PDF-rendering gebruiken dezelfde runs en bouwen alleen nog uitvoerformaten op uit semantiek.
- Afbeeldingsmetadata voor export komt uit `DocumentView`-blocks in plaats van opnieuw de bronregel te ontleden.
- Editor en editorpagina herkennen scène- en afbeeldingsblocks via de centrale documentgrens in plaats van rechtstreeks via losse parsers.
- `parse_block_line()` en `parse_document()` leveren voor afbeeldingsregels dezelfde attributen.
- Regressietests toegevoegd voor centrale inline-runs, letterlijke ongepaarde sterren en afbeeldingssemantiek.
- Geen nieuwe manuscriptsyntaxis, geen escaping geactiveerd en geen bestaande manuscriptbytes herschreven.
- Geautomatiseerde testsuite: 532 passed, 45 skipped, 304 subtests passed.

## 1.2.17 — DocumentView als gedeelde manuscriptlezer

- XHTML/EPUB-rendering doorloopt nu rechtstreeks de centrale `DocumentView`-blocks in plaats van opnieuw regels en blockprefixen te interpreteren.
- Inhoudsopgave-preview leest tussenkoppen via dezelfde centrale semantiek als export en editor.
- Afbeeldingsblock-ranges voor masking/protectie komen nu uit `DocumentView` in plaats van een eigen regelscan.
- Blockopmaak in de editor hergebruikt de centrale blockclassificatie en contentgrenzen; hierdoor ontstaat minder dubbele Markdownlogica.
- Centrale helper toegevoegd voor zichtbare inline-tekst: alleen daadwerkelijk gepaarde opmaakmarkers verdwijnen; letterlijke losse tekens blijven staan.
- Geen nieuwe manuscriptsyntaxis, geen opslagmigratie en geen herschrijving van bestaande hoofdstukken.
- Geautomatiseerde testsuite: 529 passed, 45 skipped, 304 subtests passed.

## 1.2.16 — DocumentView voor zoeken, spelling en Meelezer

- Zoeken, spelling en AI-manuscriptcontext gebruiken nu dezelfde centrale `DocumentView`-interpretatie als editor en export.
- Technische inline-markers, Open-puntmarkers, scènebreuken en blockprefixen worden voor zoeken/spelling centraal gemaskeerd met behoud van exacte bronoffsets.
- Afbeeldingspaden en layoutmetadata blijven buiten zoek- en spellingstekst; natuurlijke alttekst en captions blijven beschikbaar.
- Meelezer-context bevat schrijverstekst en semantische elementen in plaats van technische QuietWriter-bronsyntax; scènebreuken worden expliciet als `[Scènebreuk]` aangeboden.
- Een letterlijk, ongepaard sterretje zoals `*31623455` blijft volledig gewone tekst in zoeken, spelling en AI-context.
- Oude source-based regressietest voor spelling aangepast aan de nieuwe centrale interpretatielaag.
- Geen manuscriptmigratie of nieuwe persistente syntaxis ingevoerd.
- Volledige geautomatiseerde testsuite: 526 passed, 45 skipped, 304 subtests passed.

## 1.2.15 — DocumentView crashfix

- Crash opgelost wanneer de centrale `DocumentView` lege manuscripttekst verwerkt.
- Opstarten en export konden via woordtelling een lege tekst doorgeven; de lege `DocumentView` bevat nu expliciet `blocks=()`.
- Regressietest toegevoegd voor een volledig lege manuscriptbron.
- Volledige lokale testsuite: 523 passed, 45 skipped, 304 subtests passed.
- Geen manuscriptformaat, migratie of gebruikersdata gewijzigd.

## 1.2.14 — Centrale manuscriptinterpretatie

- PDF- en DOCX-export gebruiken nu dezelfde centrale blockinterpretatie als editor en EPUB/XHTML.
- Woordtelling telt via `DocumentView` alleen zichtbare manuscriptinhoud; structurele markering zoals `***` en lijstprefixen telt niet meer als woord.
- De ongebruikte oude `exporting/xhtml.py`-parser is verwijderd zodat er één afwijkende parser minder bestaat.
- Nieuwe centrale, read-only `DocumentView` toegevoegd voor één gedeelde interpretatie van manuscriptblocks, inline spans en bronranges.
- Eerste twee consumers gebruiken dezelfde blockclassificatie: de manuscripteditor en XHTML/EPUB-rendering.
- Nieuwe `MANUSCRIPT_SYNTAX.md` legt de feitelijke 1.2.13-syntaxis vast en kiest als richting: gangbare Markdownconventies waar mogelijk, QuietWriter-extensies alleen waar nodig.
- Letterlijke losse sterretjes zoals `*31623455` blijven gewone tekst; parsing van inline-opmaak is in `DocumentView` expliciet per fysieke regel.
- Bekende ambiguïteiten zoals `- Kom je?` en `1944. ...` worden door de nieuwe laag gesignaleerd maar nog niet stil herschreven.
- Geen bestaande manuscriptbytes, boekformaten of migraties gewijzigd.
- Verouderde release-metadatatest aangepast aan de opgeschoonde historische roadmap.
- Lokale volledige testsuite na deze stap: 519 passed, 45 skipped, 304 subtests passed.

## 1.2.13 — Open punten definitief stabiel

- Open punt afronden behoudt de scrollpositie ook wanneer de geselecteerde rij tijdens de refresh verdwijnt.
- De Open punten-lijst start bij een ander boek weer bovenaan in plaats van de scrollpositie van het vorige boek over te nemen.
- Twee Qt-regressietests toegevoegd voor beide scenario's via de echte MainWindow-route.

## 1.2.12 — Open punten behoudt lijstpositie

- Live verversen van Open punten behoudt de geselecteerde rij wanneer dat punt nog bestaat.
- De scrollpositie van lange lijsten blijft tijdens typen, Ongedaan maken en Opnieuw behouden.
- Herstel van selectie en scroll gebeurt zonder navigatiesignalen naar de editor af te vuren.

## 1.2.11 — Smalle panelen en live Open punten

- Meelezer-uitleg en privacywaarschuwing schalen betrouwbaar mee met smalle rechterpanelen.
- Open punten verversen live tijdens tekstbewerkingen, inclusief Ongedaan maken en Opnieuw.
- Paneeltests schrijven niet meer naar echte gebruikersinstellingen.

## 1.2.10 — Paneeluitleg en Open-puntenpolish

- Open punten verversen direct vanuit de actuele editorbron, zodat een nieuw punt meteen in het open rechterpaneel verschijnt vóór autosave.
- De spellingscontrole maskeert technische Open-puntmarkeringen met behoud van bronoffsets; `qw` en `todo` worden niet meer als woorden gecontroleerd.
- PanelHelp berekent zijn teksthoogte opnieuw bij resize en vertaling, zodat uitleg in smalle panelen niet wordt afgekapt.
- Help-iconen van alle rechterpanelen worden bij een live themawissel opnieuw ingekleurd, ook wanneer het paneel gesloten is.
- De Meelezer-toestemmingsmelding gebruikt echte lay-outmarges in plaats van niet-effectieve QSS-padding.
- Toevoegen behoudt de hoogte van de verborgen helpknop, zodat de titel niet verspringt.
- De Qt-regressietest voor In dit hoofdstuk volgt de gedeelde `panel_help.title`.

## 1.2.9 — Paneeluitleg en laatste HiDPI-polish

- Gedeelde, inklapbare uitleg toegevoegd aan de rechterpanelen Zoeken, In dit hoofdstuk, Open punten, Meelezer, Spellingscontrole, Versiegeschiedenis en Bewaarplaats.
- Uitleg staat bij eerste gebruik open, wordt per paneel onthouden en kan via de ?-knop opnieuw worden geopend.
- De eerste Open-punt-uitleg is niet langer modaal; de uitleg staat voortaan in het paneel zelf.
- Instellingen → Algemeen bevat nu Alle uitleg weer tonen, zonder andere instellingen te wijzigen.
- De Meelezer-privacywaarschuwing is visueel onderscheiden van gewone uitleg en uitleg klapt tijdelijk in bij Context/Snelacties.
- Woordenboekinformatie reserveert hoogte op basis van de werkelijke runtimebreedte.
- Het lege vlak in In dit hoofdstuk gebruikt de paneelachtergrond transparant.
- Help-iconen volgen live het actieve thema.

## 1.2.8 — HiDPI-instellingen en rechterpaneel-uitlijning

- De werkmapkiezer kan op smallere logische breedtes krimpen, zodat de knop **Map kiezen** bij 1920×1080 op 125% DPI volledig zichtbaar blijft.
- De woordenboekinformatie reserveert expliciet voldoende hoogte voor lange bron- en padregels en wordt niet meer afgesneden.
- **In dit hoofdstuk** houdt titel en uitleg bovenaan vast wanneer er nog geen gekoppelde scènes zijn; de actieknop blijft onderaan zoals bij de andere rechterpanelen.
- De Open-puntengeometrietest is gemarkeerd als Qt-test en draait daardoor ook mee in gerichte `pytest -m qt`-runs.

## 1.2.7 — Qt-geometrietest zelfstandig gemaakt

- De regressietest voor de breedte van verborgen Open-puntmarkeringen gebruikt geen `pytest-qt`/`qtbot` meer.
- De test volgt nu hetzelfde patroon als de overige Qt-tests met `QApplication` en `QTest.qWait`.
- Geen productgedrag gewijzigd ten opzichte van 1.2.6.

## 1.2.6 — Open-puntmarkering zonder overlap

- Open-puntmarkeringen gebruiken nu een eigen verborgen tekststijl; gewone Markdown-markeringen zoals `**` behouden hun bestaande geometrie.
- De markerbreedte wordt samengedrukt op basis van de werkelijke gemiddelde tekenbreedte van het 1-punts editorfont in plaats van een vaste `-2 px`, zodat omliggende tekst niet meer over elkaar heen valt.
- Regressietest toegevoegd voor de geometrie van zowel een open-puntmarkering als verborgen vet-markers.

## 1.2.5 — Open punten gehard

- Open punten gebruiken nu compacte markers in de manuscriptbron; notities staan veilig in `planning/open_points.json`, dat automatisch meegaat in geschiedenis en QWBOOK.
- Ctrl+X, Ctrl+V, slepen/neerzetten en andere destructieve routes kunnen beheerde markers niet meer stil beschadigen.
- Kopiëren zet alleen zichtbare schrijverstekst op het systeemplakbord; technische QuietWriter-markers lekken niet meer naar andere apps of publicatieteksten.
- De cursor slaat verborgen open-puntmarkers over en de markeropmaak is verder samengedrukt, zodat er geen lange onzichtbare cursortrajecten of opvallende gaten ontstaan.
- Export verwijdert open-puntmarkers nu ook defensief uit voor-/achterwerk.
- De rechter gereedschapsrail kan op lage/HiDPI-schermen scrollen in plaats van de minimale vensterhoogte op te drijven.
- Instellingen reserveren correct hoogte voor langere Duitse, Franse en Spaanse hulpteksten.
- Nederlandse ontbrekende vertalingen vallen weer terug op de Nederlandse codetekst; andere talen gebruiken Engels als productfallback.

## 1.2.4 — Open punten en extra talen

- Nieuwe **Open punten**: markeer geselecteerde tekst of de cursorpositie, voeg optioneel een notitie toe en vind alle open punten terug in een boekoverzicht.
- Open punten vervangen eigen `XXX`/`TODO`/`???`-notatie: QuietWriter legt dit bij eerste gebruik uit en waarschuwt vóór export; technische markers komen niet in gewone exports of AI-context terecht.
- Vanuit de exportcontrole kun je rechtstreeks naar het overzicht Open punten springen.
- Nieuwe interfacetalen: **Duits, Frans en Spaans**, naast Nederlands en Engels. Alle locale-bestanden hebben dezelfde sleutel- en placeholdercontracten.
- Engelse fallback toegevoegd voor toekomstige ontbrekende vertaalsleutels.
- Live themawissels verversen nu ook de handmatig gekleurde manuscriptgroepen **Voorwerk/Achterwerk** en de actie **wijzig**, zodat Lamplicht en andere thema’s geen achtergebleven accentkleur tonen.

## 1.2.3 — Lamplicht en exportwizard-uitlijning

- Nieuw warm donker thema **Lamplicht** toegevoegd zonder nieuwe themalogica.
- Kop, stappenrij, navigatie en inhoud van Begeleid exporteren volgen op brede schermen nu dezelfde maximale kolombreedte.
- De modusschakelaar Begeleid / Zelf instellen blijft daardoor visueel bij de wizard in plaats van aan de uiterste rechterrand van het venster.

## 1.2.2 — Exportwizard polish

- De vaste Terug/Volgende-balk volgt nu dezelfde maximale breedte als de wizardinhoud, zodat Volgende op brede schermen dichter bij de gemaakte keuze blijft.
- Doelkaarten berekenen hun minimumhoogte opnieuw na een resize, zodat onnodige lege ruimte onder beschrijvingen verdwijnt.
- De UI-reference legt bewust vast wanneer setup-navigatie boven de scrollinhoud of onderaan een modale wizard staat.

## 1.2.1 — Exportwizard navigatie

- De navigatie van Begeleid exporteren staat nu direct onder de stapindicator en blijft buiten de scrollbare inhoud.
- Na het kiezen van een doel is **Volgende** meteen zichtbaar; een kaart kiezen gaat bewust niet automatisch naar de volgende stap.
- De inhoud van lange wizardstappen blijft onafhankelijk scrollbaar, terwijl Terug/Volgende op een vaste, voorspelbare plek blijven.

## 1.2.0 — Begeleid exporteren

- Nieuwe begeleide exportwizard naast de bestaande handmatige exportpagina, met doelen voor e-reader, afdrukken, Word, delen, back-up en website.
- Eén gedeelde exportroute voor beide modi, zodat wizard en handmatige export dezelfde exporters en veiligheidscontroles gebruiken.
- `.qwbook` kan het Meelezer-gesprek bewust weglaten; deze privacykeuze geldt nu ook voor gesprekken die in versiegeschiedenis-snapshots voorkomen.
- QWBOOK-preflight telt nu ook bestanden uit versiegeschiedenis en houdt rekening met uitgesloten Meelezer-gesprekken.
- Als exporteren lukt maar de exportvoorkeuren door een extern conflict niet kunnen worden opgeslagen, meldt de klaar-pagina dat expliciet.
- Windows-build maakt naast versiegebonden releasebestanden ook vaste `QuietWriter-windows-portable.zip`-assets voor blijvende downloadlinks.

## 1.1.0 — Stabiele feature-release en Windows build-hardening

- Bundelt de sinds 1.0.0 afgeronde Darlings-, onboarding-, DOCX- en `.qwbook`-functionaliteit als nieuwe stabiele release.
- Windows-build pinnt PyInstaller op 6.22.3 en compileert de bootloader lokaal uit bron.
- Onedir, `upx=False` en `console=False` blijven expliciet behouden.
- Build schrijft voortaan ook `QuietWriter-<versie>-exe.sha256` en toont de EXE SHA-256 na de build.
- Nieuwe release-checklist voor VirusTotal/false-positive-afhandeling en handmatige publicatie zonder GitHub Actions.
- Geen nieuwe productfunctionaliteit ten opzichte van de groen geteste 1.0.23-bronbasis.

## 1.0.23 — Snellere Qt-tests

- Testinfrastructuur: na iedere test worden achtergebleven top-level Qt-vensters gesloten en via `deleteLater()` opgeruimd.
- Hiermee stapelen `MainWindow`-instanties uit Qt-tests niet meer op en blijft de volledige suite snel.
- Geen wijziging aan productgedrag of bestandsformaten.

## 1.0.22 — `.qwbook` herstelgedrag en voorkeur onthouden

- `Versiegeschiedenis meenemen` wordt nu per boek onthouden.
- Een `.qwbook` zonder geschiedenis behoudt bestaande versiegeschiedenis van hetzelfde boek.
- Weesgeschiedenis wordt pas opzijgezet nadat het volledige pakket succesvol is gevalideerd.
- Een mislukte import laat bestaande versiegeschiedenis dus ongemoeid.

## 1.0.21 — `.qwbook` back-upherstel en compacte overdracht

- Een `.qwbook` kan weer worden teruggezet nadat het boek definitief is verwijderd, ook als oude weesgeschiedenis in `archive/` is achtergebleven.
- Weesgeschiedenis wordt veilig bewaard onder `archive/.orphaned/` in plaats van de import te blokkeren.
- Export kan versiegeschiedenis optioneel uitsluiten voor een kleiner overdrachtsbestand.
- Oude v1-pakketten worden bij import ook van lokale `source_file`-paden opgeschoond.

## 1.0.20 — `.qwbook` hardening en complete back-up

- Windows-veilige `.qwbook`-padvalidatie in twee lagen; backslashes, stationsletters, traversal, gereserveerde namen en paden buiten de importmap worden geweigerd.
- Import gebruikt een tijdelijke map onder `.cache/` in plaats van `books/`, zodat crashresten niet op de Boekenplank verschijnen.
- Import en herstel uit de Prullenbak blokkeren dubbele boek-identiteiten.
- `.qwbook` bevat nu ook boekgebonden versiegeschiedenis en verborgen boekdata zoals het Meelezer-gesprek.
- Lokale `metadata.source_file`-paden worden uit huidige en historische `book.json`-bestanden verwijderd vóór verpakking.
- Grootte-, bestandsaantal- en compressieverhoudingslimieten beschermen tegen onredelijk grote of kwaadaardige archieven; import streamt bestanden in plaats van ze volledig in geheugen te lezen.
- Bij `.qwbook` wordt na export alleen **Map openen** aangeboden; **Bestand openen** is verborgen.

## 1.0.19 — `.qwbook` compleet boekformaat

- `.qwbook` exporteert de volledige boekmap als één overdraagbaar QuietWriter-bestand.
- Pakketmanifest bevat formaatversie, boekidentiteit en SHA-256/size per bestand.
- Import verifieert alle bestanden en werkt via een tijdelijke map voordat het boek zichtbaar wordt.
- Bestaande boeken met dezelfde identiteit worden nooit stil overschreven.
- Corrupte pakketten, padtraversal, dubbele entries en future-format pakketten worden fail-closed geweigerd.
- Exporteren bevat nu QWBOOK en Boek importeren accepteert `.qwbook`.
- Roundtrip-tests controleren byte-exact behoud van manuscript, Planning, publicatie, AI-boekcontext, instellingen en assets.

## 1.0.18 — DOCX-import taal veilig in Boekdetails

- DOCX-import bewaart de hoofdtaal uit Word (`en-US` → `en`, `nl-NL` → `nl`) zodat Boekdetails de taal niet stil terugzet.
- DOCX-importwaarschuwingen voor tabellen en afbeeldingen volgen nu de gekozen UI-taal.

## 1.0.17 — DOCX-import taal en fallbacktitels

- DOCX-import leest de standaarddocumenttaal uit Word en bewaart die als boektaal.
- Word-taalcodes worden bij import genormaliseerd naar BCP 47.
- Pagina's zonder korte kop krijgen unieke boekbrede fallbacktitels in plaats van telkens "Deel 1".
- Fallbacktitels volgen de UI-taal: "Deel N" in het Nederlands en "Part N" in het Engels.

## 1.0.16 — DOCX import/export verfijnd

- ieder hoofdstuk begint bij DOCX-export op een nieuwe pagina;
- Word-documenttaal volgt de ingestelde spellingstaal van QuietWriter;
- de boekomslag wordt als eerste pagina meegenomen;
- grote afbeeldingen worden proportioneel binnen het afdrukbare paginagebied geschaald;
- import van layout-zware Word-documenten gebruikt ook expliciete pagina-einden, Title/Subtitle en grote displaykoppen;
- zwevende Word-afbeeldingen worden nu correct geteld en als nog-niet-ondersteund gemeld.

## 1.0.14 — DOCX import en export

- DOCX toegevoegd als vierde exportformaat naast EPUB, PDF en Markdown.
- Gedeelde `python-docx`-laag voor Word-import en -export.
- Export bewaart boek-/hoofdstukstructuur en QuietWriter-opmaak (vet, cursief, onderstrepen, doorhalen en inline code); inline afbeeldingen worden meegenomen waar mogelijk.
- Import leest QuietWriter-DOCX en gewone Word-documenten met Heading 1/2, lijsten, citaten en ondersteunde inline-opmaak.
- Niet betrouwbaar ondersteunde Word-inhoud, zoals tabellen en geïmporteerde afbeeldingen, wordt expliciet gemeld in plaats van stil genegeerd.

## 1.0.13 — onboarding polish en veilige statusherstel

- updatecontrole onderscheidt nu expliciet een lokale versie die hoger is dan de nieuwste stabiele GitHub-release;
- radioselecties hebben in alle thema’s een duidelijkere rand en geselecteerde toestand;
- hoofdstukkenlijst en rechterpaneel bewaren hun echte zichtbaarheid ook wanneer QuietWriter vanaf Boekenplank of Instellingen wordt afgesloten;
- de first-run teller eindigt logisch op 6 van 6 wanneer de optionele rondleiding uitstaat;
- resetwaarschuwing vermeldt expliciet dat een opgeslagen OpenRouter-sleutel wordt verwijderd;
- dubbele Werkmap-rij in de first-run is verwijderd.

## 1.0.12 — begeleide first-run en veilige reset

- First-run uitgebreid met live themapreview en een duidelijk voorbeeld.
- Optionele teksttour toegevoegd voor Boekenplank/schrijven, Planning/Bewaarplaats en Meelezer/export/herstel.
- Updatevoorkeur toegevoegd: handmatig controleren kan altijd; automatische GitHub-check is opt-in en downloadt niets automatisch.
- Bestaande `--first-run`-flag expliciet behouden voor handmatig testen zonder instellingen eerst te wissen.
- Instellingen bevat nu `Standaardinstellingen herstellen…`: alleen programma-instellingen worden gereset, de bestaande werkmap met boeken/verhalen blijft behouden en is vooraf klikbaar zichtbaar.
- Na reset wordt de volledige setup bij de volgende start geforceerd, ook wanneer de bestaande werkmap al bestaat.
- Bewaarplaats-intro compacter gemaakt zonder overmatige witregels.

## 1.0.11 — Darlings-tekst en volgende onboardingfase

- Bewaarplaats-intro herschreven vanuit het schrijversidee “Don't kill your darlings”; technische uitleg over Markdown is uit de gebruikersintro verwijderd.
- Roadmap aangescherpt: na Darlings volgt een begeleide first-run met live themapreview en een expliciete keuze voor automatische GitHub-updatechecks; handmatig controleren blijft altijd beschikbaar.

## 1.0.10 — Rechterpanelen en Darlings UX

- Een bestaande manuscriptselectie blijft behouden wanneer Bewaarplaats, Meelezer, Zoeken, Toevoegen of Versiegeschiedenis wordt geopend; alleen het verlaten van een actief Spelling-paneel ruimt de spellingsselectie op.
- De lege-markercontrole bij Knippen kijkt alleen naar nieuw geïntroduceerde problematische markerruns en blokkeert niet langer een hoofdstuk vanwege al bestaande letterlijke `****`/`~~~~`.
- Bewaarplaats heeft een eigen pictogram in zowel de linkerrail als de rechter gereedschapsrail.

## 1.0.9 — Darlings UX en bronhygiëne

- Vaste Bewaarplaats-tool in de rechter editorrail met Kopiëren, Knippen en Bewaarplaats openen; rechtermuisknop blijft een aanvullende snelroute.
- Bewaarplaats toont herkomst expliciet als Boek en Hoofdstuk.
- Naar prullenbak is een gewone knop naast Invoegen/Opslaan en gebruikt duidelijke knoppen in plaats van generieke Yes/No.
- De veilige halve-selectiestrategie verwijdert markers van spans waarvan alle zichtbare inhoud is weggeknipt, zodat lege Markdown-opmaak niet opstapelt.
- Nieuwe Qt-regressietests voor de vaste editorroute en zichtbare herkomst.

## 1.0.8 — Darlings knippen hersteld en bruikbaarder

- Herstelt `Knippen naar bewaarplaats`: verificatie gebruikt nu de bestaande `FragmentStore.load()`-API.
- Gedeeltelijke selecties in vet/cursief krijgen een extra veilige verwijderstrategie die zichtbare tekens verwijdert en Markdown-markers waar mogelijk behoudt.
- De bestaande fail-closed validatie blijft leidend: alleen een resultaat met exact dezelfde resterende zichtbare tekst en opmaak wordt uitgevoerd.
- Nieuwe regressietests voor veelvoorkomende halve opmaakselecties.

## 1.0.7 — Darlings knippen, herstel en snellere invoegcontrole

- Knippen naar bewaarplaats toegevoegd met fail-closed Markdownverwijdering.
- Fragment wordt eerst veilig opgeslagen en geverifieerd; bij commitfout blijft de tekst bewust dubbel staan.
- Fragmenten zijn nu zichtbaar, herstelbaar en definitief verwijderbaar via Prullenbak.
- Invoegvalidatie berekent stijl per teken lineair in plaats van spans per teken te scannen.

## 1.0.6 — Darlings invoegen fail-safe en contextmenu

- Invoegen bij cursor valideert nu vóór schrijven de verwachte zichtbare tekst en opmaak per teken.
- Markdown-markergrenzen en gelijke stijlen worden waar veilig samengevoegd; onveilige combinaties worden geweigerd in plaats van de bestaande opmaak te beschadigen.
- De regressietest bestrijkt alle cursorposities met gemengde, gedeeltelijke en geneste fragmentopmaak.
- Na Annuleren bij een extern metadata-conflict worden zoeken en tagfilter uitgeschakeld totdat het conflict via Opslaan is opgelost.
- Rechtsklik op een fragment in de Bewaarplaats biedt Invoegen bij cursor en Naar prullenbak.
- Bron-ZIP blijft vrij van test-/buildcaches.

## 1.0.5 — Darlings invoegen gehard

- Invoegen bij cursor normaliseert cursorposities in verborgen Markdown-markers.
- Opgemaakte fragmenten splitsen bestaande inline-opmaak veilig wanneer dat nodig is.
- Invoegen in inline code verschuift bij opgemaakte fragmenten naar een veilige rand.
- Esc of sluiten van het metadata-conflictvenster annuleert nu zonder lokale of externe waarden te overschrijven.
- Qt-conflicttests bijgewerkt naar het 1.0.4-keuzemodel en tuple-tags.
- Uitgebreide propertytest voor alle invoegposities over vet, cursief, doorhalen en code.

## 1.0.4 — Darlings invoegen bij cursor en conflictkeuze

- Darlings kunnen vanuit de Bewaarplaats op de actieve manuscriptcursor worden ingevoegd; het fragment blijft daarna bestaan.
- Invoegen is één undo-actie, vervangt een bestaande selectie niet en weigert read-only/history/corrupte hoofdstukken en afbeeldingsblokken.
- Metadata-conflicten tussen twee computers vragen direct om een expliciete keuze: lokale invoer bewaren of de versie op schijf gebruiken; de versie op schijf wordt in de melding getoond.
- Er blijft na een conflict geen tussentoestand meer over die zoeken, navigeren of afsluiten later stil kan opslaan.
- Bron-ZIP hygiene: `.pytest_cache/` wordt niet meer meegeleverd.

## 1.0.3 — Darlings stap 2 reviewfixes

- Ontbrekende runtime-import voor Kopiëren naar bewaarplaats hersteld en afgedekt met een echte Qt-test.
- Zoeken en tagfilter slaan niet-opgeslagen metadata eerst veilig op en wissen invoer niet meer stil.
- Externe metadatawijzigingen houden lokale invoer zichtbaar en klaar voor een bewuste tweede opslagpoging.
- Gedeeltelijke selecties in vet/cursief krijgen gebalanceerde Markdownmarkeringen voor veilig later invoegen.
- Undefined-names-check is verplicht onderdeel van de oplevercontrole voor Darlings-iteraties.

## 1.0.2 — Darlings Bewaarplaats en kopiëren

- Bewaarplaats toegevoegd als globale pagina naast de Boekenplank.
- Fragmenten zoeken en filteren op tags; read-only Markdownpreview.
- Titel, notitie en tags bewerken met verplichte revisioncontrole.
- Afwijkende/corrupte fragmentbestanden worden gemeld zonder de rest te verbergen.
- Editorcontextmenu: geselecteerde canonieke Markdownbron kopiëren naar Bewaarplaats.
- Bronboek, hoofdstuk en beperkte contextankers worden vastgelegd.
- Nederlandse en Engelse UI-teksten toegevoegd.

## 1.0.1 — Darlings opslagbasis en reviewhardening

- Eerste interne v2-bouwsteen voor Darlings: één Markdownbestand per fragment, zonder UI of editorkoppeling.
- Fragmentlijsten en zoekresultaten blijven bruikbaar wanneer één bestand corrupt, afwijkend of een sync-conflictkopie is; fouten worden per bestand gerapporteerd.
- Fragmenttekst bewaart nu ook witregels aan begin en einde exact.
- Metadatawijzigingen ondersteunen optimistic concurrency via file revisions en weigeren stale writes.
- Fragment-id's worden gevalideerd vóór padgebruik zodat create/restore nooit buiten de werkmap kan schrijven.
- Sortering gebruikt echte datetimes en UTC-timestamps om DST-/timezonefouten te voorkomen.
- Alleen openen van de fragmentopslag maakt geen mappen meer aan.
- DOCX-export is expliciet opgenomen in de v2-roadmap naast DOCX-import.

## 1.0.0 — eerste stabiele release

- Eerste stabiele QuietWriter-release na de RC1–RC5 hardening.
- Geen nieuwe productfunctionaliteit ten opzichte van de gevalideerde RC5-baseline.
- Praktijkvalidatie afgerond voor groot boek, Windows 150% DPI, Ollama, OpenRouter en twee-computer conflictgedrag.
- Persona-, woordenboek-, locale-, corrupte optionele context- en releasehardening uit de RC-rondes zijn onderdeel van deze baseline.
- Nieuwe productfunctionaliteit gaat vanaf hier via de v2-roadmap; Darlings is de eerste geplande v2-feature.

## 1.0.0-rc5 — corrupte optionele context mag de app niet blokkeren

- Beschadigd `persona/schrijver.md` blokkeert de applicatiestart niet meer; de Schrijverspersona opent alleen-lezen.
- De Meelezer slaat een beschadigde Schrijverspersona, Boekprofiel of Boekgeheugen veilig over in plaats van te crashen.
- Contextoverzicht en verzonden context melden expliciet welke beschadigde bron niet is meegestuurd.
- Nieuwe regressietests bewaken zowel de startup-fallback als de AI-contextfallback.

# Changelog

## 1.0.0-rc4 — laatste conflict- en localehardening

- Schrijverspersona kan nu ook veilig omgaan met een extern verwijderd `schrijver.md`: ontbrekend op schijf is een echte revision-state en wordt niet stil overschreven als het bestand intussen terugkomt.
- Een corrupte globale persona wordt niet overschreven; lokale wijzigingen worden onder `archive/persona/` veiliggesteld zodat afsluiten niet vastloopt zodra de herstelkopie gelukt is.
- Twaalf foutief dubbel-geëscapete locale-meldingen tonen weer echte witregels; een regressietest verbiedt letterlijke `\\n` in vertaalwaarden.
- Persoonlijk woordenboek en `altijd_negeren.txt` worden vóór schrijven opnieuw ingelezen, samengevoegd en atomair opgeslagen zodat syncwijzigingen van een andere computer niet verdwijnen.
- De write-auditdocumentatie omvat voortaan ook directe `write_text`/`write_bytes`/serializer-routes.
- Darlings-ontwerp aangescherpt: bij mislukte Knippen-flow is dubbel beter dan kwijt; geen `pending`-status in het MVP en geen tweede zelfgeschreven YAML-parser.

## 1.0.0-rc3 — persona-conflictbeveiliging

- Schrijverspersona detecteert externe wijzigingen vóór opslaan.
- Conflictkeuze bewaart de versie die anders verloren zou gaan onder `archive/persona/`.
- Meelezer-gesprekslog is expliciet gedocumenteerd als last-writer-wins uitzondering voor 1.0.
- V2-implementatie blijft bevroren tot na stabiele 1.0.0.

## 1.0.0-rc2 — release- en Windows-hardening

- Tweede release candidate op dezelfde feature-frozen 1.0-lijn; geen nieuwe grote productfunctionaliteit.
- Publieke distributie bevat geen interne DEV/PROD-launchers meer.
- Windows-build/smoke en release-hygiene zijn verder aangescherpt.
- Zoekcache/SQLite-afhandeling sluit mislukte connecties en cachehandles expliciet en kan een ongeldige cache veilig weggooien/herbouwen.
- Het hoofdvenster sluit de zoekindex expliciet bij normaal afsluiten.
- Documentatie is na RC2 geconsolideerd tot een kleine canonieke set; de chronologische review findings, review notes en tussentijdse rapporten zijn uit de actieve ontwikkelset verwijderd.
- De historische `tests/legacy`-suite is opgeheven; relevante regressies zijn naar de actieve suite overgenomen en verouderde implementatietests zijn verwijderd.
- Overdraagbaarheidsreview 56: CI-workflows terug in de bronset, volledige OFL 1.1-fontlicenties hersteld en met regressietest bewaakt.
- LEESMIJ is versieneutraal gemaakt; de OpenRouter API-keyopslag als gewone lokale setting is expliciet gedocumenteerd.
- De editor-keuze voor tekstbreedte is iets verbreed zodat `Normaal` niet wordt afgekapt, zonder de lange-titel/minimum-width fix terug te draaien.
- Brandingdocumentatie is herschreven rond de echte bron/generator en `shapely` staat in de devrequirements.
- `DEVELOPER_REFERENCE.md`, `UI_REFERENCE.md` en `VALIDATION.md` maken runtimepaden, boekstructuur, concrete UI-regels en de basis voor groene claims overdraagbaar.
- Packagingtests gebruiken een tijdelijke stage via `QUIETWRITER_STAGE_DIR`, zodat `pytest` geen `release/stage` in de bronboom achterlaat.

## 1.0.0-rc1 — eerste publieke release candidate

- Eerste release candidate voor de kleine testgroep; de functieset is bevroren en tot 1.0.0 worden alleen regressies en releaseblokkades opgelost.
- Gebaseerd op de groen verklaarde 0.36.10-lijn: first-run, gescheiden DEV/PROD-profielen, schone portable Windows-build, lokale crashlogging, tweetaligheid en release-smoketest.
- De AI-laag is expliciet een **Meelezer**: feedback, persona-/stijlcontrole, feiten, continuïteit en consistentie; QuietWriter positioneert hem niet als co-auteur of herschrijver.
- OpenRouter toont gratis modellen herkenbaar en kan daarop filteren; OpenRouter-welkomsttekst is lokaal en verstuurt niets totdat de gebruiker zelf een vraag stelt. Ollama kan lokaal opwarmen in een achtergrondworker.
- De editor heeft een globale, presentatie-only tekstbreedte (**Extra smal / Smal / Normaal / Breed / Extra breed**) zonder invloed op manuscript of export.
- Release notes publiceren expliciet de bekende beperking en de nog uit te voeren praktijktests voor deze RC.

## 0.36.10 — release-candidate fixes

- OpenRouter: het filter **Alleen gratis modellen tonen** wist een opgeslagen model niet meer wanneer de catalogus nog niet is opgehaald. Het filter wordt pas toegepast zodra prijsmetadata beschikbaar is; expliciete `:free`-modellen blijven zichtbaar.
- Editor: de tekstbreedtekeuze in de werkbalk is compacter gemaakt en het losse label is verwijderd.
- Editor: lange boektitels worden alleen visueel met een ellipsis ingekort en kunnen de minimale vensterbreedte niet meer oprekken; de volledige titel blijft als tooltip beschikbaar.
- LEESMIJ: opgeslagen met UTF-8 BOM voor maximale compatibiliteit met Windows-tekstviewers.
- Releasebron: tijdelijke `release/stage`- en pytest-cachebestanden worden niet meer in de ontwikkel-ZIP meegenomen.
- Vanaf deze versie geldt feature freeze richting `1.0.0-rc1`: alleen regressiefixes.

## 0.36.9 — ruimere schaal voor tekstbreedte

- De tekstbreedte heeft nu vijf niet-technische standen: **Extra smal / Smal / Normaal / Breed / Extra breed**.
- De bestaande visuele breedtes schuiven één label op: de oude Smal wordt Extra smal, de oude Normaal wordt Smal, de oude Breed wordt Normaal en de oude Extra breed wordt Breed.
- **Normaal** is daardoor voortaan merkbaar ruimer en beter passend op moderne brede schermen; **Extra breed** voegt een nieuwe, nog ruimere stand toe.
- De standaardinstelling blijft semantisch **Normaal**. Bestaande gebruikers die Normaal hadden gekozen krijgen daardoor automatisch de nieuwe, ruimere normale weergave.
- Tekstbreedte blijft uitsluitend een globale weergavevoorkeur en heeft geen invloed op manuscript of export.

## 0.36.8 — globale tekstbreedte in de editor

- De schrijfeditor krijgt een globale keuze **Smal / Normaal / Breed / Extra breed** waarmee de tekstkolom direct smaller of breder wordt zonder de lettergrootte te veranderen.
- De keuze staat zowel direct in de editor als onder **Instellingen → Uiterlijk → Tekstbreedte** en geldt voor alle boeken binnen hetzelfde profiel.
- Tekstbreedte is uitsluitend weergave: manuscripttekst, Markdown, woordtelling en export worden niet aangepast.
- De editor bewaart een wijziging direct; Instellingen gebruikt dezelfde globale voorkeur en licht expliciet toe dat de keuze geen invloed heeft op manuscript of export.
- Nieuwe regressietests bewaken de presets, veilige fallback en het presentation-only contract.

## 0.36.7 — correcte UTF-8 in OpenRouter-streams

- OpenRouter Server-Sent Events worden nu expliciet als UTF-8 gedecodeerd. Daardoor verschijnen Nederlandse tekens zoals `scène`, `één` en `café` niet meer als mojibake (`scÃ¨ne`, `Ã©Ã©n`).
- Nieuwe regressietest bewaakt UTF-8-inhoud in gestreamde OpenRouter-antwoorden.

## 0.36.6 — gratis OpenRouter-modellen beter zichtbaar

- OpenRouter-modelmetadata bewaart nu de actuele prompt- en outputprijs en markeert modellen als gratis wanneer beide nul zijn; expliciete `:free`-varianten en `openrouter/free` worden eveneens herkend.
- In de modelkeuzelijst staan gratis OpenRouter-modellen voortaan vóór betaalde modellen, met een `🆓`-markering; `🧠` blijft daarnaast zichtbaar wanneer thinking wordt ondersteund.
- Nieuwe optie **Alleen gratis modellen tonen** filtert de OpenRouter-lijst zonder betaalde modellen te verwijderen uit de opgehaalde catalogus.
- De optie is alleen zichtbaar bij OpenRouter en wordt als gebruikersvoorkeur opgeslagen. **Modellen ophalen** ververst de gratis/betaald-status.
- Tooltips en Nederlandstalige/Engelstalige uitleg beschrijven wat de gratis-markering betekent.

## 0.36.5 — release-hardening na review 53

- Regressie in Instellingen opgelost: de genormaliseerde werkmap wordt nu in `save_settings()` bepaald, zodat Opslaan weer werkt voor thema, taal, AI, spelling en werkmap.
- Alleen een echte werkmapwijziging toont nog de melding dat een herstart nodig is; oude en nieuwe paden worden daarvoor eerst op dezelfde manier genormaliseerd.
- `--smoke-test` gebruikt een volledig tijdelijke INI en tijdelijke appdata en kan daardoor nooit meer de echte DEV-instellingen of het DEV-crashlog wijzigen.
- Smoke-modus toont bij een opstartfout geen modale dialoog meer maar schrijft naar stderr en eindigt met exitcode 1; ook onverwachte Python-/threadfouten tijdens de smoketest maken de run rood.
- De Windows CI-smoketest heeft een timeout van vijf minuten zodat een defect proces de workflow nooit uren kan blokkeren.
- `LEESMIJ.txt` wordt na de PyInstaller-build expliciet naast `QuietWriter.exe` geplaatst en niet meer in `_internal/`. De releasecontrole bewaakt beide voorwaarden.
- De LEESMIJ vermeldt nu expliciet dat de ZIP eerst moet worden uitgepakt, de SmartScreen-stappen, het crashlogpad en leesbare Windows-paden.
- `build_exe.cmd` installeert zo nodig `pyflakes` en draait `tools/check_undefined_names.py` vóór staging/build, zodat undefined names een lokale release-build direct blokkeren.

## 0.36.4 — veilige werkmap en snelle Meelezer-warmup

- Relatieve werkmappen worden voortaan onder de gebruikersmap geplaatst en nooit relatief aan de programmamap. Dit geldt zowel voor de first-run wizard als voor Instellingen.
- OpenRouter krijgt bij het openen van de Meelezer geen warmup-request meer. De welkomsttekst wordt lokaal getoond; er worden dan geen persona-, boekprofiel- of boekgeheugengegevens verstuurd en er worden geen tokens verbruikt.
- Ollama-warmup start rechtstreeks in de achtergrondworker zonder voorafgaande synchrone bereikbaarheidstest. Een trage of niet-bereikbare provider bevriest de interface daardoor niet meer bij het openen.
- Ook gewone Meelezer-verzoeken voeren geen blokkerende provider-check meer uit op de GUI-thread; netwerkfouten worden door de worker afgehandeld.
- De Windows CI-smoketest gebruikt nu `--smoke-test` en laat QuietWriter de volledige startup doorlopen tot het hoofdvenster; een foutdialoog telt daardoor niet meer als geslaagde build.
- `LEESMIJ.txt` toegevoegd aan de portable release met starten, SmartScreen, opslag/back-up, AI/privacy en probleemrapportage in Nederlands en Engels.

## 0.36.3 — AI Meelezer als expliciete productrol

- QuietWriter positioneert de AI-laag voortaan expliciet als **Meelezer**: een tweede paar ogen voor feedback, persona-/stijlcontrole, feiten, continuïteit en consistentie, niet als co-auteur.
- **Herschrijf selectie** is verwijderd. De resterende snelacties zijn Feedback, Persona-check en Feitencheck en vragen nooit om vervangende manuscripttekst.
- De basis-systeemprompt verbiedt het model om manuscripttekst te schrijven of te herschrijven, ook wanneer de gebruiker daarom vraagt; de Meelezer geeft observaties, vragen, suggesties en verbeterpunten waarmee de schrijver zelf beslist.
- Instellingen → **AI Meelezer**, de editoractie **Meelezer**, het paneel **Meelees-assistent** en de first-run teksten gebruiken dezelfde positionering in Nederlands en Engels.
- De uitleg bij **Schrijverspersona** beschrijft nu waarom de persona de Meelezer helpt om de eigen stem, toon, ritme en voorkeuren van de schrijver te herkennen zonder die stem over te nemen.
- Een echt nieuw Meelezer-gesprek krijgt bij openen een model-warmup. Tijdens die korte initialisatie staat **De meelees-assistent wordt geladen…** in het gesprek en invoer blijft uitgeschakeld; de modelintroductie verschijnt daarna als eerste antwoord.
- De warmup wordt pas gestart wanneer de gebruiker de Meelezer opent of **Nieuw gesprek** kiest. Er wordt voor de warmup geen manuscripttekst meegestuurd; de gewone manuscriptcontext wordt pas gebruikt bij een echte vraag.
- Nieuwe regressietests bewaken de drie snelacties, het anti-ghostwriting promptcontract, de Meelezer-terminologie en de privacygrens van de warmup.

## 0.36.2 — documentstructuur en directe first-run taalwissel

- Ontwikkeldocumentatie is verplaatst naar `documents/dev/`; gebruikersdocumentatie staat in `documents/`.
- QuietWriter- en third-partylicenties staan nu in `documents/licenses/`; build-staging, PyInstaller en de Over-pagina gebruiken deze nieuwe locatie.
- De first-run wizard schakelt direct van taal zodra Nederlands/English wordt gekozen. Titel, stappen, uitleg en navigatieknoppen worden opnieuw vertaald zonder herstart.
- De gekozen taal blijft na afronden van first-run actief voor de rest van dezelfde applicatiestart.
- Nieuwe regressietests bewaken zowel de documentindeling als live taalwissel tijdens first-run.

## 0.36.1

- First-run wizard gebouwd met vier korte stappen: taal/thema, werkmap, spelling en AI.
- Bestaande gebruikers worden stil gemigreerd via `first_run_done`; een bestaande standaardwerkmap telt ook als bestaand gebruik.
- Productie- en ontwikkelprofiel toegevoegd aan dezelfde executable (`--profile prod|dev`) met gescheiden QSettings, werkmappen, logs en Windows AppUserModelID.
- `--first-run` toegevoegd voor veilige, expliciete wizardtests zonder instellingen eerst te hoeven verwijderen.
- Portable build maakt `QuietWriter PROD.cmd` en `QuietWriter DEV.cmd` als eenvoudige launchers.
- AI blijft voor nieuwe gebruikers standaard uit; wanneer AI uit staat wordt Ollama bij startup niet benaderd.

## 0.36.0

- Nieuwe allowlist-gebaseerde release-staging via `tools/prepare_release.py`; een rommelige ontwikkelmap kan niet meer rechtstreeks in de distributie terechtkomen.
- `build_exe.cmd` bouwt voortaan uitsluitend vanuit `release/stage` en levert daarna een schone `release/QuietWriter-<versie>/` plus portable ZIP en SHA-256 op.
- PyInstaller `onedir`-configuratie, Windows versie-informatie en Nederlandse Hunspell-download uit de packaging-review geïntegreerd.
- Release-hygiene blokkeert onder meer `ppm`, tests, Git-metadata en review-/tussenrapporten.
- Windows GitHub-build gebruikt dezelfde lokale buildroute, zodat CI en lokaal packaginggedrag niet uit elkaar lopen.
- `release/` en PPM zijn expliciet uitgesloten via `.gitignore`.

## 0.35.4

- Herstelt aangepaste Planning-statussen en relatietypen bij bewerkbare keuzelijsten.
- CI faalt bij pyflakes alleen nog op ongedefinieerde namen/syntaxfouten, niet op ongebruikte imports.
- Python 3.12+ is nu het expliciete bron/runtimecontract; `main.py` controleert dit vóór de app-import.

## 0.35.3 — releasefundament afronden

- Startblokker uit 0.35.2 opgelost: `ai/ui.py` importeert `tr` expliciet.
- CI krijgt `pyflakes` als algemene undefined-name gate; daarnaast bewaakt een lokale AST-test modules die `tr()` gebruiken.
- Resterende zichtbare Nederlandse teksten in Engelse modus vertaald: statusbalk, editor-contextmenu, AI-chat, spelling, vervangen, fout/statusmeldingen en boekenplank.
- Planning-statussen en relatietypen worden alleen voor weergave vertaald; canonieke opgeslagen waarden blijven ongewijzigd.
- Nieuwe boeken gebruiken de gelokaliseerde begintitel `Hoofdstuk 1` / `Chapter 1`.
- Interne future-book context gebruikt stabiele ids en wordt pas in de dialoog vertaald.
- Dode `MainWindow.build_ai_context` verwijderd.
- Actiekolom in de Inhoudsboom verbreed zodat `wijzig` / `edit` niet onder het inklaptabje valt.
- OFL-sjabloonplaceholders uit de vier fontlicenties verwijderd.
- Nederlandse en Engelse locale hebben dezelfde 1091 sleutels.
- Oude regressietests zijn bijgewerkt naar het vertaalde contract; hun functionele dekking blijft behouden.

## 0.35.2 — vertaling, licenties en releasebronnen

- Crash-cooldown herkent terugkerende fouten nu op exceptiontype + laatste tracebacklocatie, niet op wisselende fouttekst.
- `nl.json` en `en.json` zijn gelijkgetrokken; alle gebruikte letterlijke `tr()`-sleutels bestaan in beide talen.
- Zichtbare UI-teksten in de releasekritieke schermen lopen via `tr()`; contextkeuzes gebruiken stabiele interne ids zodat vertaling geen logica verandert.
- Nieuwe regressiegates bewaken ontbrekende vertaalsleutels, dynamische AI-profielsecties en hardgecodeerde widgetteksten.
- Fontmanifest voor Merriweather, Literata, Source Serif 4 en EB Garamond toegevoegd, inclusief lokale OFL 1.1-teksten.
- CI haalt de gebundelde fontbestanden op vóór de testsets; de voormalige twee fontfailures horen nu groen te zijn.
- Eigen `LICENSE` en `THIRD_PARTY_LICENSES.md` toegevoegd; Over toont beide licentieoverzichten naast de afzonderlijke fontlicenties.
- First-run-contract aangescherpt: een bestaande standaardwerkmap is al voldoende om een bestaande gebruiker niet opnieuw door onboarding te sturen.

## 0.35.1 — releasefundament II

- Crashmeldingen worden samengevoegd: maximaal één venster tegelijk, extra fouten worden geteld en elke fout blijft afzonderlijk in het log staan.
- Dezelfde herhalende fout opent na sluiten gedurende 60 seconden geen nieuw venster.
- Opstartfouten vóór de normale Qt-eventloop krijgen een modale melding met toegang tot het lokale logbestand.
- Het woordmerk op de Over-pagina gebruikt altijd de lichte hero-kleur, passend bij de donkere hero-achtergrond in alle thema's.
- SVG-woordmerk en UI-iconen worden HiDPI-bewust gerenderd; QIcon bevat 1×- en 2×-pixmaps.
- Qt-waarschuwingen blijven naast het log ook zichtbaar op stderr als er geen eerdere Qt-handler was.
- First-run-contract gebruikt niet langer `workspace` als indicator maar een eigen `first_run_done` plus detectie van bestaande gebruikersdata.
- CI installeert op Ubuntu expliciet de Qt-runtimebibliotheken die PySide6 offscreen nodig heeft.
- Splash-tagline heeft iets meer ademruimte onder het woordmerk.

## 0.35.0 — releasefundament I

- Start van de 1.0-releasefase; AI en overige featurebouw zijn buiten bugfixes bevroren.
- Definitieve QuietWriter-branding toegevoegd: multi-size Windows-icoon, AppUserModelID en thema-gekleurde woordmerken op splash en Over.
- Crashlog verhuisd van de werkmap naar lokale appdata per computer; Qt-berichten worden mee gelogd en onverwachte Python/threadfouten kunnen een niet-modale melding met logknop tonen.
- GitHub Actions toegevoegd voor current/legacy en Qt-runs op Ubuntu en Windows.
- First-run ontwerp voor 0.36 en het gezamenlijke `PLAN_1_0.md` opgenomen.

## 0.34.10

- De opt-inmelding voor hoofdstukplanning is compacter gemaakt: minder regels, dezelfde privacyboodschap en dezelfde knop **Begrepen**.
- Qt-tests krijgen automatisch de marker `qt` wanneer ze de `app`-fixture gebruiken of PySide6 importeren; `pytest -m qt` vervangt daarmee de onvolledige naamfilter `-k qt`.
- `pytest.ini` registreert de `qt`-marker expliciet en `tests/README.md` beschrijft de verplichte reviewruns.
- Geen wijziging aan AI-promptgedrag, Planning-schema of opslag.

## 0.34.9

- Opt-inmelding voor hoofdstukplanning heeft nu een knop **Begrepen**; daarmee kan de gebruiker bewust uit blijven zonder de checkbox aan/uit te hoeven zetten.
- De instellingcontrole gebruikt een robuuste `contains`-fallback, zodat AI-runtimefakes en lichte testdoubles niet onnodig aan QSettings gekoppeld zijn.
- Qt-test voor de opt-inmelding controleert de widgetstatus correct, zonder `isVisible()` op een gesloten contextpaneel.
- Reviewproces: echte Qt-runs staan vanaf deze release expliciet als door Claude uit te voeren in de reviewnotes.

## 0.34.8

- Hoofdstukplanning naar AI is voor bestaande gebruikers nu expliciete opt-in: ontbrekende instelling betekent standaard uit.
- Het AI-contextpaneel legt rustig uit dat deze nieuwe context kan worden meegestuurd en dat externe providers gegevens buiten de computer ontvangen.
- Bestaande expliciete voorkeuren blijven behouden.
- Nog geen contextlengtelimiet; truncatie wordt later als aparte context-budgetfunctie ontworpen.

# 0.34.7

## Hoofdstukplanning expliciet naar AI-context

- Het AI-contextpaneel heeft een expliciete schakelaar **Planning van dit hoofdstuk gebruiken**. De voorkeur wordt bewaard in QSettings (`ai_use_chapter_planning`) en staat standaard aan.
- Alleen bruikbare opgeslagen Planning van het actieve hoofdstuk kan automatisch meegaan. Geen scènes, corrupte Planning of een nieuwere Planning-versie schakelt de actie uit zonder de voorkeur te wissen.
- De samenvatting zegt voortaan eerlijk **wordt meegestuurd** of **niet meegestuurd**. **Context bekijken** toont dezelfde exacte hoofdstukplanning en dezelfde actuele status.
- De systeemprompt houdt automatische hoofdstukplanning en handmatig geselecteerde **Planning-context…** als twee aparte secties. Manuscripttekst blijft leidend wanneer de uitgewerkte tekst afwijkt van het plan.
- Terug naar de Boekenplank gebruikt het geladen AI-store-object als enige bron voor de interne boekstatus; Planning-contextacties staan dan ook intern uit.
- Geen Planning-schemawijziging, geen automatische herkenning en geen writes naar Planning.

# 0.34.6

## AI-context begintoestand en foutcontext

- `Planning-context…` krijgt bij koude start direct de juiste uitgeschakelde toestand; na het openen van een boek wordt de knop via de bestaande `set_book()`-route actief.
- De contexttekst die bij een Planning-fout in het gesprek wordt opgeslagen is weer zelfstandig begrijpelijk: `Planning niet beschikbaar — …`.
- Geen nieuwe Planning- of AI-contextlogica; hoofdstukplanning blijft preview-only.

## 0.34.5 — Planning-contextknop herstellen en responsieve PROGRAMMA-scheiding

- De bestaande knop **Planning-context…** wordt na het openen van een boek weer direct actief. De knop baseert zich op het al geladen AI-boek/store en niet uitsluitend op `MainWindow.active_book()`, dat tijdens transactionele adopt pas later wordt gecommit.
- Foutredenen voor Planning-context bevatten niet langer zelf de prefix `Planning-context niet beschikbaar`; de UI voegt de context toe. Daardoor verdwijnen dubbele formuleringen en blijft de foutstatus vertaalbaar/structureel.
- **Context bekijken** toont Planning-velden compacter: opeenvolgende veldregels krijgen geen lege regel meer, zonder de prompttekst voor daadwerkelijk geselecteerde Planning-context te wijzigen.
- De divider vóór het vaste **PROGRAMMA**-blok is responsief: in een ingeklapte rail op ruime schermen verdwijnt hij, omdat PROGRAMMA al duidelijk onderaan staat; zodra het middendeel moet scrollen blijft de scheiding zichtbaar als extra oriëntatiehulp.
- Geen automatische hoofdstukplanning naar AI en geen schemawijziging in deze release.

## 0.34.4 — transparante hoofdstukplanning vóór automatische AI-context

- Het AI-contextblok toont nu expliciet welke context altijd wordt meegestuurd: Schrijverspersona, Boekprofiel en Boekgeheugen.
- Voor het actieve manuscript-hoofdstuk toont het AI-contextblok een samenvatting van de opgeslagen Planning (`x scènes · y personages`) met de expliciete melding **nog niet automatisch meegestuurd**.
- **Context bekijken** toont de exacte opgeslagen hoofdstukplanning zoals die in een volgende slice als AI-context zou kunnen worden gebruikt. 0.34.4 verandert de AI-prompt nog niet.
- De preview gebruikt dezelfde opgeslagen Planning als **In dit hoofdstuk** en bevat titel, status, locatie, synopsis, doel, conflict, uitkomst, notities en gekoppelde personages.
- AI Planning-contextfouten hebben nu een expliciet `error`-veld in plaats van herkenning via Nederlandse labeltekst; foutmeldingen krijgen daardoor geen dubbele `Planning: Planning-context ...`-prefix.
- Planning-JSON met een UTF-8-BOM wordt via `utf-8-sig` correct als Planning gelezen. Ook een nieuwere Planning-versie met BOM blijft dus herkenbaar als **nieuwer** en wordt niet per ongeluk als gewone corruptie behandeld.
- Geen Planning-schemawijziging en geen automatische Planning→AI-koppeling in deze release.

## 0.34.3 — Planning-context fail-safe, History-guard en zichtbaardere railgroepen

- De ingeklapte railseparator is 2 px hoog in plaats van 1 px, met dezelfde thematische borderkleur: duidelijker zichtbaar zonder de rail zwaarder te maken.
- `In dit hoofdstuk` zet expliciet `qproperty-indent: 0` op scènetitels en veldlabels, zodat koppen en waarden links uitlijnen.
- De statusbalk gebruikt correct enkelvoud: `1 woord` in plaats van `1 woorden`, zowel voor boek- als hoofdstuktelling.
- De bestaande AI-functie **Planning-context** faalt niet meer stil bij corrupte of nieuwere Planning. Keuzevenster en contextstatus tonen een korte reden; een AI-vraag gaat zonder Planning-context door.
- **Versiegeschiedenis → Deze versie herstellen** weigert een herstel zolang live Planning door een nieuwere QuietWriter is geschreven. Er wordt niets gedeeltelijk teruggezet; de gebruiker krijgt de instructie QuietWriter bij te werken.
- Nieuwe actuele regressies bewaken beide Planning-routes, Unicode/visuele contracten en de History-guard.

## 0.34.2 — statusbalk samenvoegen, Planning-versies veilig onderscheiden en tests aanscherpen

- De losse telling **Boek bevat … woorden** onder de hoofdstukboom is verwijderd. De vaste statusbalk toont nu boek- en hoofdstuktelling samen: `Boek: x woorden · Hoofdstuk n van m: y woorden`.
- Planning-validatie is gecentraliseerd in `planning_validation.py`; `PlanningStore` en Integriteit gebruiken dezelfde structuurregels.
- Planning-data met een **nieuwere formaatversie** krijgt een eigen `FuturePlanningFormatError`. Het boek blijft open en Planning blijft alleen-lezen, maar Integriteit markeert dit als `aux_json_newer` en **niet herstelbaar** met de instructie QuietWriter bij te werken.
- `In dit hoofdstuk` onderscheidt nieuwere Planning-data van beschadigde Planning en adviseert bij een nieuwere versie om QuietWriter bij te werken.
- De separator-Qt-test meet voortaan de 1px inhoudslijn in plaats van de widgethoogte inclusief marge.
- Zeven regressiebestanden voor veel teruggekomen kernrisico's zijn teruggeplaatst in `tests/current/`: transactionele adoptie, onleesbare bronnen met lokale invoer, Planning-notities/false-dirty, exportconflicten, History-preview en exportcorrectheid.
- De verouderde Planning-character-fake in `tests/legacy/` is bijgewerkt. Legacy is opnieuw groen behalve de twee bekende ontbrekende fontresources.
- Releasebeleid vastgelegd: volledige legacy-suite verplicht bij elke nieuwe minor-release.

## 0.34.1 — Planning-bronhardening en vollediger hoofdstukcontext

- De testsuite is opgesplitst in `tests/current/` en `tests/legacy/`: `pytest` draait voortaan alleen de compacte actuele suite; historische regressies blijven apart uitvoerbaar.
- Geldige JSON met een ongeldige Planning-structuur (`scenes`/`characters` geen lijst, `character_ids`/`relations` geen lijst, onbekende Planning-versie) blokkeert het openen van het boek niet meer. Het betreffende Planning-onderdeel wordt alleen-lezen en verwijst naar Integriteit.
- Integriteit controleert nu ook de structuur van `planning/outline.json` en `planning/characters.json`, niet alleen of het geldige JSON-objecten zijn.
- **In dit hoofdstuk** toont naast titel/synopsis/status/locatie/personages nu ook opgeslagen **Doel, Conflict, Uitkomst en Notities** per scène wanneer ingevuld.
- Scènes in het rechterpaneel hebben een duidelijke kaartstructuur en zichtbare subkoppen; `subsectionTitle` en contextveldlabels hebben nu echte themastijlen.
- De hoofdstuk-/woordentelling in de statusbalk is een blijvende editorstatus: tijdelijke meldingen mogen hem vervangen, maar na afloop komt de telling terug.
- Ingeklapte railseparators zijn echte 1px vlakken met de gewone borderkleur in plaats van een nauwelijks zichtbare HLine.
- `ChapterContextPanel` verbergt oude widgets vóór `deleteLater()`, zodat headless/uitgestelde eventloops geen overlappende oude context laten zien.
- Nieuwe NL/EN locale-keys voor het hoofdstukcontextpaneel en de Planning-bronwaarschuwing.

## 0.34.0 — Planning tijdens schrijven: eerste slice

- Nieuwe rechterpaneelfunctie **In dit hoofdstuk** toont alleen-lezen de opgeslagen Planning voor het actieve manuscript-hoofdstuk.
- Het paneel leest scènes en gekoppelde personages rechtstreeks uit `PlanningStore`; er wordt geen tweede bron van waarheid en geen nieuw dataformaat geïntroduceerd.
- Verweesde personagekoppelingen en scènes voor andere hoofdstukken worden stil overgeslagen. Corrupte `outline.json`/`characters.json` geeft een korte foutmelding zonder de editor te blokkeren.
- Het paneel is onafhankelijk van AI en blijft beschikbaar wanneer AI is uitgeschakeld. Bij Voorwoord/Nawoord, geschiedenis-preview en een beschadigd hoofdstuk is het niet beschikbaar.
- **Planning openen** gebruikt de bestaande centrale navigatie. De actieve linkerrailknop wordt bij programmatic navigation automatisch in beeld gescrold.
- Linkerrail-selectie gebruikt voortaan één expliciete `QButtonGroup` over zowel het scrollende deel als het vaste PROGRAMMA-blok. Daardoor kunnen Schrijverspersona, Instellingen en Prullenbak niet tegelijk geselecteerd blijven met een boekpagina.
- Eerste slice voegt nog géén Planning-data toe aan AI-prompts en schrijft niets vanuit het nieuwe paneel.

## 0.33.1 — Railafwerking en AI-contexttransparantie

- **PROGRAMMA** staat vast onderaan de linkerrail, buiten het scrollende boek/AI-gedeelte; **Menu** blijft vast bovenaan. Instellingen en Prullenbak zijn daardoor ook op lage schermhoogte direct bereikbaar.
- In de ingeklapte rail tonen dunne separators de grenzen tussen zichtbare groepen; in de uitgeklapte rail nemen de tekstkoppen die rol over.
- Persona, Boekprofiel en Boekgeheugen leggen weer expliciet uit dat hun inhoud bij iedere AI-vraag naar de gekozen provider wordt gestuurd. Bij een externe provider verlaten die gegevens de computer.
- Boekprofiel vermeldt opnieuw dat bewuste projectspecifieke afwijkingen de globale Schrijverspersona voor dat boek kunnen overrulen.
- De railhoogtetest laadt nu het echte QuietWriter-stylesheet, zodat de gemeten scrollbarbreedte overeenkomt met de applicatie.
- De oude 0.32.2-previewtest is bijgewerkt van de verwijderde kop **SCHRIJVEN** naar het huidige **AI-CONTEXT**-model.

## 0.33.0 — Informatiearchitectuur en declaratieve rail

- Linker navigatie is opnieuw opgebouwd vanuit één declaratief railmodel (`state → model → render`). Zichtbaarheid van items, groepen en fallback-bestemming staat niet langer verspreid over losse `setVisible()`-regels.
- Nieuwe groepen: **BIBLIOTHEEK**, **HUIDIG BOEK**, **AI-CONTEXT** en **PROGRAMMA**. Boekgeheugen en Boekprofiel staan onder AI-CONTEXT; Schrijverspersona blijft globaal onder PROGRAMMA.
- Railrendering is puur: de renderer verandert alleen zichtbaarheid. Paneel sluiten en wegsturen van een pagina die na een gecommitteerde instelling verborgen wordt gebeuren uitsluitend in `_apply_committed_navigation_effects()`, nooit tijdens preview.
- Fallback staat centraal in het model: een verborgen actieve/terugkeerpagina valt terug op **Inhoud** met open boek, anders **Boekenplank**.
- De rail gebruikt een verticale `QScrollArea`, zodat 700/720/768 px hoogte niet door alle navigatie-items wordt opgedrukt. De smalle scrollbar heeft gereserveerde breedte binnen de bestaande 64/218 px rail.
- Uitlegteksten voor Schrijverspersona, Boekprofiel en Boekgeheugen zijn op elkaar afgestemd rond het contextmodel: schrijver (globaal), boekprofiel (dit boek), geheugen (wat AI moet blijven weten).
- De conflictmelding **Structuuractie niet uitgevoerd** is generieker gemaakt naar **Actie niet uitgevoerd**.
- Testhardening uit reviewronde 33: onverwachte dialogen vanuit timers/slots worden ook in teardown gedetecteerd; `QDialog.exec`, `QInputDialog` en `QFileDialog` zijn suitebreed afgevangen; code-health gebruikt een absoluut pakketpad en controleert dat er werkelijk bronbestanden zijn gevonden.
- Nieuwe railtests bevatten handmatig uitgeschreven verwachte toestanden, algemene invarianten, fallbacktests, een 16-toestanden runtime-matrix en hoogtetests op 700/720/768 px.

## 0.32.7

- Test-hardening zonder productwijzigingen.
- Nieuwe pakketbrede AST-test detecteert onbereikbare top-level statements na een onvoorwaardelijke `return` of `raise`; dit vangt de 0.32.4-startcrashklasse zonder PySide6-runtime.
- De broze positietest voor `ManuscriptEditor.source_text()` is verwijderd.
- Centrale `tests/conftest.py`-guard laat onverwachte `QMessageBox.information`, `warning`, `critical`, `question` en instance-`exec()` direct als testfout eindigen in plaats van de Qt-suite te laten hangen.
- De specifieke dialogenfixture uit `test_review_0324.py` is verwijderd; de bewaking geldt nu suitebreed.

## 0.32.6

- Preventieve dirty-baseline voor vrije publicatieteksten (Voorwoord, Nawoord en vergelijkbare Markdown-items): presentatiepasses maken de tekst niet meer dirty; terugtypen naar de opgeslagen bron maakt weer clean; een geslaagde save verplaatst de baseline.
- De hangende Qt-test uit reviewronde 31 krijgt een echte `workspace` in de fixture, zodat de legitieme melding **Werkmap gewijzigd** niet meer onbedoeld modaal blokkeert.
- De 0.32.4-reviewtests falen nu expliciet op onverwachte `QMessageBox.information/warning/critical`-dialogen in plaats van eindeloos te wachten.
- Het 0.32.5-startupvangnet is aangescherpt met AST: `ManuscriptEditor.__init__` mag geen geneste methodedefinitie of voortijdige `return` bevatten. Dit vangt de 0.32.4-foutklasse ook zonder PySide6-runtime.
- Geen productgedrag gewijzigd buiten deze preventieve dirty-regel en testhardening.

## 0.32.5

- Hotfix: `ManuscriptEditor.source_text()` stond in 0.32.4 per ongeluk midden in `__init__`. Daardoor werd de resterende editorinitialisatie onbereikbaar en kon QuietWriter bij startup crashen.
- De volledige `ManuscriptEditor`-initialisatie staat weer in `__init__`; `source_text()` is een normale aparte methode na de constructor.
- Regressietest toegevoegd die de constructorvolgorde bewaakt.
- Geen functionele wijzigingen ten opzichte van de bedoelde 0.32.4-functionaliteit.

## 0.32.4

- Koude start toont alleen Bibliotheek/programmafuncties: alle boeknavigatie en de kop **HUIDIG BOEK** volgen centraal of er werkelijk een actief boek is.
- Planning-notities gebruiken dezelfde brongebaseerde dirty-detectie als de hoofdstuk-editor; presentatiepasses vanuit Instellingen maken geen leeg `notes.md` meer en starten geen autosave.
- `ManuscriptEditor.source_text()` is de gedeelde persistente bronrepresentatie voor manuscriptachtige editors. Planning-notities, hoofdstukken en vrije publicatietekst gebruiken dezelfde Unicode-veilige route.
- Planning-notities bewaren harde spaties en U+2028 bij een echte save en conflict-snapshot.
- Scènescheiding invoegen/verwijderen en afbeelding invoegen/verwijderen bouwen documentbrede wijzigingen niet meer op uit `toPlainText()`, zodat typografische Unicode in de rest van het hoofdstuk intact blijft.
- Nieuwe Qt-regressietests voor koude-startnavigatie, presentatiepasses zonder notes-write en Unicode-behoud in Planning-notities.

## 0.32.3

- Editorbron centraal gemaakt via `_editor_source_text()`: dirty-detectie, baseline, conflictsnapshot en save gebruiken dezelfde Qt-bronrepresentatie.
- Hoofdstukken met harde spaties, Unicode line separators of BOM worden niet meer vals als gewijzigd gezien door presentatie-/spellingswerk.
- Gewone hoofdstuk-saves gebruiken `QTextDocument.toRawText()` met Qt-alineascheiding terug naar `\n`, zodat harde spaties en U+2028 behouden blijven.
- Nieuwe runtime-regressietests voor speciale Unicode-tekens en bronbehoud.

## 0.32.2
- Editor dirty-status vergelijkt voortaan de echte manuscripttekst met de laatst geladen/opgeslagen bron; rehighlight/presentatiepasses starten geen autosave meer.
- Spellingsacties zoals negeren/woordenboek toevoegen kunnen daardoor niet langer zonder tekstwijziging een hoofdstuk laten herschrijven.
- Live preview van AI en Geavanceerde opties houdt nu ook SCHRIJVEN-groepskop en Integriteit-witruimte synchroon, ook na rail in-/uitklappen.
- AI-paneel wordt tijdens een niet-opgeslagen preview niet meer gesloten; alleen een gecommitteerde AI-uit schakelt het paneel uit.
- Settings-save bewaart de vorige QSettings-toestand en rolt effectieve runtime-previews terug als sync mislukt.
- Nieuwe regressietests voor brongebaseerde dirty-detectie, previewconsistentie en Settings-rollback.

# Changelog

## 0.36.6 — gratis OpenRouter-modellen beter zichtbaar

- OpenRouter-modelmetadata bewaart nu de actuele prompt- en outputprijs en markeert modellen als gratis wanneer beide nul zijn; expliciete `:free`-varianten en `openrouter/free` worden eveneens herkend.
- In de modelkeuzelijst staan gratis OpenRouter-modellen voortaan vóór betaalde modellen, met een `🆓`-markering; `🧠` blijft daarnaast zichtbaar wanneer thinking wordt ondersteund.
- Nieuwe optie **Alleen gratis modellen tonen** filtert de OpenRouter-lijst zonder betaalde modellen te verwijderen uit de opgehaalde catalogus.
- De optie is alleen zichtbaar bij OpenRouter en wordt als gebruikersvoorkeur opgeslagen. **Modellen ophalen** ververst de gratis/betaald-status.
- Tooltips en Nederlandstalige/Engelstalige uitleg beschrijven wat de gratis-markering betekent.

## 0.32.1 — Instellingen direct toepassen en Planning-uitleg

- Instellingen gebruikt nu een expliciete verwijzing naar `MainWindow`; `settings_saved()` wordt na Opslaan daadwerkelijk uitgevoerd in plaats van stil te verdwijnen via de tussenliggende `CurrentPageStack`.
- AI- en Geavanceerde-optieschakelaars geven direct een live preview in de hoofdnavigatie. Verlaat je Instellingen zonder op te slaan, dan keert de rail terug naar de opgeslagen toestand.
- Spelling uit wordt na Opslaan onmiddellijk op het geopende manuscript toegepast: rode markeringen verdwijnen, het spellingspaneel sluit en de spellingsknop verdwijnt zonder herstart.
- QuietWriter kan weer normaal starten wanneer `spell_enabled=False`; de woordenboek-/highlighterinitialisatie gebeurt pas nadat `SpellPanel` bestaat.
- Terugkeren uit Instellingen wordt na een opgeslagen featurewijziging opnieuw veilig naar Inhoud geleid wanneer de oorspronkelijke pagina inmiddels verborgen is.
- Planning heeft nu dezelfde pagina-opbouw als andere boekfuncties: titel **Planning** met een korte uitleg boven Personages/Outline/Notities.
- De regel **Geavanceerde opties gebruiken** toont nog maar één tekstlabel; het vinkje zelf is kaal en heeft een toegankelijke naam.
- Dezelfde expliciete `MainWindow`-route wordt ook gebruikt voor theme-preview en het bijwerken van opgehaalde AI-modellen, zodat deze Settings-acties niet meer afhankelijk zijn van Qt-parenting.

## 0.32.0 — Functiezichtbaarheid en directe editorfeedback

- **AI-assistent gebruiken** stuurt nu alle AI-oppervlakken: AI-assistent, Schrijverspersona, Boekprofiel en Boekgeheugen verdwijnen uit de interface wanneer AI uit staat. De onderliggende Markdown en AI-instellingen blijven volledig bewaard en verschijnen weer bij opnieuw inschakelen.
- Instellingen → Algemeen bevat **Geavanceerde opties gebruiken**. Deze staat standaard aan en bepaalt in 0.32.0 uitsluitend of **Integriteit & herstel** in de boeknavigatie zichtbaar is. De instelling verandert of verwijdert geen boekdata.
- Spellingscontrole uitschakelen verwijdert rode onderstrepingen direct uit het reeds geopende manuscript, sluit een eventueel geopend spellingspaneel en verbergt de spellingsknop. Een herstart is niet meer nodig.
- Integriteit toont bij een beschikbare herstelkopie ook de herkomst, bijvoorbeeld een lokale conflictversie met tijdstip. De selectie van de nieuwste geldige herstelkopie verandert niet.
- Navigatie na Instellingen valt veilig terug op Inhoud wanneer de pagina waarvandaan Instellingen werd geopend door de nieuwe zichtbaarheidsschakelaar verborgen is.

## 0.31.6 — Corrupte bron tijdens lokale invoer

- Extern beschadigd `ai/memory.md` of `ai/boekprofiel.md` blokkeert de conflictflow niet meer wanneer lokale invoer nog dirty is.
- De lokale Boekgeheugen-/Boekprofiel-invoer wordt tijdens adoption-preflight eerst als `conflict_local` in Versiegeschiedenis bewaard; daarna opent de beschadigde bron in de bestaande alleen-lezen-foutstaat.
- Planning-notities volgen hetzelfde fail-closed patroon: dirty lokale notities worden veiliggesteld en een beschadigd `planning/notes.md` wordt niet terug over de foutstaat heen hersteld.
- Bij een onleesbare eigen bron wordt de normale mine/disk-conflictdialoog overgeslagen: overschrijven is dan niet veilig; QuietWriter bewaart lokaal werk en verwijst naar Integriteit.
- De transactionele 0.31.5-preflight blijft leidend: een fout bij het maken van het herstelpunt laat de live UI volledig op de oude boekversie staan.

## 0.31.5 — Transactionele live-book adoptie
- Drie-wegs merges voor Boekgeheugen, Boekprofiel en Boekdetails worden nu volledig voorbereid vóórdat één pagina naar de nieuwe live-bookstate wordt omgebonden.
- Eventuele `conflict_local`-recoveryversies worden in die preflight gemaakt. Als zo'n snapshot door een lock of schrijffout mislukt, blijft de volledige bestaande workspace op het oude `Book`-object staan.
- De commitfase gebruikt de vooraf berekende mergeplannen en schrijft zelf geen recoveryversies meer.
- Conflictmeldingen en de statusmelding van Boekdetails worden pas getoond nadat alle pagina's én de centrale revision-baseline succesvol op hetzelfde nieuwe `Book`-object staan.
- Hiermee wordt het laatste bekende gemengde-statepad uit reviewronde 21 gesloten zonder de bestaande conflictkeuzes of merge-regels te veranderen.

## 0.31.4 — Exportconflictflow en volledig publicatieherstel
- Exportinstellingen vangen echte externe boekwijzigingen nu zichtbaar af in plaats van een Qt-exceptie naar de excepthook te laten ontsnappen. Bij een schone editor wordt de nieuwste boekversie centraal geadopteerd en kiest de gebruiker de exportinstelling daarna opnieuw.
- Als manuscript- of publicatietekst nog pending is, gebruikt Export dezelfde bestaande editor-conflictflow als Media zodat lokale tekst niet door een reload verloren kan gaan.
- Afgekapte maar UTF-8-geldige `export/settings.json` wordt al bij het binden van de Exportpagina herkend; de pagina gaat fail-closed met de bestaande herstelmelding in plaats van per klik te falen.
- Integriteit controleert nu ook alle bestaande `publication/texts/*.md`-bestanden op UTF-8 en markeert beschadigde publicatietekst als herstelbaar via Versiegeschiedenis.
- De opslagguard blijft de laatste verdedigingslaag: geen van deze UI-routes mag corrupte of extern gewijzigde bronbytes stil overschrijven.
- De transactionele/all-or-nothing commit van `adopt_active_book()` blijft bewust apart voor 0.31.5; deze release houdt de export- en herstelbasis eerst schoon en testbaar.

## 0.31.3 — Exportrevisie, spelling en corruptieguards
- Exportinstellingen gebruiken nu dezelfde revision-guard als andere boekstores: verify vóór write en refresh van de baseline erna. Eigen wijzigingen op Export veroorzaken daardoor geen vals extern conflict.
- De Exportpagina onderdrukt writes tijdens het laden van UI-instellingen, zodat een reload nooit door signalen terugschrijft.
- Spellingscursorvolging ververst foutoffsets zodra de documentrevision wijzigde; de refresh selecteert daarbij geen tekst.
- Het onderscheid tussen typen en doelbewuste cursorbeweging gebruikt echte `contentsChange`-tekstmutaties in plaats van een revision-heuristiek.
- Bestaande JSON-bronnen voor Planning, Publicatie en Export worden vóór opslaan ook syntactisch gevalideerd. Afgekapte maar geldige UTF-8-JSON kan niet meer stil worden overschreven.
- Beschadigde vrije publicatietekst opent als alleen-lezen herstelmelding; normale save weigert de corrupte bytes te vervangen.
- De witruimte vóór Integriteit volgt centraal de actieve-boekmodus en verdwijnt ook via Boekenplank.
- Transactionele preflight voor conflict-snapshots/dialogen tijdens `adopt_active_book` blijft als afzonderlijke architectuurfix open; 0.31.3 verandert die commitflow bewust niet.

## 0.31.2 — Veilige adoptie en spelling volgt cursor
- Resterende JSON-bronnen beschermd tegen ongeldige UTF-8; exportinstellingen toegevoegd aan Integriteit.
- Centrale voorbereidingsfase vóór `adopt_active_book`; actieve identiteit/revision tracking pas als laatste gecommit.
- Spellingspaneel volgt doelbewuste cursorbeweging zonder editorselectie te wijzigen.
- Witruimte vóór Integriteit synchroniseert direct met open/dicht boek.

## 0.31.1 — Boekvolgorde en onderscheidende iconen
- HUIDIG BOEK volgt nu de schrijfworkflow: Inhoud, Planning, Boekgeheugen, Boekprofiel, Media, Boekdetails, Exporteren, Integriteit.
- Kleine witruimte vóór Integriteit in de uitgeklapte rail.
- Eigen iconen voor Boekgeheugen, Boekprofiel en Integriteit; Schrijverspersona behoudt het persona-icoon.
- Tabvolgorde volgt de nieuwe knopvolgorde.
- Technische reviewnotitie toegevoegd voor transactionele boekadoptie en de volgende spellingsstap.


## 0.31.0 — Rustigere navigatie en editorpolish

- Hoofdnavigatie gegroepeerd met subtiele kopjes: Bibliotheek, Huidig boek, Schrijven en Programma.
- Groepskopjes verdwijnen in de ingeklapte rail; Huidig boek verschijnt alleen wanneer een boek open is.
- Automatisch opslaan is nu vast gedrag en kan niet meer worden uitgezet. Ctrl+S blijft direct opslaan.
- De oude autosave-schakelaar is uit Instellingen verwijderd; bestaande configuraties worden naar autosave=true genormaliseerd.
- De boekteller heet nu expliciet `Boek bevat … woorden`; de hoofdstukstatus onderin blijft `Hoofdstuk x van y · … woorden`.
- Geen wijzigingen aan spellingscontrole of transactionele boekadoptie in deze release.

## 0.29.4 — Publicatie-save en corruptiebestendige zoekacties

- De hoofdstuk-corruptievlag geldt nu uitsluitend voor manuscripttekst en kan publicatietekst niet meer stil overslaan.
- Voorwerk/Achterwerk wist de hoofdstuk-corruptiestatus expliciet; publicatie-save wordt vóór de hoofdstukguard afgehandeld.
- Zoeken over sectie/boek slaat onleesbare hoofdstukken over en meldt dit in de statusbalk.
- Alles vervangen slaat onleesbare hoofdstukken over in plaats van halverwege te crashen.
- Dupliceren van een beschadigd hoofdstuk wordt veilig geweigerd met `CorruptSourceError`.
- Extra regressietest borgt dat dupliceren geen enkel bestand wijzigt.


## 0.29.3 — Corrupte bronbestanden fail-closed
- Nieuwe `CorruptSourceError` in de storage-laag weigert normale writes over bestaande tekstbestanden die geen geldige UTF-8 zijn.
- De guard geldt voor hoofdstukken, Boekgeheugen, Boekprofiel en Planning-notities; alleen de expliciete Integriteit-herstelroute kan zulke bytes vervangen.
- Boekgeheugen en Boekprofiel bewaren een expliciete corrupte-bronstatus: navigatie, sectiewissels, Opslaan en AI-Onthouden kunnen de bron niet meer overschrijven.
- De editor bewaart een expliciete corrupte-hoofdstukstatus; autosave en programmatische mutaties worden geneutraliseerd. Invoegen, AI en spelling zijn uitgeschakeld zolang het huidige hoofdstuk beschadigd is; Zoeken blijft bruikbaar maar vervangen niet.
- Een geldig leeg UTF-8-bestand blijft normaal schrijfbaar.

## 0.29.2 — Onleesbare tekst veilig herstellen
- Integriteit blijft bereikbaar wanneer gewone tekstbestanden ongeldige UTF-8 bevatten.
- Huidig hoofdstuk, Boekprofiel, Boekgeheugen en Planning-notities krijgen een expliciete alleen-lezen foutstaat bij decode-fouten.
- Beschadigde tekst wordt nooit stil als lege inhoud geladen; autosave kan het bronbestand daardoor niet overschrijven.
- Herstel blijft centraal herladen zodat een hersteld bestand direct weer de actuele inhoud toont.
- Transactionele/all-or-nothing centrale adopt staat expliciet gepland voor 0.30.0.

## 0.29.1 — Herstel sluit nu veilig aan op de live editor

- Integriteit neemt vóór iedere audit eerst centraal de actuele schijftoestand over. Een bestand dat tijdens een geopende sessie verdwijnt of beschadigt kan daardoor direct worden hersteld zonder eerst via de Boekenplank te heropenen.
- Na een geslaagd herstel wordt het boek centraal opnieuw geladen en geadopteerd. Editor, Planning, Boekdetails, Boekprofiel, Boekgeheugen, Media en Export wijzen daarna allemaal naar dezelfde herstelde live toestand.
- Het huidige hoofdstuk-id wordt bij de reload behouden, zodat de editor het herstelde hoofdstuk direct opnieuw van schijf toont in plaats van stale tekst te bewaren.
- Future-format en corrupte manifests blijven read-only auditbaar: als `load_book` ze niet veilig kan adopteren, neemt de integriteitschecker het over.
- Een bewust geblokkeerd boek wordt bij een audit niet stil opnieuw getrackt of gedeblokkeerd. `Library.is_book_blocked()` maakt die toestand expliciet.
- Herstelbron-lookup wordt per audit gecachet zodat selecteren van dezelfde issue niet telkens de volledige versiegeschiedenis hoeft te doorlopen.

## 0.29.0 — Integriteit & herstel

- Nieuwe pagina **Integriteit** voor het geopende boek.
- De controle is volledig read-only: er wordt nooit automatisch gerepareerd.
- Fouten en waarschuwingen worden per bestand getoond met een korte uitleg.
- Herstel is alleen beschikbaar wanneer Versiegeschiedenis een geldige herstelkopie bevat.
- Herstel gebruikt de bestaande transactionele backend en maakt eerst `pre_integrity_repair`.
- Oudere boekformaten kunnen expliciet vanaf deze pagina worden gemigreerd; vooraf wordt een volledige herstelversie gemaakt.
- Legacy boeken behouden hun oude formaat bij normaal openen/opslaan en worden dus niet langer stil naar formaat 2 geschreven vóór die expliciete migratie.
- Nieuw `BookBlockedError` onderscheidt bewust geblokkeerde/losgekoppelde boeken van gewone schrijffouten.
- Integriteit is aangesloten op de centrale live-book lifecycle, revisiebewaking en navigatie-saveguards.

## 0.28.4 — Veilige detach en Boekdetails-conflictflow

- Future-format loskoppelen blokkeert het oude boek nu tegen alle latere writes in plaats van de revisiebewaking te verwijderen.
- Planning heeft een force-detach die geen `save_pending()` uitvoert en achtergebleven notes/personageconcepten opruimt.
- Boekdetails verwerkt gewone externe wijzigingen via reload + bestaande drie-wegs merge en kan daardoor niet meer vastlopen op de saveguard.
- Boekdetails gebruikt een expliciete MainWindow-referentie voor de future-format recoveryroute.
- Nieuwe regressietests voor write-block/reopen-semantiek.
- Pakketversie verhoogd naar 0.28.4.

## 0.28.3 — Centrale future-format exit en Boekdetails-saveguard

- Future-format conflicten vanuit Planning, Boekprofiel en Boekgeheugen gebruiken nu één centrale `preserve_local_and_close_future_book()`-route. De lokale invoer wordt eerst als `conflict_local` in Versiegeschiedenis veiliggesteld; pas daarna wordt het incompatibele boek zonder savepoging losgekoppeld.
- Mislukt het maken van die recovery-snapshot, dan blijft het boek open en blijft de lokale invoer in de pagina staan. QuietWriter kiest ook hier fail-closed boven een geforceerde terugkeer naar de boekenplank.
- Boekdetails heeft nu een echt boolean save-contract. Niet-opgeslagen metadata, waaronder synopsis, wordt vóór terugkeer naar de boekenplank, afsluiten en hoofdnavigatie opgeslagen; bij mislukken blijft de gebruiker op de huidige workspace.
- Ook Boekdetails gebruikt de centrale future-format route en kan zijn actuele formulierstate als recovery-only Book in History bewaren zonder het toekomstige live manifest te muteren.
- Nieuwe regressietests bewaken de centrale route, de drie Planning/AI-pagina-aansluitingen en de Boekdetails-guards.
- Pakketversie verhoogd naar 0.28.3.

## 0.28.2 — Schrijffouten en future-format UI-grens

- Nieuwe `StorageWriteError` vormt één domeinfout voor veilige storage-writes. Blijvende locks en andere `OSError`s verlaten de storage niet meer als losse platformexcepties. De oorspronkelijke live file blijft ongewijzigd.
- De manuscripteditor behandelt `StorageWriteError` als tijdelijk niet opgeslagen: `dirty` blijft waar, autosave probeert later opnieuw en navigatie/afsluiten stoppen omdat `save()` `False` retourneert.
- `closeEvent()` heeft daarnaast een laatste fail-safe rond de editorsave: iedere onverwachte save-exceptie negeert het close-event en laat het venster open.
- Conflict met een boek dat intussen door een nieuwere QuietWriter naar een toekomstig formaat is geschreven bewaart eerst de lokale hoofdstuktekst in `conflict_local`, toont een duidelijke update-melding en koppelt het incompatibele boek zonder verdere savepoging los. Dezelfde bescherming is toegevoegd voor openstaande publicatietekst.
- `force_return_to_bookshelf()` is een expliciete no-save route en wordt alleen gebruikt nadat lokale conflictinhoud aantoonbaar in History is veiliggesteld. Dit voorkomt een oneindige conflictdialoog tegen een formaat dat deze versie niet kan laden.
- `metadata` in `book.json` moet ontbreken, `null` of een JSON-object zijn. Audit en loader hanteren daarmee ook voor dit laatste veld hetzelfde structurele contract.
- Byte-exact herstel gebruikt nu dezelfde retryende atomaire write-infrastructuur als tekst; een korte Windows/Dropbox-lock op een binair herstelbestand faalt niet meer direct.
- `migrations.py` is opnieuw leesbaar uitgeschreven zodat validatie- en migratievoorwaarden afzonderlijk reviewbaar zijn.
- Nieuwe regressietests dekken de domeinfout, behoud van originele bytes, metadata-validatie, binaire retry en broncontroles op de UI-failsafes.
- Pakketversie verhoogd naar 0.28.2.

## 0.28.1 — Integriteitsherstel na failure-injection review

- `load_book()` valideert het boekformaat en de structurele velden die de loader werkelijk gebruikt. Toekomstige formaten worden vóór openen geweigerd; een oudere QuietWriter kan daardoor een later format 3+ niet stil als format 2 terugschrijven.
- Onbekende top-level sleutels uit `book.json` worden in `Book.extra_manifest` bewaard en bij iedere normale manifestwrite teruggeschreven. Forward-compatible metadata verdwijnt dus niet meer door een gewone hoofdstuksave.
- Audit en loader delen `validate_manifest_structure()`, zodat ontbrekende sectie-/hoofdstukvelden niet meer door de audit kunnen worden goedgekeurd terwijl openen daarna faalt.
- Herstel uit History valideert kandidaten inhoudelijk: aux-JSON moet een object zijn, tekst moet geldige UTF-8 zijn en media moet exact de SHA-256 uit het live mediamanifest hebben. `pre_integrity_repair`-snapshots worden als herstelbron overgeslagen. Na de write wordt dezelfde regel opnieuw gecontroleerd voordat herstel als geslaagd geldt.
- Gericht herstel schrijft alle bestandstypen byte-exact via een sibling tempbestand + `os.replace`; CRLF en andere byteverschillen worden niet genormaliseerd.
- History sorteert deterministisch op `(created_at, id)`, waarbij de microseconden in de version-id de volgorde bepalen wanneer meerdere snapshots dezelfde seconde delen.
- Dubbele hoofdstukbestanden worden na padnormalisatie en `casefold()` vergeleken, zodat `chapters/./x.md` en hoofdlettervarianten niet als verschillende koppelingen gelden.
- Boekformaatwaarden accepteren alleen echte integers; `bool`, floats en numerieke strings worden geweigerd. Een migratie die niets hoeft te wijzigen maakt geen `pre_migration`-checkpoint.
- `_safe_atomic_write_text()` valt na blijvende `PermissionError` niet langer terug op directe overschrijving. De operatie faalt liever met behoud van de oorspronkelijke bytes dan de live file bij crash/stroomuitval te kunnen afkappen.
- `list_books()` houdt niet-openbare boeken als diagnose bij; de boekenplank meldt dat één of meer boeken niet konden worden geopend in plaats van ze volledig stil te laten verdwijnen.
- Nieuwe 0.28.1-regressietests dekken alle zes reviewbevindingen plus no-op migratie en de aangescherpte atomiciteitsgarantie.
- Pakketversie verhoogd naar 0.28.1.

## 0.27.1 — Media Manager correctness na runtime-review

- Herstelbare hoofdstukken in `trash/chapters/<book-id>/` tellen nu mee als actieve mediagebruikers. Hun image-paden worden geïnterpreteerd vanuit de oorspronkelijke hoofdstuklocatie en in Media getoond als **Prullenbak: <titel>**. Een asset die alleen in de prullenbak wordt gebruikt blijft daardoor beschermd totdat dat hoofdstuk definitief wordt verwijderd.
- Een onleesbaar hoofdstuk in de prullenbak blokkeert cleanup conservatief, net als een onleesbare live of historische Markdownbron. QuietWriter concludeert nooit "ongebruikt" als herstelbare inhoud niet betrouwbaar kon worden geïnspecteerd.
- De Media-pagina geeft bij batch-cleanup nu expliciet alleen de op dat moment `can_cleanup`-assets door. Daardoor kan één historisch onveilige ongebruikte afbeelding de veilige opruimbare subset niet meer blokkeren. De `MediaManager`-API zelf blijft bewust streng: wie een onveilig asset-id expliciet aanvraagt krijgt nog steeds `MediaCleanupError`.
- `ExternalModificationError` heeft een eigen Media-flow. Bij een schone editor wordt de nieuwste diskversie centraal via `adopt_active_book()` overgenomen en de inventaris ververst. Zijn er niet-opgeslagen manuscript-/publicatiewijzigingen, dan gebruikt Media eerst de bestaande editor-conflictafhandeling zodat automatisch herladen nooit lokale tekst kan weggooien.
- Nieuwe regressietests dekken trash-only gebruik + herstel, onleesbare prullenbakinhoud en het opruimen van een veilige subset naast een historisch onveilig asset.
- Pakketversie naar 0.27.1 verhoogd.

## 0.27.0 — Media Manager en veilige asset-cleanup

- Nieuwe boekpagina **Media** met een tekstgerichte inventaris van book-local afbeeldingen en de huidige omslag. Per afbeelding worden status, oorspronkelijke bestandsnaam, afmetingen, bestandsgrootte, huidige verwijzingen en historische verwijzingen zichtbaar gemaakt zonder een nieuwe thumbnail-/galerijlaag.
- Nieuwe `MediaManager`-laag scant alle Markdownbronnen binnen het boek, dus niet alleen hoofdstukken maar ook publicatie-, planning- en AI-Markdown. Daardoor kan een handmatig gebruikte asset niet als ongebruikt worden opgeruimd alleen omdat hij buiten het manuscript staat.
- Integriteitsstatus onderscheidt **Gebruikt**, **Ongebruikt**, **Ontbreekt** en **Gewijzigd**. Bestanden die fysiek onder `assets/images/` staan maar niet in `assets/manifest.json` voorkomen worden apart als **Niet geregistreerd** getoond en in deze versie nooit automatisch verwijderd.
- **Ongebruikte opruimen** is bewust conservatief: cleanup wordt geblokkeerd zodra één Markdownbron niet betrouwbaar kan worden gelezen, controleert de revision vóór én direct na het maken van het herstelpunt en verwijdert nooit een nog live gerefereerde asset.
- Voor iedere cleanupbatch wordt exact één volledig `media_cleanup`-herstelpunt in Versiegeschiedenis gemaakt. Daarna wordt eerst het manifest atomisch bijgewerkt en pas daarna worden binaries best-effort verwijderd; een Windows-/sync-lock kan daardoor hooguit een zichtbaar niet-geregistreerd restbestand achterlaten, nooit een manifest dat naar een al verwijderde gebruikte afbeelding wijst.
- History-aware cleanup controleert oude snapshots. Een live ongebruikte UUID-afbeelding mag worden verwijderd als iedere historische versie die hem gebruikt zijn eigen binary bevat. Ontbreekt die historische herstelkopie — ook in het conservatieve geval van onleesbare historische Markdown plus een manifestverwijzing — dan wordt cleanup geweigerd.
- Omslagen worden in Media alleen gerapporteerd; wijzigen/verwijderen blijft in Boekdetails. Zo blijft coverownership buiten de inline-media-cleanup.
- Nieuwe regressietests dekken gebruik/ongebruik, missing/modified, niet-geregistreerde bestanden, publicatie-Markdown, selectieve en batch-cleanup, revision-races, één herstelcheckpoint, herstel na cleanup en incomplete historische snapshots. Een headless Qt-test controleert daarnaast de Media-pagina wanneer PySide6 beschikbaar is.
- Pakketversie naar 0.27.0 verhoogd.

## 0.26.0 — EPUB-validatie en reader-navigatie

- EPUB-export valideert voortaan het daadwerkelijk opgebouwde ZIP-archief vóór een bestaand exportbestand wordt vervangen. De interne controle bewaakt de verplichte ongecomprimeerde `mimetype`, `container.xml` → package-resolutie, EPUB 3 package/identifier, unieke manifest-items, spine-idrefs, precies één nav-resource en alle lokale XHTML-links, afbeeldingen en fragmenttargets.
- Een mislukte interne EPUB-controle laat een eerder goed exportbestand ongemoeid; de tijdelijke mislukte export wordt verwijderd en de gewone exportfout-UX toont de concrete integriteitsfout.
- Het EPUB-navigatiedocument bevat nu een minimale `landmarks`-navigatie. **Start lezen** (`bodymatter`) wijst naar het eerste echte hoofdstuk; wanneer de publicatiestructuur een zichtbare Inhoud-pagina bevat wordt die daarnaast als `toc`-landmark aangeboden. De bestaande volledige EPUB 3-ToC blijft ongewijzigd.
- De Exporteren-pagina legt uit dat QuietWriter na EPUB-export de structuur/interne verwijzingen controleert en toont na succes **EPUB voltooid en intern gecontroleerd**. Deze ingebouwde controle is een productintegriteitsguard en pretendeert geen volledige vervanging van EPUBCheck te zijn.
- Nieuwe regressietests dekken een geldige export, beide landmarksvarianten, detectie van een ontbrekend navigatiedoel en de garantie dat een validatiefout nooit een bestaand exportbestand overschrijft.
- Pakketversie naar 0.26.0 verhoogd.

## 0.25.2 — code-review ronde 6: regressiebewaking en laatste correctness-randen

- De twee Qt AI-racetests uit 0.21.6/0.22.6 initialiseren `active_book()` nu vóór `AIPanel` wordt gemaakt en wisselen de actieve testboekreferentie vóór iedere `set_book()`. De productcode was al correct; de tests bewaken hun oorspronkelijke racecondities weer zodra PySide6 beschikbaar is.
- PDF zet `QTextDocument.documentMargin` expliciet op 0. De eigen body-rechthoek bevat de paginamarges al; de standaard 4 px Qt-documentmarge kan daardoor geen lege laatste pagina met alleen running header/paginanummer meer veroorzaken.
- Thinking-capabilitymetadata die tijdens startup al door Ollama is opgehaald, wordt meteen in dezelfde per-model runtimecache gezet als bij **Modellen ophalen**. Een bekende `thinking_can_disable = false` wordt dus ook zonder handmatige refresh gerespecteerd.
- Boekprofiel, Boekgeheugen en Boekdetails gebruiken bij een same-book adopt een echte drie-wegs veldmerge: lokale-only edits blijven lokaal, disk-only edits volgen schijf en een veld dat aan beide kanten verschillend wijzigde houdt de schijfversie live. De volledige lokale invoer wordt in dat laatste geval eerst als `conflict_local` in Versiegeschiedenis veiliggesteld en zichtbaar gemeld.
- De Markdown-escape voor vrije `##`-regels is volledig round-trip-safe gemaakt. Ook tekst die de gebruiker letterlijk als `\## ...`, `\\## ...`, enzovoort invoert behoudt exact hetzelfde aantal backslashes na opslaan en opnieuw openen.
- `Library.manifest_text()` levert de canonieke `book.json`-weergave zonder live state te schrijven, zodat Boekdetails een herstelversie van lokale formulierwaarden kan maken zonder het actuele boek te muteren.
- Nieuwe regressietests dekken de testfixturevolgorde, nul-documentmarge, startup thinking-cache, verliesvrije backslash/H2-roundtrip en de drie-wegs merge/recoverycontracten.
- Pakketversie naar 0.25.2 verhoogd.

## 0.25.1 — code-review ronde 5: PDF-, Planning- en profielintegriteit

- PDF-typografie gebruikt nu dezelfde paintdevice/DPI als `QPdfWriter` vóór HTML-layout. CSS-puntgroottes worden daardoor niet meer met scherm-DPI (meestal 96) berekend en vervolgens op 144 dpi verkleind; 10,8 pt blijft daadwerkelijk circa 10,8 pt in de PDF.
- PDF-afbeelding + onderschrift worden niet meer beschermd met de door Qt rich-text genegeerde CSS-regel `page-break-inside: avoid`. Na de eerste layout controleert QuietWriter de echte `QTextTable`-geometrie; tabellen die een paginagrens kruisen krijgen programmatisch `PageBreak_AlwaysBefore` en worden opnieuw gelayout.
- Planning-conflicten bewaren dirty Notities of een geopend personageformulier alleen automatisch wanneer het bijbehorende `planning/notes.md` respectievelijk `planning/characters.json` niet extern gewijzigd is. Bij een echte dubbele wijziging blijft de schijfversie live en wordt de lokale invoer apart in Versiegeschiedenis veiliggesteld.
- Niet-opgeslagen wijzigingen aan een bestaand personage worden nu net als een nieuw-personageconcept als pending formulierstate herkend. Bij een same-book reload zonder conflict op `characters.json` wordt het detailformulier met de lokale kandidaat opnieuw geopend.
- Schrijverspersona, Boekprofiel en Boekgeheugen escapen veldregels die met `## ` beginnen als standaard Markdown (`\## ...`) en halen die escape bij het parsen terug weg. Vrije tussenkoppen en zelfs tekst die gelijk is aan een QuietWriter-rubriek kunnen daardoor niet meer naar een ander veld verschuiven of verdwijnen bij opslaan/heropenen.
- Een dirty Schrijverspersona wordt bij navigeren en afsluiten via dezelfde save-guard verwerkt als Boekprofiel en Boekgeheugen; het venster kan niet meer sluiten nadat een mislukte persona-save.
- Thinking-uit capabilitymetadata wordt per provider/model gecachet. Als de provider expliciet meldt dat thinking niet kan worden uitgeschakeld, stuurt de chat geen `think:false`/`reasoning.enabled=false` meer, ook niet wanneer de globale checkbox uit een eerder model aangevinkt bleef.
- De twee oudere Qt-race-regressietests hebben weer een actuele fake `active_book()` en profiel/geheugen-readers, zodat ze op een PySide6-testomgeving opnieuw hun oorspronkelijke AI-isolatiegedrag controleren.
- Nieuwe regressietests dekken `##`-roundtrips, PDF-DPI/keep-together-broncontract, conflict-aware Planning-preservation, bestaand-personage-drafts, persona-saveguards en thinking-capabilityguard.
- Pakketversie naar 0.25.1 verhoogd.

## 0.25.0 — PDF-export MVP

- De gereserveerde PDF-kaart op **Exporteren** is geactiveerd. QuietWriter maakt nu rechtstreeks met de bestaande PySide6/Qt-stack een vaste, gepagineerde PDF; er is geen nieuwe PDF-library of Windows-component toegevoegd.
- De renderer gebruikt dezelfde bewezen route als de afzonderlijke PDF-spikes: `QTextDocument` voor rijke tekst/paginering en `QPdfWriter` + `QPainter` voor eigen marges, lopende kop en paginanummers. Uitvoer wordt eerst naar een tijdelijk bestand geschreven en daarna atomisch naar de gekozen exportmap verplaatst.
- PDF heeft een kleine, eigen instellingenset: **Klassiek/Modern/Literair**, **A5/A4**, **Compact/Standaard/Ruim** voor marges, optionele paginanummers, optionele rustige lopende kop en sectietitels als eigen pagina. Deze voorkeuren worden per boek in `export/settings.json` bewaard.
- De bestaande publicatiestructuur wordt meegenomen: titelpagina, copyright, epigraaf, vrije voor-/achterwerkonderdelen, eenvoudige inhoudslijst, secties en hoofdstukken. Hoofdstukken en publicatieonderdelen starten als vaste pagina-eenheden; een actieve titelpagina blijft vrij van running header/paginanummer.
- Manuscriptopmaak en inline afbeeldingen worden rechtstreeks uit de immutable `ExportDocument`-snapshot gerenderd. Klein/Middel/Groot/Volledig, links/midden/rechts en korte links/rechts tekstomloop worden in PDF vertaald naar dezelfde intentie als EPUB.
- De tweede losse PDF-spike toonde een Qt-randgeval bij **tekstomloop + lang onderschrift**. Productcode probeert dit niet met fragiele layouttrucs te repareren: lange onderschriften vallen in PDF automatisch terug op een normaal links/rechts afbeeldingsblok zonder omloop. Preflight meldt hoeveel afbeeldingen zo veilig worden teruggezet. EPUB behoudt zijn eigen floatgedrag.
- Grote afbeeldingen/tabellen kregen in 0.25.0 een CSS `page-break-inside: avoid`-hint. Code-review ronde 5 toonde aan dat Qt rich-text deze CSS-eigenschap negeert; 0.25.1 vervangt dit door een expliciete layout-/page-break-pass.
- Nieuwe regressietests dekken PDF-instellingen, PDF als echte exportkeuze, pure HTML-opbouw, veilige onderschriftfallback en de Qt-loze importeerbaarheid van de exportlaag.
- Pakketversie naar 0.25.0 verhoogd.

## 0.24.0 — afbeeldingslayout en eenvoudige tekstomloop

- Afbeeldingen hebben nu drie eenvoudige presentatie-eigenschappen naast alt-tekst en onderschrift: **Breedte** (Klein/Middel/Groot/Volledige breedte), **Plaatsing** (Links/Midden/Rechts) en optionele **Tekstomloop** voor links/rechts geplaatste afbeeldingen.
- Nieuwe afbeeldingen starten rustig als **Groot + Midden + geen omloop**. Bestaande manuscripten zonder layoutmetadata behouden hun historische gedrag: **Volledige breedte + Midden + geen omloop**.
- Layout blijft gewone, leesbare Markdown. QuietWriter bewaart alleen een optionele HTML-comment achter het afbeeldingsblok, bijvoorbeeld `<!-- qw:image width=medium align=left wrap=true -->`; andere Markdownlezers mogen die metadata veilig negeren.
- Volledige breedte normaliseert naar Midden en schakelt tekstomloop uit. Gecentreerde afbeeldingen kunnen eveneens geen tekstomloop krijgen; de UI voorkomt daardoor combinaties zonder zinvolle presentatie.
- Het afbeeldingspaneel toont de gekozen relatieve breedte en plaatsing direct in de preview. De manuscripteditor positioneert de beschermde afbeeldingskaart overeenkomstig links/midden/rechts en toont een compacte layoutregel; echte live tekstomloop in de editor wordt bewust niet gesimuleerd met een fragiele custom-renderlaag.
- EPUB-export vertaalt de intentie naar semantische CSS-klassen: 30/50/70/100% relatieve breedte, links/midden/rechts en `float`-gebaseerde omloop. Als een reader floats vereenvoudigt blijft de afbeelding als normaal blok leesbaar.
- Zoek/vervang en spelling beschermen ook de QuietWriter-layoutcomment; alt-tekst en onderschrift blijven wel gewone doorzoekbare tekst.
- Markdown-media-export is uit de actieve productplanning gehaald. De volgende productstap is een **PDF-spike**, gevolgd door PDF-uitwerking als de Qt-route kwalitatief voldoet en daarna bredere EPUB-reader-validatie (Calibre als eerste referentie).
- Nieuwe regressietests dekken legacy-defaults, layout-roundtrip, normalisatie, beschermde metadata, EPUB-klassen/CSS en de volledige insert/edit-pipeline.
- Pakketversie naar 0.24.0 verhoogd.

## 0.23.11 — Ollama thinking-capability fallback

- Ollama-modeldetectie gebruikt naast het gedetailleerde `thinking`-object nu ook de algemene `capabilities`-lijst uit `/api/show`. Modellen die zoals `ollama show` alleen `Capabilities: thinking` rapporteren krijgen daardoor correct de 🧠-markering.
- De 🧠-betekenis is aangescherpt naar **thinking/reasoning ondersteund**. Als gedetailleerde metadata expliciet meldt dat `false` niet beschikbaar is, blijft **Thinking uitschakelen** disabled; bij capability-only metadata mag QuietWriter `think:false` aanvragen zonder te claimen dat iedere modelvariant dit gegarandeerd honoreert.
- Tooltips en AI-helptekst maken het onderscheid tussen bekende toggle-ondersteuning en capability-only detectie zichtbaar.
- Nieuwe regressietests dekken de `/api/show`-vorm die overeenkomt met `ollama show qwen3:4b` en `deepseek-r1:8b`.
- Pakketversie naar 0.23.11 verhoogd.

## 0.23.10 — zichtbare thinking-capabilities per model

- De modelkeuze in Instellingen → AI toont voortaan **🧠** vóór modellen waarvoor de gekozen provider expliciet meldt dat thinking/reasoning kan worden uitgeschakeld. Het icoon is alleen presentatie; het echte model-id blijft ongewijzigd bij opslaan en aanvragen.
- Ollama-capabilities worden tijdens modeldetectie via `/api/show` gelezen. Alleen modellen waarvan `thinking.values` zowel een thinking-modus als `false` bevat krijgen het icoon. `values: [false]` wordt terecht als geen thinking gezien; modellen met alleen niveaus zoals `low/medium/high` worden niet ten onrechte als uitschakelbaar gemarkeerd.
- OpenRouter gebruikt `supported_parameters` uit de modellen-API; modellen met de genormaliseerde parameter `reasoning` krijgen de thinking-markering.
- De instelling **Thinking uitschakelen** wordt disabled wanneer QuietWriter voor het geselecteerde, opgehaalde model expliciet weet dat uitschakelen niet wordt ondersteund. Bij onbekende metadata blijft de instelling beschikbaar in plaats van ondersteuning te verzinnen.
- De AI-instellingen leggen de markering uit: zonder thinking zijn antwoorden vaak sneller en directer en dat kan prettig zijn bij creatief schrijven; het effect op stijl en kwaliteit verschilt per model.
- Capability-ophalen is best-effort: ontbrekende of oudere Ollama-metadata bij één model mag de volledige modellenlijst niet blokkeren.
- Nieuwe regressietests bewaken Ollama `thinking.values`, OpenRouter `supported_parameters`, het gescheiden displaylabel/model-id en de dynamische thinking-control.
- Pakketversie naar 0.23.10 verhoogd.

## 0.23.9 — compacte AI-zijbalk en thinking-regie

- Het AI-paneel is opnieuw geordend rond de chat: alleen **AI-assistent** en **Nieuw gesprek** blijven permanent bovenaan; manuscriptcontext, Planning-context en snelacties staan compact onder de chat/composer en klappen alleen open wanneer ze nodig zijn.
- **Huidig hoofdstuk** blijft de standaardcontext maar neemt niet langer permanent ruimte in. De compacte knop **Context** toont alleen **Context · aangepast** wanneer een andere manuscriptcontext of Planning-selectie actief is.
- **Context bekijken** opent voortaan een aparte inspectiedialoog in plaats van een blijvend tekstvak in de smalle AI-zijbalk. De geselecteerde Planning-inhoud blijft daarin letterlijk controleerbaar.
- **Snelacties** zijn inklapbaar. In Instellingen → AI kan **Snelacties standaard uitklappen** worden gekozen; standaard blijft de zijbalk compact.
- Nieuwe AI-instelling **Thinking uitschakelen**. Bij Ollama stuurt QuietWriter `think: false` als top-level `/api/chat`-parameter; bij OpenRouter wordt `reasoning.enabled=false` meegestuurd. Als de instelling uit staat gebruikt QuietWriter de standaard van provider/model. Met thinking uit gebruikt de tijdelijke status **AI werkt…** in plaats van **Denken…**.
- Ollama behandelt `think` niet meer als generieke modeloptie: de parameter staat bewust op requestniveau zodat ondersteunde thinking-modellen hem daadwerkelijk kunnen respecteren.
- Nieuwe regressietests bewaken de providerpayloads, compacte AI-layout en opslag van beide nieuwe AI-voorkeuren.
- Pakketversie naar 0.23.9 verhoogd.

## 0.23.8 — AI-snelacties

- Het AI-paneel heeft vier compacte **Snelacties**: **Feedback**, **Herschrijf selectie**, **Persona-check** en **Feitencheck**. De vierde actie is toegevoegd op basis van praktijkgebruik met Boekgeheugen en continuïteitscontrole.
- Snelacties zijn bewust alleen bewerkbare prompttemplates. Een klik vult het gewone AI-invoerveld en verstuurt niets automatisch; de gebruiker kan de opdracht altijd nog aanpassen voordat Qwen/Ollama/OpenRouter wordt aangeroepen.
- **Herschrijf selectie** is alleen beschikbaar wanneer daadwerkelijk manuscripttekst geselecteerd is. De prompt vraagt expliciet betekenis, feiten, perspectief en bedoeling te behouden en respecteert de bestaande persona-, boekprofiel-, geheugen- en Planning-context.
- **Feedback** en **Feitencheck** verwijzen expliciet naar de bestaande contextlagen; **Persona-check** controleert stijl en stem zonder automatisch te herschrijven.
- Alle snelacties worden tijdens een lopende AI-opdracht tijdelijk uitgeschakeld en gebruiken dezelfde rustige `suggestionButton`-interactiestijl als andere compacte keuzes.
- Nieuwe regressietests bewaken de vier prompttemplates, selection-only gedrag en dat een snelactie nooit rechtstreeks `send()` aanroept.
- Pakketversie naar 0.23.8 verhoogd.

## 0.23.7 — zichtbare geheugenbevestiging in AI-chat

- Na **Onthouden** verschijnt direct een subtiele lokale QuietWriter-regel in de AI-chat, bijvoorbeeld **Opgeslagen in Boekgeheugen · Canon & feiten**. De gebruiker hoeft de statusbalk daardoor niet te zien om te weten dat de actie geslaagd is.
- Dezelfde bevestiging verschijnt na **Bewerken → Onthouden**. De geheugenkaart verdwijnt daarna zoals voorheen wanneer het voorstel is afgehandeld.
- Bevestigingsregels worden als lokaal `notice`-bericht in de conversatie bewaard zodat ze na heropenen zichtbaar blijven, maar worden nooit als user/assistant-history terug naar het AI-model gestuurd.
- Foutgedrag blijft ongewijzigd: bij een mislukte opslag blijft de voorstelkaart staan met de concrete foutmelding.
- Regressietests bewaken zichtbare chatfeedback, beide onthoudroutes en uitsluiting van notices uit providercontext.
- Pakketversie naar 0.23.7 verhoogd.

## 0.23.6 — Onthouden hotfix

- **Onthouden** overschrijft een zojuist toegevoegd AI-geheugenvoorstel niet langer vlak vóór de schijfwrite met de nog zichtbare, oudere tekst uit de Boekgeheugen-editor.
- Formulieropslag en programmatic geheugenopslag zijn gescheiden: gewone **Opslaan** synchroniseert eerst het actieve tekstveld; een goedgekeurd AI-voorstel persisteert juist de reeds samengestelde `self.memory`-state zonder die opnieuw uit de widget te lezen.
- De bestaande succes-/foutfeedback uit 0.23.5 blijft behouden. Na een geslaagde opslag verdwijnt de voorstelkaart en staat de regel direct in `ai/memory.md`.
- Regressietest toegevoegd voor exact de 0.23.5-volgorde waarin `_store_editor()` de zojuist geappende regel weer verwijderde.
- Pakketversie naar 0.23.6 verhoogd.

## 0.23.5 — AI-context en geheugenactie hardening

- **Onthouden** is niet langer een stille UI-actie: vóór opslag wordt Boekgeheugen expliciet aan het actieve live boek gekoppeld. Een geslaagde actie geeft **Opgeslagen in Boekgeheugen** in de statusbalk; een mislukte actie laat de voorstelkaart staan en toont daar de fout in plaats van zonder feedback niets te doen.
- **Bewerken → Onthouden** gebruikt dezelfde persistente route en dezelfde feedback als direct Onthouden. Een conflict waarbij de schijfversie wordt gekozen blijft het voorstel zichtbaar houden.
- Het toevoegen van geheugenregels is als UI-onafhankelijke Markdown-operatie afgedekt: de regel komt als gewone bullet in de gekozen rubriek en exacte duplicaten worden niet opnieuw toegevoegd.
- De AI-systeemprompt is uit de Qt-widget gehaald naar een aparte testbare promptbuilder. Regressietests controleren nu de daadwerkelijke promptinhoud in plaats van alleen UI-bronregels.
- **Planning-context** wordt in de prompt direct na de gekozen manuscriptcontext geplaatst en krijgt een expliciete instructie dat de gebruiker deze informatie voor de huidige vraag bewust heeft geselecteerd en dat AI die actief moet gebruiken wanneer relevant.
- **Context bekijken** toont voortaan de letterlijke geselecteerde Planning-inhoud (personages, scènes en notities), zodat zichtbaar te controleren is wat werkelijk naar het model gaat.
- Nieuwe regressietests dekken geheugenappend/deduplicatie, actieve-book binding, succes/foutfeedback en de exacte Planning-inhoud van de uiteindelijke systeemprompt.
- Pakketversie naar 0.23.5 verhoogd.

## 0.23.4 — Gerichte Planning-context voor AI

- Het AI-paneel heeft een nieuwe **Planning-context…**-keuze. Per geopend boek kan de gebruiker specifieke personages, specifieke scènes en optioneel de vrije Planning-notities aanvinken.
- Alleen expliciet geselecteerde Planning-data wordt meegestuurd. QuietWriter voegt geen volledige Planning-database automatisch aan iedere vraag toe; kleine lokale modellen houden zo een compacte, doelgerichte context.
- Geselecteerde personages worden met hun relevante profielvelden en relaties aangeleverd; geselecteerde scènes bevatten synopsis, hoofdstuk, betrokken personages, locatie, doel, conflict, uitkomst, status en notities.
- De AI-instructie onderscheidt drie bronnen expliciet: manuscript = wat daadwerkelijk in het verhaal staat, Planning = wat bedoeld/gepland is, Boekgeheugen = blijvende afspraken/kennis. Verschillen moeten benoemd worden en mogen niet stil worden samengevoegd.
- De Planning-selectie blijft tijdens het geopende boek actief, maar wordt bij een echte boekwissel leeggemaakt. Er wordt niets extra op schijf opgeslagen.
- Pakketversie naar 0.23.4 verhoogd.

## 0.23.3 — Actief Boekgeheugen en geheugenvoorstellen

- De AI-systeeminstructie gebruikt Boekgeheugen actiever: bij analyse, feedback, feitencontrole en herschrijven moet het model relevante geheugenfeiten en besluiten vergelijken met de actuele manuscriptcontext en duidelijke tegenstrijdigheden uit zichzelf signaleren.
- Actuele manuscripttekst blijft autoritatief wanneer het verhaal aantoonbaar is veranderd; een oudere geheugenregel wordt dan niet stil als waarheid afgedwongen.
- AI kan maximaal twee duurzame geheugenvoorstellen aan een antwoord koppelen via een klein modelvriendelijk intern markerformaat. Het markerblok wordt nooit als gewone chattekst opgeslagen of getoond.
- Geheugenvoorstellen verschijnen als een zichtbare kaart met **Onthouden · Bewerken · Negeren**. Alleen een expliciete gebruikersactie schrijft naar `ai/memory.md`; AI heeft nog steeds geen autonome schrijfrechten op het geheugen.
- **Bewerken** laat zowel categorie als tekst aanpassen voor opslag. Exact dubbele geheugenregels worden niet nogmaals toegevoegd.
- De interne voorstelmarker wordt ook tijdens streaming verborgen, zodat er geen technische protocoltekst in de chat flitst.

## 0.23.2 — Transparant boekgeheugen

- Nieuw **Boekgeheugen** als zelfstandige boekpagina naast Boekprofiel. De gebruiker beheert vijf vrije geheugenrubrieken: Canon & feiten, Stijl van dit boek, Besluiten, Terugkerende voorkeuren en Open aandachtspunten.
- Per boek is `ai/memory.md` de enige bron van waarheid. Het bestand blijft gewone, leesbare Markdown en wordt pas aangemaakt wanneer de gebruiker het geheugen expliciet opslaat.
- Boekgeheugen is bewust handmatig in deze release: AI leest het mee maar kan `memory.md` nergens zelf wijzigen. Automatische of voorgestelde herinneringen horen pas in 0.23.3.
- `ai/memory.md` valt onder dezelfde revision/conflictbeveiliging, versiegeschiedenis en herstelroute als Boekprofiel. Externe wijzigingen worden nooit stil overschreven.
- Same-book reloads mergen geheugenvelden veilig: lokaal gewijzigde rubrieken blijven staan, onaangeraakte rubrieken volgen de nieuwste schijfversie.
- AI ontvangt voortaan vier zichtbare lagen: globale Schrijverspersona, projectspecifiek Boekprofiel, expliciet Boekgeheugen en de gekozen manuscriptcontext. Als actuele manuscripttekst aantoonbaar botst met geheugen, krijgt de actuele tekst voorrang en moet AI het verschil benoemen.
- Planning blijft de bron voor personages, scènes en outline; Boekgeheugen is bedoeld voor boekbrede kennis, beslissingen en terugkerende voorkeuren die niet al gestructureerd elders staan.
- Pakketversie naar 0.23.2 verhoogd.

## 0.23.1 — Boekprofiel en Nederlandse voorbeeldpersona’s

- Nieuw **Boekprofiel** als zelfstandige boekpagina naast Boekdetails/Exporteren. De UI gebruikt dezelfde rustige profielopzet als de Schrijverspersona, met vrije tekst onder vaste rubrieken voor Genre & doelgroep, Kernpremisse, Vertelperspectief & tijd, Sfeer & toon, Thema’s & motieven, Setting & wereld, Tempo & spanningsboog, Relaties/romantiek/intensiteit, Afwijkingen van schrijverspersona, Redactionele aandachtspunten en Aanvullende instructies.
- Per boek blijft `ai/boekprofiel.md` de enige bron van waarheid. Het bestand is gewone leesbare Markdown, wordt pas bij Opslaan aangemaakt en kan buiten QuietWriter met iedere teksteditor worden bekeken of bewerkt.
- Boekprofielen vallen onder dezelfde revision/conflictbeveiliging en versiegeschiedenis als Planning/Publicatie. `ai/` wordt meegenomen in snapshots en herstel; een externe wijziging geeft een expliciete keuze tussen lokaal profiel en schijfversie.
- Same-book reloads zijn profielbewust: lokaal gewijzigde velden blijven staan, terwijl onaangeraakte velden de nieuwste schijfwaarden overnemen. Zo veroorzaakt een conflict elders in het boek geen stille profieloverschrijving.
- AI ontvangt voortaan drie zichtbare lagen: globale **Schrijverspersona**, projectspecifiek **Boekprofiel** en de gekozen manuscriptcontext. Als het boekprofiel bewust afwijkt van de persona, heeft die projectspecifieke instructie voor dat boek voorrang.
- De drie voorbeeldpersona’s zijn vervangen door Nederlandse vertrekpunten: **Chantal van Gastel** (feelgood/chicklit), **Saskia Noort** (thriller) en **Carry Slee** (jeugd/tiener). Het blijven bewerkbare profielen op basis van brede genre-/vertelkenmerken; er wordt geen auteurstekst meegeleverd of gekopieerd.
- Pakketversie naar 0.23.1 verhoogd.

## 0.23.0 — Gestructureerde schrijverspersona

- De Schrijverspersona is opnieuw ontworpen als een begrijpelijk profiel met twaalf vaste onderdelen: Stem & toon, Vertelstijl, Taal & woordkeuze, Zinnen & ritme, Beschrijving & zintuigen, Dialoog & interactie, Emotie/spanning/intimiteit, Scènes & verteltempo, Redactionele voorkeuren, Vermijden, Voorbeeldteksten en Aanvullende instructies.
- `persona/schrijver.md` blijft de enige bron voor AI en blijft gewone, buiten QuietWriter leesbare Markdown. De nieuwe UI is uitsluitend een presentatie- en bewerkingslaag boven dat bestand.
- Bestaande vrije persona's worden zonder inhoudsverlies ingelezen. Zolang zij de nieuwe koppen nog niet gebruiken, staat de volledige oude inhoud in Aanvullende instructies; bij Opslaan wordt het bestand naar de nieuwe gestructureerde Markdownvorm geschreven.
- Drie bewerkbare voorbeeldpersona's toegevoegd: Jane Austen (sociale observatie/ironie), Arthur Conan Doyle (observatie/mysterie/voortgang) en Virginia Woolf (innerlijke waarneming/associatief ritme). De voorbeelden gebruiken brede stijlkenmerken en bevatten geen overgenomen auteurstekst.
- De persona-pagina toont expliciet het pad naar `schrijver.md`, heeft een zichtbare dirty-state en schrijft pas bij Opslaan naar schijf. Wisselen tussen onderdelen bewaart lokale invoer in het formulier.
- Nieuwe werkmappen starten direct met het gestructureerde Markdowncontract; bestaande werkmappen worden niet automatisch herschreven.
- De AI-promptsemantiek is bewust niet gewijzigd: AI leest nog steeds exact het complete `schrijver.md` als schrijversprofiel.
- Pakketversie naar 0.23.0 verhoogd.

## 0.22.7 — pending-state en media-boundary hardening

- De legacy-omslagdetectie uit 0.22.5 gebruikt niet langer alleen het ontbreken van `cover_file`. Oude pre-0.20-boeken die door 0.20–0.22 al eens zijn geopend en daardoor inmiddels `"cover_file": ""` bevatten, kunnen hun globale `boekomslagen/<slug>.*` weer eenmalig adopteren zolang de 0.20+ book-local `assets/manifest.json`-marker ontbreekt. Nieuwe boeken met dezelfde slug blijven geïsoleerd.
- Same-book adopt/reload in Planning bewaart dirty Notities en een nog niet opgeslagen nieuw-personage-concept wanneer het conflict in een ander planningsbestand zit. Dirty notities worden vóór de reload bovendien in de lokale conflictversie opgenomen, zodat ze niet alleen in RAM overleven. Het planningbestand waarover de gebruiker expliciet een conflictkeuze maakte blijft wel autoritatief herladen.
- Navigeren naar Boekdetails forceert eerst de pending editor/publicatie-save, zodat een achterlopende autosave niet pas bovenop een reeds bewerkt formulier een conflict opent. Als een same-book adopt toch plaatsvindt terwijl Boekdetails lokale wijzigingen bevat, blijft dezelfde pagina bestaan en worden alleen onaangeraakte velden met de nieuwste externe waarden gemerged; lokale velden en een pending omslag blijven staan.
- Zoeken/Vervangen gebruikt naast de lengtevaste image-maskering nu expliciete beschermde bronranges. Een treffer met een begin- of eindspatie mag daardoor niet meer over de grens tussen alt-/captiontekst en beheerde Markdown-image-syntax lopen. `Vervangen`, `Alles vervangen` en het getoonde resultaataantal gebruiken dezelfde veilige matchset.
- Nieuwe regressietests dekken de vier bevindingen uit code-review ronde 4, inclusief een pre-0.20-omslag met reeds aanwezige lege `cover_file`, image-boundary zoektermen en source-invariants voor pending-state adopt.
- Pakketversie naar 0.22.7 verhoogd.

## 0.22.6 — AI-streamintegriteit en scènebreuk-randgevallen

- **Stop AI** blijft nu geldig wanneer de gebruiker annuleert terwijl Ollama of OpenRouter nog in `requests.post()` wacht op modelstart/responseheaders. De cancelstatus wordt vóór de aanvraag gereset en `_set_active()` wist hem niet meer zodra de response later beschikbaar komt; de response wordt dan direct gesloten zonder alsnog tokens te verwerken.
- Ollama- en OpenRouter-streams herkennen providerfouten die met HTTP 200 midden in een stream worden meegestuurd. Een `error`-payload wordt als `RuntimeError` met de providerdetails doorgegeven aan de bestaande AI-foutafhandeling, zodat de gebruikersvraag plus foutmelding bewaard blijven in plaats van als een leeg, zogenaamd geslaagd antwoord te verdwijnen.
- `AIPanel.set_book()` maakt onderscheid tussen een echt ander boek en een nieuw `Book`-object met hetzelfde boek-id. Conflictresolutie of versieherstel van hetzelfde live boek ververst alleen het `ConversationStore`-pad; een lopende AI-worker, boekgeneratie, chatbuffer en nog niet opgeslagen gebruikersvraag blijven intact. Een echte boekwissel houdt de bestaande strikte worker-isolatie uit 0.21.6.
- Scènebreuk invoegen knipt nooit meer midden door een lopende regel. Staat de cursor midden in tekst, dan wordt `***` na het einde van die regel geplaatst; staat de cursor al aan het begin van een regel/alinea, dan komt de breuk ervoor. Voorloopspaties aan de rechterkant van de invoeggrens worden genormaliseerd en de bestaande bescherming tegen dubbele aangrenzende scènebreuken blijft actief.
- Nieuwe regressietests dekken annuleren tijdens de verbindingsfase voor beide providers, mid-stream foutpayloads, scènebreuken midden in een zin en — waar PySide6 beschikbaar is — AI-continuïteit tijdens same-book adopt/reload.
- Code-review ronde 3 (bevindingen 1–24) is hiermee volledig verwerkt; de productroadmap kan weer worden hervat.
- Pakketversie naar 0.22.6 verhoogd.

## 0.22.5 — cache, startup en legacy-storage hardening

- `.cache/book_search.db` is nu expliciet een wegwerp-cache. Een corrupte/half-gesynchroniseerde SQLite-database wordt verwijderd en opnieuw opgebouwd; als zelfs de schijfcache niet bruikbaar is, valt QuietWriter terug op een in-memory index. Cacheproblemen mogen startup of manuscript-save daardoor niet meer blokkeren.
- Legacy globale omslagen worden niet langer op basis van alleen de huidige slug gevonden. Alleen een manifest van vóór 0.20 dat het veld `cover_file` nog niet bevat kan bij laden een bestaande `boekomslagen/<slug>.*` als expliciete legacy-omslag adopteren. Nieuwe boeken met dezelfde titel erven die omslag dus niet, en **Omslag verwijderen** verwijdert nooit meer een toevallig gelijknamige globale omslag van een ander boek.
- Een onbereikbare werkmap veroorzaakt bij startup geen stille `pythonw`-crash meer. QuietWriter toont de betreffende map en fout en biedt **Andere map kiezen…** of **Afsluiten**; een succesvol gekozen alternatief wordt als nieuwe werkmap opgeslagen.
- `delete_book()` schakelt revision-tracking pas uit nadat de verplaatsing naar de prullenbak werkelijk is geslaagd. Een Windows-/Dropbox-lock laat een niet-verwijderd boek dus beschermd en getrackt achter.
- Boekdetails bouwt titel/metadata voortaan in een deep-copy kandidaat op. Coverwijzigingen worden als één guarded transactie voorbereid en bij een mislukte manifestcommit teruggedraaid; pas na volledig succes worden titel/metadata in het gedeelde live `Book`-object overgenomen. Een mislukte Boekdetails-save kan daardoor niet later via editor-autosave alsnog stil worden weggeschreven.
- `save_chapter()` behandelt `last_used` als best-effort metadata. Als de hoofdstuktekst wel is opgeslagen maar `book.json` tijdelijk niet kan worden bijgewerkt, blijft de tekstsave geldig en wordt de revision-baseline meteen naar de werkelijk opgeslagen hoofdstukinhoud verzet. De volgende save ziet daardoor geen vals extern conflict over de eigen tekst.
- Nieuwe regressietests dekken reviewbevindingen 15, 16, 17, 21, 22 en 23, inclusief corrupte cache, same-slug legacy covers, delete-tracking en coverrollback bij mislukte Boekdetails-persistentie.
- Pakketversie naar 0.22.5 verhoogd.

## 0.22.4 — exportcorrectheid en directe typografie-refresh

- Een opgeslagen wijziging van schrijflettertype of tekstgrootte wordt nu ook expliciet op alle reeds aanwezige tekens van het **al geopende hoofdstuk** toegepast. Alleen widget/document-defaults wijzigen bleek onvoldoende: bestaande `QTextCharFormat` kon de vorige font blijven tonen tot een hoofdstuk opnieuw werd geladen. Na de basisfont-pass legt de manuscript-highlighter koppen, inline-opmaak, code en verborgen Markdown-markers opnieuw aan.
- EPUB-rendering volgt nu QuietWriter's documentmodel: iedere niet-lege manuscriptregel / ieder `QTextBlock` wordt een eigen `<p>`. Eén Enter blijft daardoor één alinea in de EPUB in plaats van door CommonMark-achtige soft-line folding met de volgende regel te worden samengevoegd.
- Overlappende selectie-opmaak wordt bij EPUB-export stack-gebaseerd gebalanceerd. Gekruiste combinaties zoals `**een *twee** drie*` en vet + doorhalen produceren geldige geneste XHTML doordat doorlopende binnenste tags zo nodig tijdelijk worden gesloten en heropend.
- De Markdown-importer decodeert nu de double-quoted JSON/YAML-scalars die de publieke Markdown-export sinds 0.21.8 bewust schrijft. Ook eenvoudige single-quoted YAML-scalars worden ontquote. Titel, beschrijving, tags en andere scalars stapelen daardoor geen letterlijke quotes/escapes meer op bij export → import → export.
- `##`-tussenkoppen krijgen in EPUB-hoofdstukken stabiele `h-1`, `h-2`, … anchors. Staat de publicatie-inhoudsopgave op **Hoofdstukken + tussenkoppen**, dan verschijnen die koppen als geneste links in zowel `contents.xhtml` als EPUB 3 `nav.xhtml`; bij **Alleen hoofdstuktitels** blijven ze bewust afwezig.
- De ingebouwde XML-controle vermeldt bij eventuele resterende ongeldige EPUB-XHTML het betreffende document/hoofdstuk in plaats van alleen een kale parserfout.
- Nieuwe regressietests dekken de handmatig gevonden 0.22.3-fontrefresh-regressie en reviewbevindingen 9–12.
- Pakketversie naar 0.22.4 verhoogd.

## 0.22.3 — tekstintegriteit, stale spelling en conflict-UX

- **Alles vervangen** gebruikt nu exact dezelfde lengtevaste image-maskering als Zoeken. Alleen treffers die in de gemaskeerde tekst zichtbaar zijn worden op de corresponderende offsets van de originele Markdown vervangen; beheerde image-paths, UUID-bestandsnamen en Markdown-syntax blijven daardoor byte-for-byte intact. Alt-tekst en onderschriften blijven bewust gewone zoekbare tekst.
- **Spelling → Wijzigen** controleert vóór iedere mutatie of de opgeslagen `start:end`-offset nog steeds exact naar hetzelfde fout gespelde woord wijst. Is de editor of hoofdstuktitel intussen gewijzigd, dan wordt de foutenlijst ververst en de dichtstbijzijnde gelijke treffer opnieuw geankerd; bestaat die niet meer, dan wordt niets gewijzigd.
- Structuuracties vanuit Voorwerk/Achterwerk mislukken niet langer stil wanneer `self.chapter is None`. QuietWriter toont een expliciete externe-wijzigingsdialoog, kan de nieuwste live boekstate centraal adopteren en meldt dat de oorspronkelijke structuuractie niet is uitgevoerd. Niet-opgeslagen publicatievelden worden daarbij nooit stil weggegooid: die moeten eerst via hun eigen conflictpad worden opgeslagen/opgelost.
- De instellingenpagina past schrijflettertype, tekstgrootte, regelafstand, inspringing en alinearuimte tijdens het wijzigen niet meer op de verborgen manuscripteditor toe. De bestaande fontkaart blijft de lokale preview; thema blijft wel live previewen. Na **Opslaan** wordt de schrijflayout één keer toegepast en alleen bij een echte layoutwijziging wordt de presentatie-Undo-historie opgeschoond, zodat Ctrl+Z geen onzichtbare font-/blokopmaakstappen meer tegenkomt.
- `UI_GUIDE.md` is weer onderdeel van de releasebron en documenteert dat instellingenpreview de manuscript-Undo-stack niet mag muteren.
- Nieuwe regressietests dekken beschermde image-paths, stale spellingsposities, publicatiecontext-conflictgedrag en de Undo-grens rond opgeslagen manuscriptstijl.
- Pakketversie naar 0.22.3 verhoogd.

## 0.22.2 — history-preview isolatie en veilig versieherstel

- History-preview is nu expliciet editor-only. Zodra de gebruiker naar Planning, Boekdetails, Export, Instellingen of een andere hoofdpagina navigeert, verlaat de editor de historische weergave en koppelt hij terug naar het live boek. Andere pagina's kunnen daardoor nooit een `archive/`-snapshot als actief werkboek erven.
- **Huidige treffer vervangen**, **Alles vervangen** en **Spelling → Wijzigen** hebben een extra read-only guard tijdens history-preview. Programmatic text mutations kunnen daardoor ook buiten de normale read-only-widgetbeveiliging geen archiefhoofdstuk aanpassen.
- De normale editor-conflictafhandeling weigert nu expliciet te draaien zolang `self.book` een historische snapshot is. De preview wordt eerst veilig verlaten; de gewone conflictresolver kan daardoor nooit een archive-pad tracken of beschrijven alsof het live is.
- **Deze versie herstellen** heeft een eigen conflictpad gekregen. Als het live boek tijdens de preview extern is gewijzigd, wordt herstel niet uitgevoerd, de preview gesloten, de nieuwste live schijfversie geladen en een gerichte melding getoond. De archive-snapshot blijft byte-for-byte ongemoeid.
- Een tijdelijke revision-verificatiefout tijdens herstel sluit eveneens veilig de preview zonder de gewone conflictroute op de snapshot los te laten.
- Normaal verlaten van history-preview verzet de revision-baseline bewust niet. Als Dropbox tijdens de preview iets wijzigde, blijft dat bij de eerstvolgende schrijfactie detecteerbaar; alleen een succesvol opnieuw van schijf geladen live boek wordt opnieuw centraal getrackt.
- Nieuwe regressietests dekken read-only guards, preview-exit bij hoofdnavigatie, de dedicated restore-conflictroute en — waar PySide6 beschikbaar is — echte MainWindow-scenario's waarin Planning/Export en een extern restore-conflict het archief niet wijzigen.
- Pakketversie naar 0.22.2 verhoogd.

## 0.22.1 — centrale live-bookstate en conflictintegriteit

- QuietWriter heeft nu één centrale live-bookreferentie in `MainWindow`. Een vers geladen boek wordt via `adopt_active_book(...)` in één stap gedeeld met Editor, Planning, Boekdetails en Export; de editor koppelt daarbij het open hoofdstuk opnieuw aan het nieuwe `Book`-object.
- Conflictoplossing in Planning en Publicatie gebruikt dezelfde centrale adopt-route. Een verschoven revision-baseline kan daardoor niet meer samengaan met een editor die nog oude hoofdstuktekst of een verweesd `Chapter`-object vasthoudt.
- Planning-persistentie rapporteert voortaan expliciet `mine`, `disk` of `failed`. Alleen bij `failed` wordt een lokale kandidaat teruggerold; de keuze **Versie op schijf gebruiken** wordt niet meer achteraf door de oude in-memory lijst overschreven.
- **Openen** vanaf de boekenplank werkt altijd met een opnieuw van schijf geladen manifest. `Library.touch_book()` schrijft alleen `last_used` naar die actuele structuur en kan een stale bookshelf-object dus niet meer gebruiken om extern toegevoegde hoofdstukken uit `book.json` te verwijderen.
- Boekdetails wordt bij iedere centrale live-book-adopt opnieuw aan exact hetzelfde object gekoppeld. Na een conflict of versieherstel kan de pagina daardoor geen oude boekstructuur/metadata meer terugschrijven die de editor later weer ongedaan maakt.
- `PublicationEditor` heeft een expliciete `adopt_book()`-route die na een gecoördineerde reload niet probeert het oude object opnieuw op te slaan, maar het huidige publicatie-item veilig opnieuw laadt.
- Nieuwe regressietests dekken stale-bookshelf `touch_book`, de centrale identity-invariant, drie-uitkomsten Planning-conflicten en — waar PySide6 beschikbaar is — een echte MainWindow-adopt met extern toegevoegd hoofdstuk.
- Pakketversie naar 0.22.1 verhoogd.

## 0.21.10 — Cleanup, performance, testdekking en AI-instellingen-UX

- **Modellen ophalen** geeft nu direct inline voortgang (`Modellen ophalen…`) en daarna een expliciete succesmelding met het aantal gevonden modellen. Een fout blijft zowel inline als via de bestaande foutdialoog zichtbaar.
- De AI-modelkeuze is nu een echte niet-bewerkbare combobox. De gebruiker kiest uitsluitend uit de opgehaalde/provider-specifieke modellen; klikken op het veld zelf opent de keuzelijst en modelnamen kunnen niet meer per ongeluk handmatig worden gewijzigd.
- De boekenplank berekent woordenaantallen per refresh maximaal één keer per boek en hergebruikt die waarde zowel voor sortering als voor de kaart. Sorteren op woordenaantal veroorzaakt daardoor geen dubbele hoofdstuk-I/O meer.
- `BookCover.paintEvent()` maakt niet langer bij iedere repaint nieuwe `QSettings`-instanties; één settingsobject wordt per coverwidget hergebruikt.
- De oude, niet meer aangeroepen Markdown-exportmethode in `BookDetailsPage` is verwijderd. Export loopt uitsluitend via de modulaire `Exporteren`-pagina en `exporting/markdown_exporter.py`.
- Veilige cleanup uitgevoerd op aantoonbaar ongebruikte imports/lokalen. `zip()`-semantiek is expliciet gemaakt: `strict=True` waar EPUB-secties en paden exact één-op-één moeten lopen, en `strict=False` bij bewust overlappende buurparen in de UI.
- Extra regressiedekking toegevoegd voor AI-modelstatus/selection-only gedrag, OpenRouter streaming-foutdetails, de enige actieve Markdown-exportroute en de boekenplank-hotpaths.
- Het hogere-prioriteit externe code-review herstelprogramma 0.21.1–0.21.10 is hiermee afgerond. De bestaande productroadmap wordt hervat; portable Markdown-media is de eerstvolgende productstap.
- Pakketversie naar 0.21.10 verhoogd.

## 0.21.9 — kleine correctness/UX

- Ollama-modeldetectie respecteert nu daadwerkelijk de door de caller gevraagde timeout; de compatibiliteitslaag geeft `timeout` door aan `OllamaProvider.list_models()`.
- OpenRouter geeft bij HTTP-fouten de foutmelding uit de JSON-response door in plaats van alleen een generieke `401/429 Client Error`.
- Bij een ongeldige vervangingsafbeelding blijft in bewerkmodus de naam van het werkelijk gekoppelde bestand zichtbaar; QuietWriter suggereert niet langer dat de mislukte vervanging is geaccepteerd.
- Scene-break invoegen is symmetrisch beveiligd: staat direct links of rechts van de cursor al een `***`-blok, dan wordt geen tweede scene-break aangemaakt. De eerder vermoedelijke bevinding is hiermee gereproduceerd en bevestigd.
- Nieuwe gerichte regressietests voor timeout-doorgifte, OpenRouter-foutdetails, image-label en dubbele scene-breaks.


## 0.21.8 — Exportvalidatie, crash-infrastructuur en woordenboeklabels

- EPUB-coverrendering valideert nu iedere omslag met Qt vóór een JPEG/PNG in `artwork_with_text`-modus ongewijzigd wordt doorgegeven. Lege of corrupte coverbytes kunnen daardoor niet meer ongemerkt in een structureel geldige maar visueel kapotte EPUB terechtkomen.
- De vaste publicatie-Markdown blijft dezelfde frontmattervelden en volgorde gebruiken, maar quote YAML-gevoelige scalars deterministisch. Titels met `: `, meerregelige beschrijvingen, commenttekens en YAML-achtige waarden zoals `Yes` blijven daardoor geldige strings zonder een nieuwe runtime-dependency.
- Crashlogging is best-effort gemaakt: een onschrijfbare workspace-logmap kan de applicatie niet meer vóór installatie van het vangnet laten crashen. QuietWriter probeert automatisch een tijdelijke OS-map en start zonder crashlog als zelfs die niet beschikbaar is.
- `crash.log` wordt bij 2 MiB geroteerd naar één `crash.log.1`; als rename door sync/antivirus geblokkeerd wordt, probeert QuietWriter het actieve log veilig af te kappen. Crashlogging kan zo niet onbeperkt blijven groeien.
- Woordenboeklabels zijn uitgebreid met veel meer Nederlandse taal- en landnamen en gebruiken consequent **Taal — Land** als beide codes bekend zijn. Bij onbekende codes wordt de complete genormaliseerde locale getoond in plaats van een verwarrende half-vertaalde combinatie.
- Dictionary discovery verkiest nu een specifieke locale uit de bovenliggende Office-map boven een kale bestandsnaam. Een `nl.dic` onder `nl-NL/` wordt bijvoorbeeld als `nl_NL` / **Nederlands — Nederland** aangeboden.
- Nieuwe regressietests dekken YAML-escaping/parsing, lege en corrupte covers, crashlogrotatie/fallback en locale-label/inferentiegedrag.
- Roadmap: 0.21.8 is afgerond; 0.21.9 (Kleine correctness/UX) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.8 verhoogd.

## 0.21.7 — Spellingcorrectheid en woordenboekencoding

- Spellingscontrole accepteert woorden met een hoofdletter niet langer automatisch als correct. De normale Hunspell-regels worden gebruikt; zonder Hunspell blijft de eenvoudige woordenlijst case-insensitive, zodat bekende woorden aan het begin van een zin gewoon geldig blijven terwijl echte hoofdletter-tikfouten wel worden gemeld.
- De known-word cache bewaart bij actieve Hunspell-dictionaries de exacte woordvorm als sleutel, zodat hoofdletterregels niet door een eerder gecachte lowercase/uppercase variant worden omzeild.
- Hunspell `.dic`-bestanden worden niet meer hardcoded als UTF-8 met `errors='ignore'` gelezen. QuietWriter leest eerst `SET <ENCODING>` uit het bijbehorende `.aff`-bestand en decodeert daarmee strikt; zonder bruikbare declaratie volgt een gecontroleerde UTF-8 → Latin-1 fallback zonder diakrieten stil te verwijderen.
- **Alles negeren**, **Altijd negeren** en **Toevoegen aan woordenboek** hervatten nu op basis van de tekstpositie van de zojuist behandelde fout. Als dezelfde fout eerder in het hoofdstuk ook verdwijnt, kan de volgende overgebleven fout daardoor niet meer door een verschoven lijstindex worden overgeslagen.
- Nieuwe regressietests dekken hoofdletter-tikfouten, case-insensitive fallback, Latin-1 Hunspellwoordenboeken en — waar PySide6 beschikbaar is — de indexverschuiving van alle drie globale spellingacties.
- Roadmap: 0.21.7 is afgerond; 0.21.8 (Export & crash-infrastructuur) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.7 verhoogd.

## 0.21.6 — AI state-isolatie en provider/model-synchronisatie

- AI-aanvragen zijn nu gekoppeld aan zowel een oplopende boekgeneratie als een request-id en de concrete `ProviderChatWorker`. Tokens, thinking-output, success, failure en cancellation van een oude worker worden genegeerd zodra het zichtbare boek of de actieve aanvraag niet meer overeenkomt.
- Boekwisselen tijdens een lopende AI-aanvraag blokkeert de GUI niet langer maximaal 2,5 seconde. De oude worker wordt geannuleerd en als achtergrondworker aangehouden tot zijn `finished`-signaal; de nieuwe boekcontext kan direct worden geladen.
- Een laat `finished`-signaal van een oude worker kan `self.worker` van een nieuwere aanvraag niet meer leegmaken of de nieuwe worker per ongeluk `deleteLater()` geven. Alle nog levende workers worden sterk bijgehouden en bij afsluiten gezamenlijk gestopt/afgewacht.
- Hierdoor kan een stale cancel/done/fail van Boek A de berichtenlijst of `ConversationStore` van Boek B niet meer muteren of naar schijf schrijven. De bestaande `ConversationStore` hoeft daarvoor zelf geen cross-book heuristiek te krijgen: alleen callbacks van de nog actuele request-context mogen hem aanroepen.
- De AI-instellingen houden provider en model nu als één samenhangende formulierstate bij. Wisselen Ollama ↔ OpenRouter leegt/ververst de modelcombo direct vanuit de live providerselectie; een model van de vorige provider kan niet meer onder de nieuwe provider worden opgeslagen. Niet-opgeslagen modelkeuzes worden per provider apart onthouden tot Opslaan.
- `ContextBuilder` vangt een stale hoofdstukreferentie bij **Huidige sectie** defensief af en laat een onleesbaar niet-actief hoofdstuk in sectie/boek-context als duidelijke placeholder staan in plaats van de hele AI-aanvraag te laten crashen.
- De **+ Toevoegen**-flyout en zijn keuzes gebruiken subtielere 4px-hoeken in plaats van de opvallende 10/8px afronding.
- Nieuwe regressietests bewaken request/book-isolatie, worker-identity bij cleanup, live provider/model-synchronisatie, context-fallbacks en de flyout-stijl. Een aanvullende Qt-runtime-test reproduceert, waar PySide6 beschikbaar is, de late-cancel race tussen Boek A en Boek B.
- Roadmap: 0.21.6 is afgerond; 0.21.7 (Spellingcorrectheid) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.6 verhoogd.

## 0.21.5 — Publicatie & Planning data-integriteit

- Hoofdstuk-contextmenu uitgebreid met **Verwijderen** naast Hernoemen en Dupliceren. De bestaande verwijderactie in de rechter werkbalk blijft beschikbaar; beide routes gebruiken dezelfde bevestigde, herstelbare hoofdstukverwijdering.
- De hoofdstuk-/sectie-tekstprompt is niet langer gebaseerd op `QInputDialog`. QuietWriter gebruikt nu een eigen klein dialoog met betrouwbare **Opslaan / Annuleren**-knoppen op Windows, voor zowel Hernoemen als Nieuw hoofdstuk/sectie.
- `PublicationEditor.set_book()` reset bij navigatie binnen hetzelfde boek niet langer `key`, dirty-state en geladen data vóór `open_item()` de vorige publicatiepagina kan opslaan. Onopgeslagen structured en vrije-tekst-publicatiegegevens gaan daardoor niet meer stil verloren bij wisselen tussen Voorwerk/Achterwerk-items.
- Bestaande personages worden voortaan via een kandidaat-kopie bijgewerkt. Een mislukte `persist_characters()` kan daardoor geen in-memory mutatie achterlaten die bij een latere, andere save alsnog stil naar schijf wordt geschreven.
- Nieuwe en bewerkte outline-scènes gebruiken hetzelfde snapshot/rollback-patroon als verwijderen: faalt de persist, dan wordt de in-memory scènecollectie teruggezet.
- Scènes die nog verwijzen naar een inmiddels verwijderd hoofdstuk worden niet langer onzichtbaar. De Outline toont ze onder **Verweesde scènes**; openen/bewerken maakt herstel of herplaatsing mogelijk.
- Bij het verwijderen van een personage worden na de geslaagde personage-save ook diens `character_ids` uit scènes verwijderd. Als die tweede save door een extern conflict niet lukt, meldt QuietWriter dit expliciet in plaats van oude scènegegevens blind terug te schrijven.
- Een ingevuld maar nog niet opgeslagen nieuw-personage-concept wordt bij boekwissel niet meer stil weggegooid: de gebruiker kiest **Opslaan / Niet opslaan / Annuleren**. `PlanningPage.save_pending()` omvat daardoor nu zowel personagedrafts als notities.
- Boekverwijdering heeft een echte pre-delete guard gekregen: actieve planning én manuscripttekst moeten eerst succesvol kunnen worden opgeslagen voordat de boekmap naar de prullenbak verhuist. De oude post-delete `save_pending()`-aanroep is verwijderd.
- De geneste f-string in de personagerelatieweergave is herschreven zodat `characters_page.py` ook onder Python 3.11 parseert; QuietWriter zelf blijft op Python 3.12 gericht.
- Nieuwe regressietests bewaken de gelokaliseerde prompt, hoofdstuk-contextdelete, publicatie same-book guard, candidate/rollback-patronen, verweesde scènes, draft-save-pending, pre-delete saveguard en Python-3.11-syntaxcompatibiliteit.
- Roadmap: 0.21.5 is afgerond; 0.21.6 (AI state-isolatie) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.5 verhoogd.

## 0.21.4 — Prullenbak & herstelbaarheid

- De prullenbak toont voortaan zowel verwijderde boeken als verwijderde hoofdstukken in één chronologische lijst, met duidelijk onderscheid tussen boek en hoofdstuk plus het bijbehorende boek.
- Nieuwe hoofdstukverwijderingen bewaren naast de recoverable `.md`-kopie een kleine JSON-sidecar met boek-, sectie-, titel- en positiegegevens. Daardoor kan een hoofdstuk terugkeren op zijn oorspronkelijke plek; als de oorspronkelijke sectie intussen is verwijderd, wordt die sectie bij herstel opnieuw aangemaakt.
- Hoofdstukken die al in 0.21.3 naar `trash/chapters/` zijn verplaatst zonder metadata blijven als legacy-item zichtbaar en herstelbaar; ze vallen terug op de eerste beschikbare sectie.
- `Library.restore_trashed_chapter()` is rollback-safe: een mislukte manifest-write verwijdert de tijdelijk teruggeschreven live file en herstelt het in-memory model, terwijl de trashkopie beschikbaar blijft.
- Een boek en één of meer van zijn verwijderde hoofdstukken kunnen in één herstelactie worden geselecteerd; boeken worden bewust eerst hersteld en daarna pas hoofdstukken.
- Definitief verwijderen van een weggegooid boek ruimt nu ook `trash/chapters/<book_id>` op. **Prullenbak legen** verwijdert zowel boek- als hoofdstuk-trash, zodat verwijderde hoofdstukinhoud niet onzichtbaar op schijf blijft staan.
- Definitief verwijderen verwerkt items afzonderlijk met foutafhandeling; een fout op één item voorkomt niet dat de lijst wordt ververst of dat andere geselecteerde items worden afgehandeld. Ook een gedeeltelijk mislukte `Prullenbak legen`-actie geeft een normale waarschuwing en ververst daarna altijd de UI.
- Hernoemen en aanmaken van hoofdstukken/secties gebruiken nu één gelokaliseerde tekstprompt met **Opslaan / Annuleren** in plaats van Qt's native OK/CANCEL-labels.
- Nieuwe regressietests dekken metadata, herstelpositie, herstel van een verdwenen sectie, legacy-trash uit 0.21.3, rollback bij mislukte restore, boek+chapter-herstel, purge bij definitief boek verwijderen en volledige lege-prullenbaksemantiek.
- Roadmap: 0.21.4 is afgerond; 0.21.5 (Publicatie & Planning data-integriteit) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.4 verhoogd.

## 0.21.3 — Hoofdstuk- en storage-integriteit

- Hoofdstuk-drag-and-drop bewaart de oorspronkelijke verplaatsingsintentie nu ook bij een `ExternalModificationError`: na een succesvol opgelost extern conflict wordt de reorder opnieuw berekend tegen het vers geladen boek en één keer opnieuw opgeslagen. De oude situatie waarin het conflict wel werd opgelost maar de drag stil verloren ging is daarmee gesloten.
- Als de boekstructuur tijdens conflictresolutie zó is veranderd dat bronhoofdstuk of doel niet meer bestaat, wordt de verplaatsing niet geforceerd en krijgt de gebruiker een gerichte waarschuwing. Een tweede extern conflict tijdens de retry veroorzaakt geen oneindige herhaal-/dialooglus.
- `Library.delete_chapter()` verplaatst niet langer de enige live hoofdstukkopie vóórdat `book.json` veilig is bijgewerkt. Eerst wordt een recoverable kopie in chapter-trash gemaakt, daarna wordt de manifestmutatie gecommit en pas na succes wordt het live bestand best-effort verwijderd. Bij een mislukte manifest-write worden model en tijdelijke trashkopie teruggedraaid.
- Dezelfde rollback-regel is doorgetrokken naar `add_section()`, `add_chapter()`, `rename_chapter()`, `rename_section()` en `duplicate_chapter()`: een mislukte manifest-write laat het live model niet meer half-gemuteerd achter; nieuw aangemaakte UUID-hoofdstukbestanden worden waar mogelijk weer opgeruimd.
- Nieuwe regressietests forceren manifest-write failures en controleren dat model, bronbestand, manifest en tijdelijke trashstatus consistent blijven. De drag-retrylogica heeft daarnaast een broncontracttest; Qt-runtime-interactie blijft aanvullend handmatig/optioneel getest.
- De externe code-review is voor dit domein opnieuw getoetst: het contextloze conflictgedrag bij rename/add/delete/duplicate is verwarrend maar veroorzaakt vóór de mutatie geen bevestigd dataverlies; contextuele structurele conflictdialogen blijven daarom buiten deze data-integriteitshotfix.
- Roadmap: 0.21.3 is afgerond; 0.21.4 (hoofdstuk-prullenbak & herstelbaarheid) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.3 verhoogd.

## 0.21.2 — Undo/Redo root-cause hotfix

- De extern aangeleverde en vooraf gereproduceerde `manuscript_editor`-Undo-patch is geïsoleerd op de 0.21.1-codebasis toegepast; de resulterende file is byte-voor-byte gelijk aan het meegeleverde `manuscript_editor.py.fixed`.
- Actieve lege vervolgalinea's gebruiken voor line-height en bottom-margin voortaan hetzelfde blockformat als de normale alinea waarin ze na de eerste letter veranderen. Alleen duurzame lege separator-alinea's krijgen nog `MinimumHeight` en de compacte lege-regelmarge. Daardoor ontstaat bij het typen van de eerste letter geen extra block-formattransitie meer die als los Qt-undo-commando kan eindigen.
- `ManuscriptEditor.undo()` en `redo()` onderdrukken formatting-scheduling zolang Qt de eigenlijke undo/redo uitvoert en wissen daarna `_format_join_previous`; een undo/redo-trigger kan daardoor geen nieuwe formatteringspass meer aan de zojuist gewijzigde undo-stack vastplakken.
- Ctrl+Z/Ctrl+Y worden in `keyPressEvent()` expliciet via deze editor-overrides geleid met `QKeySequence.StandardKey.Undo/Redo`, omdat Qt's standaard `QTextEdit`-keypad de Python-level overrides anders kan omzeilen.
- Nieuwe regressietests bewaken de broncontracten én, waar PySide6 beschikbaar is, toetsenbordgedreven Ctrl+Z-convergentie, Undo→Redo→Undo-stabiliteit en formatgelijkheid van een actieve lege vervolgalinea.
- De roadmap bevat nu de volledige externe code-review als hogere-prioriteitsreeks 0.21.3–0.21.10 vóór nieuwe featurebouw; bestaande productroadmapitems blijven behouden.
- Pakketversie naar 0.21.2 verhoogd.

## 0.21.1 — Eerste externe code-review fixes

- `EditorPage.tree_context_menu()` importeert `QMenu` nu expliciet. Rechtsklikken in de manuscriptboom kan daardoor niet meer op een `NameError` stuklopen.
- `CurrentPageStack.minimumSizeHint()` en `sizeHint()` respecteren nu ook een expliciete `setMinimumSize()` van de zichtbare pagina via `expandedTo(page.minimumSize())`. Verborgen pagina's blijven de hoofdvensterhoogte niet bepalen, maar de actieve pagina mag wel zijn eigen minimum afdwingen.
- Nieuwe regressietests leggen beide fixes vast.
- De eerste externe code-review is vergeleken met de werkelijk uitgegeven 0.20.3-code. De genoemde undo-refactorpunten (`reset_undo_history`, één formatting-schedule, `_make_block_format` en `joinPreviousEditBlock`) waren daar al aanwezig en zijn daarom niet nogmaals gewijzigd; de resterende alinea/Undo-bug vraagt een andere oorzaak.
- Pakketversie naar 0.21.1 verhoogd.

## 0.20.3 — Alinea-inspringing en Undo-hotfix

- De alinea-inspringing wordt niet langer pas 90 ms na het eerste zichtbare karakter toegevoegd. Een gewone Enter maakt de nieuwe `QTextBlock` direct met de juiste vervolg-alinea-opmaak, zodat de cursor al vóór het typen op de ingesprongen positie staat.
- Enter en de bijbehorende paragraph-layout zijn één undo-transactie. De visuele `QTextBlockFormat` kan daardoor niet meer als los undo-item tussen de eerste letter en de rest van de zin komen te staan.
- Tekstgedreven formatteringscorrecties gebruiken `QTextCursor.joinPreviousEditBlock()` wanneer werkelijk een blockformat moet veranderen. Presentatie-opmaak vervuilt daardoor de tekstuele undo-keten niet meer.
- Een tweede Enter normaliseert de eerste lege vervolgregel tot een echte blanco alinea en maakt daarna een flush-left nieuwe alinea; de 0.20.1-fix voor zichtbare lege regels blijft behouden.
- Lege/whitespace-only actieve vervolgalinea's behouden hun inspringing. Een spatie typen laat de cursor dus niet terugvallen naar de linkermarge.
- Na het laden en de initiële manuscript-layout wordt de setup-only undo-historie expliciet leeggemaakt; een vers geopend hoofdstuk heeft geen verborgen formatteringsactie om ongedaan te maken.
- De dubbele formatteringsschedule vanuit `EditorPage.on_text_changed()` is verwijderd; de manuscripteditor bezit voortaan zelf de text-driven layoutcyclus.
- Nieuwe Qt-runtime-regressies dekken directe inspringing na Enter, whitespace op een lege vervolgalinea en herhaald Undo over tweede zin, eerste letter en Enter.
- Portable Markdown-media schuift door naar 0.20.4; de beschermde imageblokken van 0.20.2 zijn inhoudelijk ongewijzigd.

## 0.20.2 — Beschermde afbeeldingsblokken in de editor

- Inline media blijft op schijf gewone Markdown, maar beheerde image-regels zijn in de manuscriptruimte niet meer als ruwe `![...](../assets/images/...)`-syntaxis zichtbaar of rechtstreeks bewerkbaar.
- Nieuwe modulaire `ImageBlockCard` toont thumbnail/placeholder, alt-tekst, onderschrift en expliciete **Bewerken**/**Verwijderen**-acties bovenop een echt gereserveerd QTextBlock. De kaart wordt gepositioneerd via Qt's `blockBoundingRect()` zodat invoegen, laden, scrollen en resizen dezelfde uitlijning houden.
- Klikken op de kaart selecteert alleen het mediablok; bewerken start uitsluitend via **Bewerken**, Enter/Return op een geselecteerd blok of het beschermde contextmenu.
- Het bestaande Afbeelding-scherm in de rechterrail heeft nu een echte editmodus: huidige preview, alt-tekst en onderschrift worden geladen, **Afbeelding vervangen…** importeert alleen bij expliciete vervanging en **Opslaan** wijzigt het bestaande Markdown-blok.
- Afbeeldingsblokken zijn atomair beschermd tegen typen, Enter, Delete/Backspace, Cut/Paste, tekst-drag/drop en opmaakacties die een selectie over het mediablok heen zouden wijzigen.
- Verwijderen gebruikt QuietWriter's centrale gelokaliseerde bevestiging met **Ja/Nee** en verwijdert alleen de manuscriptverwijzing; de immutable asset blijft bewaard voor historie/herstel.
- Historische/read-only weergave toont de media-kaarten zonder bewerk/verwijder-acties.
- De ruwe Markdownregel wordt visueel ingeklapt door de presentatie-highlighter; de bron blijft wel volledig round-tripbaar voor opslag, historie en export.
- 0.20.2 is bewust vóór portable Markdown-media geplaatst; de `<slug>-assets/` companionmap en link-rewriting schuiven door naar 0.20.4.

## 0.20.1 — Hotfix lege alinea's in de editor

- Een gewone Enter/Return wordt in de manuscripteditor nu expliciet als `QTextCursor.insertBlock()` ingevoegd. Dit omzeilt een Qt-randgeval waarbij Return op een lege paragraaf met custom `QTextBlockFormat` de opmaak kan resetten/reflowen en de cursor visueel terug omhoog springt.
- Lege manuscriptblokken gebruiken een expliciete `MinimumHeight` op basis van het ingestelde schrijflettertype en de regelafstand. Een bewuste dubbele Enter blijft daardoor een zichtbare lege alinea, ook nadat de 90-ms visuele formatteringspass is uitgevoerd.
- Shift+Enter en modifier-combinaties blijven aan Qt zelf overgelaten; alleen gewone Enter/Return wordt door QuietWriter beheerd.
- Runtime-regressietest toegevoegd die twee Enters invoert, de formattering uitvoert en controleert dat de bron `\n\n`, drie tekstblokken en een niet-ingeklapte lege paragraaf behoudt.
- De geplande portable Markdown-media-export schuift door naar 0.20.4; de EPUB/mediafunctionaliteit van 0.20.0 is inhoudelijk ongewijzigd.

## 0.20.0 — Book-local media en afbeeldingen in EPUB

- Nieuwe modulaire `quietwriter/media/`-laag voor book-local assets. Ieder nieuw boek heeft `assets/images/`, `assets/cover/` en een klein revision-guarded `assets/manifest.json`; bestaande boeken worden zonder verplichte migratie ondersteund.
- Afbeeldingen worden bij import gekopieerd naar een UUID-bestandsnaam, blijven immutable en worden op SHA-256 gededupliceerd. De oorspronkelijke naam, media type, afmetingen, bestandsgrootte en hash staan in het manifest; JPG/JPEG en PNG zijn de eerste ondersteunde inlineformaten.
- De rechterrail **Toevoegen** bevat nu **Afbeelding** met preview, alt-tekst en optioneel onderschrift. Annuleren kopieert niets; pas **Invoegen** importeert het bestand en voegt één standaard Markdown-imageblok op de cursorpositie in.
- Manuscriptstatistieken tellen imageblokken niet als woorden. Spelling en zoeken negeren de beheerde UUID-/padsyntaxis, terwijl alt-tekst en onderschrift wel natuurlijke tekst blijven. AI-context vervangt het pad door een compacte `[Afbeelding: …]`-beschrijving.
- Export snapshots verzamelen alle gebruikte media via hetzelfde bestaande `ExportAsset`-model. EPUB kopieert inline assets naar `EPUB/images/`, neemt ze op in `package.opf` en rendert imageblokken als semantische `<figure><img/><figcaption>…</figcaption></figure>`.
- EPUB-preflight blokkeert ontbrekende of gewijzigde assets; zware binaries worden niet bij iedere editor-save gehasht, maar hun bytes worden bij export tegen de manifest-SHA gecontroleerd.
- Historieversies nemen `assets/` volledig mee. Bij herstel worden benodigde snapshot-assets teruggezet, maar nieuwere UUID-binaries nooit automatisch verwijderd; expliciete ongebruikte-media-opruiming is een latere functie.
- Nieuwe/vervangen boekomslagen worden voortaan in `assets/cover/` van het boek opgeslagen. Oude globale omslagen onder `boekomslagen/` blijven volledig leesbaar als backward-compatible fallback.
- Markdown-export met inline afbeeldingen wordt in 0.20.0 bewust door preflight geblokkeerd: 0.20.4 voegt de afgesproken portable `-assets` companionmap en link-rewriting toe in plaats van nu kapotte paden te exporteren.

## 0.19.4 — Rustiger splash en compactere Over-pagina

- Het splashscherm toont nog maar één QuietWriter-naam; de kleine dubbele merkregel boven de grote titel is verwijderd. De bestaande startup-status, voortgang, versie en copyright blijven ongewijzigd.
- De Over-pagina is teruggebracht tot productintro, lokale opslag/privacy, copyright, technische omgeving en fontlicenties. De drie ontwerpprincipe-kaarten en de grotendeels dubbele Maker-tekst zijn verwijderd.
- Runtime-informatie heeft nu de expliciete sectietitel **Technische omgeving** in plaats van als losse diagnostische regel tussen de overige inhoud te staan.
- **Over** staat in de instellingen-navigatie direct onder **Spelling**. De flexibele lege ruimte staat voortaan onder Over, zodat de pagina niet meer visueel los onderaan de sidebar hangt.

## 0.19.3 — Volwaardig opstartscherm en vernieuwde Over-pagina

- Het oude 450-ms splashvenster is vervangen door een echte startup-flow: de splash blijft zichtbaar terwijl lettertypen, werkmap, AI-provider en hoofdinterface worden voorbereid en sluit pas wanneer Qt/Windows het hoofdvenster daadwerkelijk heeft blootgelegd. Er is geen kunstmatige minimumduur.
- De splash volgt het actieve QuietWriter-thema en toont appnaam, tagline, actuele opstartstatus, een subtiele onbepaalde voortgangsbalk, versie en copyright. Alle zichtbare teksten lopen via `nl.json`/`en.json`.
- De Over-pagina heeft een compacte QuietWriter-hero gekregen en geeft naast versie/maker nu ook de ontwerpprincipes **Tekst centraal**, **Lokaal als basis** en **Lichtgewicht** weer.
- Een aparte privacytekst legt uit dat manuscripten in de gekozen werkmap worden bewaard, Ollama lokaal kan draaien en dat tekst/context bij gebruik van een externe AI-provider naar die provider kan worden verzonden.
- Runtime-informatie (Python, PySide6, Qt en platform) staat subtiel op de Over-pagina voor diagnose/support; de bestaande uitklapbare fontlicenties blijven behouden.

## 0.19.2 — Vaste publicatie-Markdown

- Markdown op **Exporteren** volgt nu het vaste publicatieformaat uit de bestaande bestanden: een verplichte header tussen `---` met `title`, `date`, `slug`, `description`, `meta`, `intro`, `author` en `tags` in stabiele volgorde.
- De 0.19.1-opties om frontmatter of sectiemarkeringen uit te schakelen zijn verwijderd; de publicatieheader is onderdeel van het formaat en kan niet per ongeluk verdwijnen.
- Een los verhaal met precies één hoofdstuk dat dezelfde titel heeft als het boek krijgt geen redundante `# Titel` meer. De tekst begint direct na de header, zoals in bestaande publicatiebestanden.
- Meerhoofdstukboeken behouden wel hoofdstukkoppen en onzichtbare sectiemarkeringen om hun structuur te bewaren.
- De rijkere Markdown import/round-triplaag blijft apart bestaan en bewaart extra QuietWriter-metadata; deze wijziging raakt EPUB niet.

## 0.19.1 — Exporteren-pagina en EPUB 3

- Nieuwe modulaire **Exporteren**-pagina direct onder Boekdetails. EPUB en Markdown zijn beschikbaar; PDF is zichtbaar als latere, bewust nog uitgeschakelde optie zonder extra dependency.
- Export bouwt eerst één immutable `ExportDocument`-snapshot uit opgeslagen boek-, hoofdstuk- en publicatiegegevens. EPUB en Markdown lezen daardoor niet ieder afzonderlijk uit live editorstate.
- Volledige lichte EPUB 3-pipeline toegevoegd met alleen Python-standaardbibliotheek plus de al aanwezige PySide6-stack: `mimetype`, container, package/manifest/spine, EPUB 3-nav, XHTML-hoofdstukken, CSS-templates en metadata.
- Drie rustige exporttemplates toegevoegd: Klassiek, Modern en Literair. De templates zijn gewone CSS-bestanden onder `quietwriter/export_templates/`.
- Boekomslag ondersteunt twee expliciete modi: **artwork zonder tekst**, waarbij QuietWriter zelf titel en auteur toevoegt, en **artwork met tekst**, waarbij de afbeelding inhoudelijk ongewijzigd wordt gebruikt. Hiervoor is geen extra beeldlibrary toegevoegd.
- Het exportassetmodel is generiek (`ExportAsset`) zodat toekomstige afbeeldingen in hoofdstukken via dezelfde snapshot/pipeline kunnen reizen; 0.19.1 gebruikt dit model nog alleen voor de omslag.
- Boekdetails bevat nu een aparte **Boektaal**-metadatawaarde. UI-taal en boektaal blijven bewust gescheiden; EPUB gebruikt de boektaal.
- De oude Markdown-exportactie is uit Boekdetails gehaald en verhuisd naar Exporteren. Per boek worden alleen exportvoorkeuren in `export/settings.json` bewaard; de uitvoermap blijft een lokale app-instelling.
- EPUB wordt eerst naar een tijdelijk bestand geschreven en pas na volledige opbouw atomair op de doelnaam geplaatst. Preflight controleert minimaal titel, auteur, boektaal, hoofdstukken, omslag en EPUB-ISBN.
- Nieuwe regressietests controleren de EPUB-containerstructuur, ongecomprimeerde eerste `mimetype`-entry, parseerbare XML/XHTML, navigation/spine, relatieve inhoudslinks, snapshotbuilder en QuietWriter-markupconversie.

## 0.18.14 — Windows-tekstweergave en afronding interactiepolish

- De manuscripttypografie gebruikt op Windows nu volledige font hinting met grayscale-antialiasing in plaats van subpixel-antialiasing. Dit is gericht op de schrijfruimte en font-preview, zodat lichte seriftekst op donkere thema's geen rode/cyaan ClearType-randjes krijgt; de rest van de applicatie houdt de platformstandaard.
- De font-preview in Instellingen gebruikt exact dezelfde `WritingTypography`-route als de editor, zodat familie, gewicht, hinting en antialiasing representatief zijn voor de echte schrijfruimte.
- De resterende Planning-details zijn aan de locale- en interactiebaseline gekoppeld: Personages-navigatie, veldlabels, relatieteksten en conflict/save-meldingen volgen `nl.json`/`en.json`; niet-klikbare Outline-kaarten adverteren geen hoverinteractie meer.
- Publicatie is consequent gemaakt als detail/document-flow: setup, publicatiestructuur en gestructureerde velden volgen de app-locale; Titelpagina, Epigraaf, Inhoud en Copyright hebben een zichtbare Opslaan-knop met dirty-state; vrije publicatietekst heeft dezelfde expliciete Opslaan-lijn naast autosave.
- Versiegeschiedenis volgt de app-locale voor koppen, types, datumtaal en getalnotatie. Enter/Return activeert dezelfde versie als een muisklik; de steractie blijft selectie-afhankelijk.
- Prullenbak heeft selectie-afhankelijke Herstellen/Definitief verwijderen-acties, gelokaliseerde bevestigingen en keyboard-activatie via Enter/Return. Destructieve acties blijven expliciet bevestigd.
- De resterende hover/pressed/focus- en toetsenbordpass van Iteratie 18 is hiermee functioneel afgerond. De eerder uitgevoerde contrasttests over alle veertien thema's blijven automatisch bewaakt; de handmatige DPI/lage-hoogte-smoketest blijft op verzoek uitgesteld.

## 0.18.13 — Uitgebreide themafamilie en contrastpass

- Acht nieuwe kleurenschema's toegevoegd: **Porselein**, **Nevel**, **Salie**, **Lavendel**, **Nord Licht**, **Inkt**, **Diepblauw** en **Aurora**. De bestaande zes thema's blijven beschikbaar; Instellingen toont nu veertien live-preview thema's.
- **Nord Licht** en **Aurora** zijn geïnspireerd op de officiële Nord-families Snow Storm/Polar Night/Frost/Aurora, vertaald naar QuietWriter's eigen semantische UI-tokens.
- Nieuwe semantische token `accent_text` scheidt primaire-knoptekst van `hero_text`. Donkere thema's kunnen daardoor donkere tekst op heldere accentknoppen gebruiken zonder de hero-kleuren te misbruiken.
- Contrast van bestaande thema's is centraal aangescherpt, met name `muted`, focus en enkele statuskleuren in Helder, Warm, Papier, Nacht, Grafiet en Middernacht.
- Geautomatiseerde contrasttests bewaken vanaf nu AA-contrast voor normale en secundaire tekst op alle gangbare oppervlakken, primaire knoppen normaal/hover, status- en hero/history-tekst en minimaal 3:1 voor focusindicatoren.
- De donkere uitbreiding is bewust gespreid: **Inkt** is vrijwel zwart, **Diepblauw** is diep navy en **Aurora** combineert een donkere Nord-basis met de kleurrijkere Aurora/Frost-accenten.

## 0.18.12 — Editor-state, directe zoeknavigatie en planning/detail-consistentie

- Undo/Redo gebruikt nu de actuele `QTextDocument`-state als bron van waarheid en synchroniseert opnieuw na de visuele formatteringspass; de knoppen blijven daardoor niet meer ten onrechte uitgeschakeld.
- Zoekresultaten navigeren met één muisklik naar het gevonden woord; Enter/Return blijft hetzelfde resultaat activeren. Bij een match in een ander hoofdstuk loopt ook de Inhoud-selectie mee met het werkelijk geopende hoofdstuk.
- Slepen van een hoofdstuk verandert niet langer de actieve Inhoud-selectie wanneer de editor een ander hoofdstuk toont. De sleepgreep en gewone klikken op structurele rijen (secties, Voorwerk, Boek, Achterwerk) laten de actieve tekstselectie ongemoeid; alleen de expliciete `wijzig`-actie bij Voorwerk/Achterwerk navigeert naar publicatie-instellingen.
- Outline-dialoogknoppen Opslaan/Annuleren en verwijderbevestigingen volgen de actieve QuietWriter-locale in plaats van de systeemtaal van Qt. Dezelfde gelokaliseerde Ja/Nee-confirmatie wordt nu ook voor personageverwijdering gebruikt.
- Notities heeft naast de bestaande veilige autosave nu een zichtbare primaire Opslaan-knop met dirty-state, in lijn met Personages en Outline.
- Boekdetails is verder aan `nl.json`/`en.json` gekoppeld. `Gepubliceerd` toont gelokaliseerd Ja/Nee of Yes/No, maar bewaart intern bewust de bestaande canonieke metadatawaarden `Yes`/`No`.
- Boekenplank, Instellingen en Over zijn in deze pass opnieuw op cursor/focus/hover-baseline gecontroleerd; daar waren geen aanvullende codewijzigingen nodig.

## 0.18.11 — Editor- en hoofdchrome-polish

- De manuscripteditor gebruikt op Windows expliciet de I-beam tekstcursor. De scènebreuk-hover zet de viewportcursor niet langer via `unsetCursor()` terug naar een overgeërfde pijlcursor; alleen de kleine verwijderactie gebruikt bewust de handcursor.
- De object-specifieke buttonstijlen van de hoofdrail, gereedschapsrail, compacte editorbuttons, secundaire acties, suggesties en geschiedenisbanner hebben nu eigen hover/pressed/focus-states. Daarmee kunnen hun specifiekere QSS-selectors de globale interactiestates niet meer stil overschrijven.
- De niet-klikbare kaart rond **Toevoegen → Scènebreuk** heeft geen hover-highlight meer; alleen de echte Toevoegen-knop communiceert interactie.
- De hoofdstukkenboom ondersteunt nu een expliciete keyboard-activatie: Enter/Return opent een hoofdstuk of publicatie-item; op sectie-/groepsrijen klapt Enter de groep open of dicht. De bestaande single-click-muisbediening blijft ongewijzigd.
- De **+ Toevoegen**-flyout geeft na openen focus aan de eerste keuze, ondersteunt Tab/Shift+Tab en sluit met Escape; Escape brengt focus terug naar de opener.
- Rechter editorpanelen (Zoeken, AI, Spelling, Toevoegen, Versiegeschiedenis) kunnen met Escape worden gesloten; focus keert dan terug naar het bijbehorende rail-icoon.
- Zoek/vervang heeft een expliciete Tab-volgorde die de visuele leesrichting volgt. De spellingscontrole focust bij openen de eerste suggestie/actie en ordent dynamische suggesties vóór de vaste acties.
- Undo/Redo zijn alleen actief wanneer de editor die actie daadwerkelijk kan uitvoeren en hebben expliciete toegankelijke namen. Bij hoofdstukwissel, publicatiecontext en boek sluiten wordt hun status opnieuw gesynchroniseerd.
- Icon-only hoofd- en gereedschapsrailknoppen hebben expliciete accessible names; het Inhoud-randtabje houdt tooltip en accessible name synchroon.

## 0.18.10 — Interaction baseline

- Eerste stap van de resterende UI/UX-polish uitgevoerd: één consistente basis voor hover, pressed, focus en disabled states.
- Alle normale `QPushButton`-varianten krijgen een zichtbare keyboard-focus; borderless navigatie-, compact-, flyout-, formatting- en chipknoppen reserveren transparante borders zodat focus geen layoutverspringing veroorzaakt.
- Hoofdrail, gereedschapsrail, Planning- en Instellingen-navigatie houden checked/selected en focus visueel uit elkaar.
- Checkboxes, radiobuttons, lijsten en bomen krijgen een expliciete focus-state; tekstvelden en combo/spin controls behouden hun bestaande focusrand.
- Flyout-, compact-, relation-chip-, inhoudrand- en primaire/destructieve knoppen hebben nu expliciete focus/pressed-pariteit waar hun specifiekere QSS-regels de globale button-state eerder konden overschrijven.
- UI-richtlijnen uitgebreid met cursorsemantiek, focusuitzonderingen en Tab/Shift+Tab/flyout-regels. Gewone desktopknoppen houden bewust de normale pijlcursor; handcursors blijven voor linkachtige/inline acties en sleepgrepen.
- De DPI/lage-hoogte eind-smoketest is op verzoek voorlopig uitgesteld; eerdere structurele layout-hardening blijft behouden.

## 0.18.9 — Windows drag/drop crash: QPainter fix

- Crashdiagnostiek uit 0.18.8 heeft de harde crash gelokaliseerd: Windows rapporteerde een native access violation in `ManuscriptTree.paintEvent()` tijdens `QDrag.exec()`.
- De custom tree-overlay gebruikt nu maximaal één `QPainter` tegelijk op het viewport. In 0.18.8 konden de selectie-accent en drop-lijn ieder een painter openen terwijl de eerste nog actief was.
- Tijdens een native drag wordt de extra selectie-accent niet meer custom geschilderd; alleen de drop-lijn wordt getekend. De gewone Qt-selectieachtergrond blijft zichtbaar.
- De drag bewaart geen `QTreeWidgetItem` meer als drop-target. `dragMoveEvent()` zet het doel direct om naar gewone waarden (`type`, `id`, `y`) zodat `paintEvent()` geen Shiboken/C++ itemwrapper hoeft te derefereren tijdens de native drag-loop.
- Ook de bron-`QTreeWidgetItem` wordt losgelaten vóór `QDrag.exec()`; alleen hoofdstuk-id, titel en drag-pixmap blijven over.
- `paintEvent()` controleert of de painter actief is en beëindigt hem expliciet via `try/finally`.
- Nieuwe regressietests bewaken dat er maar één viewport-painter bestaat en dat geen tree-itemwrapper de native drag-loop overleeft.


## 0.18.8 — Drag/drop hardening en crashdiagnostiek

- De drag-beveiliging start nu al bij mouse-down op de hoofdstukgreep, vóór `QTreeWidget.mousePressEvent()`. Daardoor kan een focuswissel naar de boom niet meer via `chapter_title.editingFinished` → `rename_current()` de Inhoud-boom herbouwen terwijl Qt het aangeklikte item nog verwerkt.
- Hoofdstuk-autosave én de aparte publicatie-free-text-autosave worden tijdens de volledige drag-interactie gepauzeerd. Opslaan/conflictafhandeling kan daardoor niet meer in de geneste event-loop van `QDrag.exec()` terechtkomen.
- `ManuscriptTree` heeft expliciete `dragStarted`/`dragFinished`-signalen en houdt de drag-guard via `try/finally` actief tot één event-loop-turn ná het terugkeren uit de native drag. Ook een geannuleerde drag of alleen klikken op de greep geeft de guard betrouwbaar vrij.
- `populate_tree()` is een gecoalesceerde refresh-transactie: tijdens een drag wordt `tree.clear()` nooit uitgevoerd. Vervolgacties die een verse boom nodig hebben (zoals selectie/openen) kunnen samen met de refresh worden uitgesteld, zodat geen oud boommodel tegen een nieuw boekmodel wordt gebruikt.
- Externe-wijzigingsdialoog en publicatie-conflictafhandeling krijgen een tweede drag-guard, zodat een toekomstige/directe call tijdens slepen veilig wordt uitgesteld in plaats van een modale dialoog te openen.
- Na een hoofdstukverplaatsing wordt `self.chapter` opnieuw gekoppeld aan het Chapter-object uit de nieuw geordende (deep-copied) secties.
- Navigatie/afsluiten respecteert voortaan een geweigerde editor-save; een boek of venster kan daardoor niet worden gesloten terwijl een drag nog actief is.
- Permanente crashdiagnostiek toegevoegd in `<werkmap>/logs/crash.log`: `faulthandler` schrijft native/fatale Python-stacks en `sys.excepthook`/`threading.excepthook` schrijven onverwerkte Python-exceptions.
- Nieuwe regressietests bewaken de vroege drag-guard, timerpauzes, deferred tree-refresh, Chapter-rebinding en crashlogging.


## 0.18.7 — Drag-and-drop stabiliteit, AI-verbergen en programmataal

- Hoofdstukken slepen bouwt de Inhoud-boom niet langer synchroon opnieuw op vanuit Qt's actieve `dropEvent`; de verplaatsing wordt pas na het drop-event uitgevoerd. Dit voorkomt een native Qt-crash waarbij boomitems tijdens de drag-loop werden vernietigd.
- Als de AI-assistent is uitgeschakeld, wordt die toestand na herstel van de venster-/paneelstatus opnieuw afgedwongen. De AI-knop kan daardoor niet via oude UI-state terugkeren en een eventueel actief AI-paneel wordt gesloten en uit de actieve rechterpaneelpagina gehaald.
- De bestaande `nl.json`/`en.json`-infrastructuur is nu daadwerkelijk gekoppeld aan een opgeslagen programmataal. Instellingen biedt Nederlands en Engels; de keuze wordt bij de volgende start toegepast.
- Nieuwe regressietests voor deferred chapter drops, AI-zichtbaarheid na state restore en runtime locale-selectie.

## 0.18.6 — Hoofdstukselectie en optionele AI

- Het hoofdstuk dat automatisch opent bij het openen van een boek wordt nu ook direct geselecteerd in de Inhoud-boom.
- Hoofdstukselectie is rij-gebaseerd: titel en sleepgreep vormen visueel één geselecteerde regel, met nog maar één accentlijn in plaats van een accent per kolom.
- Nieuwe instelling **AI-assistent gebruiken**. Uitschakelen bewaart de bestaande provider/modelinstellingen, maakt de AI-configuratie inactief en verbergt de AI-knop uit de editorrail.
- De AI-instellingen leggen expliciet uit dat QuietWriter zelf geen AI-model bevat, dat Ollama lokaal kan draaien en dat OpenRouter een externe provider is.
- Nieuwe AI-teksten zijn toegevoegd aan zowel de Nederlandse als Engelse locale.

## 0.18.5 — Boekenplank hero hersteld
- Donkere boekenplank-header loopt weer volledig over de beschikbare contentbreedte; alleen de inhoud binnen de hero volgt de gecentreerde max-width contentas.
- De gecentreerde host uit 0.18.4 krimpt inhoud niet langer onbedoeld tot een derde van de pagina; content groeit tot de beschikbare breedte of de ingestelde maximum breedte.
- Transparante hero-inner voorkomt dat de algemene QWidget-achtergrond een lichte uitsparing over de donkere hero schildert.
- Kaartmaten, spacing, sortering en zoekgedrag uit 0.18.4 blijven ongewijzigd.

## 0.18.4 — Boekenplank polish
- Boekenplank gebruikt nu één gecentreerde contentas met een maximale breedte; op brede schermen wordt lege ruimte links en rechts bewust gebalanceerd in plaats van alleen rechts te blijven staan.
- Hero, sorteer/zoekbalk en kaartgrid volgen dezelfde horizontale uitlijning.
- Boekkaarten zijn subtiel vergroot en spacing/schaduwen zijn verfijnd, zonder de rustige dichtheid van de plank te verliezen.
- Responsive kaartgrid blijft automatisch het aantal kolommen aanpassen aan de beschikbare breedte.
- Zoekveld heeft een bruikbare minimum breedte; sortering gebruikt stabiele interne keys in plaats van zichtbare/vertaalde tekst.
- Alle boekenplankteksten zijn toegevoegd aan zowel `nl.json` als `en.json`.

## 0.18.3 — Zichtbare value-controls en Toevoegen als zijpaneel

- QSpinBox-velden hebben nu expliciete, contrastrijke chevron-assets voor omhoog/omlaag; de klikgebieden uit 0.18.2 blijven behouden.
- De rechterrail-functie Toevoegen gebruikt geen los QMenu meer maar hetzelfde uitklapbare rechterpaneelpatroon als Zoeken, AI, Spelling en Geschiedenis.
- Het nieuwe InsertPanel heeft intern een CurrentPageStack, zodat toekomstige invoegflows (bijvoorbeeld afbeeldingen met instellingen) in hetzelfde paneel kunnen doorstappen zonder nieuwe popup-taal.
- Scènebreuk invoegen sluit het Toevoegen-paneel daarna automatisch.
- Nieuwe invoegteksten zijn toegevoegd aan zowel nl.json als en.json.

## 0.18.2 — Spinbox-bediening en editor micro-interacties

- QSpinBox-subcontrols krijgen expliciete klikgebieden; de bovenste stapknop wordt niet meer door het tekstveld overlapt.
- Scènebreuken hebben nu een hover-only verwijderknop met tooltip; verwijderen blijft één gewone editorhandeling en normaliseert alleen de omliggende witregels.
- Toevoegen-flyout heeft een expliciete pressed-state en publicatie-/scènebreukteksten lopen via de locale-bestanden.
- Nederlandse en Engelse locale-keys uitgebreid voor de nieuwe interacties.

## 0.18.1 — Instellingenlayout en uitleg

- Instellingenrijen gebruiken nu vaste onzichtbare kolommen, zodat labels/uitleg en bediening op alle pagina's exact op dezelfde x-posities uitlijnen.
- De rijen hebben meer verticale ademruimte en bredere control-kolommen; grote schermen blijven rustig terwijl lage laptops via de bestaande scrollviewport blijven werken.
- Werkmapveld verbreed met een bruikbare minimale breedte, zodat paden niet onnodig vroeg worden afgekapt.
- Fontkeuze heeft nu een volwaardige preview-card naast de dropdown met voorbeeldzin en familie/grootte-meta-informatie.
- Combo boxes zijn subtiel afgerond en de dropdownzone is visueel rustiger gemaakt, zonder een nieuwe componentstijl te introduceren.
- Alle knoppen in de zwevende opmaaktoolbar tonen nu ook in het non-activating toolbarvenster betrouwbare hover-uitleg; minder evidente acties hebben beschrijvende tooltips.
- Instellingen- en Over-teksten die in deze iteratie zijn aangeraakt zijn naar locale-keys verplaatst. Naast `nl.json` is een Engelse `en.json` toegevoegd als basis voor latere UI-localisatie.
- Nieuwe regressietests bewaken de kolomuitlijning, font-preview, werkmapbreedte, tooltips, combo styling en NL/EN locale-keys.

## 0.18.0 — UI-consistentie en editorinteractie

- Instellingen opnieuw opgebouwd als rustige tweekoloms settingspagina: naam en noodzakelijke uitleg links, bediening rechts.
- Verwante instellingen zijn gegroepeerd onder subtiele sectiekoppen; de vormgeving is vastgelegd in `UI_GUIDE.md` voor toekomstige schermen.
- Uiterlijk toont het lettertypevoorbeeld nu naast de fontkeuze, zodat de open dropdown de preview niet meer bedekt.
- Microcopy toegevoegd voor minder vanzelfsprekende opties, waaronder Automatisch opslaan (3 seconden na typen; Ctrl+S bij uitgeschakelde autosave), manuscriptinspringing, slimme quotes, opslag, AI en spelling.
- De Opslaan-knop van Instellingen is alleen actief wanneer formulierwaarden werkelijk afwijken van de laatst opgeslagen staat; na succesvol opslaan wordt de dirty-state gereset en blijft de bestaande `Opgeslagen`-feedback behouden.
- De zwevende selectie-toolbar is non-activating: hij accepteert geen keyboard focus en zijn knoppen hebben `NoFocus`, zodat geselecteerde tekst met Delete/Backspace/typen bewerkt kan blijven worden.
- Het normale Qt-rechtermuisknopmenu van de editor blijft intact en heeft nu aanvullend **Opmaak** met vet, cursief, onderstrepen, doorhalen, code en alineastijlen.
- Nieuwe regressietests bewaken de settings-row taal, font-previewplaatsing, dirty-state, non-activating toolbar en uitbreiding van het standaard contextmenu.

## 0.17.1 — Layout hardening op lage schermhoogte

- Structurele fix voor de Windows/Qt minimum-size bug: verborgen pagina's in stacks bepalen niet langer de minimumhoogte van het hoofdvenster.
- Nieuwe `CurrentPageStack` rapporteert uitsluitend de size hints van de zichtbare pagina; toegepast op hoofdmodus, Instellingen, Planning, personagecanvas, editorcontent en publicatie-editor.
- Instellingenpagina's gebruiken voortaan een echte scrollviewport; lange inhoud kan groeien zonder de vensterhoogte op te drijven.
- De vaste Opslaan-zone van Instellingen blijft buiten de scrollbare inhoud en dus bereikbaar op lage laptopschermen.
- Qt's native `saveGeometry()/restoreGeometry()` blijft leidend; er is geen custom clamp, handmatige `setGeometry()` of Windows-specifieke workaround meer.
- De standaard eerste venstergrootte is verlaagd naar 1280×720 zodat een verse start ook op compactere laptops binnen de werkruimte valt.
- Nieuwe regressietests bewaken zowel de stackarchitectuur als het gedrag waarbij een verborgen enorme pagina de minimumhoogte niet mag beïnvloeden.

## 0.17.0 — Meegeleverde schrijftypografie en Over

- Nieuwe fontcatalogus met vier aanbevolen schrijffamilies: Merriweather, Literata, Source Serif 4 en EB Garamond.
- QuietWriter registreert meegeleverde fontbestanden bij opstarten alleen binnen de applicatie; Windows-installatie is niet nodig.
- Instellingen → Uiterlijk groepeert de fontkeuze voortaan in **Aanbevolen** en **Systeemfonts** en toont elke familie maar één keer.
- Nieuwe live voorbeeldregel voor de gekozen schrijftypografie.
- Nieuwe **Over**-pagina onderaan Instellingen met versie-informatie, projectinformatie, maker Lucas Bonsel en fontlicenties.
- De vier gekozen fontfamilies zijn geverifieerd als SIL Open Font License 1.1; copyright- en licentieteksten staan per familie onder `resources/fonts/`.
- `font_manifest.json` legt familie, volgorde, bron en verwachte variable-fontbestanden vast.
- Bron/build-helper `tools/fetch_bundled_fonts.py` haalt exact de geverifieerde upstream binaries op voor packaging/source builds.

## 0.16.3

- Planning gebruikt nu één consistente paginataal: titel links en primaire actie rechts voor verzamelschermen.
- Personages heeft een volwaardige knop `Nieuw personage`; het losse plusje is verwijderd.
- De personagelijst behoudt zijn vaste breedte en gebruikt een subtiel micro-label onder de paginaheader.
- Notities gebruikt dezelfde marges en titelhiërarchie als Outline en Personages, terwijl de editor vrijwel de volledige inhoudsruimte houdt.
- Instellingen heeft alleen nog `Opslaan`; weg navigeren zonder opslaan is de natuurlijke annuleeractie en herstelt live previews.
- Design-audit uitgevoerd op de overige hoofdschermen: formulierpagina's houden hun onderaan geplaatste Opslaan-acties, collectiepagina's gebruiken acties in de header en de Boekenplank blijft bewust een afwijkende hero/startpagina.


## 0.16.2
- Inhoudsopgave opnieuw uitgelijnd; preview staat nu linksboven en de radiokeuze heeft duidelijke thema-eigen indicators.
- Voorwerk, Boek en Achterwerk zijn altijd zichtbaar in de manuscriptboom; Voorwerk/Achterwerk kunnen direct via “wijzig” worden geconfigureerd en behouden ook leeg hun uitklappijl.
- Instellingen verduidelijkt: “Terug zonder opslaan” vervangt de oude Annuleren-knop. Modelverversing schrijft geen instellingen meer stilletjes weg; alleen Opslaan commit de formulierwaarden.
- Opslaan in Instellingen synchroniseert QSettings expliciet en toont pas daarna tijdelijk een thema-eigen “Opgeslagen”-melding rechtsboven.

## 0.16.1 — Publicatiestructuur stabiliteit
- Opgelost: zero-argument `changed`-signalen in publicatieformulieren accepteren nu veilig payloads van Qt-signalen zoals `textEdited(str)`, `toggled(bool)` en `currentTextChanged(str)`.
- Opgelost: de Toevoegen-flyout bewaart geen verwijzing meer naar een door Qt verwijderde popup, waardoor herhaald openen niet meer kan eindigen in `Internal C++ object already deleted`.
- De manuscriptboom toont na activeren van Publicatiestructuur drie duidelijke, inklapbare zones: **Voorwerk**, **Boek** en **Achterwerk**.
- Voorwerk en Achterwerk hebben een rustige `wijzig`-actie waarmee de onderdelen opnieuw gekozen kunnen worden.
- Zonder geconfigureerde publicatiestructuur blijft de bestaande hoofdstuk-/sectieboom ongewijzigd.
- Nieuwe regressietests voor Qt-signaaladapters, popup-lifecycle en de drie manuscriptzones.

## 0.16.0 — Publicatiestructuur (MVP)
- Nieuwe publicatielaag die **Voorwerk → Manuscript → Achterwerk** als één boekstructuur behandelt.
- Via **+ Toevoegen → Publicatiestructuur** kies je met eenvoudige schakelaars welke onderdelen zichtbaar worden.
- Voorwerk: Titelpagina, Copyright, Opdracht, Epigraaf, Inhoudsopgave, Voorwoord en Inleiding.
- Achterwerk: Nawoord, Dankwoord en Over de auteur.
- Geselecteerde onderdelen verschijnen direct in de bestaande Inhoud-boom boven of onder de hoofdstukken.
- Drie expliciete contenttypen: vrije Markdowntekst, gestructureerde formulieren en gegenereerde onderdelen.
- Gestructureerde titelpagina met titel, subtitel, auteur/pseudoniem en uitgever/imprint.
- Gestructureerde copyrightpagina met editie, jaar, uitgever, ISBN-velden per formaat en optionele, vrij bewerkbare clausules.
- Inhoudsopgavegenerator met keuze tussen alleen hoofdstukken of hoofdstukken plus tussenkoppen, inclusief live voorbeeld.
- Vrije onderdelen gebruiken dezelfde rustige ManuscriptEditor maar blijven als losse Markdownbestanden opgeslagen.
- Publicatie-inhoud staat los van Planning en wordt opgeslagen onder `publication/`.
- Publicatiebestanden vallen onder dezelfde SHA-256 externe-wijzigingsbeveiliging en versiegeschiedenis als manuscript en planning.
- Versieherstel herstelt nu ook `planning/` en `publication/`, zodat een historische boekversie daadwerkelijk de bijbehorende ondersteunende boekdata terugzet.
- Exporttemplates/PDF/EPUB zijn bewust nog niet gebouwd; inhoud en semantiek zijn nu losgekoppeld van uiteindelijke vormgeving.
- Nieuwe tests voor publicatiemodellen, opslag, revision-conflicten en herstel uit versiegeschiedenis.

## 0.15.2
- Planning: de hoofdsubnavigatie en personagelijst hebben nu exact dezelfde vaste breedte.
- Personages: lege toestand gebruikt nu een echt blanco contentcanvas; het detailformulier verschijnt alleen bij Nieuw of selectie.
- Notities: gebruikt vrijwel de volledige beschikbare breedte en hoogte met kleine rustige marges.
- Windows: de custom geometry-clamp uit 0.13.5 is teruggedraaid; QuietWriter gebruikt voorlopig weer Qt saveGeometry/restoreGeometry totdat multi-monitor/DPI-gedrag apart is beoordeeld.


- Personages opent nu met een leeg contentvlak; het formulier verschijnt pas na Nieuw of selectie van een bestaand personage.
- Een nieuw personage is eerst een lokale draft en wordt pas bij Opslaan naar schijf geschreven.
- Na opslaan of verwijderen sluit de detailweergave weer naar het lege contentvlak.
- De personagelijst gebruikt een subtiele micro-label zodat subnavigatie en lijstinhoud visueel duidelijker gescheiden zijn.

## 0.15.0 — Boekplanning en ideeën (MVP)
- Nieuwe optionele **Planning**-modus in de hoofdrail, alleen zichtbaar wanneer een boek geopend is.
- Planning is modulair opgesplitst onder `quietwriter/ui/planning/`: shell, personages, outline en notities hebben elk een eigen scherm/module.
- Gestructureerde personageprofielen met vaste velden die later gericht als AI-context gebruikt kunnen worden: rol, beschrijving, persoonlijkheid, motivatie, doelen, angsten, waarden, conflicten, achtergrond, manier van spreken, gedrag onder druk en notities.
- Personagerelaties gebruiken stabiele IDs en ondersteunen bekende bidirectionele relatieparen; relaties zijn klikbaar en verwijderbaar.
- Nieuwe outline per bestaand hoofdstuk, plus **Losse ideeën**. Scènes bevatten titel, synopsis, personages, locatie, doel, conflict, uitkomst, status en notities.
- Scènes verwijzen naar stabiele `character_id`- en `chapter_id`-waarden, zodat hernoemen geen koppelingen breekt.
- Boeknotities gebruiken dezelfde `ManuscriptEditor` en blijven gewone Markdown (`planning/notes.md`).
- Planningdata staat bewust los van het manuscript in `planning/characters.json`, `planning/outline.json` en `planning/notes.md`.
- Planningbestanden vallen onder dezelfde SHA-256 revision/conflictbeveiliging als hoofdstukken en `book.json`.
- Versiegeschiedenis neemt de planning automatisch mee; lokale planning kan bij een conflict eveneens als herstelversie worden bewaard.
- Nieuwe storage-/architectuurtests voor personagevelden, relaties, scène-ID-koppelingen, Markdownnotities en externe wijzigingen.

## 0.14.0 — Veilige externe wijzigingen
- Nieuwe optimistic-concurrencylaag in `quietwriter/revisions.py`; geen lockfiles, sessieprotocol of Dropbox-specifieke code.
- Elk geopend boek krijgt in-memory revisions van `book.json` en alle hoofdstukbestanden op basis van bestandsgrootte + SHA-256. `mtime` wordt alleen diagnostisch bewaard en beslist nooit over een conflict.
- Vlak vóór iedere bewaakte schrijfactie controleert de storage-laag de volledige bekende boekstaat. Een externe wijziging wordt nooit stilletjes overschreven.
- Extern toegevoegde/verwijderde hoofdstukbestanden worden eveneens als wijziging gedetecteerd.
- Tijdelijke lees-/sync-locks zijn een aparte verificatiefout; autosave bewaart de tekst in geheugen en probeert later opnieuw in plaats van dit als inhoudsconflict te behandelen.
- Bij een echt conflict pauzeert autosave en kiest de gebruiker tussen **Mijn versie gebruiken** en **Versie op schijf gebruiken**.
- Beide conflictkeuzes maken vooraf automatisch een versie in de bestaande versiegeschiedenis (`conflict_external` of `conflict_local`).
- **Mijn versie gebruiken** laadt eerst de actuele schijfversie en legt alleen het huidige in-memory hoofdstuk daaroverheen, zodat andere externe wijzigingen behouden blijven.
- **Versie op schijf gebruiken** bewaart de lokale in-memory staat eerst als herstelversie en laadt daarna opnieuw van schijf.
- Structurele schrijfacties (manifest, hoofdstukken, secties, verplaatsen, verwijderen en herstel) gebruiken dezelfde revision-guard.
- Nieuwe regressietests voor happy path, externe hoofdstuk-/manifestwijzigingen, identieke inhoud met andere mtime, extern toegevoegde bestanden, pre-mutation guards en lokale recovery snapshots.


## 0.13.5
- Venstergeometrie wordt nu als expliciete normale `QRect` opgeslagen in plaats van via Qt's opaque `saveGeometry()`-blob.
- Opstarten op een andere computer, monitor, resolutie of DPI valideert en begrenst de opgeslagen positie en afmetingen vóór het native Windows-venster wordt aangepast.
- Een venster dat buiten alle huidige schermen valt, verhuist veilig naar het primaire scherm.
- Gemaximaliseerde status wordt los van de normale venstergeometrie bewaard.
- De oude `geometry`-instelling wordt bewust niet meer hersteld; daarmee kan een ongeldige oude geometry geen Windows `setGeometry`-waarschuwing meer veroorzaken.

## 0.13.4 — Opmaakstabiliteit en Windows font-rendering
- Scènebreuken (`***`) zijn nu beschermd tegen alle inline- en blokopmaakacties.
- Andere inline stijlen worden nooit meer in een backtick-codespan geïnjecteerd; code blijft letterlijk en ongewijzigd.
- De gedeelde `is_scene_break_line()`-helper voorkomt dat editorweergave en Markdowntransformaties verschillende definities gebruiken.
- Dode/verwarrende triple-star-parserlogica is vereenvoudigd.
- De verborgen-markertekst gebruikt niet langer een extreem 0,1-punts font of `fontStretch(1)`. Dit vermijdt een waarschijnlijke DirectWrite-trigger achter `QWindowsFontEngineDirectWrite::addGlyphsToPath: GetGlyphRunOutline failed` op Windows.
- Nieuwe gedrags-tests voor scene-break-integriteit, code-span-bescherming, multi-line style state, toolbar-state, undo en Qt runtime-opmaak.

## 0.13.3 — Samengestelde opmaak en toolbar-status
- Inline opmaak wordt nu samengesteld in plaats van elkaar te overschrijven: vet, cursief, onderstrepen, doorhalen en code kunnen betrouwbaar gecombineerd worden.
- De selectie-toolbar toont actief welke stijlen op de volledige selectie van toepassing zijn.
- Een gemengde selectie (bijvoorbeeld enkele cursieve woorden in gewone tekst) kan met één klik volledig cursief worden gemaakt en met een tweede klik volledig naar normaal worden teruggezet.
- Markdown-markeringen worden semantisch genormaliseerd bij toggelen, zodat combinaties zoals vet+cursief geen zichtbare of kapotte markers achterlaten.
- Nieuwe regressietests voor gecombineerde stijlen en gemengde selecties.


## 0.13.2
- Schrijfopmaak opnieuw opgebouwd als echte presentatie-laag boven platte Markdown.
- Markdownmarkeringen voor vet, cursief, onderstrepen, doorhalen, code, koppen, citaten en lijsten worden visueel ingeklapt in plaats van als witte tekens met normale breedte weergegeven.
- Dezelfde highlighter combineert manuscriptopmaak en spellingsonderstreping zodat beide stijlen elkaar niet overschrijven.
- Opsommingen, nummering en citaten krijgen een eigen visuele marker terwijl de Markdownbron intact blijft.
- Opmaaktoolbar heeft circa dubbel zo grote bedieningselementen en duidelijkere typografische iconen.

## 0.13.1 — PySide6 compatibiliteit

- Opgelost: startup-crash op sommige PySide6 6.x-versies bij `QTextBlockFormat.setLineHeight()`.
- De line-height modus wordt nu expliciet genormaliseerd naar de onderliggende integerwaarde en de hoogte naar `float`, conform de bindingsignature op oudere én nieuwere PySide6-versies.
- Geen functionele of visuele wijzigingen aan de manuscriptstijl.

## 0.13.0 — Schrijfopmaak en manuscriptstijl

- Nieuwe selectie-toolbar die na één seconde verschijnt bij geselecteerde tekst.
- Opmaakacties: normale alinea, tussenkop, opsomming, genummerde lijst, citaat, code, vet, cursief, onderstrepen en doorhalen.
- Opmaak blijft opgeslagen als leesbare Markdown/HTML-markup; de editor blijft een plain-text bron bewaren.
- Markdownmarkeringen worden in de schrijfruimte subtiel verborgen terwijl de opmaak visueel wordt weergegeven.
- Sneltoetsen voor vet (Ctrl+B), cursief (Ctrl+I), onderstrepen (Ctrl+U) en doorhalen (Ctrl+Shift+S).
- `***` blijft de bron voor scènebreuken, maar wordt visueel weergegeven als een rustige horizontale divider met drie punten.
- Manuscriptalinea's krijgen automatische eerste-regel-inspringing voor opeenvolgende alinea's; de eerste alinea, tekst na een lege regel, tussenkop, citaat of scènebreuk begint links.
- Nieuwe onafhankelijke manuscriptinstellingen: regelafstand, inspringing, ruimte na alinea en slimme typografische aanhalingstekens.
- Rechte dubbele quotes die tijdens typen worden ingevoerd kunnen automatisch als “slimme” quotes worden geplaatst.
- Opmaak- en manuscriptlogica is modulair opgesplitst in `manuscript_markup.py`, `manuscript_editor.py` en `selection_toolbar.py`.
- Extra regressietests voor Markdown-opmaak, lijsten, tussenkoppen, quotes en UI-architectuur.

## 0.12.1

Zie eerdere release voor de technische UI-refactor en reviewfixes.

## 0.28.0 — Integriteitscontrole, gericht herstel en migratiebasis

- Nieuwe read-only `BookIntegrityChecker` controleert `book.json`, hoofdstukstructuur/paden, UTF-8, Planning/Publicatie-JSON en AI-tekstbestanden zonder corrupte data stil als leeg te behandelen.
- Mediacontrole verifieert manifestvorm, veilige book-local paden, ontbrekende binaries en SHA-256-integriteit.
- Integriteitsproblemen hebben stabiele codes, severity en `recoverable`-metadata zodat een latere UI geen foutteksten hoeft te parsen.
- Gericht bestandsherstel kan een ontbrekend/beschadigd hoofdstuk of hulpbestand terughalen uit de nieuwste bruikbare History-kopie. Vóór iedere write ontstaat precies één volledige `pre_integrity_repair`-snapshot en de gewone external-change guard blijft gelden.
- `book.json` wordt bewust niet via gericht bestandsherstel vervangen: het manifest bepaalt de identiteit/structuur van het boek en vereist herstel op boekniveau.
- Nieuwe expliciete migratielaag met `CURRENT_BOOK_FORMAT = 2`, pure opeenvolgende migratiestappen, weigering van onbekende toekomstige formaten en behoud van onbekende velden.
- Migraties gebeuren niet stil bij openen. `Library.migrate_book_format()` maakt eerst een volledige `pre_migration`-snapshot en migreert daarna `book.json` atomisch.
- Failure-injectiontests dekken onder meer half JSON, ontbrekende hoofdstukken, corrupte hulpdata, mediachecks, onveilige paden, future-format refusal, migratiecheckpoint, herstelcheckpoint, externe wijzigingen en mislukte migratiewrites.
- Pakketversie verhoogd naar 0.28.0.
