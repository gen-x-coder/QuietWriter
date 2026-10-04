# QuietWriter — roadmap en ideeën

Status: canonieke roadmap vanaf 1.0.0  
Scope: afronding 1.0 en daarna de v2-lijn

Deze roadmap combineert de bestaande QuietWriter-ideeën met de nieuwe v2-ideeën uit de vergelijking met Neo. De volgorde is bewust gekozen op afhankelijkheden, risico en productwaarde.

## 1. Beslisregels

QuietWriter bouwt geen functies alleen omdat ze technisch interessant zijn.

Voor iedere substantiële v2-feature geldt eerst een kort ontwerpvoorstel met:

- probleem en gewenst gebruikersresultaat;
- concrete aanpak;
- betrokken bestanden en functies;
- opslagformaat en migratie-effect;
- Dropbox/twee-computer-gedrag;
- risico op dataverlies of stale state;
- invloed op History/revisions;
- invloed op zoeken, spelling, woordtelling, export en AI-context;
- testplan, inclusief failure injection waar relevant;
- expliciete scopegrens: wat we **niet** in dezelfde feature bouwen.

Pas na goedkeuring van dat voorstel wordt gebouwd.

De bestaande veiligheidsprincipes blijven gelden:

1. atomair schrijven;
2. revisioncontrole vóór mutatie;
3. niets stil verliezen;
4. corrupte bron is niet leeg;
5. future format is niet corruptie;
6. prepare vóór commit;
7. één canonieke bron per concept;
8. Dropbox/twee-computer-situaties moeten veilig blijven;
9. presentatie is geen manuscriptinhoud;
10. AI blijft Meelezer en schrijft geen manuscriptproza.

---

# Deel A — afronding van 1.0

## 2. Stabiele 1.0.0 — afgerond

De feature freeze blijft van kracht. Alleen fixes, overdraagbaarheid en praktijkvalidatie.

### 2.1 Reviewpunten vóór praktijkvalidatie — afgerond

De resterende overdraagbaarheidspunten uit reviewronde 57 zijn verwerkt:

- tekstbreedte-combo verbreed zodat ook **Extra breed / Extra wide** volledig zichtbaar zijn;
- `UI_REFERENCE.md` gebruikt consequent **Meelezer** en bevat geen `Herschrijf selectie`;
- claims over "groen" zijn gekoppeld aan `VALIDATION.md`.

Er staan daarmee geen bekende documentatie-/UI-reviewpunten meer open vóór de praktijkvalidatie. Nieuwe bevindingen tijdens die praktijkvalidatie worden als regressiefix behandeld, niet als v2-feature.

### 2.2 Praktijkvalidatie

Voor stabiele 1.0:

- clean Windows zonder Python;
- SmartScreen;
- 100%, 125%, 150% en waar mogelijk mixed DPI;
- echte Ollama cold start;
- echte OpenRouter-vraag;
- groot boek, ongeveer 150.000 woorden / 40 hoofdstukken;
- meerdere echte boeken uit oudere QuietWriter-versies;
- langere periode dagelijks schrijven;
- twee-machine syncscenario waar praktisch mogelijk.

### 2.3 Releasebesluit

1.0.0 is uitgebracht nadat de volgende voorwaarden waren afgedekt:

- geen bekende dataverliesbug openstaat;
- RC2/latere RC praktisch stabiel is;
- documentatie en tests overdraagbaar zijn;
- Windows-package schoon is;
- update naar 1.0 geen schema-onduidelijkheid introduceert.

---

# Deel B — v2 fundament

## 3. Eerst doen: twee korte architectuuronderzoeken

Deze onderzoeken leveren ontwerpbesluiten op, geen nieuwe gebruikersfeature.

### 3.1 Conflict-audit: zijn beide versies overal herstelbaar?

Status: **afgerond — geen nieuwe conflictfeature nodig**

Controleer alle conflictroutes:

- hoofdstuktekst;
- Planning;
- Boekprofiel;
- Boekgeheugen;
- Boekdetails;
- Publicatie;
- exportinstellingen waar relevant.

Vraag per route:

