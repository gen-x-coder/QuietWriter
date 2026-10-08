# QuietWriter 1.3 — Onderzoek gegevensmodel boekenplanken

## Instructie aan Claude

Lees dit document volledig voordat je een oordeel geeft.

Dit document bevat de huidige ontwerpkeuzes voor de boekenplanken in QuietWriter 1.3 en een technische vergelijking van verschillende manieren om de relatie tussen een boek en een plank op te slaan.

**Opdracht aan jou:**

1. Beoordeel de analyse hieronder onafhankelijk. Neem de conclusie van ChatGPT niet automatisch over.
2. Controleer de **werkelijke QuietWriter-code** en bestaande opslagformaten voordat je je definitieve advies geeft:
   - hoe een boek intern wordt geïdentificeerd;
   - waar boekmetadata wordt opgeslagen;
   - hoe de boekenplank/bibliotheek nu boeken ontdekt;
   - wat precies in een `.qwbook` terechtkomt;
   - hoe import, export, back-up en herstel momenteel werken;
   - of een geïmporteerd of gekopieerd boek zijn bestaande interne ID behoudt of een nieuwe krijgt.
3. Vergelijk minimaal deze drie modellen:
   - **A. `shelf_id` in het boek**
   - **B. `book_id`-lijsten in iedere plank**
   - **C. centrale bibliotheekmapping `book_id -> shelf_id`**
4. Let nadrukkelijk op:
   - QuietWriters ontwerpprincipe: **simpel en schrijven; geen bloat**;
   - één boek staat op **precies één plank**;
   - privacy zit op **plankniveau**, niet op boekniveau;
   - Demo-modus moet privéplanken en alle boeken daarop volledig kunnen verbergen;
   - een losse boekexport moet zo min mogelijk bibliotheek-/privacymetadata lekken;
   - fouttolerantie, corrupte metadata, herstel, migraties en orphaned references;
   - atomaire updates en kans op inconsistenties;
   - toekomstige onderhoudbaarheid;
   - backwards compatibility;
   - testbaarheid.
5. Geef daarna een eigen aanbeveling. Als je een ander model adviseert dan hieronder, leg concreet uit waarom.
6. Als de huidige codearchitectuur de conclusie verandert, beschrijf precies welke codefeiten daarvoor verantwoordelijk zijn.
7. Geef ten slotte een compact implementatievoorstel:
   - opslagstructuur;
   - invarianten;
   - gedrag bij import/export;
   - gedrag bij ontbrekende of corrupte shelf-metadata;
   - gedrag van Demo-modus;
   - minimaal noodzakelijke tests.

Dit is een **architectuurreview**, geen verzoek om direct code te wijzigen.

---

# 1. Huidige productkeuzes

Voor QuietWriter 1.3 willen we de bestaande boekenplank uitbreiden naar meerdere planken.

Het visuele ontwerp van Neo is het uitgangspunt: horizontale planken met boekcovers, rustig en direct bedienbaar.

De belangrijkste productkeuzes zijn inmiddels:

- ieder boek staat op **precies één plank**;
- geen tags of meerdere planken per boek;
- een plank heeft een vaste interne ID;
- de zichtbare planknaam mag worden hernoemd;
- klikken op de planknaam maakt inline hernoemen mogelijk;
- de relatie tussen boek en plank mag daarom nooit afhankelijk zijn van de planknaam;
- nieuwe boeken komen standaard op een plank **Werk in uitvoering**;
- deze standaardplank mag visueel worden hernoemd;
- privacy is een eigenschap van een **hele plank**;
- Demo-modus verbergt een privéplank inclusief alle boeken daarop;
- in Demo-modus mogen privéboeken ook niet via zoeken, recente boeken, statistieken, aantallen, covers of andere UI alsnog zichtbaar worden;
- privacy is bedoeld als presentatiemodus, niet als versleuteling of beveiliging tegen iemand met toegang tot het bestandssysteem.

Het eerdere idee van meerdere planken per boek is bewust geschrapt. Dat levert voor QuietWriter te weinig productwaarde op en introduceert extra complexiteit bij privacy, beheer en UI.

Ook een virtuele plank `Niet ingedeeld` willen we vermijden. Het uitgangspunt is dat ieder boek altijd aan één echte plank gekoppeld is.

---

# 2. De kernvraag

Waar slaan we de relatie tussen een boek en zijn plank op?

Er zijn twee voor de hand liggende modellen:

## Model A — shelf ID in het boek

Conceptueel:

```json
{
  "book_id": "book-123",
  "title": "Mijn roman",
  "shelf_id": "shelf-abc"
}
```

De plank zelf bevat alleen zijn eigen eigenschappen:

```json
{
  "id": "shelf-abc",
  "name": "Werk in uitvoering",
  "private": false,
  "order": 0
}
```

