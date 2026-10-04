# QuietWriter — v2 fundamentonderzoek

Status: afgerond ontwerp-/auditdocument na 1.0.0-rc5

Dit document voert de twee voorbereidende onderzoeken uit die vóór de eerste echte v2-feature op de roadmap stonden:

1. conflict-audit: zijn lokale en externe versies overal veilig terug te vinden?
2. documentmodel/Markdown-verkenning: is de huidige parse-architectuur sterk genoeg voor Darlings, placeholders, ghost text, DOCX en latere markup-extensies?

Er is in deze stap bewust geen nieuwe gebruikersfunctionaliteit gebouwd.

---

## 1. Conflict-audit

### Conclusie

De kern van QuietWriter is al veel verder dan een simpele "mijn versie / schijfversie"-strategie. Voor de datastromen waar daadwerkelijk auteursinhoud of duurzame boekdata verloren zou kunnen gaan, is de lokale toestand vóór acceptatie van de schijfversie herstelbaar gemaakt via History, of wordt een drie-wegs merge gebruikt met een `conflict_local`-snapshot voor conflicterende velden.

Er is **geen fundamentele nieuwe conflictarchitectuur nodig voor v2**.

Wel is er één bewuste uitzondering: exportinstellingen zijn direct toegepaste voorkeuren. Bij een extern conflict wordt de nieuwste boekstate geladen en moet de gebruiker de exportinstelling opnieuw kiezen. Dat is geen verlies van manuscript- of boekinhoud en rechtvaardigt op dit moment geen extra History-mechanisme.

### 1.1 Manuscript

Gedrag:
- externe wijziging stopt normale save;
- gebruiker kiest eigen versie of schijfversie;
- bij **eigen versie** wordt de externe live toestand eerst als `conflict_external` bewaard, daarna wordt alleen het actieve hoofdstuk met lokale tekst over de nieuwe basis gelegd;
- bij **schijfversie** wordt de lokale in-memory boekstructuur + lokale hoofdstuktekst als `conflict_local` opgeslagen voordat disk wordt geadopteerd;
- verandert disk opnieuw tijdens het oplossen, dan blijft de lokale tekst in de editor en wordt niets geforceerd;
- future-format pad bewaart lokale tekst vóór detach.

Conclusie: **beide relevante versies herstelbaar**.

### 1.2 Structuuracties zonder actief manuscript-hoofdstuk

Voor acties op boekstructuur terwijl bijvoorbeeld Publicatie actief is:
- de mislukte structuurmutatie heeft vóór de revisioncheck nog geen stale state weggeschreven;
- gebruiker kan nieuwste versie laden;
- externe live state wordt eerst als `conflict_external` opgeslagen;
- de oorspronkelijke structuuractie wordt niet automatisch opnieuw uitgevoerd.

Conclusie: veilig, en bewust conservatiever dan auto-merge.

### 1.3 Planning

Planning heeft drie afzonderlijke bronnen:
- `planning/characters.json`;
- `planning/outline.json`;
- `planning/notes.md`.

Bij conflict:
- geselecteerde lokale payload kan als `conflict_local` worden bewaard;
- ook **andere** niet-opgeslagen Planning-invoer wordt meegenomen in dezelfde herstelversie;
- als zo'n andere pending bron zelf ook extern veranderde, wordt disk live en krijgt gebruiker melding dat lokale invoer in History staat;
- niet-conflicterende pending invoer wordt na adoption opnieuw in de UI gezet;
- corrupte Notes met lokale dirty tekst worden vóór read-only adoption veiliggesteld;
- future book route bewaart lokale Planning vóór sluiten.

Conclusie: **sterke dekking; geen nieuwe v2-mechaniek nodig**.

### 1.4 Boekdetails

Boekdetails gebruikt veldniveau drie-wegs merge:
- baseline;
- lokale formulierstate;
- disk state.

Bij gelijk veld aan beide kanten gewijzigd:
- disk blijft live;
- volledige lokale kandidaat wordt als `conflict_local` in History bewaard.

Lokale-only velden blijven in het formulier staan.

Conclusie: **beide versies effectief herstelbaar**.

### 1.5 Boekprofiel

Bij dirty lokaal profiel:
- lokaal profiel en diskprofiel worden per sectie gemerged;
- conflicterende complete lokale versie wordt als `conflict_local` opgeslagen;
- corrupte externe Markdownbron + lokale dirty state -> lokale state wordt eerst veiliggesteld;
- daarna mag bron read-only/corrupt worden geopend.

Conclusie: veilig.

### 1.6 Boekgeheugen

Zelfde patroon als Boekprofiel:
- drie-wegs merge per sectie;
- volledige lokale versie in `conflict_local` bij echte conflictvelden;
- lokale state bewaren vóór corrupt/read-only adoption.

