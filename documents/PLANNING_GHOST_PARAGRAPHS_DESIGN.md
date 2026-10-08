# QuietWriter 1.3 — Planning dichter bij het schrijven: spookalinea's

**Status:** fase 1 gebouwd in 1.3.0-dev.18.  
**Publieke release:** 1.2.32.  
**Architectuurregel:** Planninghulp is uitsluitend presentatie en wordt nooit manuscriptinhoud.

## Productdoel

Een schrijver moet bij een nog leeg hoofdstuk kunnen zien wat daar volgens Planning hoort te gebeuren, zonder tussen Planning en Schrijven te hoeven wisselen en zonder het manuscript te vervuilen.

De ghostlaag toont de scènes die in Planning aan het actieve hoofdstuk zijn gekoppeld. Per scène worden titel, synopsis, status, personages/locatie en indien ingevuld doel, conflict en uitkomst compact weergegeven. Planning-notities blijven uit de ghostlaag; daarvoor bestaat het volledige paneel **In dit hoofdstuk**. Sinds dev.22 maakt status juist de workflow zichtbaar: open scènes en geschreven scènes blijven herkenbaar zonder dat QuietWriter zelf probeert te bepalen of een scène klaar is.

## Wat we uit NEO meenemen

De openbare NEO-bron bevestigt drie nuttige ontwerpprincipes:

- ghost-inhoud telt niet als manuscriptwoorden;
- een ghost verdwijnt wanneer de schrijver echte tekst maakt;
- ghostgedrag hoort bij de presentatielaag en niet bij exportinhoud.

NEO laat ghosts dichter tegen de bewerkbare documentstructuur aan liggen en onderhoudt daarom extra logica voor beforeinput en undo/redo. QuietWriter kiest voor fase 1 een strengere scheiding: de Planningtekst komt helemaal niet in `QTextDocument`.

## Fase 1: leeg hoofdstuk

De editor schildert Planninghulp bovenop het viewport wanneer aan alle voorwaarden is voldaan:

1. er is een gewoon actief hoofdstuk;
2. het hoofdstuk bevat geen manuscripttekst;
3. opgeslagen Planning bevat ten minste één aan dit hoofdstuk gekoppelde scène;
4. de editor is niet in geschiedenispreview/corrupte alleen-lezenmodus;
5. **Instellingen > Uiterlijk > Planninghulp in editor** staat op **Tonen**.

De opgeslagen scènevolgorde is leidend. Als niet alles in het zichtbare editorvlak past, wordt compact aangegeven dat er meer scènes zijn. Het volledige overzicht blijft beschikbaar via **In dit hoofdstuk**.

## Harde veiligheidseisen

Planninghulp:

- komt nooit in Markdown;
- komt nooit in `QTextDocument`;
- telt niet mee in woordtelling;
- komt niet in zoekresultaten;
- wordt niet door spelling gecontroleerd;
- komt niet in export of `.qwbook`-manuscripttekst;
- komt niet in AI-manuscriptcontext;
- maakt geen Undo-stappen;
- verandert dirty/autosave-status niet.

De laag wordt uitsluitend met `QPainter` na de normale editorpaint getekend.

## Gedrag tijdens schrijven

Zodra het QTextDocument niet meer leeg is, wordt de ghostlaag niet meer getekend. De eerste echte letter laat de hulp dus verdwijnen zonder bronwijziging. Als de schrijver de tekst weer volledig verwijdert of via Undo terugkeert naar een leeg hoofdstuk, verschijnt de hulp opnieuw.

Dit is bewust anders dan tekst die "wordt overschreven": er bestaat niets om te verwijderen. De schrijver schrijft altijd in het echte lege manuscript.

## Planning wijzigen

Planning blijft de enige bron van de getoonde inhoud. Terugkeren vanuit Planning naar Schrijven vernieuwt de context direct. Gebroken personageverwijzingen worden, net als in het bestaande paneel **In dit hoofdstuk**, overgeslagen en niet gerepareerd door de editor.

## Instelling

**Planninghulp in editor:** Tonen / Verbergen. Standaard: Tonen.

De helptekst zegt expliciet dat de hulp niet in het manuscript terechtkomt, niet meetelt en niet wordt geëxporteerd. De instelling bevat geen manuscriptdata en kan op elk moment worden gewijzigd.

## Niet in fase 1

- ghosts tussen reeds geschreven scènes;
- automatische koppeling tussen scène n en scènebreuk n;
- ghosts als bewerkbare Planning;
- drag/drop of herschikken vanuit de editor;
- Planning-notities in de ghostlaag;
- persistente markers in Markdown.

## Mogelijke fase 2

Pas na praktijkgebruik onderzoeken:

- scène n koppelen aan tekstsegment n;
- nog niet geschreven scènes onder het laatste geschreven segment tonen;
- duidelijke degradatie wanneer het aantal scènebreuken en geplande scènes uiteenloopt.

Ook fase 2 moet presentation-only blijven.