## Model B — book IDs in de plank

Conceptueel:

```json
{
  "id": "shelf-abc",
  "name": "Werk in uitvoering",
  "private": false,
  "order": 0,
  "book_ids": [
    "book-123",
    "book-456"
  ]
}
```

Het boek zelf weet dan niets over zijn plank.

Tijdens de analyse blijkt echter dat er nog een derde model relevant is.

## Model C — centrale bibliotheekmapping

De plank bevat geen lijst met boeken en het boek bevat geen shelf-ID.

De bibliotheek bewaart de relatie afzonderlijk:

```json
{
  "default_shelf_id": "shelf-wip",

  "shelves": [
    {
      "id": "shelf-wip",
      "name": "Werk in uitvoering",
      "private": false,
      "order": 0
    },
    {
      "id": "shelf-private",
      "name": "Privé",
      "private": true,
      "order": 1
    }
  ],

  "book_shelves": {
    "book-123": "shelf-wip",
    "book-456": "shelf-private"
  }
}
```

Dit derde model verdient serieuze aandacht omdat de planktoewijzing eigenlijk **bibliotheekmetadata** is en geen inhoudelijke eigenschap van het manuscript.

---

# 3. Model A — `shelf_id` in ieder boek

## Voordelen

### 3.1 Eén boek heeft vanzelf maximaal één plank

De datastructuur dwingt het gewenste model vrijwel automatisch af:

```text
book -> shelf_id
```

Er kan niet per ongeluk hetzelfde boek tegelijk in twee shelf-lijsten staan.

Dat past goed bij de productregel: **één boek, één plank**.

### 3.2 Een boek verplaatsen is een kleine wijziging

Verplaatsen betekent slechts:

```text
book.shelf_id = new_shelf_id
```

Er hoeven geen twee collecties synchroon te worden aangepast.

### 3.3 Hernoemen van planken is veilig

Omdat boeken naar een vaste shelf-ID verwijzen en niet naar de naam, kan:

```text
Werk in uitvoering
```

worden hernoemd naar:

```text
Mijn romans
```

zonder dat de boeken hoeven te worden aangepast.

### 3.4 Relatie blijft aanwezig als de centrale shelf-index beschadigd raakt

Als de plankdefinities tijdelijk verloren gaan maar de boeken intact zijn, bevatten de boeken nog steeds hun shelf-ID.

Bij herstel van de shelf-definities kunnen de relaties mogelijk automatisch terugkeren.

Dit beperkt de *blast radius* van een beschadigd centraal shelf-bestand.

### 3.5 Groeperen is eenvoudig

Bij het opbouwen van de boekenkast kan QuietWriter de boeken op `shelf_id` groeperen.

Voor de aantallen boeken waar QuietWriter mee werkt is het prestatieverschil met andere modellen praktisch irrelevant.

---

## Nadelen

### 3.6 Shelf-toewijzing wordt onderdeel van het boek

Dit is architectonisch het grootste nadeel.

De vraag is of:

> "Dit boek staat op plank X in mijn huidige QuietWriter-bibliotheek"

werkelijk een eigenschap van het **boek** is.

Waarschijnlijk niet.

Een plank is eerder vergelijkbaar met de lokale ordening van een bibliotheek. Als hetzelfde manuscript naar een andere computer of een andere gebruiker gaat, hoeft die ordening niet mee te reizen.

### 3.7 Losse boekexport wordt lastiger

Stel dat een `.qwbook` het volledige boek inclusief metadata bevat.

Als daarin ook staat:

```json
"shelf_id": "8ed34a..."
```

dan reist een lokale bibliotheekverwijzing mee.

Op een andere installatie bestaat die shelf-ID waarschijnlijk niet.

Er zijn dan drie mogelijkheden:

1. de shelf-ID toch exporteren;
2. hem tijdens export verwijderen;
3. naast het boek ook de plankmetadata exporteren.

Optie 1 creëert orphaned references.

Optie 3 maakt een losse boekexport onnodig afhankelijk van de lokale bibliotheek.

Optie 2 is waarschijnlijk de juiste keuze, maar betekent dat de serializer moet weten welke metadata lokaal is en welke werkelijk bij het boek hoort.

### 3.8 Privacymetadata kan onnodig meereizen

De shelf-ID zelf zegt niet direct dat een plank privé is, maar kan wel lokale informatie blootgeven of later gekoppeld worden aan bibliotheekmetadata.

Voor een overdraagbaar boekformaat is het netter als dit soort lokale organisatie-informatie helemaal niet in het boek zit.

### 3.9 Import moet shelf-ID normaliseren

Als een geëxporteerd boek toch een shelf-ID bevat, moet de importer bepalen wat daarmee gebeurt:

- bestaat deze plank lokaal?
- is dezelfde ID toevallig voor iets anders gebruikt?
- moet de plank worden aangemaakt?
- moet het boek naar `Werk in uitvoering`?
- mag een privéstatus impliciet worden overgenomen?

Dat is meer beleid dan we voor een simpele boekimport willen.

### 3.10 Plank verwijderen vraagt updates in meerdere boeken

Als plank `shelf-abc` wordt verwijderd en er staan twintig boeken op, moeten twintig boekrecords worden aangepast naar de standaardplank.

Dat is goed oplosbaar, maar het raakt meerdere afzonderlijke bestanden/records.

Als halverwege een schrijfactie of crash optreedt, kan een gedeeltelijke migratie ontstaan tenzij dit transactioneel wordt afgehandeld.

### 3.11 Bibliotheekorganisatie kan boekwijzigingen veroorzaken

Als shelf-ID deel is van de boekmetadata, wordt alleen het verplaatsen van een boek mogelijk al gezien als een wijziging aan het boek.

Afhankelijk van de huidige QuietWriter-opslag kan dit gevolgen hebben voor:

- autosave;
- wijzigingsdatums;
- revision history;
- checkpoints;
- synchronisatie;
- export "modified" status.

Dat moet expliciet in de echte code worden gecontroleerd.

---

# 4. Model B — `book_id`-lijsten in iedere plank

## Voordelen

### 4.1 Bibliotheekorganisatie blijft buiten het boek

Het boek weet niets van planken.

Een `.qwbook` kan daardoor exact hetzelfde boek zijn ongeacht hoe de gebruiker zijn lokale boekenkast heeft georganiseerd.

Dit geeft een nette scheiding:

```text
boek = manuscript en boekmetadata
bibliotheek = presentatie en ordening
```

### 4.2 Losse export is vanzelf schoon

Een boekexport hoeft geen shelf-ID te verwijderen, want de relatie staat niet in het boek.

Bij import kan het nieuwe of geïmporteerde boek simpelweg op `Werk in uitvoering` worden gezet.

### 4.3 Privacy zit precies waar zij conceptueel hoort

Als privacy een eigenschap van een plank is, is het logisch dat de plank ook weet welke boeken erbij horen:

```text
private shelf -> [book ids]
```

Demo-modus kan alle privéplanken overslaan.

### 4.4 Een complete plank kan eenvoudig worden verwerkt

Voor de UI is:

```json
{
  "shelf": "...",
  "book_ids": [...]
}
```

een directe representatie van wat er getoond moet worden.

### 4.5 Bibliotheekwijzigingen veranderen geen boekbestand

Een boek naar een andere plank verplaatsen hoeft het manuscript of de boekmetadata niet aan te raken.

Dat kan gunstig zijn voor revisions, autosave en exportstatus.

---

## Nadelen

### 4.6 Eén-boek-één-plank is niet structureel gegarandeerd

Met twee lijsten kan per ongeluk dit ontstaan:

```text
Shelf A: [book-123]
Shelf B: [book-123]
```

De datastructuur staat dit toe, terwijl het productmodel zegt dat het niet mag.

De applicatie moet dus altijd een invariant afdwingen:

> Iedere geldige book-ID komt exact één keer voor in alle shelf-lijsten samen.

Dat is extra foutgevoeligheid.

### 4.7 Verplaatsen is conceptueel een tweezijdige operatie

Een verplaatsing vereist:

1. book-ID uit oude plank verwijderen;
2. book-ID aan nieuwe plank toevoegen.

Bij een crash of fout tussen beide operaties kan het boek:

- op twee planken staan;
- of op geen enkele plank staan.

Als alle shelves in één klein JSON-bestand atomair worden opgeslagen is dit risico klein, maar de datastructuur zelf voorkomt het niet.

### 4.8 Verwijderde boeken kunnen stale references achterlaten

Als een boek uit de bibliotheek wordt verwijderd maar de shelf-lijst niet correct wordt bijgewerkt:

```text
shelf -> book ID die niet meer bestaat
```

De UI moet zulke verwijzingen kunnen detecteren en opruimen.

### 4.9 Nieuwe boeken kunnen "vergeten" worden

Als het aanmaken/importeren van een boek slaagt maar het toevoegen aan `Werk in uitvoering` niet, bestaat het boek wel maar staat het nergens.

Dat botst met de wens om geen `Niet ingedeeld`-concept te hebben.

### 4.10 Beschadiging van shelf-metadata raakt alle relaties

Als één centraal shelves-bestand alle `book_ids` bevat en dat bestand verloren gaat, is mogelijk de volledige indeling van de boekenkast verdwenen.

De boeken zelf blijven intact, maar hun planktoewijzing niet.