- blijft diskversie bestaan?
- wordt lokale dirty versie vóór verlies als `conflict_local` of equivalent opgeslagen?
- is die versie via History terug te vinden?
- blijft de live bron onaangetast bij snapshotfailure?

Als dit al overal klopt: **niets bouwen**.

Alleen een klein gat dichten wanneer de oplossing eenvoudig in bestaande revision/History-architectuur past.

### 3.2 Verkenning intern documentmodel

Status: **afgerond — read-only documentview vóór Placeholders, geen grote refactor nu**

Doel: bepalen of nieuwe markupfeatures op termijn één centrale parser nodig hebben.

Inventariseer:

- welke modules Markdown zelf parsen;
- welke regexen bestaan in editor, highlighter, zoeken/vervangen, spelling, export, woordtelling en AI-context;
- welke logica al centraal in `manuscript_markup.py` zit;
- welke protected ranges bestaan voor afbeeldingen;
- waar round-trip van source exact moet blijven.

Onderzoek een toekomstig model met blokken/inlines, bijvoorbeeld:

- paragraph;
- heading;
- scene break;
- image;
- todo;
- emphasis;
- strong;
- code/literal;
- later eventueel footnote.

Harde eis:

- Markdown op schijf blijft de bron;
- parser/model mag nooit bron normaliseren zonder expliciete write;
- exact round-tripgedrag is belangrijker dan "mooie AST";
- prestaties bij grote hoofdstukken moeten meetbaar blijven.

**Waarom dit vroeg komt:** placeholders, DOCX-import, toekomstige footnotes en rijkere media-markup raken allemaal dezelfde parsegrens. We willen niet vier nieuwe regex-eilanden bouwen voordat we weten waar de architectuur naartoe moet.

Uitkomst: zie `documents/V2_FOUNDATION_RESEARCH.md`. Bestaande source fidelity blijft leidend; Darlings vereist geen parserrefactor. Vóór Placeholders ontwerpen we een kleine centrale read-only `DocumentView/BlockView`-laag met source offsets en uitbreidbare protected ranges.

---

# Deel C — v2.0: hoogste prioriteit

## 4. Bewaarplaats voor tekstfragmenten ("Darlings")

Status: **eerste echte v2-feature**

### Waarom eerst

Dit is:

- direct nuttig tijdens schrijven;
- conceptueel eenvoudig voor de gebruiker;
- goed te bouwen zonder manuscriptformaat te veranderen;
- een mooie test voor bibliotheekniveau-data en Dropboxveiligheid;
- basis voor latere schrijfstatistiek, omdat verplaatsen naar Darlings als aparte schrijfactie kan worden geregistreerd.

### Gewenst gedrag

Twee acties vanuit selectie:

- **Knippen naar bewaarplaats**
- **Kopiëren naar bewaarplaats**

Per fragment:

- Markdowntekst;
- bronboek;
- bronhoofdstuk;
- datum;
- eigen titel/notitie;
- tags;
- ankertekst vóór en na oorspronkelijke plek;
- unieke id.

Acties:

- terugzetten op oorspronkelijke plek als ankers nog betrouwbaar zijn;
- invoegen bij cursor in elk boek;
- zoeken/filteren;
- verwijderen via veilige prullenbak.

### Voorkeursopslag

Bibliotheekniveau:

`<werkmap>/fragments/<uuid>.md`

Metadata in YAML-frontmatter.

Waarom één bestand per fragment:

- minder syncconflicten;
- eenvoudig herstel;
- menselijk leesbaar;
- fragmenten onafhankelijk overdraagbaar;
- geen monolithisch JSON-bestand met veel schrijvers.

### Ontwerpvragen

#### Grote verwijdering automatisch aanbieden?

Voorkeur: **niet automatisch bij iedere delete**.

Mogelijke rustige variant:

- alleen na grote selectie-cut/delete;
- niet als modal popup;
- eventueel korte undo-achtige lokale notice: "Naar bewaarplaats verplaatsen";
- instelbaar/uitschakelbaar.

Het schrijven mag niet worden onderbroken.

#### UI

Voorkeur:

- **eigen boek-onafhankelijke pagina** voor beheer/zoeken;
- compacte rechterpaneelvariant alleen voor snel invoegen tijdens schrijven.

