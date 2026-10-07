# QuietWriter 1.2.24: onafhankelijke code- en architectuurreview

**Reviewer:** Claude · **Datum:** 7 oktober 2026 · **Snapshot:** `QuietWriter-1.2.24-Claude-review.zip` (`__version__ = "1.2.24"`)
**Opdracht:** `CLAUDE_REVIEW_1_2_24.md`. Er is geen productiecode gewijzigd: alle tests en harnassen staan buiten de
projectmap.

Legenda: **[getest]** = gereproduceerd met code of Qt-events · **[gelezen]** = vastgesteld door code-inspectie, niet
uitgevoerd · **[afgeleid]** = conclusie op basis van het voorgaande.

---

## 1. Executive summary

De richting klopt. `DocumentView` is voor alle **renderende** consumers (editorhighlighter, EPUB, PDF en DOCX-export)
nu echt de enige interpretatiebron. In mijn tests geven die vier exports exact dezelfde zichtbare tekst, inclusief
escapes. De `ImportDocument`-grens voor DOCX is schoon, en de transactionele import rolt correct terug bij schrijf-
en mediafouten. De suite is groen.

Toch is 1.2.24 **niet releaseklaar**. De escaping is geïmplementeerd als **echte, onzichtbare tekens in het
editordocument**, en de editor behandelt ze niet als één geheel. Gevolg:

- **Blocker.** Een `*` typen en die als tikfout wegbackspacen laat een zichtbare backslash achter (`a*` + Backspace +
  `b` → bron en export: `a\b`). Twee keer Delete, wat zichtbaar "niets doet", maakt van letterlijk `*nadruk*`
  cursieve tekst.
- **High.**
  - Kopiëren en plakken van vette of cursieve tekst binnen QuietWriter levert zichtbare sterretjes op.
  - Delete, Backspace, Enter, Zoek-en-vervang en Shift+Enter kunnen gewone tekst nog steeds structuur geven.
  - Zoeken vindt zichtbare tekst als `5*3` of `was heel moe` niet.
  - Typen kost bij elke toets een volledige herparse van het hoofdstuk, twee keer. Bij 30k woorden is dat 93 ms per
    toets, bij 100k woorden 294 ms. Een DOCX zonder koppen wordt precies zo'n hoofdstuk.

**Advies:** maak escapes in de editor **atomair**, en dwing de productregel af als invariant op elke bewerking. Doe
dat vóór er nieuwe syntax (links, tabellen) bij komt. Platte, Markdownachtige opslag blijft de juiste keuze, maar dan
als **QuietWriter-profiel** met syntaxversie, niet als belofte van CommonMark-compatibiliteit (zie §10).

---

## 2. Wat ik daadwerkelijk heb getest en geïnspecteerd

**Omgeving:** Linux, Python 3.13, PySide6 6.11.2 (offscreen), python-docx 1.2.0, markdown-it-py (CommonMark-referentie).

| Onderdeel | Hoe | Resultaat |
|---|---|---|
| `tools/check_undefined_names.py` | uitgevoerd | ✅ OK |
| `tools/check_locales.py` | uitgevoerd | ✅ 1511 sleutels in 5 talen |
| `pytest` (volledig, met Qt) | uitgevoerd | ✅ **672 geslaagd, 0 overgeslagen**, 304 subtests (121 s) |
| `main.py --smoke-test` | uitgevoerd | ✅ rc 0 |
| Escaping in de echte editor | eigen Qt-harnas met `QTest.keyClick`/`keyClicks`, Ctrl+B/I, Ctrl+Z/Y, Shift+Enter, `createMimeDataFromSelection`/`insertFromMimeData` op `ManuscriptEditor` | 46 scenario's; zie §5 |
| Consumers naast elkaar | dezelfde lastige bron door zoeken, vervangen, woordtelling, AI-context, PDF-HTML, DOCX, EPUB en Markdown, met de Markdown-uitvoer weer gerenderd door CommonMark | zie §4 en §5 |
| DOCX-import | eigen corpus van 3 documenten en 5 foutinjecties via `Library.import_docx_book` | zie §6 |
| Performance | `parse_document`/`count_words`/`text_for_language_tools`/`text_for_ai_context` op 2k–100k woorden; echte toetslatentie in `MainWindow`; cProfile; DOCX-import van 85k woorden met 20 beelden | zie §7 |
| Code | `document_view.py`, `manuscript_markup.py`, `import_document.py`, `docx_io.py`, `media/markup.py`, `media/store.py`, de importroute in `storage.py`, de relevante delen van `manuscript_editor.py` en `editor_page.py`, `darlings_page.py`; afhankelijkheden met grep; dode code met vulture | zie §4 en §8 |

**Teststatus:** de opdracht noemt 563 geslaagd en 45 overgeslagen (608 in totaal). Deze zip geeft 672 geslaagd met
PySide6 aanwezig. Het verschil komt waarschijnlijk door een andere snapshot of andere parametrisatie. Dit heb ik niet
verder uitgezocht.

**Niet getest:**
- Windows zelf. De IME en dode toetsen (bijvoorbeeld `^` + `*` op een internationaal toetsenbord), die via
  `inputMethodEvent` en niet via `keyPressEvent` binnenkomen, heb ik niet getest. Ze kunnen de escaping omzeilen
  [afgeleid].
- Slepen van tekst binnen de editor (drag & drop).
- Echte Word-bestanden. Mijn DOCX-corpus is gebouwd met python-docx en handgeschreven OOXML.
- Een schermlezer.
- OneDrive en virusscanners tijdens `os.replace` van de staging-map.
- Het EPUB-resultaat in een echte e-reader. Ik heb alleen de XHTML-tekst gecontroleerd.

---

## 3. Bevindingen per ernst

### BLOCKER

#### B1. De verborgen escape-backslash is een los, navigeerbaar en verwijderbaar teken [getest]

