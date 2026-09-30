# QuietWriter UI-richtlijnen

QuietWriter moet tijdens het schrijven zo weinig mogelijk als een interface voelen. Nieuwe schermen gebruiken daarom dezelfde visuele grammatica in plaats van per functie een nieuw patroon te introduceren.

## Paginasoorten

### Overzicht
- Titel links, één primaire actie rechts.
- Lijsten en lege toestanden blijven rustig; geen formulier tonen zolang niets is gekozen.
- Voorbeelden: Personages, Outline.

### Instellingen
- Vaste subnavigatie links.
- Scrollbare inhoud rechts; de Opslaan-actie blijft buiten de scrollviewport.
- Instellingen staan in rijen met vaste onzichtbare kolommen: naam en noodzakelijke uitleg links, bediening rechts. De control-kolom begint op iedere rij exact op dezelfde positie.
- Boekniveau-pagina's die een eigen concept introduceren tonen bovenaan een duidelijke paginatitel met één korte, rustige uitlegzin vóór de detailnavigatie of formulieren. Planning, Boekgeheugen en Boekprofiel volgen hierin hetzelfde patroon.
- Verwante instellingen krijgen een kleine gedempte sectiekop.
- Uitleg alleen waar gedrag of gevolgen niet vanzelf spreken.
- Complexere controls mogen binnen de rechterkolom breder zijn; korte controls blijven compact.
- Preview-elementen horen naast hun keuze wanneer dat vergelijken makkelijker maakt, niet eronder als de dropdown ze afdekt.
- Opslaan is alleen actief wanneer waarden gewijzigd zijn.
- Schrijflettertype en manuscriptlayout worden in Instellingen niet live op de verborgen editor toegepast. De lokale preview blijft binnen het instellingenscherm; na Opslaan wordt de presentatie één keer toegepast en mag QuietWriter de presentatie-Undo-historie opschonen zodat font-, regelafstand- en inspringwijzigingen nooit als manuscriptbewerkingen verschijnen.
- Een feature-schakelaar verandert zichtbaarheid/activatie, nooit inhoud. Tijdelijk uitschakelen mag geen persona-, boekprofiel-, boekgeheugen-, spellings- of hersteldata verwijderen.
- **Geavanceerde opties** staat standaard aan. Een functie die hieronder wordt geplaatst is specialistisch maar niet minder veilig; verbergen mag nooit stille mutaties of een tweede gedragspad introduceren.

### Detail/formulier
- Vaste header, scrollbare inhoud, primaire actie onderaan wanneer commit nodig is.
- Voorbeelden: Boekdetails, gestructureerde publicatiepagina's.

### Document
- Inhoud domineert; zo weinig mogelijk chrome.
- Voorbeelden: manuscript, boeknotities, vrije publicatietekst.

### Setup-flow
- Een tijdelijke keuze- of configuratiestap mag Gereed/Annuleren gebruiken als beide acties betekenis hebben.

## Interactie

- Acties die vanuit het AI-gesprek lokale boekdata wijzigen (zoals **Onthouden**) geven hun geslaagde resultaat als subtiele QuietWriter-bevestiging in de chat zelf; gebruik hiervoor geen modale succesdialoog. Lokale bevestigingsregels worden niet als gesprekcontext terug naar het AI-model gestuurd.
- Selecteren van tekst mag toetsenbordbewerkingen nooit blokkeren.
- Zwevende hulpmiddelen mogen geen keyboard focus van de editor stelen.
- Het standaard contextmenu blijft beschikbaar en kan QuietWriter-acties aanvullen.
- Primaire, secundaire en destructieve acties gebruiken overal dezelfde button-stijlen.
- Flyouts en tijdelijke balken sluiten zodra hun context verdwijnt.
- Icon-only knoppen krijgen altijd een tooltip; minder vanzelfsprekende symbolen krijgen beschrijvende tekst in plaats van alleen een functienaam.
- Alle toetsenbordbereikbare interactieve controls hebben een zichtbare focus-state die niet uitsluitend op kleurtekst of hover leunt. Focus mag dezelfde semantische `focus`-token gebruiken, maar mag geen layoutverspringing veroorzaken.
- Hover bevestigt dat iets interactief is; pressed geeft een korte, duidelijk afwijkende state. Checked/selected blijft zichtbaar wanneer de muis weg is en blijft onderscheidbaar van focus.
- Cursorsemantiek volgt desktopconventies: gewone knoppen, menu's en selectierijen houden de pijl; bewerkbare tekst gebruikt de tekstcursor; alleen linkachtige/inline acties gebruiken de handcursor; sleepgrepen gebruiken open/gesloten hand; resize-handles gebruiken de bijbehorende resizecursor.
- Controls die bewust geen focus mogen stelen (zoals de zwevende selectie-toolbar en de hover-delete bij scènebreuken) blijven `NoFocus`; dit is een expliciete uitzondering, geen standaard voor icon-only acties.
- Tab en Shift+Tab volgen de visuele/logische leesvolgorde. Een flyout die met het toetsenbord wordt geopend geeft focus aan zijn eerste actie en kan met Escape gesloten worden; na sluiten keert focus terug naar de opener.
- Kleine editor-flyouts (zoals **+ Toevoegen**) gebruiken een subtiele 4px buitenradius en 4px actieknoppen; grotere 10–12px kaartafrondingen zijn gereserveerd voor echte contentkaarten/panelen.
- In de manuscriptruimte blijft de cursor expliciet een I-beam, ook wanneer een scènebreuk wordt gehoverd. Alleen de afzonderlijke hover-delete is een handactie.
- Tijdelijke rechterpanelen in de editor sluiten met Escape wanneer focus in het paneel staat; focus keert terug naar de railactie die het paneel opende.
- Een boom/lijst die primaire navigatie bevat moet ook zonder muis bruikbaar zijn: pijltjestoetsen verplaatsen selectie en Enter/Return activeert het geselecteerde inhoudsitem of toggelt een structurele groep wanneer openen niet van toepassing is.

## Responsive gedrag

- Beschikbare vensterruimte is leidend; content mag nooit het hoofdvenster groter afdwingen.
- Lange content zit in een scrollviewport.
- Verborgen pagina's mogen via stacks geen minimumafmetingen van het hoofdvenster bepalen.
- Controleer releases op lage laptophoogte en 100%, 125% en 150% schaal wanneer mogelijk.