Dus mogelijk beide, maar niet in eerste slice noodzakelijk.

MVP:
- eigen pagina + editoractie.

Later:
- rechterpaneel voor snelle insert.

#### Afbeeldingen

MVP: **alleen tekst**.

Reden:
- cross-book mediareferenties maken assets/UUID's complex;
- een "fragment met afbeelding" is eigenlijk een mini-documentpakket.

Later eventueel:
- fragmentassets kopiëren naar een aparte fragmentassetstore.

### Tests

- atomic write;
- Dropbox/revision gedrag;
- knippen faalt -> manuscript blijft;
- fragmentwrite geslaagd maar manuscriptwrite faalt -> transactioneel herstel;
- anker exact/ambigu/verdwenen;
- cross-book insert;
- trash/restore;
- Markdownformatting exact behouden.

---

## 5. `.qwbook`: volledig boek als transport- en back-upformaat

Status: **zeer hoog, direct na Darlings**

### Waarom vroeg

QuietWriter heeft al een sterke interne boekstructuur maar mist één veilige overdraagbare verpakking.

Dit lost op:

- compleet boek delen;
- afbeeldingen behouden;
- back-up buiten de werkmap;
- import op andere computer;
- latere migratie/diagnose;
- veilige basis vóór grotere v2-schema-uitbreidingen.

### Concept

`.qwbook` is technisch een ZIP met eigen extensie.

Interne boekopslag blijft exact zoals nu.

Voorbeeld:

```text
mijnboek.qwbook
├── qwpackage.json
├── book.json
├── chapters/
├── assets/
├── planning/
├── publication/
├── export/
├── ai/                    optioneel
├── .quietwriter/          optioneel
└── history/               optioneel
```

### `qwpackage.json`

Minimaal:

- package format version;
- QuietWriter-versie;
- exportdatum;
- book id;
- bestandspad;
- grootte;
- SHA-256 per bestand;
- optionele componentflags.

### Exportkeuzes

Standaard:

- boekdata;
- hoofdstukken;
- media;
- Planning;
- Publicatie;
- exportinstellingen;
- Boekprofiel/Boekgeheugen: waarschijnlijk aan.

Optioneel:

- AI-gesprekken: standaard uit;
- History: standaard uit of aparte keuze.

### Import

Verplicht:

- manifest valideren;
- hashes controleren;
- zip-slip blokkeren;
- absolute paden blokkeren;
- maximale unpacked grootte;
- maximale file count;
- future package format weigeren;
- geen stille overwrite.

Bestaat book-id al:

- importeren als kopie;
- bestaand boek vervangen.

Bij vervangen:

1. huidig boek veilig checkpointen;
2. package volledig in tijdelijke locatie valideren;
3. prepare;
4. pas daarna commit/replace.

### Automatische back-up

Mooie uitbreiding, maar liefst aparte tweede slice.

Bijvoorbeeld:

`<werkmap>/backups/<book_id>/...qwbook`

Opties:

- dagelijks;
- bij eerste save van dag;
- maximaal N exemplaren;
- historie wel/niet includen.

Back-up mag nooit dezelfde revision/conflictsemantiek krijgen als live boek: het is output, geen tweede live bron.

### Markdown-subset inventarisatie in dezelfde ontwerpfase

Alleen documenteren, nog niet bouwen:

- voetnoten;
- poëzie/verzen met harde regeleinden;
- gecentreerde tekst;
- kleinkapitalen;
- harde spaties;
- eventuele andere book-specific typography.

Voorkeur:
- gangbare Markdown waar mogelijk;
- `<!-- qw:... -->` alleen voor QuietWriter-specifieke semantiek.

---

## 6. Placeholders / open punten

Status: **hoog**

### Waarom vóór Spookalinea's

Placeholders zijn persistent manuscriptmarkup en dwingen ons eerst protected ranges, source round-trip, zoeken, spelling en export goed uit te breiden.

Dat is een bruikbare basis voor latere editor-overlayfuncties.

### Gebruikersflow

Sneltoets / contextmenu:

- met selectie: bestaande tekst markeren;
- zonder selectie: `[…]` of rustige placeholder invoegen;
- optionele notitie.

Voorbeeldbron:

```markdown
toen <!-- qw:todo id=3f2a -->mevrouw Xxx<!-- /qw:todo --> eindelijk aanbelde
```

### Metadata

Voorkeur: marker bevat alleen id.

Notities in:

`planning/todos.json`

Waarom:

- notitie hoeft niet in proza-source;
- uitgebreidere metadata mogelijk;
- status/datum;
- overzicht per boek;
- later AI-voorstellen mogelijk.

Maar de ontwerpfase moet ook het nadeel behandelen: marker + metadata vormen twee gekoppelde bronnen.

Alternatief:
- notitie encoded in commentaar.

Beslisregel:
- kies de variant die bij kapotte/missende metadata het manuscript het best leesbaar en herstelbaar houdt.

### UI

- markering in editor;
- rode `danger`-stip bij hoofdstuk;
- rechterpaneel **Open punten**;
- per hoofdstuk groeperen;
- snippet + notitie;
- klik -> navigeren;
- Afgehandeld -> marker verwijderen, zichtbare tekst behouden.

### Export

Markers nooit zichtbaar.

Preflight:
- waarschuwing met aantal open punten.

### Integraties

Moeten marker-safe zijn:

- zoeken/vervangen;
- spelling;
- woordtelling;
- AI-context;
- Undo/Redo;
- History;
- export.

### Meelezer later

Meelezer mag een open punt **voorstellen**.

Nooit automatisch marker plaatsen.

---

## 7. Lamplicht-themafamilie

Status: **hoog, laag risico**

Dit kan grotendeels parallel aan de eerste v2-features.

### 7.1 Lamplicht

Donkere warme omgeving en donkere pagina.

Past in bestaand themamodel.

Waarschijnlijk eerste kleine v2-polishfeature.

### 7.2 Lamplicht Papier

Donkere omgeving + crèmekleurige editor.

Hiervoor theme model uitbreiden met optionele editor-specifieke tokens:

- `editor_text`;
- `editor_muted`;
- `editor_select`.

Fallback:
- `text`;
- `muted`;
- `select`.

Daarmee blijven bestaande thema's compatibel.

### Waarom deze uitbreiding nuttig is

Dezelfde editor-specifieke kleurlaag kan later ook logisch gebruikt worden voor:

- ghost text;
- placeholder highlight;
- page-like editor rendering.

### Open vraag

`QTextEdit#aiInput` gebruikt nu mogelijk dezelfde `editor`-achtergrond. In ontwerp vaststellen of AI-input visueel:

- deel van papier/editor;
- of deel van appchrome

is.

### Pagina-effect

Zachte pagina-schaduw en smaller "vel" alleen als:

- geen complexe custom painting nodig is;
- DPI/layout eenvoudig blijft;
- tekstbreedte-instelling leidend blijft.

---

# Deel D — v2.1: Planning dichter bij schrijven

## 8. Spookalinea's uit Planning

Status: **hoog, maar ná placeholders/theme groundwork**

### Productdoel

Planning zichtbaar tijdens schrijven zonder manuscript te vervuilen.

### Harde architectuurregel

Ghost text:

- komt nooit in Markdown;
- komt nooit in `QTextDocument` als echte broninhoud als dat te voorkomen is;
- telt niet mee;
- komt niet in zoekresultaten;
- spelling negeert het;
- export negeert het;
- AI-context negeert het;
- Undo negeert het.

### Fase 1

Bij leeg hoofdstuk:

- scene title;
- synopsis;
- personages;
- eventueel goal/conflict/outcome compact.

Puur visueel.

Zodra gebruiker begint te schrijven, verdwijnt/verschuift de hulp.

### Fase 2

Scènegericht:

- scène n koppelt aan tekstsegment na scènebreuk n-1;
- niet geschreven scènes verschijnen onder laatste geschreven segment.

### Technische voorkeursrichting

Onderzoeken als:

- viewport overlay;
- extra paint pass;
- layout overlay buiten source document.

Niet als echte grijze tekst in het document als dat:
- cursor offsets;
- search;
- serialization;
- Undo

