# QuietWriter — ontwerp Bewaarplaats / Darlings

Status: ontwerp gereed, **niet implementeren vóór stabiele 1.0.0**.

## 1. Doel

De Bewaarplaats bewaart tekstfragmenten die een schrijver uit het manuscript wil halen zonder ze definitief kwijt te raken. Fragmenten zijn boekonafhankelijk en kunnen later in hetzelfde of een ander boek worden ingevoegd.

Dit is schrijfgereedschap, geen tweede manuscriptarchief en geen algemene notitiedatabase.

## 2. Productgedrag

Eerste slice:

- selectie **Knippen naar bewaarplaats**;
- selectie **Kopiëren naar bewaarplaats**;
- bibliotheekniveau-pagina met fragmenten;
- fragment openen/bekijken;
- invoegen op cursor in ieder boek;
- zoeken/filteren op titel, notitie, tags en tekst;
- verwijderen via een herstelbare prullenbak.

Niet in eerste slice:

- afbeeldingen;
- AI-classificatie;
- automatische opslag bij iedere Delete/Cut;
- syncservice;
- complexe rich preview;
- automatische terugplaatsing wanneer de oorspronkelijke plek niet eenduidig is.

## 3. Canonieke opslag

Voorkeur:

```text
<werkmap>/fragments/
    <uuid>.md
<werkmap>/trash/fragments/
    ...
```

Eén bestand per fragment beperkt syncconflicten en houdt data menselijk leesbaar.

Voorgestelde inhoud:

```markdown
---
id: 6a5d...
created_at: 2026-10-03T14:15:00
source_book_id: ...
source_book_title: ...
source_chapter_id: ...
source_chapter_title: ...
source_before: "laatste stuk context ervoor"
source_after: "eerste stuk context erna"
title: "Alternatieve ontmoeting"
tags: [dialoog, later]
---

De originele **Markdown** van het fragment.
```

Gebruik voor het lezen/schrijven van de kopmetadata de bestaande Markdown-frontmattercode uit `markdown_io` (zoals `split_frontmatter` en de bestaande scalar-decodering), of leg complexe ankermetadata als JSON vast. Bouw geen tweede ad-hoc YAML-quotinglaag: `source_before` en `source_after` kunnen dubbele punten, quotes en regeleinden bevatten.

De metadata-header krijgt een eigen package/schema-versie zodra het formaat definitief wordt vastgesteld.

## 4. Waarom geen enkel JSON-bestand

Een monolithisch `fragments.json` zou bij twee computers iedere toevoeging hetzelfde bestand laten wijzigen. Eén fragment per bestand:

- verkleint conflictoppervlak;
- maakt herstel eenvoudig;
- maakt handmatige inspectie mogelijk;
- laat fragmenten onafhankelijk kopiëren;
- past bij QuietWriters file-first ontwerp.

Een kleine afgeleide zoekindex/cache mag later bestaan, maar is nooit autoritatief.

## 5. Knippen is een transactie

`Knippen naar bewaarplaats` verandert twee bronnen:

1. nieuw fragment opslaan;
2. geselecteerde tekst uit hoofdstuk verwijderen.

Veiligste volgorde:

### Prepare

- valideer actieve selectie;
- lees persistente/source-text exact;
- controleer book revision;
- maak fragment-id en metadata in memory;
- schrijf fragment eerst naar tijdelijke/finale veilige fragmentroute;
- verifieer dat fragment leesbaar is.

### Commit manuscript

- voer tekstverwijdering via normale editor/source-route uit;
- gewone autosave/revisionbeveiliging blijft gelden.

### Failure

Als manuscriptwijziging niet veilig kan worden opgeslagen:

- manuscript blijft/wordt teruggebracht naar lokale zichtbare state;
- faalt het verwijderen/opslaan van het manuscript nadat het fragment al veilig is geschreven, dan blijft de tekst bewust op beide plekken staan: **dubbel is beter dan kwijt**;
- er komt daarom geen aparte `pending`-status in het MVP; de bestaande manuscript-autosave/conflictflow blijft verantwoordelijk voor de brontekst;
- nooit lokale tekst verliezen om de fragmentactie “af te maken”.

