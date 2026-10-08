# QuietWriter — onderzoek intern boek- en manuscriptmodel

**Status:** onderzoeksdocument, nog geen architectuurbesluit  
**Baseline:** QuietWriter 1.2.13  
**Datum:** 6 oktober 2026  
**Doelgroep:** QuietWriter-ontwikkelaars en onafhankelijke reviewers, waaronder Claude

Dit document onderzoekt of QuietWriter op langere termijn Markdown moet blijven gebruiken als canonieke manuscriptopslag, of dat een ander model beter past bij een groeiende gebruikersgroep en rijkere boekfunctionaliteit.

Het document is bewust opgezet als **beslis- en reviewdocument**. De bedoeling is niet dat een reviewer de bestaande keuze verdedigt, maar dat aannames worden aangevallen en alternatieven aantoonbaar worden gewogen.

## 1. Onderzoeksvraag

> **Wat is voor QuietWriter op langere termijn het beste interne boek- en manuscriptmodel, nu er echte gebruikers, bestaande boeken, DOCX-import en steeds meer semantische functies zijn?**

Twee begrippen moeten uit elkaar blijven:

1. **persistente opslag op schijf**;
2. **intern documentmodel in geheugen**.

Deze hoeven niet hetzelfde formaat te hebben.

## 2. Scope en niet-doelen

### Wel onderzoeken
Romans en langere fictie, hoofdstukken/scènes, prozaalinea's, inline-opmaak, afbeeldingen, eenvoudige tabellen, Open punten/annotaties, toekomstige voetnoten/literaire typografie, DOCX-import, export, herstel, sync/conflicten, migratie, leesbaarheid buiten QuietWriter en performance.

### Geen DOCX-roundtrip
Een Word-document wordt bij import een QuietWriter-boek. Exacte Word-layout of identieke reconstructie is geen doel.

### Primaire DOCX-use case
Titel, hoofdstukken, alinea's, vet/cursief/onderstreping/doorhalen, scènebreuken, hyperlink, enkele afbeeldingen, eenvoudige tabellen, page breaks en eenvoudige front/back matter.

Complexe Word-features mogen buiten scope vallen mits dat expliciet wordt gemeld.

## 2.1 Semantiek is niet hetzelfde als layout

Onderscheid:

- **inhoudelijke semantiek**: alinea, hoofdstuk, scènebreuk, afbeelding, tabel, voetnoot, citaat;
- **inline betekenis**: nadruk, cursief, link, open punt;
- **publicatielayout**: marges, exacte positie, paginering, font, kolommen, zwevende objecten.

QuietWriter hoeft bij import vooral de eerste twee betrouwbaar te begrijpen.

## 3. Huidige QuietWriter-architectuur

### Manuscriptbron
QuietWriter gebruikt nu een bewust beperkte Markdownachtige syntaxis als canonieke manuscriptbron.

Relevante code:
- `quietwriter/manuscript_markup.py`
- `quietwriter/exporting/markup.py`
- `quietwriter/media/markup.py`

Ondersteund zijn onder andere vet, cursief, underline, strike, code, scènebreuken, blockquotes, lijsten en afbeeldingmarkup.

### Presentatie is niet de bron
Qt-presentatie mag manuscriptbytes niet stil wijzigen.

### Open punten
Open punten combineren een compacte marker in manuscripttekst met notities in `planning/open_points.json`. Dit toont zowel de kracht als de grens van Markdown + sidecars.

### Huidige DOCX-import
`quietwriter/docx_io.py` gebruikt `python-docx`.

De importer begrijpt onder meer:
- titel/auteur;
- documenttaal;
- Heading 1/2;
- QuietWriter Word-stijlen;
- page breaks;
- alinea's;
- bold/italic/underline/strike;
- codeherkenning;
- lijsten;
- quotes;
- hyperlinktekst;
- hard line breaks;
- style inheritance.

De importer normaliseert naar de huidige QuietWriter-Markdownsubset.

In 1.2.13 worden **tabellen en afbeeldingen nog niet geïmporteerd**; de gebruiker krijgt een waarschuwing.

### Export
Export heeft al een abstraherende laag (`exporting/models.py`, `builder.py`, DOCX/EPUB/PDF/Markdown exporters). Opslag- en uitvoerformaat hoeven dus niet gelijk te zijn.

## 4. DOCX-basis relevant voor QuietWriter

DOCX is een ZIP met OOXML en resources. Voor ons vooral:
- `word/document.xml`
- `word/styles.xml`
- relationships
- `word/media/`
- numbering/style-relaties

Conceptueel: paragraphs (`w:p`), runs (`w:r`), properties, tables (`w:tbl`), drawings/images, breaks en style inheritance.