compliceert.

### Instelling

Ghost text moet volledig uit te zetten zijn.

---

## 9. Planning uitbreiden — pas op basis van praktijk

Na ghost paragraphs wordt duidelijker welke Planning-data echt tijdens schrijven waarde heeft.

Kandidaten:

- scènes vrij tussen hoofdstukken verplaatsen;
- inklapbare hoofdstukgroepen;
- compactere inline-scènebewerking;
- eerste verschijning van personage;
- belangrijke hoofdstukken;
- locaties als aparte entiteit;
- rijkere relaties;
- aliasherkenning.

### Nog niet automatisch bouwen

- grafische relation map;
- Kanban;
- volledige tijdlijn;
- uitgebreide worldbuildingdatabase.

Eerst observeren of ghost paragraphs + huidige Planning het echte probleem al oplossen.

---

# Deel E — v2.2: schrijfinzicht

## 10. Schrijfstatistiek

Status: **hoog, maar pas na Darlings**

### Waarom na Darlings

Een tekstverplaatsing naar Darlings moet apart herkenbaar kunnen zijn.

Anders wordt "schrappen" vertekend.

### Wat meten

Per dag/per boek:

- **geschreven**;
- **geschrapt**;
- **netto**.

Aanvullend:

- huidige boekomvang;
- eventueel actieve schrijftijd.

### Dagdoel

Standaard op **geschreven woorden**, niet netto.

Waarom:
- redigeren straft gebruiker niet;
- herschrijven mag positieve productie zijn.

### Diffmodel

Per succesvolle opslag:

- vorige persistente bron;
- nieuwe persistente bron;
- woorddiff per hoofdstuk.

Een herschreven zin telt:
- verwijderd;
- én toegevoegd.

### Darlings

Verplaatsing naar bewaarplaats:

- technisch geschrapte tekst;
- liefst als aparte categorie zichtbaar.

### Schrijftijd

Optioneel:

- activity timer;
- korte inactivity threshold;
- geen surveillanceachtige precisie.

### Dropbox

Voorkeur: append/partition per apparaat, zodat machines niet hetzelfde bestand overschrijven.

Bijvoorbeeld:

`<werkmap>/stats/<device-id>/<date>.json`

Liever stabiele gegenereerde device-id dan computernaam als computernaam kan wijzigen.

Weergave aggregeert apparaten.

### UI

Rustig:

- dagdoel;
- 30-dagen-grafiek;
- geen motiverende popups;
- geen streak-shaming;
- geen onderbreking tijdens schrijven.

---

# Deel F — v2.3: import en portability

## 11. DOCX-import

Status: **ja, na `.qwbook` en markupverkenning**

### Waarom niet eerder

DOCX is intrinsiek rommelig. De import moet landen op een stabiele manuscript-/media-architectuur.

### Bibliotheekkeuze eerst benchmarken

Vergelijk:

#### `python-docx`
Plus:
- volwassen;
- directe OOXML-objecten.

Min:
- semantische conversie zelf bouwen;
- dependency/packagegrootte.

#### `mammoth`
Plus:
- sterk in DOCX -> semantische HTML.

Min:
- HTML tussenlaag;
- eigen mapping naar QuietWriter Markdown.

#### XML zelf
Plus:
- volledige controle;
- geen zware dependency.

Min:
- veel edge cases;
- onderhoudsrisico;
- kans op halve DOCX-parser.

Voorkeur pas na proefbestandmatrix bepalen.

### Mapping

Minimaal:

- Heading 1/2 -> hoofdstuk/sectie volgens importwizard;
- bold/italic;
- alinea's;
- scènebreuken;
- afbeeldingen;
- page breaks als mogelijke grens;
- lege paragraphs zorgvuldig.

### Importpreview

Verplicht:

- gevonden hoofdstukken;
- titel;
- woordtelling;
- samenvoegen;
- splitsen;
- waarschuwingen.

### Wat niet importeren

Duidelijk rapporteren:

- track changes;
- comments;
- headers/footers;
- exotische Word-layout;
- niet-ondersteunde fields.

### Hergebruik

Waar mogelijk eindigen in dezelfde create/import-route als Markdownimport.