**Waar:** `manuscript_editor.py` `keyPressEvent` (regel ~774–806) zet `\*` in het document. Daarna behandelt Qt de
`\` als een gewoon teken. Er is geen cursor-, Backspace- of Delete-logica die het paar `\x` als één eenheid ziet.

| Reproductie (echte toetsaanslagen) | Bron daarna | Zichtbaar / export |
|---|---|---|
| typ `a*`, Backspace, typ `b` | `a\b` | **`a\b`** (er staat een backslash in je boek) |
| typ `5*3`, ←, Backspace | `5\3` | **`5\3`** |
| typ `- `, 2× Backspace, typ `Kom` | `\Kom` | **`\Kom`** |
| typ `*nadruk*`, Home, Delete, dan Delete vóór de tweede `*` | `*nadruk*` | **cursief "nadruk"**: de sterren verdwijnen, terwijl beide Deletes zichtbaar niets deden |
| typ `a*b`, zet de cursor tussen `\` en `*` (bereikbaar met ←), typ `X` | `a\X*b` | **`a\X*b`** |
| typ `5*3`, 2× ← vanaf het eind | cursorpositie 2 | de cursor staat **binnen** de escape |

**Waarom blocker:** het gebeurt bij het meest alledaagse gebruik, namelijk een tikfout corrigeren. Het beschadigt
zichtbare tekst stil, wordt opgeslagen en komt in elke export terecht. De handmatige Windows-check ("`*316…` blijft
gewone tekst") dekt alleen typen, niet corrigeren.

**Richting (geen code):** behandel `(backslash, escaped char)` als een atomaire eenheid in de editor.
- Cursorbewegingen slaan de backslash over.
- Backspace en Delete verwijderen het paar.
- Typen binnen het paar verplaatst eerst de cursor naar buiten.
- Na elke bewerking normaliseert een kleine regel weesbackslashes (een `\` die door een bewerking geen
  escapebaar teken meer volgt) binnen dezelfde undo-transactie.

### HIGH

#### H1. Kopiëren en plakken van opgemaakte tekst binnen QuietWriter maakt zichtbare sterretjes [getest]

**Waar:** `createMimeDataFromSelection` (`manuscript_editor.py:302`) haalt alleen escapes en open-puntmarkers weg,
niet `**`, `*` en `<u>`. `insertFromMimeData` (`:326`) escapet de geplakte tekst daarna als letterlijke invoer.

**Reproductie:** selecteer `Hij was **heel** moe en *erg* stil.` en kopieer.
- Op het klembord staat `'Hij was **heel** moe en *erg* stil.'`.
- Na plakken toont de editor letterlijk `Hij was **heel** moe en *erg* stil.`. De opmaak is weg en de sterren zijn
  zichtbaar.
- Naar Word of e-mail lekt dezelfde Markdownsyntax mee.

**Richting:** zet op het klembord `text/plain` = de zichtbare projectie (via `inline_runs`). Geef binnen de app een
eigen MIME-type mee (bijvoorbeeld `application/x-quietwriter-source`) dat de bron behoudt, met dezelfde validatie als
`prepare_markdown_insertion`. Optioneel kan `text/html` mee voor Word.

#### H2. Gewone tekst kan nog steeds structuur worden zonder expliciete opmaakactie [getest]

De escaping vangt alleen het moment dat je een spatie na een prefix typt. Elke andere bewerking die een regelbegin
verandert, wordt niet gecontroleerd:

| Reproductie | Resultaat |
|---|---|
| `In 1944. Het was koud.`, selecteer `In ` en druk Delete | regel wordt **genummerde lijst** "Het was koud." |
| `Hij riep - Kom je mee?`, cursor vóór `- Kom`, Enter | nieuwe regel wordt **opsomming** "Kom je mee?" |
| `x- Kom`, Backspace op `x` | **opsomming** "Kom" |
| Zoek `Bram`, vervang door `*Bram*` (`replace_searchable_text`, en `editor_page.py:2346` `cur.insertText(...)`) | **cursief** "Bram": de vervangtekst wordt niet geëscaped |
| Shift+Enter, typ `- twee` | de editor toont gewone tekst; DocumentView en export zien een **opsomming** (zie H4) |
| Plak `![foto](assets/images/<32 hex>.png)` | er ontstaat een **beheerd afbeeldingsblok** naar een niet-bestaand bestand |
| Typ of plak een open-puntmarker | de markerparser (`placeholders._NEW_OPEN_RE`) negeert escapes. Getypt `\<!--qw:todo:…-->` wordt alsnog een open punt |

**Richting:** dwing de productregel af als **invariant per bewerking**, niet per toets. Vergelijk na elke niet-
expliciete bewerking (toets, delete, enter, plakken, vervangen, slepen) de `classify_block_line` en de inline-spans van
de geraakte regels vóór en na. Ontstaat er nieuwe structuur zonder expliciete actie, voeg dan in dezelfde
undo-transactie de escape toe. Eén centrale `ensure_literal_edit(old, new, changed_range)` vervangt dan de verspreide
toetslogica.

#### H3. Zoeken divergeert van wat de schrijver ziet [getest]

**Waar:** `collect_search_matches` (`editor_page.py:2279–2296`) zoekt in `text_for_language_tools`. Die vervangt
escapes **en opmaaktekens** door spaties (`document_view.py:279–302`).

| Zoekterm (zichtbaar in de editor) | Gevonden? |
|---|---|
| `5*3` (bron `5\*3`) | ❌ |
| `C:\pad` (bron `C:\\pad`) | ❌ |
| `**literal**` (letterlijk getypt) | ❌ |
| `was heel moe` (bron `was **heel** moe`) | ❌ (spaties op de plek van `**`) |
| `*31623455`, `Kom je mee` | ✅ |

**Richting:** zoek in een **zichtbare projectie met offsettabel** (zichtbare index → bronindex) in plaats van in een
masker met spaties. Dat lost ook de zoekopdrachten over opmaakgrenzen op. Vervangen moet dan via de escaping-
serializer.

#### H4. Shift+Enter (U+2028) en andere Unicode-regelscheidingstekens splitsen DocumentView-blocks [getest]

**Waar:** `parse_document` gebruikt `str.splitlines(keepends=True)` (`document_view.py:184`). Python splitst daar ook
op `\u2028`, `\x0c`, `\x85`, `\x1c`–`\x1e` en `\u2029`.

**Reproductie:** typ `Regel een`, Shift+Enter, `regel twee`.
- Bron: `'Regel een\u2028regel twee'`.
- Qt ziet 1 blok.
- DocumentView ziet 2 alinea's, waarvan de eerste tekst `'Regel een\u2028'` is (het scheidingsteken zit in de
  bloktekst).
- `een\u2028- twee` wordt in DocumentView een **opsomming**, terwijl de editor één alinea toont. De escape-check in
  `keyPressEvent` ziet het prefix `Regel een\u2028-` en escapet niet.

Hiermee klopt "één fysieke bronregel = één alinea" niet meer tussen de editor en de exports.

**Richting:** splits uitsluitend op `'\n'`. Leg vervolgens bewust vast wat U+2028 betekent (zie het voorstel in §9.3).

#### H5. Volledige herparse van het hoofdstuk bij elke toetsaanslag, twee keer [getest]

**Waar:** `on_text_changed` → `update_counts` (`editor_page.py:1558`) → `toPlainText()` → `count_words` →
`parse_document` over het hele hoofdstuk. cProfile: 99% van de toetstijd, 20 `parse_document`-aanroepen bij 10
toetsen. Daarnaast maakt `_editor_source_text()` per toets een volledige kopie voor de dirty-check. Zie §7.

### MEDIUM

**M1. Oude boeken (vóór 1.2.19) worden anders weergegeven zonder dat hun bytes veranderen [getest]**

`escape_ranges` (`manuscript_markup.py:31`) herkent `\` vóór `\ * ~ ` < > # - .` **overal in de regel**. De
schrijfkant maakt `\-`, `\>`, `\#` en `\.` echter alleen aan het **begin van een regel**.