## Boekenplank
- Op brede schermen gebruikt de boekenplank een gecentreerde contentas met een maximum breedte; lege ruimte wordt links en rechts gebalanceerd.
- Hero-inhoud, zoek/sorteerbediening en kaartgrid volgen dezelfde horizontale ankers.
- Boek- en nieuw-boekkaarten gebruiken exact dezelfde buitenmaat en een responsive grid; voeg geen decoratieve zijpanelen toe alleen om brede schermen te vullen.

### Navigatie- en opslagdetails
- In de Inhoud-boom vertegenwoordigt de geselecteerde rij de inhoud die werkelijk in het centrale werkvlak is geopend. Een sleepgreep of structurele kop (sectie, Voorwerk, Boek, Achterwerk) mag die selectie niet verplaatsen zolang de centrale tekstcontext niet verandert.
- Expliciete inline-acties zoals `wijzig` mogen wel naar een andere werkcontext navigeren en nemen dan de selectie/focus zichtbaar mee.
- Zoekresultaten zijn directe navigatiedoelen: één klik of Enter/Return opent de match en selecteert het gevonden bereik.
- Wanneer een documentachtig planningsscherm autosave gebruikt maar vergelijkbare schermen een zichtbare commitactie hebben, blijft een expliciete Opslaan-knop beschikbaar. De dirty-state bepaalt of die actie actief is; autosave blijft een vangnet en geen onzichtbaar afwijkend interactiepatroon.
- Applicatie-eigen dialoogknoppen (Ja/Nee, Opslaan/Annuleren) volgen de gekozen QuietWriter-locale en mogen niet terugvallen op de systeemtaal van Qt. Ook eenvoudige tekstprompts voor aanmaken/hernoemen gebruiken de gedeelde gelokaliseerde prompt in plaats van native OK/Cancel-labels.
- Documentachtige schermen met autosave die onderdeel zijn van een expliciete detailflow (zoals Notities en vrije publicatietekst) tonen daarnaast een zichtbare Opslaan-knop met dirty-state; na succesvol opslaan wordt die knop weer disabled.
- Niet-interactieve kaarten krijgen geen hover-background. Alleen de daadwerkelijke inline actie of knop communiceert klikbaarheid.
- Historie- en herstel-lijsten bieden Enter/Return als equivalent van hun primaire veilige muisactie. Destructieve acties worden nooit impliciet door list-activatie uitgevoerd.
- Een centrale same-book reload/conflictoplossing mag lokale, nog niet opgeslagen invoer in een **ander** formulier of planningdocument nooit stil vervangen. Alleen de conflicterende bron wordt autoritatief herladen; dirty invoer elders blijft staan of wordt veldgewijs gemerged met de nieuwe live state.
- Boekdetails gebruikt bij een externe same-book reload een drie-wegs merge per veld. Lokaal-only wijzigingen blijven in het formulier, disk-only wijzigingen volgen schijf en wanneer hetzelfde veld aan beide kanten verschillend is gewijzigd blijft de schijfwaarde live terwijl de volledige lokale formulierinvoer eerst apart in Versiegeschiedenis wordt bewaard. Een gekozen/verwijderde pending omslag blijft expliciet van de gebruiker totdat die Opslaan kiest.
- **AI-assistent gebruiken** is de centrale zichtbaarheidsschakelaar voor AI-gerelateerde oppervlakken. Uitgeschakeld verdwijnen AI-assistent, Schrijverspersona, Boekprofiel en Boekgeheugen uit de navigatie, maar hun bestanden en instellingen blijven bestaan.
- Wanneer een instelling de pagina verbergt waarvandaan Instellingen werd geopend, keert de gebruiker na Opslaan terug naar een geldige zichtbare bestemming (bij een open boek: Inhoud).
- Zichtbaarheidsschakelaars die direct begrijpelijk zijn (zoals AI en Geavanceerde opties) mogen hun navigatie-effect live voorvertonen terwijl Instellingen open is. Zonder Opslaan moet die preview bij het verlaten van Instellingen terugvallen op de laatst opgeslagen toestand; inhoud wordt nooit verwijderd.
- Spellingscontrole uit moet onmiddellijk zichtbaar zijn in het reeds geopende document: geen rode onderstrepingen en geen actieve spellingsbediening; een herstart of hoofdstukwissel mag nooit nodig zijn.
- Integriteit/herstel vermeldt bij een concrete herstelactie waar de geselecteerde herstelkopie vandaan komt wanneer die metadata bekend is; herstel mag niet als een onzichtbare “nieuwste versie” worden gepresenteerd.

## Schrijfweergave en font-rendering

- De editor en font-preview gebruiken dezelfde `WritingTypography`-route; een preview moet de werkelijke schrijfruimte representeren.
- Op Windows gebruikt de manuscriptruimte volledige hinting en grayscale-antialiasing (`NoSubpixelAntialias`) om gekleurde subpixelranden rond lichte tekst op donkere achtergronden te voorkomen. Dit is bewust beperkt tot de schrijf-/previewfonts; gewone applicatiechrome houdt de platformstandaard.
- Een themakleur mag nooit worden gebruikt om font-rendering te repareren. Scherpte/hinting en contrast zijn afzonderlijke verantwoordelijkheden.

## Thema's en contrast

- Thema's wijzigen uitsluitend semantische tokens; schermen en widgets bevatten geen thema-specifieke hardcoded kleuren.
- `accent_text` is de tekstkleur voor primaire/accentacties en staat los van `hero_text`. Dit is noodzakelijk bij donkere thema's met een relatief helder accent.
- Gewone en secundaire (`muted`) tekst halen minimaal 4,5:1 op `bg`, `panel`, `panel2` en `editor`. Primaire knoptekst, statuskleuren en hero/history-tekst halen eveneens minimaal 4,5:1 op hun vaste achtergrond.
- De zichtbare focusindicator haalt minimaal 3:1 ten opzichte van alle gangbare oppervlakken. Disabled states mogen bewust lager contrast hebben, omdat ze geen actieve bediening communiceren.
- QuietWriter biedt zowel neutrale lichte schema's als warme, koele en diep-donkere varianten. Warm/Papier blijven voor papierachtige voorkeuren; Porselein/Nevel/Salie/Lavendel/Nord Licht bieden lichte alternatieven zonder uitgesproken geelzweem.
- Nord Licht en Aurora zijn Nord-geïnspireerd; Aurora mag bewust kleurrijker zijn, maar blijft dezelfde contrast- en interactieregels volgen als de rustige thema's.