Geen tweede boek-creatiearchitectuur.

---

## 11a. DOCX-export

Status: **ja, expliciet gewenst voor v2**

Doel:

- een boek rechtstreeks als `.docx` kunnen exporteren;
- hoofdstukken/secties, alinea's, bold/italic, scènebreuken en waar haalbaar afbeeldingen correct mappen;
- export moet dezelfde canonieke manuscriptbron gebruiken als de bestaande EPUB/PDF/Markdown-export;
- geen stille inhoudsvervorming of bronmutatie;
- eerst `python-docx` als waarschijnlijke uitvoerlaag beoordelen, met tests op Word/LibreOffice-compatibiliteit.

DOCX-export is technisch onafhankelijk van DOCX-import en hoeft daar niet op te wachten.

---

## 12. Meer interfacetalen

Status: **ja, kan parallel met DOCX**

Dit is vooral infrastructuur + vertaalwerk.

### Contextbestand

`quietwriter/locales/_context.json`

Per key:

- betekenis;
- UI-type;
- plaats;
- placeholders;
- maximale lengte;
- vaste term.

### Vertaalhandleiding

`documents/TRANSLATING.md`

Bevat:

- nieuwe locale toevoegen;
- toon;
- vaste producttermen;
- placeholders;
- canonical storage versus display;
- testprocedure.

### Controlescript

`tools/check_locales.py`

Controleert:

- ontbrekende sleutels;
- extra sleutels;
- placeholdermismatch;
- context ontbreekt;
- optioneel lengtewaarschuwingen.

Lengte is waarschuwing, geen harde generieke fout: sommige talen zijn structureel langer.

### Fallback

Ontwerp herzien.

Logische voorkeur:

- actieve locale;
- Engels als productfallback;
- default string uit code als laatste vangnet.

Nederlands hoeft niet langer technische fallback voor alle talen te zijn.

### Eerste talen

- Duits;
- Frans;
- Spaans.

Interfacetaal blijft onafhankelijk van:

- boektaal;
- spellingswoordenboek.

---

# Deel G — v2.4 en later

## 13. Markdown/book typography uitbreiden

Pas op basis van echte behoefte en de documentmodelverkenning.

Kandidaten:

### Voetnoten

Voorkeur:
- gangbare Markdownsyntax `[^1]`.

Vereist:
- editorpresentatie;
- export;
- navigation/preflight;
- source round-trip.

### Poëzie/verzen

Nodig:
- harde line breaks;
- inspringing;
- voorkomen dat gewone prose wrapping betekenis verandert.

### Gecentreerde tekst

Voor:
- motto;
- opdracht;
- enkele literaire elementen.

Mogelijk QuietWriter-commentmetadata.

### Kleinkapitalen

Waarschijnlijk semantische inline extensie.

### Harde spaties

Source fidelity ondersteunt ze al als bronkarakter; UI/exportsemantiek apart documenteren.

Geen van deze features bouwen voordat exacte round-trip en exportstrategie helder zijn.

---

## 14. Pakketback-ups automatiseren

Na bewezen `.qwbook`:

- dagelijkse package-back-up;
- retention, bijvoorbeeld 14;
- handmatige "Back-up nu";
- locatie instelbaar;
- bij voorkeur zonder chat/history tenzij gekozen.

Belangrijk:
- back-upservice mag gewone save niet blokkeren;
- failure wordt zichtbaar gelogd;
- geen stil verwijderen buiten retentionbeleid.

---

## 15. Uitgebreidere Planning/worldbuilding

Alleen wanneer praktijkgebruik het vraagt:

- wiki-achtige `[[links]]`;
- locaties;
- timeline;
- relation graph;
- Kanban;
- custom fields;
- genrevelden.

**Geen feature parity met Scrivener/Neo/Obsidian als doel.**

QuietWriter blijft schrijfapp, geen algemene kennisdatabase.

---

## 16. Export/publicatie

Praktijkgedreven kandidaten:

- echte exportpreview uit dezelfde renderpipeline;
- schutblad / half-title;
- expliciete blanco pagina;
- meer TOC-niveaus;
- aanvullende front/back matter;
- meer printfijninstellingen;
- grote afbeeldingen optimaliseren;
- extra reader-validatie bij concrete incompatibiliteit.