### 4.11 Privacy vraagt aandacht bij incomplete metadata

Stel dat een privéboek door corrupte metadata niet meer in de lijst van zijn privéplank staat.

Als QuietWriter niet fail-closed werkt, kan het in Demo-modus ineens via zoeken of "recent" zichtbaar worden.

Dat moet expliciet worden afgevangen.

---

# 5. Model C — centrale mapping `book_id -> shelf_id`

Dit model houdt de relatie op bibliotheekniveau, maar legt hem niet vast als lijsten in de afzonderlijke planken.

Conceptueel:

```json
"book_shelves": {
  "book-123": "shelf-a",
  "book-456": "shelf-b"
}
```

---

## Voordelen

### 5.1 Scheiding tussen boek en bibliotheek blijft intact

Net als bij Model B bevat een los boek geen lokale shelf-relatie.

Export en import blijven daardoor schoon.

### 5.2 Eén boek kan structureel maar één shelf-ID hebben

Een dictionary/mapping heeft per `book_id` precies één waarde:

```text
book_id -> shelf_id
```

Daarmee verdwijnt het belangrijkste nadeel van Model B.

Het is niet mogelijk dat `book-123` door de datastructuur zelf tegelijk naar twee planken wijst.

### 5.3 Verplaatsen is één wijziging

```python
book_shelves[book_id] = new_shelf_id
```

Geen remove-uit-A plus add-aan-B.

Dat is eenvoudiger en minder foutgevoelig.

### 5.4 Hernoemen raakt niets anders

De mapping werkt met vaste shelf-IDs.

De zichtbare naam is vrij wijzigbaar.

### 5.5 Export blijft eenvoudig

Een losse `.qwbook` hoeft geen shelf-data te bevatten.

Bij normale import:

```text
nieuw/geïmporteerd boek -> default_shelf_id
```

De gebruiker hoeft niets over shelves te weten tijdens import.

### 5.6 Privacy is centraal afleidbaar

Demo-modus kan eerst bepalen welke shelves privé zijn en daarna welke book-IDs daaraan gekoppeld zijn.

Conceptueel:

```python
private_shelf_ids = {
    shelf.id
    for shelf in shelves
    if shelf.private
}

hidden_book_ids = {
    book_id
    for book_id, shelf_id in book_shelves.items()
    if shelf_id in private_shelf_ids
}
```

Alle UI kan vervolgens één centrale zichtbaarheidservice gebruiken.

### 5.7 Plank verwijderen is overzichtelijk

Alle mappings met de te verwijderen shelf-ID worden in hetzelfde centrale model naar de default shelf gezet.

Als dit in één atomair opgeslagen library-bestand gebeurt, is de operatie goed beheersbaar.

### 5.8 De relatie is expliciet bibliotheekmetadata

Dit sluit semantisch goed aan op de betekenis:

> "In deze bibliotheek presenteer ik dit boek op deze plank."

Dat is iets anders dan:

> "Dit manuscript *is* een boek op plank X."

---

## Nadelen

### 5.9 Centrale metadata is een single point of failure

Als de mapping verloren gaat, is de indeling van alle boeken tegelijk verdwenen.

De manuscripten blijven intact, maar QuietWriter weet niet meer op welke plank ze stonden.

Daarom zijn noodzakelijk:

- atomaire writes;
- validatie;
- eventueel een eenvoudige backup van de shelf-configuratie;
- herstelgedrag bij corrupte metadata.

### 5.10 Book-ID moet werkelijk stabiel en uniek zijn

Dit model staat of valt met een betrouwbare `book_id`.

Dat moet in de huidige code worden gecontroleerd.

Belangrijke vragen:

- Heeft ieder QuietWriter-boek nu al een permanente UUID?
- Blijft die bestaan bij hernoemen/verplaatsen?
- Wat gebeurt er bij "Opslaan als", dupliceren of import?
- Kan een `.qwbook` met een al bestaande book-ID worden geïmporteerd?
- Wordt in zo'n geval een nieuwe lokale ID toegekend?

Als `book_id` nu niet goed gedefinieerd is, moet dat eerst worden opgelost.

### 5.11 Ontbrekende mapping vraagt een duidelijke regel

Er kunnen boeken bestaan waarvoor geen entry in `book_shelves` staat, bijvoorbeeld na:

- upgrade van 1.2 naar 1.3;
- handmatig kopiëren;
- beschadigde config;
- oude back-up;
- gedeeltelijke import.

In normale modus kan QuietWriter zulke boeken automatisch aan `default_shelf_id` koppelen.

Voor Demo-modus is dat gevoeliger; zie de privacyparagraaf.

---

# 6. Export en overdraagbaarheid

Dit onderdeel weegt relatief zwaar voor QuietWriter.