## Exporteren-pagina

- Exporteren is een zelfstandige boekpagina direct onder Boekdetails; Boekdetails beheert metadata/omslag, Exporteren beheert uitvoerformaten en renderinstellingen.
- Formaatkeuze staat bovenaan als drie kaarten: EPUB, PDF en Markdown. EPUB en PDF zijn volwaardige publicatieformaten; Markdown blijft technisch beschikbaar voor uitwisseling/back-up.
- De exportpagina verandert de publicatiestructuur nooit impliciet. De knop **Publicatiestructuur aanpassen** navigeert terug naar de bestaande setup.
- Preflight is inline feedback en gebruikt geen modale dialoog voor waarschuwingen. Alleen blokkerende runtimefouten/overschrijven vragen een dialoog.
- EPUB-instellingen blijven reflowable-readerinstellingen: template, omslag, omslagtekstmodus en sectietitels. PDF heeft apart vaste-pagina-instellingen: template, A5/A4, margepreset, paginanummers, rustige lopende kop en sectietitelpagina’s.
- Na EPUB-rendering valideert QuietWriter eerst het tijdelijke, daadwerkelijk verpakte archief: mimetype/container/package/manifest/spine/nav en alle door QuietWriter gegenereerde lokale links/resources moeten intern consistent zijn voordat het doelbestand atomisch wordt vervangen.
- `nav.xhtml` bevat naast de gewone EPUB-ToC een minimale landmarks-laag: `bodymatter` naar het eerste hoofdstuk en alleen bij een zichtbare Inhoud-pagina een `toc`-landmark. Landmarks blijven beperkt tot punten die een reader daadwerkelijk als snelnavigatie kan gebruiken.
- Omslagtekst kent bewust slechts twee modi: QuietWriter voegt titel/auteur toe aan tekstloos artwork, of QuietWriter gebruikt een reeds complete omslag. Geen coverdesigner.
- De exportmap is computergebonden en staat daarom in QSettings; per-boek renderkeuzes staan onder `export/settings.json`.
- Na succesvolle export blijft de gebruiker op dezelfde pagina en krijgt hij **Bestand openen** en **Map openen**; normale successen gebruiken geen QMessageBox.
- PDF rendert via `QTextDocument` + `QPdfWriter/QPainter`; geen externe PDF-library. Een geconfigureerde titelpagina krijgt geen running header of paginanummer; daarna begint de zichtbare nummering bij 1.
- PDF-afbeeldingen volgen de bestaande Klein/Middel/Groot/Volledig en Links/Midden/Rechts-intentie. Korte onderschriften mogen links/rechts mee floaten; een lang onderschrift schakelt in PDF automatisch de omloop uit om het in de Qt-spike gevonden overlap-randgeval te vermijden. Preflight meldt deze veilige fallback als waarschuwing.
- Markdown is een vast publicatieformaat, geen generieke export met toggles: de frontmatterheader is verplicht en heeft een stabiele veldvolgorde. Een hoofdstukkop/sectiemarker wordt alleen toegevoegd wanneer die structurele informatie bewaart.

## Startup en lokale cache

- Een niet-bereikbare werkmap wordt altijd zichtbaar gemeld; startup biedt een andere werkmap kiezen of afsluiten en mag niet eindigen in een stille crash.
- `.cache/` bevat uitsluitend afgeleide data. Corruptie of een tijdelijke cachefout mag nooit manuscript-, planning- of publicatiegegevens blokkeren of als bron van waarheid worden behandeld.
- Legacy globale boekomslagen worden alleen via expliciete `cover_file`-ownership gebruikt. Een slug/titel alleen is nooit voldoende om een globale omslag aan een boek toe te kennen of te verwijderen.

## Media en afbeeldingen (0.20.0)

- Afbeeldingen zijn **book-local content**, geen globale bibliotheekresource. Nieuwe media staan onder `assets/images/`; covers onder `assets/cover/`.
- De editorbron blijft platte Markdown. Een afbeelding is in de eerste versie altijd een eigen block tussen alinea's; geen floating layout of absolute positionering.
- Vervolgalinea-opmaak is onderdeel van de alinea zelf: Enter maakt het nieuwe block direct met de juiste inspringing. Een vertraagde presentatiepass mag nooit een apart Undo-item voor inspringing creëren.
- Wijzigingen aan schrijflettertype, tekstgrootte, regelafstand, inspringing of alinearuimte previewen alleen lokaal in Instellingen. Na **Opslaan** wordt de nieuwe presentatie direct op het reeds geopende manuscript toegepast; een hoofdstukwissel mag daarvoor niet nodig zijn. Een presentatiecommit mag geen misleidende font-/blokopmaakstappen in Ctrl+Z achterlaten.
- **Toevoegen → Afbeelding** gebruikt dezelfde rechterpaneelflow als Scènebreuk: preview, alt-tekst, optioneel onderschrift, Annuleren/Invoegen. De bronfile wordt pas bij Invoegen gekopieerd.
- Alt-tekst is toegankelijkheidsinformatie en wordt in EPUB op `<img alt>` gezet. Onderschrift is presentatie-inhoud en wordt `figcaption`.
- Afbeeldingslayout blijft bewust klein: **Klein/Middel/Groot/Volledige breedte**, **Links/Midden/Rechts** en één optie **Tekst om afbeelding laten lopen**. Omloop is alleen zinvol bij links/rechts en niet bij volledige breedte; de UI schakelt ongeldige combinaties uit.
- Nieuwe afbeeldingen starten als Groot + Midden. Oude afbeeldingsregels zonder QuietWriter-layoutmetadata blijven Full + Midden voor backward compatibility.
- Layoutmetadata staat als leesbare HTML-comment achter dezelfde Markdown-image-regel (`<!-- qw:image ... -->`). Het afbeeldingsbestand en de gewone Markdown blijven daarmee de bron; geen verborgen layoutdatabase.
- De editor visualiseert breedte/uitlijning via de beschermde imagekaart en noemt tekstomloop expliciet. Hij simuleert geen echte tekstomloop met een aparte custom-renderlaag; EPUB/PDF zijn leidend voor uiteindelijke zetting.
- EPUB gebruikt relatieve 30/50/70/100%-breedtes en CSS-floats voor eenvoudige omloop. Reader-degradatie moet altijd terugvallen op een bruikbaar afbeeldingsblok.
- De editor toont de Markdown-imagebron voorlopig alleen als subtiel gemarkeerd imageblok; een echte inline beeldpreview is bewust uitgesteld tot een aparte stabiliteitspass.
- UUID-assets zijn immutable. Een afbeeldingsverwijzing uit tekst verwijderen verwijdert het bestand niet automatisch. Historie gaat vóór agressieve cleanup.
- Exportpreflight moet ontbrekende of gewijzigde media als blokkerende fout tonen; een exporter mag nooit stil een ontbrekende afbeelding overslaan.


