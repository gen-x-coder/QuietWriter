# QuietWriter: prioritering van het open werk

**Auteur:** Claude · **Datum:** 8 oktober 2026
**Basis:**
- `OPEN_WORK_OVERVIEW.md` (momentopname 1.3.0-dev.27);
- mijn reviews van dev.1 tot en met dev.27;
- `PRODUCT_AND_UI_PHILOSOPHY.md`.

---

## Hoe ik heb gewogen

Ik heb de volgorde van boven naar beneden zo afgewogen:

1. **Kan de schrijver tekst of werk kwijtraken?** Dan gaat het voor alles. "Lokaal en van jou" betekent ook: van jou
   blijft het.
2. **Is de kernhandeling "schrijven" betrouwbaar?** Typen, undo, kopiëren en plakken moeten zich gedragen zoals elke
   editor. Daar ontstaat vertrouwen in een schrijfapp, of het gaat daar verloren.
3. **Productwaarde voor de schrijver**, en dan bij voorkeur voortbouwend op wat net gebouwd is, zolang het nog vers is.
4. **Polish** bundelen in één build in plaats van er tien builds aan te besteden.
5. **Technische schuld** alleen oppakken als je er toch al in werkt (padvindersregel), of als hij iets uit de stappen
   hierboven raakt.

Een extra overweging: **1.2.32 staat nu publiek.** Echte gebruikers melden problemen, dus de mogelijkheid om bij support
te begrijpen wat er gebeurt, wordt meer waard.

---

## Prio 1: nu, in één kleine build (correctheid van de kernhandeling)

| # | Item | Waarom nu |
|---|---|---|
| 1a | **Intern kopiëren/plakken met een scènebreuk** | Dit is het enige open punt waarbij manuscriptinhoud **stil** verandert: scènebreuk en vet/cursief verdwijnen zonder melding, bij een handeling die een schrijver tientallen keren per dag doet. Minimaal: de interne invoeging moet scènebreuken op regelgrenzen toestaan. Lukt dat niet veilig, meld het dan in plaats van stil terug te vallen op platte tekst. |
| 1b | **Undo per teken: eerst 5 minuten op Windows testen** | Als het echt is, is het een kernirritatie: Ctrl+Z na een zin moet de zin terugdraaien, niet één letter. Als het een artefact van de testomgeving is, kan het punt dicht. Hoe dan ook goedkoop om te beslissen. |
| 1c | **Updatechecker: dev-versie tegenover de definitieve versie** | Moet sowieso vóór 1.3.0 gepubliceerd wordt. Anders horen dev-testers nooit dat 1.3.0 uit is. Het is een paar regels. |
| 1d | **Polishbundel** (alles klein, samen één build) | Zie hieronder. Elk los is triviaal; gebundeld kost het één reviewronde in plaats van zeven. |

Inhoud van de polishbundel (1d):
- "1 boeken" naar enkelvoud;
- tempo nooit "ongeveer 0 per dag";
- "Thinking" als label met de waarden "Modelstandaard / Uitgeschakeld";
- ongebruikte imports;
- de Planning-uitleg in lijn brengen met wat Planninghulp toont. Mijn keus: **toon geschreven scènes niet** in de
  ghostlaag. Een leeg hoofdstuk met al geschreven scènes is uitzonderlijk, en "open" is wat de schrijver nodig heeft;
- "… nog N meer": nooit een halve scène tekenen. Dat is eenvoudiger en eerlijker dan meetellen;
- lege flyout op inhoudshoogte;
- testopruiming: één autosave-fixture voor `~/.qttest` en de lege woordenboekmap.

**Omvang:** één dev-build. Dit is geen feature; het is het afmaken van wat er al is.

---

## Prio 2: volgende feature, automatische `.qwbook`-back-ups