Conclusie: veilig.

### 1.7 Publicatievrije tekst en publicatieonderdelen

Publicatie gebruikt dezelfde expliciete conflictkeuze als manuscript/Planning:
- **mijn versie** -> externe toestand eerst `conflict_external`, daarna lokale publicatiewaarde schrijven op nieuwste basis;
- **schijfversie** -> lokale publicatietekst eerst als `conflict_local`;
- future format -> lokale tekst wordt expliciet veiliggesteld vóór sluiten.

Conclusie: veilig.

### 1.8 Exportinstellingen

Exportinstellingen worden direct geschreven wanneer de gebruiker keuzes verandert.

Bij externe wijziging:
- als manuscript/publicatie dirty is, wordt eerst de bestaande veilige editor-conflictroute gebruikt;
- anders wordt nieuwste boekstate geadopteerd;
- de niet-gecommitte exportkeuze wordt niet apart in History gezet;
- gebruiker krijgt instructie de instelling opnieuw te kiezen.

Beoordeling:
- dit is **geen inhoudsverlies**;
- het betreft opnieuw te kiezen voorkeuren;
- extra History-versie voor iedere niet-opgeslagen exportkeuze zou ruis toevoegen.

Besluit: **bewust laten zoals het is**.

### 1.9 Media Manager

Media cleanup is geen mine/disk merge:
- externe wijziging -> cleanup wordt niet uitgevoerd;
- nieuwste boek/media-inventaris wordt geladen;
- gebruiker moet opnieuw controleren en cleanup opnieuw starten;
- cleanup zelf maakt vooraf een herstelpunt;
- onzekere/history-onvolledige assets zijn niet opruimbaar.

Conclusie: passend bij het veiligheidsmodel.

### 1.10 Eindbesluit conflict-audit

Voor v2 geldt daarom:

- **geen nieuwe "bewaar beide versies"-feature bouwen**;
- bestaande History/revisionarchitectuur hergebruiken;
- iedere nieuwe v2-writeflow moet aantonen welke bestaande conflictcategorie hij volgt;
- alleen wanneer een nieuwe feature geen veilige mapping heeft, wordt nieuw conflictgedrag ontworpen.

Dit voorkomt een parallel conflictsysteem.

---

# 2. Documentmodel / Markdown-verkenning

## 2.1 Huidige werkelijkheid

QuietWriter heeft geen volledige CommonMark-parser en probeert dat bewust ook niet te zijn.

Er zijn nu meerdere gespecialiseerde parse-lagen:

### `manuscript_markup.py`
Beheert vooral wat QuietWriter zelf kan maken:
- bold;
- italic;
- underline;
- strike;
- inline code;
- block prefixes voor heading/quote/list;
- scènebreukherkenning;
- selection-based formatting en broncoördinaten.

Belangrijk: inline spans gebruiken **source coordinates** en houden marker ranges apart van zichtbare inhoud. Dat is sterk voor editor round-trip en formatting.

### `media/markup.py`
Beheert managed image syntax:
- image parse;
- layout metadata;
- protected ranges;
- searchmaskering;
- spelling/search offsets;
- AI-representatie;
- woordtelling zonder image syntax/captionvervuiling.

### `exporting/markup.py` en `exporting/xhtml.py`
Parsen manuscript opnieuw voor export:
- blocks;
- headings;
- blockquote;
- lijsten;
- images;
- scènebreuken;
- inline spans.

### `ui/presentation_highlighter.py`
Interpreteert opnieuw:
- block type;
- prefixes;
- inline spans;
- media masking;
- spelling.

### `ui/manuscript_editor.py`
Heeft eigen block-classificatie voor:
- scene;
- image;
- heading/quote/lists/paragraph.

### Search / spelling / AI
Gebruiken vooral `media.markup` om image syntax te maskeren of semantisch te vervangen.

## 2.2 Sterke punten

De huidige architectuur heeft een paar zeer waardevolle eigenschappen die behouden moeten blijven:

1. **Markdown op schijf blijft exact de bron.**
2. **Source coordinates zijn first-class.**
3. Managed syntax kan beschermd worden zonder bron te vervangen.
4. Image masking behoudt lengte, waardoor zoek-/spellings-offsets exact blijven.
5. Export en editor kunnen dezelfde inline span parser gebruiken.
6. Onbekende/malformed markup blijft zichtbaar in plaats van stil te verdwijnen.
7. De parser is klein en afgestemd op wat QuietWriter werkelijk produceert.

Dit zijn belangrijke redenen om niet zomaar een externe Markdown-AST als nieuwe canonieke bron in te voeren.

## 2.3 Zwakke plek: block parsing is verspreid

Inline markup is redelijk centraal via `parse_inline_spans`, maar blockherkenning is verspreid over meerdere modules.