## Beschermde mediablokken

- Beheerde manuscriptmedia blijven standaard Markdown op schijf, maar interne assetpaden/UUID-syntaxis worden niet als gewone bewerkbare tekst aan schrijvers getoond.
- Een afbeelding is één atomair blok tussen alinea's. De visuele kaart reserveert echte documentruimte en mag omliggende tekst nooit overlappen.
- Klik op de kaart selecteert; alleen een expliciete **Bewerken**-actie of Enter op het geselecteerde blok opent de editor.
- Bewerken hergebruikt dezelfde invoegflow; verwijderen is expliciet bevestigd en verwijdert nooit automatisch het immutable assetbestand.
- Selecties of tekstbewerkingen mogen een beschermd mediablok niet stil openbreken. De Markdown-bron blijft de canonieke opslag- en exportrepresentatie.
- Zoeken/vervangen mag uitsluitend treffers aanbieden en muteren waarvan het volledige bronbereik buiten beschermde image-syntax valt. Maskering alleen is onvoldoende: ook een zoekterm met een begin- of eindspatie mag nooit een Markdown-delimiter, pad, quote of andere beheerde positie meenemen.



## AI-geheugenvoorstellen (0.23.3)

- AI mag `ai/memory.md` nooit autonoom wijzigen. Een model kan alleen een voorstel doen; opslag vereist altijd de expliciete gebruikersactie **Onthouden**.
- Een voorstel wordt buiten de gewone chattekst als compacte kaart getoond met **Onthouden · Bewerken · Negeren**. Technische markering/protocoltekst blijft volledig verborgen, ook tijdens streaming.
- **Bewerken** laat categorie en tekst aanpassen voordat het voorstel wordt opgeslagen.
- Geheugenvoorstellen zijn alleen bedoeld voor duurzame boekkennis: canon/feiten, boekspecifieke stijl, bewuste besluiten, terugkerende voorkeuren en open aandachtspunten. Planning-data wordt niet naar geheugen gekopieerd.
- Bij analyse, feedback, feitencontrole en herschrijven vergelijkt AI relevante Boekgeheugenregels actief met actuele manuscriptcontext. Een duidelijke contradictie wordt benoemd; actuele manuscripttekst heeft voorrang wanneer een verandering aantoonbaar in het verhaal staat.

## Gerichte Planning-context (0.23.4)

- Planning wordt nooit standaard volledig meegestuurd naar AI. De gebruiker kiest via **Planning-context…** expliciet welke personages, scènes en/of Planning-notities relevant zijn.
- De selectie is tijdelijk per geopend boek en wordt niet als verborgen instelling of tweede gegevensbron opgeslagen.
- Manuscript beschrijft wat daadwerkelijk geschreven is; Planning beschrijft wat bedoeld/gepland is; Boekgeheugen bevat blijvende afspraken/kennis. AI moet een verschil tussen deze bronnen zichtbaar benoemen en niet stil samenvoegen.
- Een geselecteerd personage mag relaties bij naam noemen om het profiel begrijpelijk te maken, maar niet-geselecteerde personages krijgen geen volledig profiel.
- Een geselecteerde scène bevat alleen de bestaande gestructureerde Planning-velden; QuietWriter dupliceert die informatie niet naar `memory.md`.
- Vanaf 0.34.4 toont het AI-contextblok daarnaast een **preview van de opgeslagen Planning van het actieve hoofdstuk**. Deze preview is transparantie, geen impliciete opt-in: zolang de UI expliciet **nog niet automatisch meegestuurd** meldt, mag deze hoofdstukplanning niet in `send()` of de systeemprompt terechtkomen.
- **Context bekijken** toont voor deze preview exact de tekst die later eventueel als context kan worden gebruikt. De preview moet dus uit dezelfde opgeslagen Planning worden opgebouwd als **In dit hoofdstuk**, niet uit onopgeslagen Planning-state.
- Beschikbaarheid/fouten zijn een expliciete status in het model en mogen niet worden afgeleid uit Nederlandse displaytekst. Dit is vereist voor toekomstige vertaling en voorkomt dubbele prefixen in contextmetadata.

## AI-snelacties (0.23.8)

- Snelacties zijn uitsluitend bewerkbare prompttemplates boven het gewone AI-invoerveld; een klik mag nooit automatisch een AI-aanvraag versturen.
- De eerste vaste set is **Feedback**, **Herschrijf selectie**, **Persona-check** en **Feitencheck**. Houd de set klein; voeg pas een nieuwe actie toe wanneer dezelfde opdracht aantoonbaar vaak terugkomt.
- **Herschrijf selectie** is alleen beschikbaar wanneer er werkelijk manuscripttekst geselecteerd is. De andere acties werken met de normale contextkeuze en eventuele geselecteerde tekst.
- Een snelactie mag bestaande contextlagen niet dupliceren of omzeilen: Schrijverspersona, Boekprofiel, Boekgeheugen en expliciet gekozen Planning-context blijven via dezelfde centrale promptopbouw lopen.
- Tijdens een lopende AI-aanvraag zijn snelacties disabled. Ze gebruiken compacte `suggestionButton`-stijl en blijven toetsenbordbereikbaar.

## Compacte AI-zijbalk en thinking (0.23.9)