We hoeven OOXML niet als opslagformaat te gebruiken om DOCX goed te importeren.

# 5. Open-source vergelijkingsonderzoek

## 5.1 NEO
Repo: `https://github.com/hughhowey/neo`

NEO bewaart boeken als gewone bestanden: `book.json` + `chapters/<id>.html` + sidecars en media.

Sterk:
- HTML draagt rijke semantiek natuurlijk;
- afbeeldingen, links en tabellen passen direct;
- plain files blijven inspecteerbaar.

Risico:
- minder prettig als ruwe tekst;
- DOM-normalisatie;
- rumoeriger diffs;
- Qt is geen browser-DOM.

NEO's DOCX-import is JavaScript/OOXML en normaliseert naar het eigen schrijfmodel.

## 5.2 novelWriter
Repo: `https://github.com/saga-soft/novelWriter`

novelWriter kiest bewust voor kleine leesbare tekstbestanden plus projectmetadata en rebuildbare caches. Het laat zien hoe ver plain text kan meegroeien, maar ook hoe een eigen markuptaal geleidelijk ontstaat.

## 5.3 Manuskript
Repo: `https://github.com/olivierkes/manuskript`

Manuskript besteedt veel formaatconversie uit aan Pandoc. Interessant als importcomponent, niet automatisch als opslagstrategie.

## 5.4 bibisco
Repo: `https://github.com/andreafeccomandi/bibisco`

Database-/JSON-gerichte projectstructuur. Rijke semantiek is eenvoudig, maar herstel/diff/sync buiten de app minder aantrekkelijk.

## 5.5 Quoll Writer
Repo: `https://github.com/garybentley/quollwriter`

H2-database + formeel objectmodel. Sterk in schema/relaties, maar hogere blast radius en lagere inspecteerbaarheid.

## 5.6 Aanvullende referentiepatronen

### Scrivener
Gebruik alleen als publiek formaat-/productpatroon, niet als broncodebewijs. Relevante les: veel afzonderlijke tekstdelen plus rijke metadata kan een boek robuust structureren.

### Obsidian
Local-first Markdown toont dat plain files zeer ver kunnen meegroeien, maar ook dat extensies een dialect kunnen creëren.

### ProseMirror/Tiptap als architectuurpatroon
Interessant als voorbeeld van een formeel intern DocumentModel/AST met parsers/serializers. Niet automatisch als technologie voor PySide6.

# 6. Architectuuropties

## Optie A — huidige Markdown behouden
Voordelen: minimaal migratierisico, leesbaar, goede diffs, sync/recovery eenvoudig.  
Nadelen: tabellen/media/annotaties vragen steeds meer eigen syntax en beschermingslogica.

## Optie B — QuietWriter Flavored Markdown (QWM)
Markdown gecontroleerd formaliseren tot een kleine, gedocumenteerde taal met:
- formaatversie;
- formele parser/tokenizer;
- canonical serializer;
- escapingregels;
- expliciete blocktypes;
- sidecars waar semantiek niet in proza hoort.

### Inline HTML binnen QWM
Kan handig zijn voor `<figure>`/`<table>`, maar brengt risico op:
- minder leesbare ruwe bestanden;
- tweede impliciet formaat via classes/attributes;
- sanitization/canonicalization;
- verschillen tussen Qt en export;
- structurele fouten door handmatige edits.

Claude moet custom QWM-blocks/sidecars versus embedded HTML expliciet vergelijken.

## Optie C — HTML per hoofdstuk + JSON-sidecars
Rijke documentstructuur en natuurlijke afbeelding/tabel/linksemantiek. Daartegenover staan mindere ruwe leesbaarheid, diffbaarheid en mogelijke DOM-normalisatie.

## Optie D — JSON/AST als canonieke bron
Zeer expliciet en valideerbaar, maar veel minder direct herstelbaar buiten QuietWriter en mogelijk strijdig met "lokaal en van jou".

## Optie E — formeel DocumentModel + open opslag
Editor/import/search/export werken op dezelfde semantische laag; opslag blijft apart te kiezen.

Dit kan de belangrijkste architectuurstap zijn zonder meteen bestaande bestanden te migreren.

# 7. DOCX-importmatrix

Test minimaal:
- eenvoudige roman;
- Heading 1;
- Heading 1+2;
- bold/italic/underline/strike;
- hard line break;
- scene break;
- page breaks;
- hyperlink;
- afbeelding;
- meerdere afbeeldingen;
- eenvoudige tabel;
- documenttaal;
- custom styles;
- unsupported features met duidelijke waarschuwingen.

