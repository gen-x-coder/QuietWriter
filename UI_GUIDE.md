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
- Verwante instellingen krijgen een kleine gedempte sectiekop.
- Uitleg alleen waar gedrag of gevolgen niet vanzelf spreken.
- Complexere controls mogen binnen de rechterkolom breder zijn; korte controls blijven compact.
- Preview-elementen horen naast hun keuze wanneer dat vergelijken makkelijker maakt, niet eronder als de dropdown ze afdekt.
- Opslaan is alleen actief wanneer waarden gewijzigd zijn.
- Schrijflettertype en manuscriptlayout worden in Instellingen niet live op de verborgen editor toegepast. De lokale preview blijft binnen het instellingenscherm; na Opslaan wordt de presentatie één keer toegepast en mag QuietWriter de presentatie-Undo-historie opschonen zodat font-, regelafstand- en inspringwijzigingen nooit als manuscriptbewerkingen verschijnen.

### Detail/formulier
- Vaste header, scrollbare inhoud, primaire actie onderaan wanneer commit nodig is.
- Voorbeelden: Boekdetails, gestructureerde publicatiepagina's.

### Document
- Inhoud domineert; zo weinig mogelijk chrome.
- Voorbeelden: manuscript, boeknotities, vrije publicatietekst.

### Setup-flow
- Een tijdelijke keuze- of configuratiestap mag Gereed/Annuleren gebruiken als beide acties betekenis hebben.

## Interactie

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
- Boekdetails mergeert bij een externe same-book reload alleen schijfwaarden in velden die lokaal nog onaangeraakt zijn. Lokaal gewijzigde velden en een gekozen/verwijderde pending omslag blijven expliciet van de gebruiker totdat die Opslaan kiest.

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
- Formaatkeuze staat bovenaan als drie kaarten: EPUB, PDF en Markdown. Niet beschikbare formaten blijven zichtbaar maar disabled zodat de informatiestructuur stabiel blijft.
- De exportpagina verandert de publicatiestructuur nooit impliciet. De knop **Publicatiestructuur aanpassen** navigeert terug naar de bestaande setup.
- Preflight is inline feedback en gebruikt geen modale dialoog voor waarschuwingen. Alleen blokkerende runtimefouten/overschrijven vragen een dialoog.
- EPUB-instellingen zijn reflowable-readerinstellingen: template, omslag, omslagtekstmodus en sectietitels. Papierformaat/marges/paginanummers horen uitsluitend bij een toekomstige PDF-renderer.
- Omslagtekst kent bewust slechts twee modi: QuietWriter voegt titel/auteur toe aan tekstloos artwork, of QuietWriter gebruikt een reeds complete omslag. Geen coverdesigner.
- De exportmap is computergebonden en staat daarom in QSettings; per-boek renderkeuzes staan onder `export/settings.json`.
- Na succesvolle export blijft de gebruiker op dezelfde pagina en krijgt hij **Bestand openen** en **Map openen**; normale successen gebruiken geen QMessageBox.
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


## Tekstprompts voor hoofdstukken en secties

Tekstprompts voor hoofdstukken en secties gebruiken QuietWriter's eigen `prompt_text()`-dialoog en tonen altijd **Opslaan** en **Annuleren**. Gebruik hiervoor geen native `QInputDialog`, omdat de standaardknoppen op Windows niet betrouwbaar vooraf te lokaliseren zijn. Het hoofdstuk-contextmenu bevat Hernoemen, Dupliceren en Verwijderen; de losse verwijderactie in de werkbalk blijft als tweede ingang bestaan.
## Schrijverspersona (0.23.0)

- `persona/schrijver.md` blijft de bron van waarheid; de UI mag daar geen verborgen tweede datastructuur naast opslaan.
- De persona wordt in de app als profiel met vaste onderdelen gepresenteerd, vergelijkbaar met een personagedetailformulier, maar ieder onderdeel blijft vrije tekst.
- Voorbeeldpersona's zijn bewerkbare startpunten en worden nooit automatisch opgeslagen; de gebruiker bevestigt eerst de vervanging en kiest daarna zelf Opslaan.
- Bestaande vrije of onbekende Markdown-inhoud mag bij migratie nooit verdwijnen en valt terug op Aanvullende instructies.
- De locatie van het Markdownbestand is zichtbaar zodat transparant blijft dat het buiten QuietWriter leesbaar en bewerkbaar is.
- Een persona is globaal voor alle boeken. Boek-specifieke aanwijzingen horen later in Boekprofiel/Boekgeheugen en worden niet in de schrijverspersona gemengd.