Niet:
- volledige DTP-engine.

---

## 17. Platform/distributie

Na stabiele 1.x/v2-basis:

- code signing onderzoeken;
- installer;
- auto-updater;
- macOS;
- Linux-distributie.

Volgorde:

1. signing;
2. installer;
3. updater.

Updater zonder degelijk trust/signing/rollbackmodel niet bouwen.

---

# Deel H — ideeën met lagere prioriteit

## 18. UI/editor

- spellingscontextmenu;
- alleen bij aantoonbare winst;
- hover blijft geen doel op zichzelf;
- geen extra "focus mode" zonder concreet probleem.

## 19. AI

- contextbudget;
- providercompatibiliteit;
- betere lokale Ollama-setup;
- AI-voorstellen voor feiten/open punten;
- aliasherkenning eventueel lokaal.

Altijd:
- voorstel, geen autonome manuscriptmutatie.

## 20. Diagnostiek

Kleine nuttige verbeteringen:

- versie;
- Python;
- Qt;
- OS;
- DPI;
- schermgeometrie;
- runtimeprofiel.

Geen:
- manuscript;
- API-key;
- gevoelige boekinhoud.

---

# Deel I — bewust niet bouwen

## 21. Afgewezen

### Enter-Enter-Enter
Niet bouwen.

Geen verborgen snelkoppeling waarbij:
- twee keer Enter scènebreuk;
- drie keer Enter hoofdstuk.

Reden:
- onzichtbare magie;
- kan normale prozainvoer verrassen;
- structurele mutatie door whitespacegedrag past niet bij QuietWriter.

### AI als ghostwriter
Niet bouwen.

### Herschrijf selectie
Blijft verwijderd.

### Autonome Boekgeheugenwrites
Niet bouwen.

### Automatische reparatie bij openen
Niet bouwen.

### Stille migratie bij load
Niet bouwen.

### Future-format downgraden
Niet bouwen.

### Agressieve media-cleanup
Niet bouwen.

### Tweede onafhankelijke hoofdstukvolgorde
Niet bouwen.

### Volwaardige coverdesigner
Niet bouwen.

### Complexe DTP-editor
Niet bouwen zonder fundamentele productwijziging.

### Neo-techniek die niet wordt overgenomen
Niet overnemen:

- hele boek in één editorbuffer;
- direct live bestanden overschrijven;
- monolithische UI in één bestand.

---

# Deel J — voorgestelde releasevolgorde

## 22. Mogelijke versieplanning

Versienummers zijn voorlopig; inhoudelijke volgorde is belangrijker.

### 1.0.0 — uitgebracht
- feature freeze afgerond;
- Schrijverspersona-conflictbeveiliging en corrupte-persona-afhandeling afgerond;
- Meelezer-gesprekslog als bewuste last-writer-wins-uitzondering gedocumenteerd;
- praktijkvalidatie afgerond voor de gekozen 1.0-scope;
- stabiele release.

**Belangrijk:** 1.0.0 is nu stabiel. Darlings blijft de eerste geplande v2-feature; de implementatie start pas na deze stabiele 1.0-baseline.

### 1.1.x
Alleen indien nodig:
- kleine post-release fixes;
- OpenRouter free-filter display;
- diagnostiek;
- kleine polish.

Geen grote v2-features.

### 2.0.0-alpha 1 — veilige nieuwe bouwstenen
1. conflict-audit;
2. documentmodelverkenning;
3. Darlings;
4. Lamplicht.

### 2.0.0-alpha 2 — portability en markup
5. `.qwbook`;
6. placeholders/open punten;
7. Lamplicht Papier/editor theme tokens.

### 2.0.0-alpha 3 — Planning tijdens schrijven
8. ghost paragraphs fase 1;
9. eventueel fase 2 na praktijktest.

### 2.0.0-alpha 4 — inzicht
10. schrijfstatistiek;
11. dagdoel/grafiek.

### 2.0.0-beta 1 — import, export en internationalisering
12. DOCX-import;
12a. DOCX-export;
13. locale-context/checker;
14. eerste extra taal.