- De chat is de primaire inhoud van het AI-paneel en krijgt zoveel mogelijk verticale ruimte. Alleen de paneeltitel en **Nieuw gesprek** blijven permanent boven de chat.
- **Huidig hoofdstuk** is de impliciete standaard voor manuscriptcontext en hoeft daarom niet voortdurend zichtbaar te zijn. De knop **Context** meldt alleen **Context · aangepast** wanneer Sectie/Hele boek of gerichte Planning-context actief is.
- Contextkeuze en Planning-selectie zitten in een inklapbaar contextblok onder de chat. **Context bekijken** is een tijdelijke inspectiedialoog en reserveert geen permanente zijbalkhoogte.
- Snelacties zitten eveneens in een inklapbaar blok onder de chat/composer. De instelling **Snelacties standaard uitklappen** bepaalt alleen de beginstand; de gebruiker kan het blok altijd zelf openen of sluiten.
- Context en Snelacties zijn wederzijds compact: wanneer één tijdelijk blok wordt geopend, sluit het andere.
- **Thinking uitschakelen** is providerregie, geen prompttekst. QuietWriter vraagt de provider expliciet om thinking/reasoning uit te zetten wanneer deze mogelijkheid wordt ondersteund; zonder deze instelling blijft het modelgedrag ongemoeid.
- Een provider die geen thinking-toggle ondersteunt mag hierdoor niet tot een alternatieve verborgen promptstrategie leiden. QuietWriter blijft transparant over de ingestelde requestoptie en laat het model/provider bepalen of die ondersteund wordt.

## Thinking-capabilities in modelkeuze (0.23.10)

- De modelcombo mag capability-informatie tonen zonder het echte provider-model-id te veranderen. **🧠** betekent: de provider meldt dat het model thinking/reasoning ondersteunt.
- Gedetailleerde provider-metadata blijft leidend voor de vraag of thinking aantoonbaar uitschakelbaar is. Als alleen een algemene thinking-capability bekend is, mag QuietWriter `think:false` aanvragen maar claimt de UI niet dat iedere modelvariant dit gegarandeerd honoreert.
- Geen icoon betekent niet automatisch dat een model nooit intern redeneert; het betekent alleen dat QuietWriter geen thinking/reasoning-capability heeft vastgesteld.
- Ollama-capabilities komen uit `/api/show`; OpenRouter-capabilities uit `supported_parameters`. QuietWriter raadt ondersteuning niet op basis van modelnamen.
- **Thinking uitschakelen** is alleen disabled wanneer metadata expliciet laat zien dat het geselecteerde model deze optie niet ondersteunt. Bij ontbrekende metadata blijft de control beschikbaar, omdat oudere providers/models capabilities mogelijk niet rapporteren.
- Helptekst rond thinking maakt geen universele kwaliteitsclaim: uitschakelen is vaak sneller/directer en kan bij creatief schrijven prettiger werken, maar het effect verschilt per model en taak.

## Tekstprompts voor hoofdstukken en secties

Tekstprompts voor hoofdstukken en secties gebruiken QuietWriter's eigen `prompt_text()`-dialoog en tonen altijd **Opslaan** en **Annuleren**. Gebruik hiervoor geen native `QInputDialog`, omdat de standaardknoppen op Windows niet betrouwbaar vooraf te lokaliseren zijn. Het hoofdstuk-contextmenu bevat Hernoemen, Dupliceren en Verwijderen; de losse verwijderactie in de werkbalk blijft als tweede ingang bestaan.
## Schrijverspersona (0.23.0)

- `persona/schrijver.md` blijft de bron van waarheid; de UI mag daar geen verborgen tweede datastructuur naast opslaan.
- De persona wordt in de app als profiel met vaste onderdelen gepresenteerd, vergelijkbaar met een personagedetailformulier, maar ieder onderdeel blijft vrije tekst.
- Voorbeeldpersona's zijn bewerkbare startpunten en worden nooit automatisch opgeslagen; de gebruiker bevestigt eerst de vervanging en kiest daarna zelf Opslaan.
- Bestaande vrije of onbekende Markdown-inhoud mag bij migratie nooit verdwijnen en valt terug op Aanvullende instructies.
- De locatie van het Markdownbestand is zichtbaar zodat transparant blijft dat het buiten QuietWriter leesbaar en bewerkbaar is.
- Een persona is globaal voor alle boeken. Boek-specifieke aanwijzingen horen in Boekprofiel/Boekgeheugen en worden niet in de schrijverspersona gemengd.
## Boekprofiel (0.23.1)

- `ai/boekprofiel.md` is per boek de enige bron van waarheid; er komt geen verborgen tweede opslaglaag naast.
- Het profiel gebruikt dezelfde begrijpelijke categorie-navigatie als de Schrijverspersona, maar bevat alleen project-specifieke keuzes en geen duplicaat van Planning/personagegegevens.
- Planning blijft de plek voor concrete personages, scènes en canonieke structuur. Boekprofiel beschrijft genre, doelgroep, premisse, vertelregels, sfeer, thema’s, settingregels, tempo, intensiteit en bewuste afwijkingen van de globale persona.
- AI ontvangt de globale schrijverspersona eerst en daarna het boekprofiel. Een expliciete projectspecifieke afwijking in Boekprofiel heeft voor dat boek voorrang.
- Het bestandspad blijft zichtbaar en de Markdown blijft buiten QuietWriter leesbaar/bewerkbaar.
- Bij same-book reloads blijven lokaal gewijzigde profielvelden behouden; onaangeraakte velden volgen de nieuwste schijfversie. Externe profielconflicten krijgen een expliciete keuze en herstelversie.

## Boekgeheugen (0.23.2)