| Oude bron | Was zichtbaar | Nu zichtbaar |
|---|---|---|
| `\\server\share` | `\\server\share` | `\server\share` |
| `C:\Users\lucas\.config` | idem | `C:\Users\lucas.config` |
| `pijl \-> rechts` | idem | `pijl -> rechts` |
| `regex a\.b` | idem | `a.b` |
| `\#tag` | idem | `#tag` |

Dit komt zelden voor in proza, maar het is precies "anders geïnterpreteerd zonder byteverandering". Ook
`classify_block_line` (`document_view.py:103–106`) hard-codeert een tweede, smallere escapelijst.

**Richting:**
- Maak de leesgrammatica gelijk aan de schrijfgrammatica: `\-`, `\>`, `\#` en `\.` alleen op prefixposities.
- Leg de escapeset op één plek vast.
- Gate de nieuwe interpretatie met een syntaxversie in `book.json` (zie §9.4).

**M2. Expliciete opmaak normaliseert de bron stil (non-breaking spaces) [getest]**

`apply_format_action` (`manuscript_editor.py:962`) leest `old = self.toPlainText()`. De eigen docstring van
`source_text()` waarschuwt dat `toPlainText()` U+00A0 normaliseert. `tien\u00a0procent` + Ctrl+B wordt
`**tien procent**`: de vaste spatie is weg. Hetzelfde geldt voor de checkstatus in het contextmenu (`:907`).
Gebruik `source_text()`.

**M3. DOCX-import: stil verlies en onjuiste meldingen [getest]**

Details in §6:
- Tekst in tekstvakken verdwijnt **zonder melding**.
- Veldresultaten verdwijnen, terwijl de melding zegt dat ze "waar mogelijk" zijn geïmporteerd.
- Een zachte return wordt zonder melding een nieuwe alinea.
- Een pagina-einde midden in een alinea plakt tekst zonder spatie aan elkaar (`einde.Na`).
- Tabeltekst verdwijnt volledig (wel gemeld).
- **Eén kapotte afbeelding laat de hele import mislukken**, met de verkeerde tekst "Het gekozen PNG-bestand is niet
  geldig".

**M4. Markdown-export plakt alinea's samen in elke CommonMark-renderer [getest]**

De Markdown-export schrijft de hoofdstukbron regel voor regel weg. QuietWriter-alinea's staan direct onder elkaar.
markdown-it (CommonMark) rendert 3 QuietWriter-alinea's als **één `<p>`**. Voor het exportdoel "Op een website of blog
plaatsen" verlies je dus de alineagrenzen. De escapes zelf zijn wel geldige CommonMark-escapes en renderen correct.

**M5. Architectuur: verborgen import-cycli en semantiek op de verkeerde plek [gelezen]**

- `document_view` importeert `manuscript_markup` en `media.markup` op moduleniveau. Beide importeren `document_view`
  weer lui in functies (`manuscript_markup.py:646, 658, 683`; `media/markup.py:145, 164, 244, 276, 282`). De
  cycli werken alleen dankzij die luie imports.
- Woordtelling, zoek-masking, zoeken/vervangen en AI-tekst staan in `media/markup.py`. Dat is een **mediamodule**.

Zie §4.

**M6. DOCX-import is traag door herhaalde stijlopzoekingen in python-docx [getest]**

85k woorden met 20 JPEG's duurt 16 s. cProfile: 47 van de 50 s (onder profiler) zit in `paragraph.style` en
`run.style` → `Styles.default()` → `default_for`, dat bij elke run alle stijlen scant. Een cache per
style-id tijdens één import lost dit op.

**M7. De escaping-testdekking zit op de verkeerde laag [gelezen]**

- De enige editortest voor escaping (`test_editor_escaping_imports.py`) controleert met `ast` of vier functies
  **geïmporteerd** worden.
- Er is geen enkele Qt-test die `*` typt, backspacet, kopieert of plakt.
- 38 testbestanden bevatten samen ~208 bronteksttests (`… in source`). Die bewijzen dat code bestaat, niet dat ze
  werkt.

Zie §8.

### LOW