Een `.qwbook` is bedoeld om een boek als boek te kunnen meenemen. De fysieke of visuele plek van dat boek in één specifieke lokale bibliotheek hoort daar niet noodzakelijk bij.

Daarom is het nuttig onderscheid te maken tussen twee soorten informatie.

## Boekdata

Voorbeelden:

- manuscript;
- delen/hoofdstukken;
- planning;
- notities;
- personages;
- media;
- boekprofiel;
- andere metadata die inhoudelijk bij dat boek hoort.

Deze informatie moet met een `.qwbook` mee kunnen.

## Bibliotheekdata

Voorbeelden:

- op welke plank staat het boek;
- volgorde van planken;
- privacy van een plank;
- de huidige naam van een plank;
- eventueel visuele bibliotheekinstellingen.

Deze informatie behoort eerder bij de **installatie/bibliotheek**.

Daaruit volgt een belangrijk ontwerpprincipe:

> Een losse boekexport zou idealiter geen lokale shelf-toewijzing nodig hebben.

Model B en C voldoen hier vanzelf aan.

Model A kan dit ook, maar alleen als export bewust `shelf_id` uitsluit of vertaalt.

Dat maakt Model A niet fout, maar introduceert wel een verschil tussen:

```text
interne boekmetadata
```

en:

```text
exporteerbare boekmetadata
```

dat permanent onderhouden moet worden.

---

# 7. Volledige backup is iets anders dan boekexport

Het feit dat shelf-data niet in een losse `.qwbook` hoeft te zitten, betekent niet dat de indeling nooit geback-upt moet worden.

Er zijn twee verschillende use cases:

## Een boek meenemen

Verwachting:

> "Geef mij dit boek."

Dan is het logisch dat het op de nieuwe installatie op de standaardplank terechtkomt.

## De hele QuietWriter-bibliotheek herstellen

Verwachting:

> "Zet mijn complete omgeving terug zoals hij was."

Dan moeten juist wél mee:

- shelf-definities;
- namen;
- volgorde;
- privacyvlaggen;
- book-to-shelf relaties.

De architectuur moet deze twee scenario's niet door elkaar halen.

Een library-backup kan dus de centrale shelf-configuratie meenemen, terwijl een losse `.qwbook` dat niet doet.

---

# 8. Privacy en fail-safe gedrag

De privacyfunctie is presentatieprivacy, geen cryptografische beveiliging.

Toch moet de implementatie voorkomen dat een metadatafout juist in Demo-modus privéboeken zichtbaar maakt.

## Gewenste regel

In normale modus:

- een boek zonder geldige shelf-toewijzing mag worden hersteld naar de standaardplank;
- de gebruiker moet zijn boek altijd terug kunnen vinden.

In Demo-modus:

- zichtbaarheid moet **fail-closed** zijn.

Dat betekent bijvoorbeeld:

> Als QuietWriter niet met zekerheid kan vaststellen dat een boek op een zichtbare niet-privéplank hoort, toon het dan niet in Demo-modus.

Dit voorkomt dat een kapotte of ontbrekende mapping een oorspronkelijk privéboek per ongeluk openbaar maakt tijdens een schermdeling of demonstratie.

Dat principe geldt voor alle drie modellen.

Bij Model C is het bijvoorbeeld veiliger om Demo-modus zo op te bouwen:

```text
1. laad geldige shelves;
2. bepaal expliciet welke shelves publiek zijn;
3. neem alleen books mee waarvan een geldige mapping naar zo'n publieke shelf bestaat;
4. alle ontbrekende/orphaned/ongeldige mappings blijven in Demo-modus verborgen.
```

Normale modus kan ondertussen dezelfde problemen signaleren en repareren.

---

# 9. Standaardplank

De huidige keuze is:

**Werk in uitvoering**

Nieuwe boeken en gewone geïmporteerde boeken komen daar terecht.

Technisch is het beter om niet de naam speciaal te maken, maar een vaste `default_shelf_id` te bewaren.

Bijvoorbeeld:

```json
"default_shelf_id": "shelf-wip"
```

De gebruiker kan de zichtbare naam dan wijzigen:

```text
Werk in uitvoering
```

naar:

```text
Lopende projecten
```

zonder dat de betekenis als standaardplank verloren gaat.

Voor eenvoud is het waarschijnlijk verstandig dat er altijd precies één geldige default shelf bestaat.

Een mogelijke productregel is:

- de default shelf mag worden hernoemd;
- de default shelf kan niet worden verwijderd zolang hij default is;
- QuietWriter hoeft de gebruiker niet lastig te vallen met het concept "default shelf".

Dat kan intern gewoon een invariant blijven.

---

# 10. Verwijderen van een plank