**Waarom dit de eerstvolgende feature moet zijn:**
- **Het is het enige open item tegen het kwijtraken van werk.** De versiegeschiedenis staat in dezelfde werkmap, op
  dezelfde schijf en in dezelfde synchronisatie. Wordt de map gewist, beschadigd of door OneDrive verkeerd
  gesynchroniseerd, of gaat de laptop stuk, dan helpt die geschiedenis niet. Een back-up op een andere plek wel.
- **Het past precies bij de filosofie:** lokaal, transparant, geen cloud nodig, en de schrijver kiest de plek.
- **Het bouwt op iets dat al bestaat** (de `.qwbook`-export en -import, al geharde code) en is dus relatief klein.
- **De publieke release vergroot het belang:** nieuwe gebruikers vertrouwen er hun manuscript aan toe.

**Ontwerpvoorwaarden, zodat het geen tweede live bron wordt:**
- Een back-up wordt **alleen geschreven, nooit gelezen** door de normale app. Terugzetten gaat via de bestaande import,
  als **kopie** met een nieuwe identiteit of na een expliciete keuze. Nooit stil overschrijven.
- Standaardlocatie **buiten** de werkmap en buiten de synchronisatie.
- Back-up alleen als het boek sinds de vorige back-up veranderd is (hash of revisie). Geen nutteloze kopieën.
- Moment: bij het sluiten van een boek en hooguit één keer per dag. **Nooit tijdens het typen, nooit blokkerend.**
- Retentie, bijvoorbeeld 7 dagelijkse plus 4 wekelijkse. Ook opruimen gebeurt alleen binnen de eigen back-upmap.
- Mislukken is niet fataal: één rustige statusmelding, geen dialoog.
- Presentatiemodus maakt hier niets uit: het is bestandsbeheer, geen weergave.

**Werkwijze:** eerst een kort ontwerpdocument, zoals bij de schrijfdoelen. Dan bouwen en reviewen.

---

## Prio 3: Planning verder uitbouwen, stapsgewijs, en Diagnostiek

### 3a. Planning (in deze volgorde)

| Stap | Waarom |
|---|---|
| **Scènes verplaatsen en herschikken**, plus **compactere scènebewerking** | Dit is de grootste wrijving in de Planning-workflow die net gebouwd is. Wie scènes plant, schuift ze. De flyout, statusbadges en Planninghulp worden pas echt nuttig als de outline makkelijk te onderhouden is. |
| **Inklapbare hoofdstukgroepen** | Volgt logisch zodra outlines langer worden. Klein. |
| **Eerste verschijning van personages** | Leuk en nuttig, en read-only afleidbaar uit de koppelingen tussen scènes en hoofdstukken. Laag risico. |
| Locaties, relaties en aliassen | Pas op basis van echt gebruik; het risico op "planningsoftware in een schrijfapp" groeit hier snel. |
| **Planninghulp op echte scèneposities en scènebreuken** | **Bewust laatst.** Dit koppelt planningdata aan posities in de manuscripttekst. Dat is kwetsbaar (tekst verschuift, breuken worden verwijderd) en tast de schone presentation-only-grens aan die nu zo goed werkt. Alleen met een apart ontwerp, en alleen als de vraag er echt is. |

### 3b. Veilige diagnostiekweergave

- **Waarom hier:** met een publieke release komen er meldingen binnen. Een knop "Diagnostiek kopiëren" levert versie,
  profiel, platform, werkmapstatus, `library.json`-bron, de laatste crashlogregels en instellingen zonder geheimen. Dat
  scheelt bij elke supportvraag heen-en-weer, en het is klein.
- **Voorwaarden:** geen manuscripttekst en geen titels (privéplanken!), geen API-sleutels, en de gebruiker ziet altijd
  eerst wat er gekopieerd wordt.

---

## Prio 4: grotere inhoudelijke stappen (plannen, nog niet bouwen)