| # | Bevinding | Waar | Soort |
|---|---|---|---|
| L1 | Weesmappen `.import-<uuid>` na een crash of kill worden nooit opgeruimd. `list_books` slaat ze alleen over. Mogelijk grote beelden, en ze synchroniseren mee met OneDrive. | `storage.py:1228`; geen opruimcode gevonden | [gelezen] |
| L2 | De "validatie" vóór publiceren controleert alleen of de hoofdstukbestanden bestaan, niet of de beeldverwijzingen resolven of de UTF-8 weer parseert. | `storage.py:1275–1284` | [gelezen] |
| L3 | Voetnoten worden gedetecteerd op de **relatie** (`/footnotes`), niet op `w:footnoteReference`. Dat kan valse meldingen geven bij Word-bestanden met alleen separatorvoetnoten. Eindnoten, opmerkingen en VML-beelden (`v:imagedata`) worden niet gedetecteerd. | `docx_io.py:479–483, 260` | [gelezen] |
| L4 | AI-context nummert elke genummerde regel als `1.` (`3. derde punt` → `1. derde punt`). | `document_view.py:438–439` | [getest] |
| L5 | De Bewaarplaats-preview en naamloze fragmenttitels tonen de ruwe bron (`5\*3`, `**vet**`, `\- Kom`). Zoeken in fragmenten gaat over de bron. De roundtrip terug in het manuscript is wél correct. | `darlings_page.py:116–118, 161–168, 364` | [getest] |
| L6 | Dode of alleen-in-tests gebruikte code: `_BLOCK_PREFIX_RE` (`manuscript_markup.py:15`), `_BULLET_RE`/`_NUMBER_RE` (`pdf_exporter.py:49–50`), `text_without_image_blocks`. `parse_docx_book` en `paragraph_to_markdown` worden alleen door tests gebruikt (12 testbestanden), terwijl de productie `import_docx_book` gebruikt (6 testbestanden). | diverse | [gelezen] |
| L7 | Versie- en documentatiedrift. `README.md:5` zegt "Status: `1.2.12`" en `SNAPSHOT_INFO.txt` zegt 1.2.13. `MANUSCRIPT_SYNTAX.md` spreekt zichzelf tegen: "nog geen algemene escapingregel" en "Zoek/spelling/AI volgen later" staan naast de 1.2.19/1.2.21-secties. Geen test koppelt `README` aan `__version__`. | | [gelezen] |
| L8 | CRLF wordt LF bij de eerste save (`read_text` gebruikt universele newlines, de write `newline=''`). Dit bestond al vóór 1.2.24 en is semantisch neutraal, maar strikt genomen een byteverandering. | `storage.py` `read_chapter` | [gelezen] |
| L9 | `inline_runs` kost O(tekens × spans): een alinea van 20k tekens met 800 spans duurt 627 ms. Zeldzaam, maar het treft exports van zwaar opgemaakte geplakte tekst. | `document_view.py:331–335` | [getest] |
| L10 | Ctrl+B over een selectie die op een spatie eindigt geeft `**Een … en **`. QuietWriter leest dat als vet, CommonMark niet (niet right-flanking). Dat is pas relevant zodra Markdown-compatibiliteit belangrijk wordt. | `toggle_inline` | [getest] |

---

## 4. Architectuurbeoordeling

### A1. Is `DocumentView` werkelijk de centrale interpretatiebron?

Voor **renderen en exporteren: ja**. Gebruik dat ik heb nagelopen:
- De highlighter gebruikt `parse_block_line` en `escape_ranges`.
- XHTML/EPUB en PDF gebruiken `iter_content_blocks` en `content_inline_runs`.
- DOCX-export gebruikt `inline_runs`.
- Contents/publication gebruikt `visible_block_text`.
- Spelling en zoeken gebruiken `text_for_language_tools`.
- AI gebruikt `text_for_ai_context`.

Mijn kruistest (§5) gaf identieke zichtbare tekst in PDF, DOCX en EPUB.

**Nog niet centraal:**