### 2.0.0-beta 2
15. verdere extra talen;
16. `.qwbook` automatische backups;
17. geselecteerde Planning-polish uit praktijkfeedback.

### 2.0.0
Alleen wanneer:
- nieuwe datamodellen stabiel zijn;
- `.qwbook` backward/forward gedrag getest is;
- placeholders source-safe zijn;
- ghost text bewezen presentation-only is;
- statistiek Dropboxveilig is;
- import geen stille inhoudsvervorming veroorzaakt;
- migraties van 1.x naar 2.0 getest zijn.

---

# Deel K — afhankelijkhedenkaart

## 23. Wat hangt waarvan af?

```text
1.0 stabiel
   |
   +-- Conflict-audit
   |
   +-- Documentmodel-verkenning
   |
   +-- Darlings
   |      |
   |      +-- Schrijfstatistiek
   |
   +-- .qwbook
   |      |
   |      +-- Automatische backups
   |
   +-- Theme editor tokens
   |      |
   |      +-- Lamplicht Papier
   |      +-- ghost/placeholder theming
   |
   +-- Placeholders
   |      |
   |      +-- AI open-punt voorstellen
   |      +-- toekomstige markup-extensies
   |
   +-- Ghost paragraphs
   |      |
   |      +-- Planning polish
   |
   +-- DOCX-import
   |
   +-- Locale context/checker
          |
          +-- Duits/Frans/Spaans
```

Belangrijk:
- Darlings en `.qwbook` zijn grotendeels onafhankelijk en kunnen technisch eventueel parallel;
- placeholders en ghost paragraphs raken editor/markup en liever niet tegelijk bouwen;
- schrijfstatistiek wacht op Darlings zodat verplaatsingen correct kunnen worden geclassificeerd;
- DOCX wacht op de markup-inventaris zodat import niet meteen nieuwe parse-schuld creëert.

---

# Deel L — prioriteitsmatrix

## 24. Hoge waarde / relatief beheersbaar

1. Darlings
2. `.qwbook`
3. Placeholders
4. Lamplicht
5. Locale-context + checker

## 25. Hoge waarde / technisch gevoeliger

6. Ghost paragraphs
7. Schrijfstatistiek
8. DOCX-import
9. Lamplicht Papier/editor-specifieke theme tokens

## 26. Eerst onderzoeken

10. Intern documentmodel
11. Planning reorder
12. Locaties
13. Tijdlijn
14. Wiki-links
15. Relatievisualisatie
16. uitgebreidere typography/footnotes

## 27. Later/platform

17. code signing
18. installer
19. updater
20. macOS/Linux

---

# Deel M — definition of ready voor een v2-feature

Een feature gaat pas van roadmap naar implementatie als het ontwerpvoorstel antwoord geeft op:

1. Welk concreet schrijfprobleem lossen we op?
2. Wat ziet/doet de gebruiker?
3. Welke bestanden/modules veranderen?
4. Welke data wordt persistent?
5. Is een schema/version bump nodig?
6. Hoe werkt twee-computer/Dropbox?
7. Welke revisions worden gecontroleerd?
8. Wat gebeurt er bij writefailure?
9. Wat gebeurt er bij corrupte/future data?
10. Hoe werkt History/herstel?
11. Wat ziet zoeken/vervangen?
12. Wat ziet spelling?
13. Wat telt woordtelling/statistiek?
14. Wat exporteert?
15. Wat krijgt de Meelezer?
16. Hoe werkt Undo?
17. Hoe werkt keyboard/focus/DPI?
18. Welke tests bewaken het contract?
19. Wat bouwen we expliciet niet?
20. Hoe migreren bestaande boeken?

---

# Deel N — nieuwe ideeën toevoegen

Nieuwe ideeën worden eerst aan deze roadmap toegevoegd met:

- probleem;
- gewenst resultaat;
- status;
- prioriteit;
- afhankelijkheden;
- data-effect;
- privacy-effect;
- belangrijkste risico;
- reden waarom dit nú relevant is.

Pas daarna volgt een ontwerpvoorstel en pas na goedkeuring implementatie.