| Item | Waarom deze plek |
|---|---|
| **Export: echte preview en meer front/back matter** | Hoge waarde in de afrondfase van een boek, maar groot, en het raakt de hele exportketen. Neem bij dit werk ook mee: **wielbescherming op de Exportpagina** en **exportlabels leegmaken bij het sluiten van een boek**. Beide liggen in dezelfde code. |
| **AI Meelezer: contextbudget zichtbaar maken** als eerste stap | Past direct bij "AI-context moet begrijpelijk zijn". De schrijver hoort te zien wat er meegaat. Daarna Ollama-setup. Voorstellen voor feiten en Open punten en aliasherkenning pas daarna; dat zijn grotere ontwerpen die de Meelezer-grens raken. |
| **Boektypografie** (voetnoten, poëzie, centreren, kleinkapitalen) | **Hoogste risico van de hele lijst.** Het raakt de manuscriptsyntaxis, de migratie, het escapen, de export en de zoekprojectie: precies de lagen die in 1.2.2x met veel moeite zijn gehard. Alleen met een apart formaatontwerp en een concrete gebruiker die het nodig heeft. Voorlopig één element tegelijk, waarschijnlijk eerst harde spaties en centreren; voetnoten als laatste. |

---

## Prio 5: alleen bij aangetoonde behoefte

**Vervolg op schrijfdoelen:**
- recente activiteit;
- een daggrens;
- werkdagen;
- meerdere apparaten samenvoegen.

v1 is net uit. Wacht op echte gebruikers voordat je uitbreidt; anders bouw je het dashboard waar de filosofie voor
waarschuwt.

**Uitbreidingen van de Boekenkast:**
- "Nieuw boek" per plank;
- een covercache;
- flikkering wegwerken;
- virtualisatie.

Alle vier zijn al bewust voorwaardelijk gemaakt, en dat blijft goed.

---

## Technische schuld: niet als eigen sprint

| Item | Wanneer |
|---|---|
| Wielbescherming in Scène bewerken, Personages en Colofon | Bij Prio 3a (dezelfde formulieren). Export bij Prio 4. |
| Consistentie van formulieren en context-subnavigatie | Telkens als je een pagina toch aanraakt. |
| Achtergebleven exportlabels | Bij het exportwerk (Prio 4). |
| `WritingProgressStore` met twee processen; gedeelde `.tmp`-naam; weescaches uit dev.8; cache-items van verwijderde boeken | Backlog. Het effect is hooguit een verkeerde telling of een paar kilobytes. Oppakken als iemand er last van heeft, of samen in één robuustheidsbuild vóór een grote release. |
| Zeer late fout bij het sluiten van een boek | Backlog. De privacy is al afgedekt; het gaat alleen om interne consistentie bij een bug. |
| Windows-bestandsversie van dev-builds | Beslissen bij de release-build van 1.3.0 (5 minuten). Niet eerder nodig. |

---

## Samengevat

1. **Nu:** één kleine build met plakken van scènebreuken, de undo-check, de updatechecker en de polishbundel.
2. **Volgende feature:** automatische back-ups, eerst als ontwerpdocument.
3. **Daarna:** Planning stapsgewijs (scènes verplaatsen en compacte bewerking eerst), plus de kleine
   diagnostiekweergave.
4. **Later:** exportpreview, inzicht in het AI-contextbudget en typografie, elk met een eigen ontwerp.
5. **Pas bij vraag:** vervolg op schrijfdoelen en extra's voor de Boekenkast.

Technische schuld gaat mee als je in de buurt werkt, niet als doel op zich.

**Eén procesadvies:** de 1.3.0-lijn bevat nu Boekenkast, Presentatiemodus, schrijfdoelen en Planning dichter bij het
schrijven. Dat is veel nog niet gepubliceerde waarde. Overweeg na Prio 1, en eventueel na de back-ups, een vast moment
om 1.3.0 echt uit te brengen. Hoe langer de dev-lijn doorloopt, hoe groter het verschil met wat gebruikers hebben en
hoe zwaarder de uiteindelijke release-test.