- `ai/memory.md` is per boek de enige bron van waarheid; geen verborgen vectorstore of tweede geheugenopslag.
- Boekgeheugen gebruikt dezelfde rustige categorie-navigatie als Schrijverspersona en Boekprofiel, met vrije tekst onder vijf rubrieken: Canon & feiten, Stijl van dit boek, Besluiten, Terugkerende voorkeuren en Open aandachtspunten.
- Planning blijft de canonieke plek voor gestructureerde personages, scènes en outline. Boekgeheugen dupliceert die gegevens niet en benoemt dit expliciet in de UI.
- AI mag het geheugen in 0.23.2 uitsluitend lezen. Opslaan gebeurt alleen door een expliciete gebruikersactie op de Boekgeheugen-pagina.
- Het bestandspad blijft zichtbaar zodat duidelijk is dat het geheugen gewone Markdown is en buiten QuietWriter bewerkt kan worden.
- Same-book reloads behouden lokaal gewijzigde geheugenrubrieken en verversen alleen onaangeraakte rubrieken vanaf schijf. Een direct conflict op `memory.md` krijgt een expliciete keuze en herstelversie.
- In AI-context volgt Boekgeheugen na Schrijverspersona en Boekprofiel. De actuele manuscripttekst blijft autoritatief wanneer die aantoonbaar botst met een oudere geheugenregel.
### AI-context en geheugenvoorstellen
- Een AI-geheugenvoorstel is pas afgehandeld nadat QuietWriter de gebruiker zichtbare feedback heeft gegeven. Bij succes verdwijnt de voorstelkaart en meldt de statusbalk dat de regel in Boekgeheugen is opgeslagen; bij falen blijft de kaart staan met een concrete foutmelding.
- **Context bekijken** moet niet alleen contextlabels tonen maar ook de letterlijk geselecteerde Planning-context. De gebruiker moet kunnen controleren welke personages, scènes en notities naar het model worden gestuurd.
- Gerichte Planning-context is opt-in per boek en per selectie. Het model krijgt expliciet te horen dat deze selectie bewust voor de huidige vraag is gekozen; niet-geselecteerde Planning-data wordt niet stil toegevoegd.

### AI-geheugenacties

- Een expliciete **Onthouden**-actie schrijft de reeds door de gebruiker goedgekeurde geheugenstate. De opslagroute mag daarbij niet opnieuw een mogelijk stale zichtbaar Boekgeheugen-tekstveld over de programmatic wijziging heen kopiëren.
- Geslaagde opslag verwijdert de afgehandelde voorstelkaart en geeft zichtbare succesfeedback; mislukte opslag laat de kaart staan met concrete foutfeedback.

## Correctnessregels na code-review ronde 5 (0.25.1)

- PDF-layout bindt `QTextDocument` vóór HTML-parsing aan de `QPdfWriter`-paintdevice. Puntgroottes en paginageometrie moeten altijd in dezelfde DPI-context worden berekend.
- Een afbeelding en onderschrift vormen in PDF één keep-together-eenheid. QuietWriter controleert de werkelijke Qt-tabelgeometrie na layout en forceert zo nodig een pagina-einde vóór de tabel; CSS `page-break-inside` wordt niet als betrouwbaar beschouwd.
- Bij een Planning-conflict mag lokale pending invoer alleen automatisch worden teruggezet als het eigen backingbestand niet in de extern gewijzigde bestanden staat. Bij een dubbele wijziging blijft de diskversie live en wordt de lokale invoer apart herstelbaar in Versiegeschiedenis bewaard.
- Een geopend bestaand personageformulier telt net als een nieuw concept als pending state zodra de verzamelde velden afwijken van het opgeslagen personage.
- Vrije tekst in Schrijverspersona, Boekprofiel en Boekgeheugen mag `##`-tussenkoppen bevatten. QuietWriter ontsnapt zulke regels in de leesbare Markdownbron en verwijdert bij het inlezen precies één eigen escape. Ook een door de gebruiker letterlijk ingevoerde `\##` of meerdere voorafgaande backslashes blijft daardoor byte-voor-inhoud gelijk.
- Een dirty Schrijverspersona valt onder dezelfde navigatie-/afsluit-saveguard als de andere profielpagina's.
- Een grijze **Thinking uitschakelen**-optie betekent ook runtime-technisch dat QuietWriter geen disable-parameter meestuurt voor dat bekende provider/model.


## Same-field externe wijzigingen (0.25.2)

- Boekprofiel, Boekgeheugen en Boekdetails volgen dezelfde conflictregel als Planning: lokale-only invoer mag blijven staan, disk-only invoer wordt overgenomen en hetzelfde veld dat op beide plaatsen verschillend wijzigde wordt nooit stil lokaal over de schijfversie heen gezet.
- Bij zo'n dubbel gewijzigd veld blijft de schijfwaarde de live bron en wordt de volledige lokale formulierstate eerst als aparte `conflict_local`-versie in Versiegeschiedenis vastgelegd. De gebruiker krijgt daar zichtbare feedback over.
- Bij centrale live-bookadoptie gebeurt die merge- en recoveryvoorbereiding vóór de eerste zichtbare pagina wordt omgebonden. Een mislukte recovery-write mag dus nooit leiden tot een workspace waarin pagina's verschillende `Book`-objecten gebruiken; meldingen volgen pas nadat de adoptie volledig is gecommit.
- Capabilitymetadata voor **Thinking uitschakelen** is runtimecache, geen formulierinstelling. Metadata die al tijdens startup wordt opgehaald moet meteen bruikbaar zijn; een handmatige **Modellen ophalen**-actie mag geen voorwaarde zijn voor correcte requestparameters.
- PDF gebruikt de eigen body-marges en daarom `QTextDocument.documentMargin = 0`; een Qt-standaardmarge mag nooit een lege fysieke slotpagina veroorzaken.

## Media Manager (0.27.0)

- **Media** is een boekniveau-pagina binnen **HUIDIG BOEK**, tussen Planning en Boekdetails. De eerste versie is bewust tekstgericht: inventaris en integriteit zijn belangrijker dan een visuele galerij.
- De pagina toont de omslag alleen ter informatie. Omslag wijzigen/verwijderen blijft onderdeel van Boekdetails; inline-media-cleanup raakt covers nooit.
- Beheerde afbeeldingen krijgen één van vier statussen: Gebruikt, Ongebruikt, Ontbreekt of Gewijzigd. Niet-geregistreerde bestanden onder `assets/images/` zijn zichtbaar maar worden nooit automatisch verwijderd.
- Opruimen is batchgericht en herstelbaar: één expliciete actie verwijdert alleen bewezen ongebruikte manifestassets en maakt daarvoor eerst één volledig `media_cleanup`-herstelpunt in Versiegeschiedenis.
- Als één live Markdownbron niet betrouwbaar gelezen kan worden, wordt cleanup geheel geblokkeerd. Onzekerheid mag nooit als 'ongebruikt' worden geïnterpreteerd.
- Historische versies zijn zelfstandig: een live ongebruikte asset mag weg wanneer iedere oude versie die hem gebruikt een eigen kopie bezit. Als zo'n kopie ontbreekt wordt cleanup geweigerd, omdat een restore anders afhankelijk kan zijn van de nog aanwezige live UUID-binary.
- Een bestandslock ná de manifestcommit mag alleen een zichtbaar ongeregistreerd restbestand opleveren. De UI claimt dan niet dat de fysieke cleanup volledig klaar is.


