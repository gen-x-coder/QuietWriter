# QuietWriter — manuscriptsyntaxis

**Status:** levende specificatie; basissemantiek vastgelegd vanuit 1.2.13, escaping, centrale schrijfkant en neutrale importlaag toegevoegd in 1.2.19–1.2.22; geen stille migratie
**Datum:** 6 oktober 2026

## Doel

QuietWriter bewaart manuscripttekst als UTF-8 platte tekst met Markdownachtige opmaak. Het doel van deze specificatie is eerst exact vast te leggen wat QuietWriter vandaag betekent, zodat editor, export, zoeken, spelling, woordtelling en AI niet langer ieder hun eigen interpretatie bouwen.

Dit document is **geen nieuwe bestandsindeling** en verandert bestaande boeken niet.

## Hoofdprincipe

De schrijver schrijft proza, geen markup.

- Gewone invoer moet gewone tekst blijven.
- Opmaak ontstaat bij voorkeur door een expliciete actie, bijvoorbeeld Ctrl+I of de opmaakbalk.
- Technische syntaxis mag niet van de schrijver eisen dat die Markdown kent.
- Als een toekomstig QuietWriter-concept niet in gewone Markdown past, mag QuietWriter een kleine eigen syntax definiëren, maar alleen via deze specificatie en de centrale `DocumentView`.

## Relatie met Markdown

QuietWriter wil waar mogelijk **gangbare Markdownconventies** gebruiken in plaats van eigen varianten.

Huidige bekende conventies:

- `**vet**`
- `*cursief*`
- `` `code` ``
- `> citaat`
- `- lijst`
- `1. lijst`
- Markdownafbeeldingen

QuietWriter 1.2.13 is echter **geen volledige CommonMark-implementatie**. De belangrijkste bewuste/historische afwijking is dat één fysieke bronregel in de editor één manuscriptalinea is. CommonMark behandelt opeenvolgende regels vaak als één alinea zolang er geen lege regel tussen staat.

Daarom noemen we het formaat voorlopig **QuietWriter-tekst met Markdownconventies**. De `.md`-achtige openheid blijft een kernwaarde; compatibiliteit met willekeurige Markdownrenderers is geen garantie.

## Blocksemantiek in 1.2.13

Iedere fysieke bronregel is één block.

In deze volgorde wordt een regel geïnterpreteerd:

1. leeg;
2. scènebreuk: exact `***` na trimmen;
3. beheerde afbeelding;
4. tussenkop: `## `;
5. citaat: `> `;
6. bullet: `- ` of `* `;
7. genummerde lijst: `getal. `;
8. anders: gewone alinea.

Deze volgorde wordt gecentraliseerd in `quietwriter/document_view.py`.

## Inline semantiek in 1.2.13

Ondersteund:

- vet: `**...**`;
- cursief: `*...*`;
- vet+cursief: `***...***`;
- onderstrepen: `<u>...</u>` — legacy QuietWriter-extensie;
- doorhalen: `~~...~~` — gangbare Markdown-extensie;
- inline code: `` `...` ``.

Inline markers worden **per fysieke regel** gekoppeld. Een marker mag dus niet over twee alinea's heen opmaak openen/sluiten.

Een losse `*` is gewone tekst. Voorbeeld:

`de man tikte het telefoonnummer in *31623455`

bevat geen geldige cursieve span en moet letterlijk blijven.

## Historische ambiguïteit en escaping

In 1.2.13 bestond nog geen algemene escapingregel. Daardoor konden gewone prozaregels toevallig op markup lijken, bijvoorbeeld:

- `- Kom je mee?`
- `1944. Het was een koude winter.`
- `Prijs: 5*3 = 15 en 2*4 = 8.`
- `* * *`

In 1.2.13 kunnen zulke regels anders worden geïnterpreteerd dan de schrijver bedoelt.

Vanaf 1.2.19 wordt nieuwe gewone invoer daarom veilig als letterlijke schrijverstekst geserialiseerd. Vanaf 1.2.25 zijn escapes bovendien atomair in de editor en wordt ook na niet-expliciete bewerkingen bewaakt dat gewone tekst niet stil nieuwe structuur wordt. Bestaande hoofdstukken worden nog steeds niet automatisch herschreven; syntaxversiebeheer voor oudere boeken blijft een afzonderlijke vervolgstap.

## QuietWriter-specifieke syntax

Bestaand:

- Open-puntmarkers `<!--qw:todo:...-->...<!--/qw:todo-->`;
- afbeeldingslayout in `<!-- qw:image ... -->`;
- `<u>...</u>` voor onderstrepen.

Deze bestaande syntax blijft leesbaar. We breiden embedded HTML/comment-syntax voorlopig niet verder uit.

## Richting voor toekomstige syntax

Wanneer een nieuw concept nodig is:

1. kijk eerst of er een gangbare Markdown/Pandoc-conventie bestaat;
2. gebruik die wanneer ze goed bij QuietWriter past;
3. anders pas een kleine QuietWriter-extensie toe;
4. documenteer de syntaxis vóór implementatie;
5. voeg parsing toe aan `DocumentView`;
6. laat alle consumers dezelfde semantiek gebruiken;
7. zorg dat oudere QuietWriter-versies de bron ten minste verliesvrij als tekst kunnen laten staan of het boek expliciet blokkeren.

Mogelijke toekomstige onderwerpen, nog **niet besloten**:

- links;
- soft line breaks voor poëzie/brieven;
- eenvoudige tabellen;
- voetnoten;
- gecentreerde semantische blocks.

## Centrale schrijfkant

Vanaf 1.2.21 geldt dezelfde centralisatie ook voor bron die QuietWriter zelf genereert.

- schrijverstekst wordt eerst letterlijk/veilig gecodeerd;
- daarna wordt expliciete semantiek zoals vet, cursief, citaat of lijst toegevoegd;
- importers bouwen niet zelf verspreid Markdowntekens aan elkaar;
- inline-opmaak wordt per fysieke regel afgesloten en opnieuw geopend, omdat inline spans niet over manuscriptalinea’s heen lopen;
- structurele QuietWriter-elementen zoals een scènebreuk worden expliciet als structuur gegenereerd, niet afgeleid uit toevallig getypte tekst.

Dit geeft twee duidelijke grenzen: `DocumentView` is de gedeelde **leeskant**, de serializerhelpers in `manuscript_markup.py` zijn de gedeelde **schrijfkant**. De opslag blijft platte, leesbare tekst.

## DocumentView

`quietwriter/document_view.py` is de centrale, read-only interpretatielaag.

Eerste contract:

- bronbytes blijven autoritatief;
- geen serializer en geen automatische normalisatie;
- blocks hebben stabiele source ranges;
- inline spans hebben source ranges;
- semantische inline-runs leveren zichtbare tekst plus stijlsets aan renderers;
- technische hidden/protected ranges kunnen centraal worden aangeboden;
- ambiguïteiten kunnen als diagnostics worden gerapporteerd.

De overgang van bestaande consumers gebeurt gefaseerd. Een consumer wordt pas omgezet wanneer regressietests aantonen dat zijn bestaande zichtbare gedrag behouden blijft of een verschil expliciet is goedgekeurd.

## Niet doen in deze fase

- geen bestaande hoofdstukken herschrijven;
- geen CommonMarkbibliotheek als directe vervanging invoeren;
- geen HTML/JSON als manuscriptopslag;
- geen nieuwe syntax toevoegen alleen om de parser mooier te maken;
- geen verborgen migratie bij openen;
- geen `DocumentView`-serializer bouwen die bestaande bron normaliseert.


## Implementatiestatus

De eerste centralisatie is uitgevoerd voor:

- editor blockclassificatie;
- XHTML/EPUB blockclassificatie;
- PDF blockclassificatie;
- DOCX-export blockclassificatie;
- woordtelling.

Deze onderdelen, inclusief zoeken, spelling en AI-context, gebruiken nu dezelfde read-only `DocumentView`-definitie. Vanaf 1.2.25 gebruikt zoeken daarnaast een zichtbare projectie met bron-offsetmapping.

## Escaping vanaf 1.2.19

QuietWriter behandelt **direct getypte en gewoon geplakte inhoud als schrijverstekst**. Wanneer zo'n tekenreeks anders als manuscriptsyntax kan worden gelezen, bewaart QuietWriter een backslash-escape in de bron. De backslash is technische syntax en wordt in de editor/presentatie verborgen.

Voorbeelden van bron → zichtbare tekst:

- `\*31623455` → `*31623455`;
- `5\*3` → `5*3`;
- `\- Kom je mee?` → `- Kom je mee?`;
- `1944\. Het jaar` → `1944. Het jaar`;
- `\## letterlijk` → `## letterlijk`.

Expliciete formatteringsacties schrijven **on-escaped** syntax en behouden dus hun semantische betekenis. Daarmee is de regel voor de editor: gewone invoer is letterlijk; opmaak is een bewuste gebruikersactie.

Bestaande manuscripten worden niet gehercodeerd. Er is geen scan die oude hoofdstukken automatisch van escapes voorziet.

## Syntaxprofiel vanaf 1.2.27

Nieuwe boeken leggen de ondersteunde manuscriptsyntax expliciet vast in `book.json`:

```json
"manuscript_syntax": {
  "version": 2,
  "features": ["escape-v1", "soft-break-u2028"]
}
```

Ontbreekt dit veld, dan behandelt QuietWriter het boek als onversioneerd/legacy. Openen of normaal opslaan voegt het veld **niet** stil toe. Een toekomstige conversie van oudere boeken moet zichtbaar, herstelbaar en betekenisbehoudend zijn. Een onbekende nieuwere versie of featureflag wordt fail-closed geweigerd in plaats van stil geïnterpreteerd.

1.2.27 introduceert dus de capability-grens, niet de migratie zelf.

## Importgrens vanaf 1.2.22

Externe importers bouwen niet rechtstreeks QuietWriter-markup. Zij leveren eerst een neutraal `ImportDocument` met semantische blocks en inline-stijlen. De centrale serializer zet dit pas aan de opslaggrens om naar QuietWriter-tekst. Daarmee zijn extern formaat, documentbetekenis en persistente syntax drie afzonderlijke verantwoordelijkheden.


## Hardening na onafhankelijke review van 1.2.24

De onafhankelijke review van 1.2.24 bevestigde de keuze voor platte, Markdownachtige opslag als QuietWriter-profiel, maar vond dat escapes nog als losse editor-tekens behandeld werden. In 1.2.25 is daarom eerst de editorgrens gehard voordat nieuwe syntax wordt toegevoegd. Links en tabellen blijven uitgesteld totdat syntaxversiebeheer en de resterende hardening zijn afgerond.