Voorbeelden:
- editor block kind;
- export block renderer;
- presentation highlighter;
- scene break helpers;
- image line parser;
- block formattingtransforms;
- Markdown import/export.

Nieuwe persistente markup zoals placeholders, footnotes of speciale boektypografie zou daardoor snel meerdere losse implementaties krijgen.

Dat is de echte technische schuld die vóór verdere markupgroei begrensd moet worden.

## 2.4 Geen volledige AST vóór Darlings

Darlings verplaatst gewone Markdowntekst buiten het manuscript en vereist **geen nieuw manuscriptmarkupformaat**.

Daarom:
- vóór Darlings geen grote parserrefactor;
- bestaande bronfuncties hergebruiken;
- Darlings moet brontekst byte-/tekstgetrouw bewaren.

Dit houdt de eerste v2-feature klein.

## 2.5 Wel vóór Placeholders: een centraal documentview-model

Placeholders zijn de eerste geplande feature die nieuwe persistente manuscriptmarkup introduceert.

Voor die feature is een kleine centrale parse-laag logisch.

Voorgesteld model: **read-only document view**, niet een nieuwe opslag- AST.

Bijvoorbeeld:

```python
DocumentView(
    source: str,
    blocks: list[BlockView],
    protected_ranges: list[SourceRange],
)
```

Mogelijke `BlockView.kind`:
- paragraph;
- heading;
- quote;
- bullet;
- numbered;
- scene_break;
- image;
- later: todo/placeholder.

Iedere block bewaart:
- `source_start`;
- `source_end`;
- zichtbare contentrange(s);
- protected ranges;
- semantische metadata waar nodig.

Inline markup blijft via `parse_inline_spans` werken en hoeft niet meteen herschreven te worden.

## 2.6 Waarom read-only view en geen serializer-AST

Een klassieke AST + serializer introduceert direct risico:
- whitespace normaliseren;
- markers herschikken;
- line endings veranderen;
- onbekende syntax verliezen;
- exact bronroundtrip breken.

QuietWriter heeft juist veel regressies opgelost door source fidelity leidend te maken.

Daarom:
- parser leest de source;
- mutaties blijven doelgerichte source transforms;
- source blijft autoritatief;
- view-model wordt opnieuw opgebouwd na mutatie;
- geen algemene "serialize(document)" in de eerste v2-fases.

## 2.7 Eén centrale protected-range API

Voor Placeholders en toekomstige markup is de beste eerstvolgende technische verbetering:

```python
protected_ranges(source) -> list[SourceRange]
searchable_text(source) -> str  # zelfde lengte
semantic_text_for_ai(source) -> str
visible_word_text(source) -> str
```

Nu is dit hoofdzakelijk image-specifiek.

Later kunnen providers van protected syntax bijdragen:
- image;
- placeholder metadata/comments;
- eventueel future footnote internals.

Belangrijk:
- zichtbare placeholdertekst mag zoekbaar/spellbaar blijven;
- metadata/commentmarkers niet;
- offsets blijven één-op-één met source waar UI-mutaties dat nodig hebben.

## 2.8 Placeholders: aanbevolen bronvorm

De roadmap stelde voor:

```markdown
toen <!-- qw:todo id=3f2a -->mevrouw Xxx<!-- /qw:todo --> eindelijk aanbelde
```

Dit is haalbaar, maar heeft één belangrijk nadeel: HTML-commentmarkers liggen **inline** in gewone proza-source. Iedere parser/formattingactie moet ze dan als protected syntax respecteren.

Aanbevolen ontwerp vóór implementatie:

- behoud zichtbare tekst tussen markers als gewone manuscripttekst;
- markers krijgen centrale source ranges;
- formatting mag over zichtbare tekst lopen maar nooit markers insluiten/verplaatsen;
- verwijderen/afhandelen verwijdert alleen markers, niet inhoud;
- zoek/spelling/woordtelling zien alleen zichtbare inhoud;
- export/AI strippen alleen markers;
- malformed markerpaar blijft zichtbaar/diagnosticeerbaar en veroorzaakt nooit tekstverlies.

Metadata in `planning/todos.json` kan, maar alleen met duidelijke degradatie:
- marker zonder metadata -> nog steeds zichtbaar open punt met generieke info;
- metadata zonder marker -> orphan in Integriteit/Planning-overzicht;
- geen manuscripttekst mag afhangen van metadata om leesbaar te blijven.

## 2.9 Ghost paragraphs

Ghost paragraphs horen **niet** in dit documentmodel als persistente blocks.

Ze zijn pure presentatie uit Planning.

Daarom:
- niet in source;
- niet in document serializer;
- niet in protected ranges;
- liefst overlay/paint/layoutlaag boven of naast source document.