Bij één boek per plank moet verwijderen voorspelbaar blijven.

Voorgesteld gedrag:

- lege plank: direct verwijderen;
- plank met boeken: QuietWriter vraagt wat er met de boeken moet gebeuren;
- eenvoudigste standaardactie: **verplaats boeken naar Werk in uitvoering/default shelf**;
- eventueel kan later "verplaats naar..." worden toegevoegd, maar alleen als daar werkelijk behoefte aan is.

Belangrijk: geen boeken verwijderen wanneer alleen een plank wordt verwijderd.

Voor Model C is dit één wijziging binnen de centrale mapping:

```text
alle mapping values == deleted_shelf_id
    -> default_shelf_id
```

---

# 11. Foutscenario's

## 11.1 Shelf bestaat niet meer

### Model A

Boek bevat een onbekende `shelf_id`.

Herstel:

- normale modus: naar default shelf;
- Demo-modus: eerst verborgen houden.

### Model B

Book-ID kan in een ontbrekende shelf niet voorkomen als het complete shelf-object weg is. De relatie is dan verloren.

Herstel:

- boeken die in geen enkele shelf-list voorkomen naar default;
- Demo-modus: niet automatisch zichtbaar maken totdat de toestand gevalideerd is.

### Model C

Mapping verwijst naar onbekende shelf-ID.

Herstel:

- normale modus: naar default;
- Demo-modus: fail-closed verbergen.

---

## 11.2 Boek bestaat niet meer

### Model A

Geen probleem voor shelves; het boekrecord zelf is weg.

### Model B

Stale `book_id` kan in shelf-list blijven staan.

Moet worden opgeschoond.

### Model C

Stale key kan in `book_shelves` blijven staan.

Moet worden opgeschoond.

Het verschil tussen B en C is hier klein.

---

## 11.3 Shelf-configuratie beschadigd

### Model A

Boeken bewaren hun eigen shelf-ID. Relaties kunnen mogelijk worden gereconstrueerd als shelf-definities worden hersteld.

### Model B

De shelf-toewijzingen zitten in dezelfde centrale data als de shelves. Bij totaal verlies zijn relaties weg.

### Model C

Zelfde risico als B als shelves en mapping in één bestand staan.

Dit is het sterkste argument vóór Model A.

Daar staat tegenover dat een klein centraal metadatarecord eenvoudig atomair en met backup/checkpoint kan worden opgeslagen, terwijl het veel complexer is om tientallen boekbestanden transactioneel aan te passen.

---

# 12. Migratie vanuit QuietWriter 1.2

Bij eerste start van 1.3 zullen bestaande boeken nog geen shelf-relatie hebben.

De migratie kan in alle modellen relatief eenvoudig zijn.

## Model A

Voor ieder bestaand boek:

```text
book.shelf_id = default_shelf_id
```

Dit betekent potentieel alle bestaande boekbestanden wijzigen.

Dat is een belangrijke overweging: een nieuwe bibliotheekfunctie veroorzaakt dan meteen writes naar ieder oud boek.

## Model B

Maak één standaardplank en vul zijn `book_ids` met alle bestaande boeken.

De boeken zelf blijven onaangeraakt.

## Model C

Maak één standaardplank en maak:

```text
book_id -> default_shelf_id
```

voor alle bestaande boeken.

Ook hier blijven de boeken zelf onaangeraakt.

Voor een veilige migratie heeft B of C daarom een duidelijk voordeel.

---

# 13. Performance

Voor de schaal van een desktop schrijfapp is performance waarschijnlijk geen beslissende factor.

Stel zelfs dat een gebruiker honderden boeken heeft:

- Model A: alle boeken groeperen op `shelf_id`;
- Model B: shelf heeft direct book-ID-lijst;
- Model C: mapping groeperen/inverteren per shelf.

Alle drie zijn triviaal snel.

We moeten dus niet kiezen op theoretische micro-optimalisaties.

Architectuur, eenvoud, exportgedrag en fouttolerantie zijn belangrijker.

---

# 14. Complexiteit in de code

## Model A

Eenvoudig bij:

- book -> shelf opzoeken;
- boek verplaatsen.

Complexer bij:

- shelf verwijderen;
- migratie;
- boekexport;
- scheiding tussen lokale en overdraagbare metadata.

## Model B

Eenvoudig bij:

- shelf -> boeken tonen;
- export van los boek.

Complexer bij:

- afdwingen dat boek exact één keer voorkomt;
- boek verplaatsen;
- detecteren van dubbele of ontbrekende entries.

## Model C

Eenvoudig bij:

- boek -> shelf;
- exact-één-shelf invariant;
- boek verplaatsen;
- export;
- migratie;
- scheiding library/book.

Iets extra werk bij:

- shelf -> alle boeken;
- centrale metadataherstel.