Voor implementatie moet deze failure-flow met tests worden vastgelegd.

## 6. Kopiëren is eenvoudiger

`Kopiëren naar bewaarplaats`:

- schrijft alleen fragment;
- manuscript blijft byte-identiek;
- geen boekrevisionmutatie nodig behalve verificatie dat de geselecteerde source nog overeenkomt wanneer selectie/source mapping relevant is.

## 7. Source fidelity

Fragmenttekst is de geselecteerde **canonieke Markdownbron**, niet `QTextEdit.toPlainText()` wanneer dat bronmarkup zou verliezen.

Moet behouden:

- bold/italic markup;
- headings voor zover selectie die bevat;
- scene break;
- harde spaties;
- Unicode sourcekarakters;
- line endings volgens bestaand source-contract waar relevant.

Protected image blocks vallen in v2.0 buiten scope.

## 8. Selecties die niet veilig zijn

Eerste versie weigert of begrenst:

- selectie die een beschermd mediablok doorsnijdt;
- gedeeltelijke interne QuietWriter-marker wanneer die tegen die tijd bestaat;
- history preview/read-only editor;
- corrupt hoofdstuk;
- future-format/write-blocked boek;
- stale external revision.

Foutmelding moet zeggen waarom de actie niet is uitgevoerd; nooit selectie deels muteren.

## 9. Broncontext voor terugplaatsen

Bij maken bewaren we beperkte ankercontext:

- `source_before`;
- `source_after`;
- boek/chapter ids.

Terugplaatsen op oorspronkelijke plek mag alleen automatisch wanneer de ankers nog eenduidig matchen.

Uitkomsten:

- **exact/eenduidig** -> gebruiker kan Terugplaatsen kiezen;
- **meerdere matches** -> niet automatisch; open hoofdstuk en laat gebruiker plek kiezen;
- **geen match** -> invoegen bij cursor of handmatig.

Nooit gokken.

## 10. Invoegen bij cursor

Invoegen gebruikt dezelfde source-safe editorroute als gewone tekstinvoer.

Regels:

- fragment blijft na invoegen standaard bestaan;
- aparte actie kan later “Invoegen en uit bewaarplaats verwijderen” bieden;
- Undo moet invoegen als één gebruikersactie kunnen terugdraaien;
- export/spelling/zoeken zien ingevoegde tekst daarna gewoon als manuscript.

## 11. Fragmentmetadata

MVP:

- UUID;
- created_at;
- source book id/title;
- source chapter id/title;
- before/after anchors;
- vrije titel;
- vrije notitie;
- tags.

Niet automatisch opslaan:

- volledige omliggende hoofdstuktekst;
- AI-context;
- gevoelige modelinformatie.

## 12. Bewerken van fragment

MVP kan fragmenttekst read-only tonen en alleen metadata laten wijzigen.

Waarom:

- minder editorcomplexiteit;
- voorkomt meteen een tweede volledige manuscripteditor.

Later kan tekstbewerking worden toegevoegd als praktijkgebruik dat vraagt.

## 13. UI

### Hoofdpagina

Boekonafhankelijk item in PROGRAMMA of een vergelijkbare globale groep.

Weergave:

- zoekveld;
- tagfilter;
- sortering nieuw/oud;
- fragmentlijst;
- detailpreview.

Kaart toont maximaal:

- titel of eerste regel;
- bronboek/hoofdstuk;
- datum;
- korte snippet;
- tags.

### Editoractie

Bij tekstselectie:

- contextmenu of selectie-toolbar: Knippen/Kopiëren naar bewaarplaats.

Geen grote nieuwe permanente toolbar.

## 14. Rustige automatische suggestie

Niet in MVP.

Later eventueel na een grote Delete/Cut:

- niet-modaal;
- korte herstelnotice;
- “Bewaren in bewaarplaats”;
- uitschakelbaar.

Geen popup bij normale redactiewerkzaamheden.

## 15. Verwijderen en trash

Fragment verwijderen gaat eerst naar:

`trash/fragments/`

Herstelbaar via Prullenbak of vanuit Bewaarplaats.

Permanent verwijderen pas via bestaande destructieve patronen.

## 16. Dropbox / twee computers

Eén fragment per bestand is de hoofdmaatregel.

Voor bestaande fragmenten die op twee machines worden gewijzigd geldt hetzelfde basisprincipe als andere auteursdata:

- revision vastleggen bij load;
- save checkt expected/current;
- geen silent overwrite.

Als fragmenttekst in MVP niet bewerkbaar is, beperkt dit conflict vooral metadatawijzigingen.

## 17. Index/cache

Een zoekindex mag later onder `.cache/`.

Regels:

- volledig herbouwbaar;
- corrupte cache weggooien;
- cache nooit enige bron van tags/notities/fragmenttekst;
- handles expliciet sluiten op Windows.

## 18. Woordtelling/statistiek

Darlings legt een semantische gebeurtenis bloot:

- tekst uit manuscript naar fragment verplaatst.

Wanneer schrijfstatistiek later wordt gebouwd kan dit apart worden geteld als:

- geschreven;
- verwijderd;
- naar Bewaarplaats verplaatst.

Darlings zelf krijgt daarom bij voorkeur een kleine event hook, maar **bouwt nog geen statistieksysteem**.

## 19. AI

MVP:

- Meelezer krijgt Darlings niet automatisch als context;
- geen AI-tags;
- geen AI-samenvattingen.

Later alleen expliciet:

- geselecteerd fragment als context;
- AI mag metadata/tag suggereren;
- nooit autonoom fragment verwijderen of terugplaatsen.

## 20. Export

Fragmenten worden nooit geëxporteerd als onderdeel van een boek, tenzij ze eerst in het manuscript zijn ingevoegd.

`.qwbook` is een aparte ontwerpvraag:

- standaard boekpackage bevat geen bibliotheekbrede Darlings;
- optioneel exporteren van gerelateerde fragmenten kan later worden onderzocht.

## 21. Migratie

Nieuwe map `fragments/` is bibliotheekniveau en vereist geen mutatie van bestaande boeken.

Bij eerste gebruik mag map worden aangemaakt.

Alleen de Bewaarplaats openen hoort bij voorkeur geen bestanden te schrijven behalve wanneer infrastructuur expliciet een lege directory nodig heeft; de bestaande regel “openen schrijft niet” blijft uitgangspunt.

## 22. Testplan voor implementatie

Minimaal:

### Storage

- create/read roundtrip;
- Unicode/Markdown exact;
- atomic failure behoudt bestaande fragmentbytes;
- externe wijziging wordt geweigerd;
- corrupte fragmentbron wordt niet overschreven;
- duplicate UUID/path wordt niet stil vervangen.

### Knippen

- normale selectie;
- fragmentwrite failure -> manuscript intact;
- manuscript save/conflict failure -> tekst niet verloren;
- Undo;
- read-only/history preview weigert;
- protected media range weigert.

### Kopiëren

- manuscript byte-identiek;
- fragment exact.

### Terugplaatsen

- unieke anchors;
- geen anchors;
- ambigue anchors;
- hoofdstuk verwijderd/verplaatst;
- ander boek.

### UI

- keyboard;
- contextmenu/selection toolbar;
- globale pagina zonder open boek;
- zoek/filter;
- trash/restore;
- locale NL/EN;
- 100/125/150% waar layout relevant is.

### Sync

- machine A laadt fragment;
- machine B wijzigt;
- A save -> geen overwrite;
- recovery blijft beschikbaar.

## 23. Definition of ready voor implementatie

Darlings-code start pas nadat:

- stabiele 1.0.0 is uitgebracht;
- persona-conflictfix in de 1.0-lijn groen is;
- praktische 1.0-validatie acceptabel is;
- keuze over fragmentfrontmatter/schema is bevestigd;
- failure-semantiek van Knippen expliciet is goedgekeurd;
- protected-rangegedrag is vastgesteld.

Tot dat moment is dit document uitsluitend een ontwerpcontract.