Het centrale documentview-model kan wel nuttig zijn om te bepalen **waar** een ghost hint visueel hoort, maar ghost inhoud zelf blijft buiten manuscriptmodel.

## 2.10 DOCX-import

DOCX-import profiteert van een centrale lijst van **ondersteunde QuietWriter-blokken**, maar mag niet via een algemene AST-serializer willekeurige source genereren.

Voorkeur:
- DOCX -> importintermediair;
- preview/warnings;
- intermediair -> gecontroleerde QuietWriter Markdownbuilder;
- vervolgens bestaande normale boek/create/write-routes.

Dat buildercontract kan dezelfde blocktypes gebruiken als DocumentView, maar is een aparte importoutputroute.

## 2.11 Footnotes en latere typography

Niet nu bouwen.

Wanneer ze komen:
- eerst als expliciete nieuwe syntax aan DocumentView toevoegen;
- daarna editor/highlighter/search/spelling/export/AI contract per feature testen;
- nooit eerst losse regex in exporter toevoegen en later editor laten volgen.

## 2.12 Performance

Een read-only view-parser moet lineair of vrijwel lineair zijn.

Doel voor grote hoofdstukken:
- geen volledige boekparse bij iedere toetsaanslag;
- parser per huidig hoofdstuk;
- eventueel per gewijzigd block wanneer nodig;
- geen zware CommonMark dependency zonder benchmark.

Meet vóór adoptie:
- 10k woorden hoofdstuk;
- 25k woorden hoofdstuk;
- veel inline formatting;
- veel managed images;
- later honderden placeholders.

## 2.13 Besluit documentmodel

### Nu
Geen parserrefactor uitvoeren.

### Voor Darlings
Bestaande source helpers gebruiken; Darlings slaat gewone Markdownfragmenten exact op.

### Vóór Placeholders
Een kleine **read-only DocumentView/BlockView-laag** ontwerpen en testen die:
- source offsets bewaart;
- bestaande blockclassificatie centraliseert;
- protected syntax uitbreidbaar maakt;
- geen serializer introduceert;
- onbekende syntax ongemoeid laat.

### Niet doen
- geen volledige CommonMark AST als nieuwe bron;
- geen QTextDocument als persistente canonieke representatie;
- geen algemene reformatter/serializer;
- geen mega-refactor vóór de eerste v2-feature.

---

# 3. Effect op roadmap

De twee funderingsstappen leveren daarmee concrete besluiten op:

1. **Conflict-audit afgerond:** bestaande architectuur is voldoende; nieuwe v2-features sluiten erop aan.
2. **Documentmodelverkenning afgerond:** geen grote parserrefactor nu; wel een kleine centrale read-only documentview vóór Placeholders.
3. **Darlings blijft de eerste echte v2-feature.**
4. `.qwbook` kan daarna onafhankelijk worden ontworpen.
5. Placeholders wacht op de centrale documentview.
6. Ghost paragraphs blijven presentation-only.
7. Schrijfstatistiek blijft na Darlings.

Dit is de basis waarop de volgende stap — het ontwerp van Darlings — kan beginnen.


## Aanvulling na reviewronde 58 — complete write-audit

De oorspronkelijke conflictaudit is opnieuw uitgevoerd door alle aanroepen van `_safe_atomic_write_text` en `atomic_write*` langs te lopen. Daarbij bleek één echte 1.0-leemte: de globale **Schrijverspersona** had nog geen optimistic-concurrencycontrole. Dat is vóór v2 gecorrigeerd.

De persona onthoudt nu de geladen file-revision. Bij Opslaan na een externe wijziging wordt niets overschreven en kiest de gebruiker tussen lokaal en schijf. De versie die anders verloren zou gaan wordt eerst buiten het live bestand bewaard onder `archive/persona/` als `conflict_local` of `conflict_external` herstelkopie. Omdat de persona globaal is en niet bij één boek hoort, komt deze kopie bewust niet in de per-boek Versiegeschiedenis terecht.

Het Meelezer-gesprek (`.quietwriter/ai_chat.json`) blijft voor 1.0 een bewuste uitzondering. Het is een afgeleid/optioneel gesprekslog en geen manuscript-, Planning-, profiel- of geheugenbron. Bij gelijktijdig gebruik op twee computers geldt last-writer-wins; dit mag in een latere versie worden verbeterd met mergegedrag, maar blokkeert 1.0 niet.

**Herhaalbare auditmethode:** bij toekomstige toevoegingen aan persistentie worden alle directe en indirecte aanroepen van `_safe_atomic_write_text`, `_safe_atomic_write_bytes`, `atomic_write*` en vergelijkbare writeroutes gecontroleerd op revisioncheck, corrupt/future gedrag, recovery en expliciet gedocumenteerde uitzonderingen.