Maar `shelf -> books` is eenvoudig af te leiden en hoeft niet persistent dubbel opgeslagen te worden.

---

# 15. Geen dubbele waarheid opslaan

Een belangrijk algemeen principe is dat we niet zowel dit:

```text
book.shelf_id
```

als dit:

```text
shelf.book_ids
```

tegelijk persistent moeten bewaren.

Dat creëert twee bronnen van waarheid.

Dan kunnen inconsistenties ontstaan:

```text
book zegt Shelf A
Shelf A bevat book niet
Shelf B bevat book wel
```

Voor QuietWriter is dat onnodige complexiteit.

Er moet precies **één canonieke relatiebron** zijn.

Afgeleide indices mogen natuurlijk in memory of als rebuildable cache bestaan.

---

# 16. Voorlopige vergelijking

| Onderwerp | A: shelf_id in boek | B: book_ids in shelf | C: centrale mapping |
|---|---|---|---|
| Exact één plank afdwingen | Sterk | Zwakker | Sterk |
| Boek verplaatsen | Zeer simpel | Tweezijdig | Zeer simpel |
| Shelf hernoemen | Simpel | Simpel | Simpel |
| Los boek exporteren | Extra filtering nodig | Natuurlijk schoon | Natuurlijk schoon |
| Import naar nieuwe library | Shelf-ref afhandelen | Simpel | Simpel |
| Migratie 1.2 -> 1.3 | Wijzigt alle boeken | Alleen librarydata | Alleen librarydata |
| Plank verwijderen | Meerdere boeken wijzigen | Centraal | Centraal |
| Privacy op plankniveau | Goed | Zeer natuurlijk | Zeer natuurlijk |
| Risico dubbele planktoewijzing | Laag | Hoger | Laag |
| Centrale metadata als failure point | Lager | Hoger | Hoger |
| Scheiding boek/library | Minder zuiver | Goed | Zeer goed |
| Testbaarheid invarianten | Goed | Meer gevallen | Goed |
| QuietWriter-simpliciteit | Goed | Redelijk | Zeer goed |

---

# 17. Voorlopige conclusie van ChatGPT

**Op basis van het productmodel, zonder de huidige broncode opnieuw te inspecteren, lijkt Model C — een centrale `book_id -> shelf_id` mapping — de beste balans.**

Niet omdat Model A technisch onjuist is. Integendeel: `shelf_id` in het boek is een valide en eenvoudige relationele modellering.

De doorslaggevende argumenten voor QuietWriter zijn echter:

1. **Een plank is bibliotheekorganisatie, geen manuscriptinhoud.**
2. **Een losse boekexport moet niet hoeven weten van lokale planken.**
3. **Een migratie naar 1.3 hoeft bestaande boeken niet te wijzigen.**
4. **Eén mapping dwingt één shelf per boek vanzelf af.**
5. **Verplaatsen blijft een enkele wijziging.**
6. **Privacy blijft volledig op bibliotheek-/plankniveau.**
7. **We vermijden de dubbele-lijstproblemen van Model B.**
8. **Het past bij "simpel en schrijven": weinig speciale gevallen, weinig verborgen koppelingen.**

Daarom zou de voorlopige opslag ongeveer kunnen zijn:

```json
{
  "schema_version": 1,
  "default_shelf_id": "shelf-7b8...",

  "shelves": [
    {
      "id": "shelf-7b8...",
      "name": "Werk in uitvoering",
      "private": false,
      "order": 0
    }
  ],

  "book_shelves": {
    "book-a1": "shelf-7b8...",
    "book-b2": "shelf-7b8..."
  }
}
```

De exacte bestandslocatie en integratie moeten pas worden bepaald nadat de bestaande QuietWriter-code is bekeken.

---

# 18. Belangrijke voorwaarde bij Model C

**Controleer eerst of QuietWriter al een betrouwbare permanente `book_id` heeft.**

Als dat niet zo is, mag Model C niet klakkeloos worden ingevoerd.

Een stabiele identiteit moet:

- niet veranderen door een titelwijziging;
- niet veranderen door shelf-hernoemen;
- niet gebaseerd zijn op een pad of bestandsnaam;
- uniek zijn binnen één library;
- expliciet gedrag hebben bij dupliceren/importeren.

Als een geïmporteerd boek dezelfde ID kan hebben als een bestaand boek, moet import een nieuwe lokale ID kunnen genereren.

Een externe/originele ID kan desgewenst apart worden bewaard, maar mag niet dezelfde functie hebben als de lokale bibliotheek-ID.

---

# 19. Aanbevolen privacy-API

Welke persistente structuur ook gekozen wordt, verspreid privacyregels niet door de GUI.

Er moet één centrale laag zijn voor zichtbaarheid.