## Media Manager correctness (0.27.1)

- Een hoofdstuk in de hoofdstukprullenbak is herstelbare inhoud en telt daarom als actuele mediagebruiker. Media toont zulke bronnen als **Prullenbak: <titel>**.
- Batch-opruimen werkt uitsluitend op de assets die de actuele inventaris als `can_cleanup` markeert. Historisch onveilige assets blijven staan zonder veilige kandidaten te blokkeren.
- Een externe wijziging tijdens cleanup wordt nooit omzeild. Met een schone editor wordt de nieuwste live-bookstate centraal geadopteerd; met pending manuscript/publicatie-invoer gaat de bestaande conflictflow vóór automatisch herladen.

### Instellingen-preview en editor-dirty
- Een live preview in Instellingen moet visueel volledig consistent zijn: knoppen, groepskoppen en spacing volgen dezelfde effectieve previewwaarden.
- Een preview mag geen inhoudelijke paneeltoestand vernietigen; pas een succesvolle Opslaan/commit mag een uitgeschakelde functie daadwerkelijk sluiten.
- Presentatiebewerkingen (highlighting, font/layout repaint, spellingmarkering) zijn geen manuscriptwijzigingen. Dirty/autosave mag alleen volgen uit gewijzigde brontekst.
- Mislukt het duurzaam opslaan van Instellingen, dan blijft de laatst betrouwbaar opgeslagen runtime-toestand actief.

### Tekstbron en presentatie

- Presentatiebewerkingen (syntax highlighting, spelling, typografie) mogen de manuscriptbron nooit als gewijzigd markeren.
- Dirty-status en opslag gebruiken dezelfde bronrepresentatie uit de editor. Vermijd `toPlainText()` voor persistente manuscripttekst wanneer dit typografische Unicode-tekens normaliseert.
- Typografische bronkarakters zoals harde spaties moeten bij een gewone save behouden blijven.

### Boeknavigatie en editorbron

- **HUIDIG BOEK** en alle boekniveau-knoppen zijn uitsluitend zichtbaar wanneer `MainWindow.active_book()` werkelijk een boek bevat. Koude start, loskoppelen en terugkeer naar de Boekenplank gebruiken dezelfde centrale zichtbaarheidstoestand.
- `ManuscriptEditor.source_text()` is de gedeelde persistente tekstbron voor manuscriptachtige editors. Dirty-baselines, conflict-snapshots en writes mogen niet elk een eigen Qt-tekstconversie gebruiken.
- Editors die alleen presentatie opnieuw toepassen (typografie, highlighting, spelling) mogen geen bestand materialiseren of autosave starten wanneer hun broninhoud niet veranderde.
- Bewerkingen die het volledige document opnieuw opbouwen gebruiken de persistente bronrepresentatie, zodat harde spaties en andere betekenisvolle Unicode buiten het bewerkte fragment intact blijven.

### Dirty-baseline voor teksteditors

- Iedere editor die Markdown of manuscriptachtige tekst kan opslaan gebruikt een baseline van dezelfde persistente bronrepresentatie als de save-route. Dit geldt voor hoofdstukken, Planning-notities en vrije publicatieteksten.
- Een presentatiepass (highlighting, spelling, typografie, repaint) mag `dirty` niet zetten wanneer de broninhoud gelijk blijft. Typen en daarna exact terugkeren naar de opgeslagen bron maakt de editor weer clean en stopt autosave.
- Na een geslaagde save wordt de baseline bijgewerkt; bij een disk-conflict of reload komt de baseline uit de daadwerkelijk geadopteerde tekst.

### Declaratieve linkerrail (0.33.0)

- De linkerrail heeft vier semantische groepen: **BIBLIOTHEEK**, **HUIDIG BOEK**, **AI-CONTEXT** en **PROGRAMMA**. Een groepskop is alleen zichtbaar wanneer de rail is uitgeklapt én minstens één item in die groep zichtbaar is.
- Railzichtbaarheid wordt volledig afgeleid uit één effectief toestandsmodel: open boek (runtime), AI aan/uit en Geavanceerde opties aan/uit (opgeslagen of tijdelijke Settings-preview). De renderer leest zelf geen `QSettings` en voert geen navigatieacties uit.
- De renderer mag uitsluitend tekenen/zichtbaarheid veranderen. Paneel sluiten, een verborgen actieve pagina verlaten en een Settings-terugkeerdoel aanpassen zijn commit-side-effects en gebeuren nooit tijdens een preview.
- Fallback bij een gecommitteerd verborgen navigatiedoel is centraal: **Inhoud** wanneer een boek open is, anders **Boekenplank**. Er mogen geen afzonderlijke fallbackregels per feature ontstaan.
- **AI-CONTEXT** betekent gegevens die AI voor het geopende boek kan gebruiken. Boekgeheugen en Boekprofiel horen hier; Schrijverspersona is globaal en staat onder **PROGRAMMA**.
- Een rail met alle functies zichtbaar moet bruikbaar blijven bij 700–768 px vensterhoogte. De navigatie mag scrollen; de inhoud van de rail mag de minimumhoogte van het hoofdvenster niet opdrijven. De scrollbar reserveert breedte binnen de bestaande rail zodat labels niet afbreken.
- Tests voor de rail halen hun verwachting niet uitsluitend uit hetzelfde model als de productcode. Naast modelinvarianten bestaan handmatig uitgeschreven referentietoestanden voor koude start, volledig boek en boek zonder AI/Geavanceerd.

### Railankers en compacte groepen (0.33.1)