| Interpretatie | Waar | Waarom problematisch |
|---|---|---|
| Escapeset (lezen) | `_ESCAPABLE_LITERAL_CHARS` overal-in-de-regel | anders dan de schrijfset (M1) |
| Escapeset (blokprefix) | eigen lijst in `classify_block_line:103–106` | tweede bron van waarheid |
| Escapeset (schrijven) | `escape_literal_typed_char` (`*~`<\`) en `escape_literal_space_prefix` (`- > ## n.`) | drie plekken, niet symmetrisch |
| Regelsplitsing | `splitlines()` in DocumentView versus `'\n'` in Qt-blokken en `split('\n')` in de serializer | H4 |
| Open-puntmarkers | `placeholders._NEW_OPEN_RE` | negeert escapes; ook getypte markers worden semantiek |
| Afbeeldingssyntax | `media.markup._IMAGE_RE` via `finditer` over de **hele tekst** in `mask_image_paths` en `_protected_image_ranges` | herkent ook afbeeldingssyntax midden in een alinea, terwijl DocumentView alleen hele regels als beeld ziet |
| Woordtelling | eigen zichtbare-tekstlogica in `count_words` | dupliceert `visible_block_text` |
| Zoek-masking | spaties in plaats van een zichtbare projectie | H3 |
| Markdown-import | `markdown_io` schrijft de bron rechtstreeks, niet via `ImportDocument` | importgrens niet uniform (§6) |

### A2. Circulaire en verkeerde afhankelijkheden

```
document_view ──(top-level)──▶ manuscript_markup ──(lazy)──▶ document_view
document_view ──(top-level)──▶ media.markup     ──(lazy)──▶ document_view
search.py ──▶ media.markup.text_for_search ──▶ document_view
```

De cycli zijn functioneel, maar ze maken de laagindeling onduidelijk: wie is fundament? Voorstel zonder big-bang:

1. `manuscript_syntax.py` (puur, zonder imports uit het project): delimiters, escapeset, `parse_inline_spans`,
   `escape_ranges`, `classify_block_line`, regelsplitsing.
2. `document_view.py`: alleen interpretatie. Importeert `manuscript_syntax` en de pure image-regex.
3. `manuscript_text.py` of `document_projection.py`: woordtelling, zichtbare projectie met offsettabel, zoeken,
   AI-tekst. Verhuist uit `media.markup`.
4. `manuscript_serialize.py`: de huidige schrijfhelpers en de bewerkingsfuncties (`toggle_inline` en dergelijke).
5. `media.markup`: alleen beeldsyntax en paden.

### A3. Scheiding bron / view / importmodel / serializer

Het concept is helder en goed gedocumenteerd: bron is autoritatief, de view is read-only, het importmodel is neutraal
en de serializer staat aan de grens. Twee zwaktes:

- **De editor heeft geen eigen model.** Die bewerkt de *bron* rechtstreeks in een `QTextDocument`. Daardoor is
  escaping een teken in plaats van een eigenschap (B1). Atomaire escapes en een bewerkingsinvariant (H2) zijn de
  minimale correctie. Een editor op een zichtbare projectie is de grote correctie (zie §11, blok 5).
- **`manuscript_markup.py` (1028 regels) mengt drie verantwoordelijkheden:** syntaxdefinitie, serializer en
  bewerkingsalgoritmen.

### A4. Is `ImportDocument` onafhankelijk genoeg van de opslagsyntax?

**Grotendeels wel.** De reader (`paragraph_to_import_block`) maakt geen enkel `*` meer aan, en escaping gebeurt
uitsluitend in `serialize_inline_text`. Mijn DOCX-test met `*31623455`, `**niet vet**`, `\pad`, `- Kom` en `1944.`
kwam correct geëscaped binnen. Beperkingen:

- **`ImportInlineRun.styles` is een `frozenset[str]` zonder attributen.** Links (href), taal en
  voetnootverwijzingen passen daar niet in. Voeg `attrs: Mapping[str, str]` toe vóór je links bouwt.
- **`ImportBlock.kind` mist `line_break` (zachte return) en `table`.** Daardoor sluipen Word-semantieken via `\n`
  in `run.text` naar de serializer, die ze als alinea-einde behandelt (M3).
- **De verliesrapportage is een losse lijst strings.** Een gestructureerde `ImportLoss(kind, count, location,
  sample)` maakt testen en tonen beter.

### A5. Kan semantiek nog ongemerkt verschillen tussen consumers?

Ja, op deze punten (alle getest):

| Consumer | Verschil |
|---|---|
| Editor ↔ export | U+2028 en andere scheidingstekens (H4) |
| Editor ↔ zoeken | escapes en opmaakgrenzen (H3) |
| Editor ↔ AI | lijstnummering (L4) |
| Editor ↔ Markdown-export | alineagrenzen (M4) en CommonMark-flanking (L10) |
| Editor ↔ klembord | opmaaktekens (H1) |
| Editor ↔ Bewaarplaats-preview | ruwe bron (L5) |

PDF, DOCX en EPUB onderling: **geen verschil gevonden**.

---

## 5. Escaping en backwards compatibility

### Testmatrix (echte Qt-events op `ManuscriptEditor`)

| Scenario | Resultaat |
|---|---|
| Typen: `*31623455`, `5*3 = 15`, `- Kom je mee?`, `1944. Het was koud.`, `## kop`, `> citaat`, `* ster`, `1. lijst`, `C:\pad\naar`, `twee *sterren* hier`, `**literal**`, `` a `code` b ``, `~~weg~~`, `<u>x</u>`, `***` | ✅ alle 15 blijven letterlijk |
| Plakken: `**sterretjes**`, meerregelige lijst, `1944.` + `## …`, `C:\temp\*.txt` | ✅ |
| Plakken: beheerde afbeeldingsregel | ❌ wordt een afbeeldingsblok (H2) |
| Plakken: open-puntmarkers | ✅ worden bewust gestript, zoals ontworpen |
| Kopiëren en plakken van opgemaakte tekst binnen de app | ❌ H1 |
| Ctrl+I over `\*31623455` (inclusief de verborgen escape) | ✅ `*\*31623455*`, zichtbaar `*31623455` cursief |
| Ctrl+I met selectie die ná de verborgen `\` begint | ⚠️ `\**31623455*`: de ster valt buiten de cursief. Klein, maar het toont dat selecties binnen escapes kunnen beginnen. |
| Ctrl+B over `5*3`, plus Undo en Redo | ✅ |
| Ctrl+B aan en uit over tekst met geëscapete sterren | ✅ terug naar `Een \*ster\* en ` |
| Typen van `*` plus Undo en Redo | ✅ één stap, bron exact terug |
| `- ` typen plus 2× Undo | ✅ `\- ` → `-` → leeg |
| Plakken plus Undo | ✅ |
| Backspace, Delete, cursor en typen rond een escape | ❌ B1 |
| Delete, Backspace en Enter die een prefix vormen | ❌ H2 |
| `setPlainText(source)` → `source_text()` roundtrip | ✅ bytes identiek |
| Exports van geëscapete tekst (PDF, DOCX, EPUB) | ✅ zichtbare tekst correct, geen backslashes |
| Markdown-export van geëscapete tekst | ✅ geldige CommonMark-escapes (wel M4) |
| Bewaarplaats: bron → fragment → invoegen | ✅ semantiek behouden; ❌ preview toont de bron (L5) |
| Opmaak over tekst met NBSP | ❌ M2 |

### Expliciete antwoorden

1. **Kan nieuwe gewone invoer nog onverwacht semantiek worden?** Ja.
   - Via Delete, Backspace en Enter die een regelprefix vormen.
   - Via het verwijderen van verborgen escape-backslashes.
   - Via Zoek-en-vervang.
   - Via Shift+Enter (H4).
   - Via plakken van afbeeldingssyntax.
   - Via (getypte) open-puntsyntax.

   Direct typen en gewoon plakken zijn nu wel goed afgedekt.
2. **Kan escaping zichtbare tekst, cursorposities, selecties of Undo beschadigen?**
   - Zichtbare tekst en cursor/selectie: **ja** (B1). De cursor kan binnen een escape staan; Backspace laat een
     zichtbare `\` achter.
   - Undo: **nee**, in alle geteste gevallen correct en atomair.
3. **Kunnen oude 1.2.13-boeken anders worden geïnterpreteerd zonder byteverandering?** **Ja**, bij elke `\` vóór een
   van ``\ * ~ ` < > # - .``, ook midden in een regel (M1). Ik heb geen gevallen gevonden waarin oude regels zonder
   backslash anders worden gelezen dan in 1.2.13. Een golden corpus van 1.2.13-hoofdstukken ontbreekt in de tests.
4. **Wordt bestaande bron bij save alsnog stil genormaliseerd?**
   - Bij een gewone save: **nee**, bytes blijven gelijk, met uitzondering van CRLF → LF (L8, dit bestond al).
   - Bij expliciete opmaakacties: **ja**, U+00A0 wordt een gewone spatie (M2).
   - Er is geen migratiescan bij openen. Dat is correct.

---

## 6. DOCX-importbeoordeling

### Route

`DOCX → read_docx_import_document → ImportDocument → serialize_import_chapter → staging (.import-<uuid>) →
_publish_staged_import (load_book + bestandscheck) → os.replace`. De route is helder en de transactiegrens zit op de
goede plek.

### Resultaten [getest]

| Geval | Uitkomst | Gemeld? |
|---|---|---|
| H1/H2 → sectie en hoofdstuk | ✅ "Deel Een" / "Hoofdstuk 1, 2" | n.v.t. |
| Direct vet en cursief | ✅ `**vet**`, `*cursief*` | n.v.t. |
| Word `Strong`/`Emphasis` en een eigen stijl afgeleid van Strong | ✅ via de stijlketen | n.v.t. |
| Markupachtige letterlijke tekst (`*316`, `5*3`, `**niet vet**`, `\pad`, `- Kom`, `1944.`) | ✅ correct geëscaped | n.v.t. |
| `List Bullet` | ✅ opsomming | n.v.t. |
| **Zachte return (`w:br`)** | ⚠️ wordt **twee alinea's** (`run.text` geeft `\n`, de serializer splitst) | ❌ **nee** |
| **Pagina-einde midden in een alinea** (niet-pagina-georiënteerde modus) | ⚠️ `Voor de pagina-einde.Na het pagina-einde.`: einde weg, geen spatie | ❌ **nee** |
| Hyperlink | tekst ✅, URL weg | ✅ |
| Tabel | **alle celtekst weg**, ook de positie | ✅ (alleen een aantal) |
| PNG 2× hetzelfde | ✅ gededupliceerd tot één bestand, twee verwijzingen | n.v.t. |
| Alt-tekst (`docPr/@descr`) | ✅ | n.v.t. |
| JPEG | ✅ | n.v.t. |
| GIF | overgeslagen | ✅ |
| Beeld midden in een alinea | wordt een blok ná de alinea; dubbele spatie blijft in de tekst (`Tekst met  midden in.`) | ✅ |
| Tracked changes `w:ins` | **ingevoegde tekst weg** | ✅ (formulering "kan" is mild: hij is altijd weg) |
| Veld `w:fldSimple` (PAGE = "7") | **resultaattekst weg** | ⚠️ melding zegt "waar mogelijk als zichtbare tekst geïmporteerd". Dat is onjuist. |
| Inline en blok-`w:sdt` | **tekst weg**, de blok-SDT-alinea volledig | ✅ ("kan niet volledig") |
| **Tekstvak (`w:txbxContent`)** | **tekst weg** | ❌ **nee: stil verlies** |
| Schrijffout bij het 2e hoofdstuk | exception, staging weg, geen half boek | ✅ |
| Mediafout | idem | ✅ |
| Doelmap bestaat al | `FileExistsError`, staging weg | ✅ |
| **Eén corrupte PNG** (content-type png) | **hele import faalt**: `UnsupportedImageError: Het gekozen PNG-bestand is niet geldig.` Ook de tekst komt niet binnen. | ⚠️ technisch en misleidend |
| Staging-resten na de foutgevallen | geen | ✅ |
| Weesstaging na crash of kill | niet opgeruimd (L1) | [gelezen] |

### Oordeel

De **transactionaliteit is goed**: in alle foutpaden bleef er niets halfs achter. De **verliesmelding is nog niet
volledig betrouwbaar**. Bij drie constructies verdwijnt tekst zonder correcte of met onjuiste melding (tekstvak, veld,
zachte return of pagina-einde). Bij tabellen verdwijnt alle tekst, terwijl behoud als platte tekst eenvoudig was. Een
enkel kapot beeld zou een waarschuwing moeten zijn, geen afgebroken import. De beeldvalidatie gebruikt de
bestandsextensie van de part (`media/store.py:98–111`) in plaats van de content-type of magic bytes. Dat is fragiel.

Aanbevolen principe: **geen tekstverlies zonder regel in het importrapport, en bij twijfel tekst behouden boven
structuur behouden.**
- Tekstvak: tekst als alinea + melding.
- Tabel: rijen als alinea's + melding.
- Veld: resultaattekst behouden (die staat in de runs tussen `w:fldChar separate` en `end`).

---

## 7. Performance

### Parserkosten (beste van 3, Linux)

| Woorden | Tekens | `parse_document` | `count_words` | `text_for_language_tools` | `text_for_ai_context` |
|---|---|---|---|---|---|
| 2.000 | 10k | 3,6 ms | 4,4 ms | 3,7 ms | 12,9 ms |
| 10.000 | 50k | 26,7 ms | 32,5 ms | 28,5 ms | 100,9 ms |
| 30.000 | 150k | 82,0 ms | 97,3 ms | 62,8 ms | 210,6 ms |
| 100.000 | 500k | 185,6 ms | 253,6 ms | 210,2 ms | 743,0 ms |

### Echte toetslatentie (`MainWindow`, boek met daarnaast 20 hoofdstukken van 5k woorden)

| Hoofdstuk | ms per toets | ms per `*`-toets |
|---|---|---|
| 10k woorden | 26 | 30 |
| 30k woorden | **93** | 110 |
| 100k woorden | **294** | 263 |

**Oorzaak:** `update_counts` herparset het hele hoofdstuk bij elke toets (H5). De highlighter zelf is per blok en
goedkoop. Een DOCX of Markdown zonder koppen wordt bij import **één** hoofdstuk: mijn test gaf 409k tekens (85k
woorden), en daarin is typen ~250–300 ms per toets.

**Snelle winst, in volgorde van rendement:**
1. Debounce de woordtelling (bijvoorbeeld 400 ms idle), net als de open punten.
2. Cache per blok op `(blocktekst) → woorden`, zodat alleen gewijzigde regels opnieuw tellen.
3. Maak de dirty-check incrementeel met `document().isModified()` en een revisieteller in plaats van een
   string-vergelijking per toets.
4. Optimaliseer `parse_inline_spans` (10M `startswith`-aanroepen bij 10 toetsen): één regex-tokenizer per regel.
5. `inline_runs`: vervang `active_at` (alle spans per teken) door een sweep over gesorteerde span-grenzen (L9).

**DOCX-import:** 85k woorden met 20 beelden kost ~16 s, en het hoofdstukaantal maakt niet uit. ~95% zit in
python-docx-stijlopzoekingen (M6); dat is op te lossen met een cache per style-id. Daarnaast draait de import
synchroon. Ik heb niet bekeken of de UI daarbij bevriest of een voortgangsindicator toont.

Geen andere O(n²)-patronen gevonden in de geteste paden.

---

## 8. Ontbrekende testdekking

Hoogste prioriteit eerst:

1. **Qt-tests met echte events voor escaping** (tegen B1 en H2): typen, Backspace, Delete, ←/→, Shift+Enter, Enter
   midden in een regel, selectie plus typen, kopiëren en plakken, en Zoek-en-vervang. Telkens met een assert op
   **bron** én **zichtbare tekst**. Mijn harnas `esc124*.py` (46 scenario's) is direct om te zetten.
2. **Eigenschapstest (Hypothesis)** voor de invariant "een niet-expliciete bewerking verandert nooit
   `classify_block_line` of het aantal inline-spans van een regel", over willekeurige proza met
   `* - # > . \ < ~ `` ` en cijfers.
3. **Golden corpus van 1.2.13-hoofdstukken** (inclusief backslashes, CRLF, BOM, NBSP en U+2028) met vastgelegde
   zichtbare tekst per consumer. Dat maakt "oude boeken worden niet anders gelezen" toetsbaar.
4. **Consumer-pariteitstest:** één bron, en de zichtbare tekst moet gelijk zijn in editor, zoeken, woordtelling, AI,
   PDF, DOCX, EPUB, Markdown→CommonMark en klembord.
5. **DOCX-verliesmatrix** per OOXML-constructie (tekstvak, veld, SDT, `w:ins`, `w:br`, page break in run, tabel,
   VML-beeld, eindnoot, corrupt beeld). Elke constructie moet de tekst behouden **of** precies één specifieke melding
   geven.
6. **Performancebudget-test:** `count_words` plus de toetsroute op 30k woorden onder X ms (ruim gekozen, als
   regressiewaarschuwing).
7. Test de productieroute `import_docx_book` in plaats van `parse_docx_book` (dat alleen nog in tests bestaat).
8. Vervang bronteksttests (`'def createMimeDataFromSelection' in source` en dergelijke) waar mogelijk door
   gedragstests. ~208 van zulke asserts geven schijnzekerheid.

---

## 9. Advies voor de volgende syntaxstap

**Vooraf:** voeg pas nieuwe syntax toe als B1 en H2 zijn opgelost. Elke nieuwe delimiter (`[`, `|`) vergroot anders
het oppervlak van precies die bugs.

### 9.1 Links

- **Syntax:** standaard CommonMark inline-link `[tekst](url)`. Geen referentielinks, geen titels, geen
  GFM-autolinks: een kale URL in proza blijft tekst.
- **Letterlijke haken:** escape bij typen en plakken alleen `[`. Zonder `[` kan geen link ontstaan; `]`, `(` en `)`
  blijven dan onschuldig. Dat houdt `(…)` en `[…]` in proza schoon in de bron. Leg `\[` ook in de leesgrammatica
  alleen voor dat geval vast.
- **Voor de schrijver:** Ctrl+K of een knop in de opmaakbalk opent een dialoog (tekst + adres). In de editor is de
  linktekst onderstreept of gekleurd en is `](url)` een verborgen, **beschermd** bereik, net als een beeldpad. Bewerken
  gaat via een klik of het contextmenu. De URL is nooit typbaar in de lopende tekst.
- **URL-fidelity:** sla op in de vorm `<…>` (`[tekst](<https://x.nl/a b?c=(d)>)`). Daarin mogen spaties en haakjes
  zonder percent-encoding, en hoeft de URL niet herschreven te worden. Escape alleen `<` en `>` in de URL. Valideer
  schemes (`http`, `https`, `mailto`) bij exporteren.
- **Neutraal model:** `ImportInlineRun(text, styles, attrs={'href': …})`, met link als attribuut en niet als stijl.
  - DOCX-import: `w:hyperlink r:id` → externe `href`. `w:anchor` (intern) → tekst behouden plus melding.
    `HYPERLINK`-velden → href uit `instrText` halen.
  - Export: EPUB `<a href>`, DOCX hyperlinkrelatie, PDF via QTextDocument-anchor, Markdown verbatim.
- **Nesting:** sta vet en cursief **binnen** linktekst toe, geen link binnen link, en een link nooit over een regel heen
  (consistent met de inline-regel).

### 9.2 Tabellen

- **Advies: nog geen canonieke tabelsyntax in het manuscript.** Voor romans zijn tabellen zeldzaam. GFM pipe tables
  zijn meerregelig, botsen met "één regel = één alinea", en maken van elke `|` in proza een risico.
- **Direct te doen (bij DOCX-import):** behoud de **tekst** van tabellen in plaats van die weg te gooien. Elke rij
  wordt een alinea, met cellen gescheiden door ` · ` (letterlijk, dus via de serializer geëscaped). Geef een melding
  "Tabel (3×4) is als tekst geïmporteerd". Neutraal model:
  `ImportTable(rows=((ImportCell(blocks=…), …), …), source_ref=…)`. Samengevoegde cellen worden afgevlakt, met
  melding.
- **Als tabellen later echt nodig zijn:** maak er een **beheerd, beschermd blok** van, net als afbeeldingen. Er
  ontstaat er alleen één via "Tabel invoegen", en bewerken gaat via een rasterdialoog. In de bron een afgebakend blok,
  bijvoorbeeld een Pandoc-achtige fenced div (`::: qw-table` … `:::`) met daarbinnen een GFM-pipetabel. Pipes betekenen
  **alleen** iets binnen zo'n expliciet afgebakend blok, nooit in gewone regels. Dat vergt wel een uitzondering op het
  regelmodel (meerregelig blok) en dus een syntaxversie (§9.4).

### 9.3 Regel- en alineamodel

- **Advies: behoud "één fysieke `\n`-regel = één manuscriptalinea".** Het is de basis onder stabiele offsets,
  inline-spans per regel, eenvoudige diffs en de robuustheid van de editor. Een overstap naar CommonMark-alinea's
  (lege regel als scheiding) zou elk bestaand boek anders laten lezen.
- **Wat dat betekent voor Markdown-compatibiliteit:** QuietWriter-bron is geen CommonMark-document. Daarom moet
  **Markdown-export een echte serializer** worden, die vanuit DocumentView een lege regel tussen alinea's zet en
  CommonMark-veilige delimiters kiest (M4, L10). Bij Markdown-import geldt het omgekeerde: alinea's samenvoegen tot
  een lege regel en via `ImportDocument` gaan.
- **Zachte return (poëzie, brieven):** leg U+2028 (LINE SEPARATOR) vast als officiële in-regel-regelbreuk. Dat is wat
  Qt bij Shift+Enter al opslaat. Het blijft platte tekst, en één alinea blijft één `\n`-regel.
  - `parse_document` splitst dan uitsluitend op `\n` (H4).
  - Export: Markdown `\`+newline (CommonMark hard break), DOCX `w:br`, EPUB `<br/>`.
  - DOCX-import: `w:br` → U+2028 in plaats van een nieuwe alinea.

### 9.4 Versiebeheer van syntax

**Ja, nu al.** De escape-introductie in 1.2.19 was al een interpretatiewijziging zonder versiemarkering, met M1 als
gevolg. Voorstel:

- `book.json`: `"manuscript_syntax": {"version": 2, "features": ["escape-v1", "soft-break-u2028"]}`. Ontbreekt dat,
  dan gaat het om een 1.2.13-boek.
- Bij de **eerste bewerking** van een boek zonder `escape-v1`:
  1. Maak een versie in Versiegeschiedenis.
  2. Escape oude letterlijke backslashes vóór escapebare tekens **expliciet** (`\` → `\\`). Toon het aantal
     ("3 regels aangepast zodat ze hetzelfde blijven tonen").
  3. Zet de feature.

  Dat is een **zichtbare, omkeerbare** migratie die bytes wijzigt om de betekenis gelijk te houden. Het tegenovergestelde
  van stil.
- Open je een boek met een **onbekende** feature (nieuwere versie), dan alleen-lezen of blokkeren met uitleg.

| Verandering | Compatibel? |
|---|---|
| Nieuwe syntax die oudere versies als letterlijke tekst laten staan **en** die oudere versies bij bewerken niet beschadigen | backwards-compatible |
| Links in een oudere versie | zichtbare `[tekst](url)` is acceptabel; Ctrl+B eroverheen kan breken (dus feature-markering nodig) |
| Andere betekenis van bestaande bytes (escapes, regelsplitsing, meerregelige blokken) | niet compatibel → versie plus expliciete conversie |

### 9.5 (Zie §10 voor de Markdownkeuze.)

---

## 10. Moet Markdownachtige opslag blijven?

| Optie | Oordeel |
|---|---|
| **Open, platte-tekstopslag als concept** | **Ja, blijven.** Herstelbaarheid (elk hoofdstuk is met Kladblok te lezen en te redden), sync-vriendelijkheid (één bestand per hoofdstuk, kleine diffs), geen vendor-lock-in, en de bestaande gebruikersdata. HTML, JSON of een database winnen alleen op rijkdom. Ze verliezen op herstelbaarheid en openheid, en vergen een migratie van élk bestaand boek. Dat is niet te rechtvaardigen. |
| **Strikte CommonMark/GFM-compatibiliteit** | **Nee, niet nastreven.** Het regel=alinea-model, `<u>`, open-puntcomments, beeldlayout-comments en de escape-op-invoer-filosofie wijken bewust af. Strikt CommonMark worden zou het alineamodel breken en elk bestaand boek anders laten lezen. |
| **QuietWriter-profiel met Markdownconventies en beperkte extensies** | **Ja, dit is de juiste positie.** Wel met drie verplichtingen: (1) het profiel is **formeel en geversioneerd** (§9.4); (2) Markdown is een **export- en importformaat met eigen serializer**, niet "de bron als .md kopiëren" (M4); (3) de editor is de enige plek waar gewone tekst bron wordt, en die grens is **atomair en invariant** (B1 en H2). |

Kort gezegd: de opslagkeuze is niet het probleem. Het probleem is dat de grens tussen "wat de schrijver typt" en
"wat in de bron staat" nu nog in de editor lekt.

---

## 11. Concrete volgorde voor de volgende ontwikkelblokken

1. **Blok 1: escapes atomair en de literal-invariant (blocker en high).**
   - Atomaire escapes: cursor, Backspace, Delete, typen erin.
   - Opruimen van weesbackslashes binnen dezelfde transactie.
   - Eén `ensure_literal_edit` na elke niet-expliciete bewerking: Enter, Delete, Backspace, plakken, vervangen,
     slepen, Shift+Enter.
   - `apply_format_action` op `source_text()`.
   - `parse_document` splitst alleen op `\n`.
   - Klembord met een zichtbare projectie plus een intern MIME-type.
   - Plakken van beeld- en markersyntax letterlijk maken.
   - **Gelijktijdig** Qt-gedragstests (§8, punten 1–2).
2. **Blok 2: zichtbare projectie als gedeelde dienst.** `visible_projection(source) → (text, offset_map)` in
   DocumentView, gebruikt door zoeken en vervangen (vervangen via de serializer), woordtelling, AI-context (met
   echte nummering), Bewaarplaats-preview en klembord. Daarbij de modulesplitsing uit §4-A2 en de opruiming van dode
   code (L6).
3. **Blok 3: performance en het syntaxversieveld.**
   - Woordtelling debounced en per blok gecached.
   - Dirty-check via revisie.
   - Tokenizer in plaats van `startswith`-loop.
   - Stijlcache in DOCX-import.
   - Daarnaast `manuscript_syntax` in `book.json`, met de expliciete, zichtbare `escape-v1`-conversie voor oude boeken
     (lost M1 op) en het golden corpus van 1.2.13.
4. **Blok 4: DOCX-import zonder stil verlies.**
   - Tekstvak, veldresultaat, SDT-tekst en tabeltekst behouden.
   - `w:br` → U+2028.
   - Een pagina-einde in een run → alineagrens of melding.
   - Een corrupt beeld wordt een melding in plaats van een afgebroken import, met validatie op content-type en magic
     bytes.
   - Gestructureerd `ImportLoss`-rapport.
   - Opruimen van wees-`.import-*` bij opstarten.
   - Markdown-import en -export via `ImportDocument` en een echte serializer.
5. **Blok 5: pas daarna links** (§9.1), met een beschermd bereik en een dialoog. Tabellen pas als er concrete vraag
   is, en dan als beheerd blok (§9.2).

---

### Bijlage: reproduceerbare harnassen

De scripts staan buiten het project, in de sessie-scratchmap, en zijn op aanvraag te leveren:
- `esc124.py`, `esc124b/c/d/e.py`: Qt-escapingmatrix met echte events.
- `consumers124.py`: pariteit tussen zoeken, vervangen, woordtelling, AI, PDF, DOCX, EPUB en Markdown/CommonMark.
- `docx124.py`: DOCX-corpus en foutinjecties.
- `perf124.py`, `prof124.py`, `docxperf124.py`, `docxprof.py`: performance en profielen.

Aanroep: `QT_QPA_PLATFORM=offscreen python3 -I <script> <pad-naar-uitgepakte-zip>`.