Conceptueel:

```python
visible_shelves(library, demo_mode)
visible_books(library, demo_mode)
```

of een equivalente service.

Belangrijk gedrag:

## Normale modus

- alle geldige shelves zichtbaar;
- private shelves zichtbaar, eventueel met subtiel slot;
- ontbrekende mapping kan naar default worden gerepareerd;
- orphaned metadata kan worden opgeschoond.

## Demo-modus

- alleen expliciet publieke shelves;
- alleen boeken met een geldige mapping naar een expliciet publieke shelf;
- private shelves volledig afwezig;
- private boeken niet in search/recent/statistieken;
- orphaned/ambigue boeken **niet tonen**.

Zo blijft privacy een centrale invariant in plaats van een verzameling losse UI-hacks.

---

# 20. Mogelijke minimale invarianten

Ongeacht implementatiedetails zouden minimaal deze regels gelden:

1. Iedere shelf heeft een unieke onveranderlijke ID.
2. Shelfnaam is alleen presentatie en mag wijzigen.
3. Er bestaat altijd één geldige `default_shelf_id`.
4. Ieder normaal zichtbaar boek hoort bij exact één geldige shelf.
5. Een boek kan nooit tegelijk bij twee shelves horen.
6. Shelf verwijderen verwijdert nooit boeken.
7. Losse boekexport hoeft geen lokale shelf-toewijzing te behouden.
8. Import van een los boek zet het boek standaard op de default shelf.
9. Demo-modus is fail-closed bij onduidelijke shelf-relaties.
10. UI-code beslist niet zelfstandig of een boek privé is; dat komt uit één centrale library/privacylaag.

---

# 21. Minimale tests die we verwachten

Claude: beoordeel of dit aansluit op de bestaande testsuite en voeg eventueel ontbrekende scenario's toe aan je advies.

## Shelf-model

- nieuwe library krijgt één default shelf;
- shelfnaam kan worden gewijzigd zonder relaties te breken;
- shelf-ID verandert niet bij rename;
- nieuw boek komt op default shelf;
- boek kan naar andere shelf;
- boek staat daarna niet meer op oude shelf;
- boek kan nooit op twee shelves tegelijk staan;
- shelf met boeken verwijderen verliest geen boeken;
- verwijderde shelf-ID blijft nergens actief achter.

## Import/export

- `.qwbook` export van een boek werkt onafhankelijk van shelf;
- import in andere library komt op lokale default shelf;
- import veroorzaakt geen verwijzing naar niet-bestaande shelf;
- dubbele book-ID wordt correct afgehandeld;
- full-library backup kan shelves en relaties wel herstellen.

## Migratie

- 1.2-library krijgt default shelf;
- alle bestaande boeken blijven beschikbaar;
- manuscriptdata wordt niet onnodig gewijzigd;
- migratie is idempotent;
- onderbroken/corrupte migratie is herstelbaar.

## Privacy

- publieke shelf zichtbaar in Demo-modus;
- private shelf niet zichtbaar;
- boeken op private shelf niet zichtbaar;
- private boek niet zichtbaar via search;
- private boek niet zichtbaar via recent;
- private boek telt niet mee in zichtbare statistiek/aantallen;
- ontbrekende of onbekende shelf-relatie wordt in Demo-modus niet zichtbaar;
- Demo-modus uit toont private shelf weer.

## Corruptie/herstel

- onbekende shelf-ID;
- onbekende book-ID;
- ontbrekende mapping;
- ontbrekende default shelf;
- dubbele shelf-ID;
- beschadigd shelf-configbestand;
- recovery beschadigt manuscriptbestanden niet.

---

# 22. Vraag die Claude expliciet moet beantwoorden

Na controle van de echte code willen we een duidelijk antwoord op:

> **Waar hoort de canonieke relatie tussen een QuietWriter-boek en één boekenplank te leven, en waarom?**

Kies bij voorkeur expliciet één van:

- **A — `shelf_id` in het boek**
- **B — `book_ids` in de shelf**
- **C — centrale `book_id -> shelf_id` mapping**
- **D — ander model**, alleen als de huidige QuietWriter-architectuur daar een aantoonbare reden voor geeft.

Geef daarna:

1. argumenten vóór;
2. argumenten tegen;
3. belangrijkste risico;
4. gedrag bij `.qwbook` export/import;
5. gedrag bij corrupte metadata;
6. benodigde migratie vanaf 1.2.32;
7. aanbevolen dataschema;
8. minimale codecomponenten die moeten wijzigen;
9. minimale tests;
10. eventuele release-blockers voordat `1.3.0-dev.1` gebouwd wordt.

**Geen codewijzigingen uitvoeren in deze review. Eerst het architectuurbesluit.**