- **Menu** blijft bovenaan vast; **PROGRAMMA** blijft onderaan vast. Alleen de boek- en AI-contextnavigatie ertussen mag verticaal scrollen.
- In uitgeklapte toestand zijn groepskoppen het primaire hiërarchische signaal. In ingeklapte toestand verdwijnen de koppen en worden zichtbare groepen gescheiden door een dunne, rustige lijn.
- Separators zijn afgeleid van dezelfde zichtbare groepen als de rail zelf: geen lijn voor een verborgen/lege groep en geen decoratieve lijnen zonder semantische grens.
- AI-contextuitleg moet overeenkomen met werkelijk requestgedrag. Als context standaard wordt meegestuurd, moet de UI dat zeggen; bij externe providers moet duidelijk zijn dat deze gegevens de computer verlaten.


## Rechterpaneel: In dit hoofdstuk
- **In dit hoofdstuk** is een editor-tool, geen permanente derde kolom en geen onderdeel van AI.
- Het paneel volgt hetzelfde open/dicht-gedrag als Zoeken, AI, Spelling en Versiegeschiedenis.
- De inhoud is alleen-lezen en beschrijft uitsluitend opgeslagen Planning. Bewerken gebeurt via **Planning openen**.
- Bij een niet-regulier hoofdstuk of onbetrouwbare bron verdwijnt de actie of verschijnt een korte rustige foutmelding; de editor zelf mag nooit worden geblokkeerd.
- Linkernavigatie heeft altijd precies één geselecteerd item. Verschillende layout-containers mogen nooit aparte selectie-eilanden vormen.


## Statusbalk en documenttellingen
- Boek- en hoofdstukwoordtelling horen op één vaste plek: de statusbalk.
- Bij een gewoon hoofdstuk: `Boek: x woorden · Hoofdstuk n van m: y woorden`.
- Geen duplicaat van de boektelling onder de hoofdstukboom.
- Tijdelijke meldingen mogen de documentstatus tijdelijk vervangen; daarna keert de telling terug.

## Nieuwere bronformaten
- Een bron die geldig is maar door een **nieuwere QuietWriter** is geschreven, is geen gewone corruptie.
- Zulke data blijft byte-identiek, alleen-lezen en mag nooit als herstelbaar naar een oudere versie worden aangeboden.
- De UI zegt expliciet dat QuietWriter moet worden bijgewerkt.


## Planning-veiligheid over alle routes (0.34.3)
- Een nieuwere Planning-versie mag niet alleen via Integriteit, maar via **geen enkele** herstel- of AI-route worden teruggezet of als gewone corruptie behandeld.
- History-herstel wordt volledig geweigerd zolang live Planning een nieuwer schema gebruikt; geen gedeeltelijke snapshotrestore.
- Als geselecteerde Planning-context niet betrouwbaar leesbaar is, gaat een AI-vraag zonder Planning-context door en toont de UI zichtbaar waarom die context ontbreekt.
- De Planning-contextdialoog mag een bestaande selectie niet stil leegmaken wanneer de bron tijdelijk onbeschikbaar is.

## Ingeklapte railgroepen
- Groepsseparators moeten subtiel maar daadwerkelijk waarneembaar zijn in lichte én donkere thema's. Vanaf 0.34.3 is de thematische separator 2 px hoog.
- Scènetitels en veldlabels in **In dit hoofdstuk** gebruiken geen automatische QLabel-inspringing; kop en waarde delen dezelfde linkerrand.


## Responsieve scheiding vast PROGRAMMA
- PROGRAMMA blijft een vast anker onderaan. In uitgeklapte toestand is de groepskop voldoende en staat er geen divider.
- In ingeklapte toestand is een divider vóór PROGRAMMA alleen nodig wanneer het scrollende middendeel daadwerkelijk overflow heeft; op ruime schermen blijft die extra lijn weg voor meer rust.
- De overige groepsseparators in het scrollende deel blijven zichtbaar volgens het railmodel.

## AI Planning-context: beschikbaarheid en fouttekst
- Een geladen boek maakt de handmatige **Planning-context…**-actie beschikbaar, ook tijdens de transactionele open/adopt-volgorde vóór `MainWindow.active_book()` definitief is gezet.
- Foutobjecten leveren een reden, geen samengestelde UI-labeltekst. De UI bepaalt zelf waar `Planning-context niet beschikbaar` of vergelijkbare contexttekst wordt geplaatst.
- Contextpreview mag visueel compact zijn; de daadwerkelijke prompttekst van expliciet geselecteerde Planning-context mag daardoor niet stil veranderen.


## AI-context: Planning van het huidige hoofdstuk
- Hoofdstukplanning wordt nooit stil meegestuurd: het AI-contextpaneel toont een expliciete schakelaar **Planning van dit hoofdstuk gebruiken**.
- De zichtbare status (`wordt meegestuurd` / `niet meegestuurd`) moet exact overeenkomen met het daadwerkelijke promptgedrag.
- **Context bekijken** toont dezelfde opgeslagen tekst die daadwerkelijk naar de provider gaat wanneer de schakelaar aan staat.
- Automatische hoofdstukplanning en handmatig geselecteerde **Planning-context…** zijn verschillende bronnen en blijven in de prompt afzonderlijk gelabeld.
- Bij corrupte, nieuwere of ontbrekende Planning wordt de hoofdstukschakelaar uitgeschakeld voor die toestand; de AI-vraag blijft bruikbaar zonder Planning.


### AI-context: nieuwe gegevenscategorieën
Nieuwe categorieën gegevens die naar een AI-provider kunnen worden gestuurd, worden niet stil bij bestaande gebruikers aangezet. De interface maakt zichtbaar wat wordt meegestuurd en biedt een expliciete keuze.


## AI-context: eerste toestemming

Nieuwe hoofdstukplanning wordt niet stil geactiveerd. Zolang `ai_use_chapter_planning` nog niet expliciet bestaat, blijft de schakelaar uit en staat er een rustige toelichting. De gebruiker kan **Begrepen** kiezen om bewust uit te blijven; daarmee wordt `False` opgeslagen en verdwijnt de melding. Aanvinken geldt eveneens als expliciete keuze.

## AI-context opt-inmelding (0.34.10)
- Houd privacyuitleg kort genoeg om het contextpaneel niet onnodig hoog te maken.
- Essentie: hoofdstukplanning is nieuw, staat standaard uit en kan bij een externe provider de computer verlaten.
- **Begrepen** bevestigt bewust uit blijven; de checkbox blijft de expliciete keuze om context wel mee te sturen.