Niet beoordelen op pixel-perfect layout.

### Tabellen en afbeeldingen
Niet automatisch flatten naar tekst als QuietWriter deze semantiek als eigen concept ondersteunt.

Onderzoek afbeelding als block met asset-id/alt/caption/breedteklasse/uitlijning en tabel als echte rows/cells-structuur.

# 8. Besliscriteria en weging

| Criterium | Gewicht |
|---|---:|
| dataveiligheid en herstel | 20 |
| veilige migratie bestaande gebruikers | 15 |
| DOCX-import normale romans | 15 |
| openheid / buiten QuietWriter leesbaar | 15 |
| filesync, conflicts en diffs | 10 |
| semantische uitbreidbaarheid | 10 |
| editorcomplexiteit/source fidelity | 5 |
| exportarchitectuur | 5 |
| performance grote boeken | 3 |
| implementatie/onderhoud | 2 |

Claude mag de weging aanpassen, maar moet dat motiveren.

# 9. Verplichte risicoanalyse

Voor ieder model:
1. schade bij corrupt hoofdstuk;
2. proza zonder QuietWriter terugvinden;
3. twee-computerconflicten;
4. write blast radius;
5. herschreven bytes bij kleine edit;
6. History-herstel;
7. future-format;
8. stille downgrade voorkomen;
9. transactionele migratie;
10. rollback naar 1.2.x;
11. rebuildbare caches;
12. sidecars als bron van waarheid.

# 10. Migratieprincipes

Een formaatwijziging vereist:
- herkenning oud formaat;
- volledige pre-migration checkpoint;
- conversie in tijdelijke locatie;
- validatie vóór commit;
- future-format blocking;
- begrijpelijke foutmelding;
- gedrag oudere versies;
- recovery zonder nieuwe versie.

Geen stille migratie tijdens gewone open-flow.

# 11. Hypothesen die moeten worden aangevallen

1. Database als manuscriptbron past waarschijnlijk slecht bij QuietWriter.
2. HTML is semantisch rijker maar mogelijk slechter voor diffs/recovery.
3. Een formeel DocumentModel kan meer opleveren dan direct opslag vervangen.
4. Semantic import + loss report is belangrijker dan Word-fidelity.
5. Markdown kan beste storage blijven als QW-syntax begrensd en formeel wordt.
6. Met een formeel DocumentModel kan de storagebeslissing later vallen.
7. Semantische fidelity is voor QuietWriter belangrijker dan layout fidelity.

# 12. Opdracht aan Claude / onafhankelijke reviewer

## Stap 1 — feiten verifiëren
Controleer storage, manuscript markup, DOCX, media, Open punten, History/revisions, exportmodel, search/spelling/word count.

## Stap 2 — externe projecten zelf onderzoeken
Minimaal NEO, novelWriter, Manuskript, bibisco en Quoll Writer. Voeg relevante open-sourceprojecten toe.

Maak onderscheid tussen broncodefeit, projectdocumentatie en inferentie.

## Stap 3 — DOCX voor QuietWriter-doelgroep beoordelen
Geen roundtrip-eis. Bepaal:
- noodzakelijke Word-constructies;
- wat `python-docx` goed kan;
- waar direct OOXML nodig is;
- of afbeeldingen/tabellen zonder storagewijziging kunnen;
- welke features alleen warning opleveren.

## Stap 4 — vijf opties vergelijken
A. huidige Markdown  
B. QWM, inclusief custom syntax versus embedded HTML  
C. HTML + sidecars  
D. JSON/AST  
E. DocumentModel + open storage

## Stap 5 — challenge de architectuur
Let op source offsets, Undo, sync, History, corruptie, future format, partial writes, performance, migratie, images/tables en hidden markers.

## Stap 6 — aanbeveling
Kies:
- Markdown behouden;
- Markdown gecontroleerd evolueren;
- storage vervangen;
- eerst intern model invoeren en storagebesluit uitstellen.

Geef argumentatie, risico's, prototype, niet-bouwen, migratie, testplan, DOCX-effect en effect op bestaande 1.2.x-boeken.

## Stap 7 — onzekerheden
Noem onbekende feiten, benodigde benchmarks/prototypes en vragen die alleen met echte gebruikersdocumenten beantwoord kunnen worden.

# 13. Beslissing nog niet genomen

Tot een expliciet architectuurbesluit:
- Markdown blijft canoniek;
- bestaande 1.2.x-boeken worden niet gemigreerd;
- geen concurrerend manuscriptformaat;
- importverbeteringen mogen storage niet impliciet wijzigen;
- dit document is onderzoek, geen refactortoestemming.
