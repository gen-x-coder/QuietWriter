# QuietWriter — review boek- en manuscriptmodel (Claude)

**Baseline:** QuietWriter 1.2.13 (snapshot `7cbf866`, dev-repo)
**Opdracht:** `documents/BOOK_FORMAT_ARCHITECTURE_RESEARCH.md` §12, stap 1–7
**Datum:** 6 oktober 2026
**Status:** reviewadvies, geen refactortoestemming. Ik heb geen QuietWriter-code gewijzigd.

---

## 0. Kort antwoord

**Advies: eerst het interne model invoeren (optie E) en meteen het besluit vastleggen dat de opslag de huidige tekstopslag blijft en gecontroleerd evolueert tot een geformaliseerde QuietWriter-syntaxis (optie B, "QWM"). HTML- en JSON-opslag (C/D) voor de 2.x-horizon afwijzen.**

De vijf belangrijkste redenen, allemaal hieronder met bewijs onderbouwd:

1. **Het grootste probleem is niet het opslagformaat, maar dat er geen centrale interpretatie is.** Hetzelfde hoofdstuk wordt door vier levende blockparsers (editor/highlighter, EPUB, PDF, DOCX-export) en één dode parser met afwijkende semantiek gelezen. Er bestaat zelfs al verschil tussen inline-parsing over de hele tekst en per regel. Het eerder genomen besluit om vóór Open punten een `DocumentView` te bouwen (V2_FOUNDATION_RESEARCH §2.13) is niet uitgevoerd. Open punten is gebouwd met afhandeling verspreid over 6+ modules, inclusief een tweede, eigen regex in de highlighter.
2. **De huidige syntaxis heeft geen escaping, en dat leidt tot stille betekenisverandering.** Gewone proza die toevallig op syntaxis lijkt, wordt anders gelezen: `- Kom je? vroeg ze.` wordt een opsommingsteken, `1944. Het jaar…` een genummerde lijst, `5*3 en 2*4` cursief, en `* * *` (een veelgebruikte scènebreuk) wordt `<ul><li><em> </em></li></ul>`. Dat geldt zowel voor de DOCX-import als voor wat de schrijver zelf typt. Dit raakt dataveiligheid in de zin van "betekenis", niet bytes.
3. **"Opslag later kiezen" is maar half waar.** Een DocumentModel ontkoppelt export, import, zoeken, AI en woordtelling van de opslag. **De editor ontkoppelt het niet.** De editor werkt met brontekst en verborgen markers op 1pt in `QTextDocument`. Undo, Darlings, Open punten en de bescherming van afbeeldingen leunen allemaal op brontekst-offsets. Een overstap naar HTML/JSON betekent hoe dan ook een nieuwe editor. Dat is de echte prijs van C/D, niet de diffs.
4. **DOCX-import is een importerprobleem, geen formaatprobleem.** Afbeeldingen en tabellen passen zonder ingrijpende opslagwijziging. De huidige importer verliest wel stil tekst: niet-geaccepteerde invoegingen (track changes), tekst in content controls en velden, URL's, voetnoten, cursief/vet via stijlen, en eigen kopstijlen. Een bestaande BSD-2-bibliotheek (`mammoth`) doet dit op dezelfde testmatrix vrijwel allemaal goed, geeft waarschuwingen en is ~14× sneller.
5. **Synchronisatie op twee computers wordt bepaald door granulariteit, niet door het formaat.** Iedere hoofdstuk-save herschrijft `book.json` (`last_used`), en de revisiecontrole werkt per heel boek. Daardoor botsen twee pc's al wanneer ze **verschillende** hoofdstukken bewerken. Dat is aangetoond. Geen van de opties A–E lost dit op. Het is een losse, goedkope verbetering.

De ranking verandert niet tussen de oorspronkelijke weging en mijn aangepaste weging (§6): **E+B > E > B > A > C > D**.

---

## 1. Werkwijze, en wat ik NIET heb kunnen testen

**Wel gedaan**
- Volledige 1.2.13-bron gelezen waar relevant (storage, markup, media, placeholders/open points, docx_io, export builder/markup/pdf/xhtml, revisions, migrations, integrity, search, editor/highlighter).
- Bestaande testsuite gedraaid (Linux, Qt offscreen): **621 passed, 1 failed**. De fout is `test_1_0_release_metadata` (verwacht `### 1.0.0 — uitgebracht` in de herschreven ROADMAP). Dat is een documenttest, geen codefout.
- DOCX-importmatrix met **24 gegenereerde Word-bestanden** door de echte `parse_docx_book` en daarna `markdown_to_xhtml` gehaald. Dezelfde set door `mammoth` 1.x ter vergelijking. Script en volledige uitvoer staan in de bijlagen.
- Gedrag op runtime bevestigd: twee-pc-conflict, future-versie van `open_points.json`, verschil tussen inline-parsing over hele tekst en per regel, woordtellingsrandgevallen, CommonMark-weergave van een QW-hoofdstuk, parse-benchmarks (25k-woordhoofdstuk, 300k-woorddocument).
- Broncode van NEO, novelWriter, Manuskript, bibisco, Quoll Writer en python-mammoth gekloond en op de relevante plekken gelezen.

**Niet getest / niet kunnen testen**
- **Echte Word-bestanden van schrijvers.** Mijn matrix is synthetisch, gemaakt met python-docx en handgeschreven OOXML. Bestanden uit Word NL, Google Docs, LibreOffice of een Scrivener-compile kunnen anders uitpakken. Vooral stijlnamen, numbering en velden verschillen.
- **Windows.** Geen Windows-run: geen Dropbox-locks, geen DirectWrite-weergave van verborgen markers, geen PyInstaller-bundeling van `mammoth`.
- **Interactieve editor-UX.** Typen, Undo en markers die verborgen blijven bij nieuwe syntaxis (escapes, tabellen als beschermde kaart) heb ik niet met de hand in de GUI geprobeerd. Wel heb ik de editorcode gelezen.
- **Echte Dropbox-sync.** Ik heb alleen twee `Library`-instanties op dezelfde map gesimuleerd. Conflicted copies en het gedrag van de sync-client heb ik niet getest.
- **Performance op de doelhardware.** Mijn tijden komen van een cloud-container.
- **Scrivener** (gesloten bron), **Pandoc** en **Obsidian** heb ik niet in broncode geverifieerd. Wat ik daarover zeg, staat in §3 gelabeld als algemene kennis.
- Het opgegeven repo `saga-soft/novelWriter` heb ik niet gebruikt. Ik heb `vkbo/novelWriter` gekloond, het bekende upstream-repo. Of `saga-soft` een fork of een verhuizing is, heb ik niet gecontroleerd.

---

## 2. Stap 1 — feitencontrole van §3 van het onderzoeksdocument

| Claim in onderzoeksdocument | Oordeel | Bewijs / nuance |
|---|---|---|
| Canonieke bron is beperkte Markdownachtige syntaxis | ✔, maar het is **geen Markdown in de interoperabele zin** | Eén regel = één alinea (`exporting/markup.py:109-113, 173-175`). CommonMark voegt enkele newlines samen: in GitHub/Obsidian wordt een QW-hoofdstuk **één alinea** (getest met markdown-it). Verder `<u>`, `**x **` als geldig vet, `<!--qw:...-->`-markers, en **geen escaping** (nergens in de manuscriptsyntaxis een `\`-escape). |
| Relevante code: `manuscript_markup.py`, `exporting/markup.py`, `media/markup.py` | Onvolledig | Ook: `exporting/pdf_exporter.py:200` (eigen blockparser), `docx_io.py:543` (eigen blockparser), `ui/manuscript_editor.py:1051` (`_block_kind`), `ui/presentation_highlighter.py:150` (eigen todo-regex), `placeholders.py`, en **dode code** `exporting/xhtml.py:69` (`render_markdown`, geen enkele import). Die dode parser heeft andere semantiek: CommonMark-achtig samenvoegen van alinea's en `###`-koppen. |
| Ondersteund: vet, cursief, underline, strike, code, scènebreuk, quote, lijsten, afbeeldingen | ✔ | Plus `## `-tussenkop. Scènebreuk alleen als exact `***` (`manuscript_markup.py:18-20`). |
| Qt-presentatie wijzigt geen bronbytes | ✔ | `source_text()` gebruikt `toRawText()` (`manuscript_editor.py:119-128`). Markers worden op 1pt verborgen (`presentation_highlighter.py:27-57`). |
| Open punten = marker + `planning/open_points.json` | ✔, met **afwijking van het veiligheidscontract** | `open_points_storage.py:29-31`: `version != 1` → `CorruptSourceError`. Een nieuwere versie wordt dus als **corrupt** behandeld, niet als future format. Runtime bevestigd. Integriteit valideert dit bestand alleen als JSON en meldt **niets** (`integrity.py:60, 138-156`). De gebruiker krijgt dus "beschadigd, herstel via Integriteit" terwijl Integriteit niets vindt. |
| DOCX-import begrijpt titel/auteur/taal | ✔ | Taal alleen uit `w:docDefaults` (`docx_io.py:44-63`). |
| …Heading 1/2, QW-stijlen, page breaks, alinea's | ✔ met kanttekening | De page-break-heuristiek (`docx_io.py:327`) maakt van een korte eerste regel op een pagina een hoofdstuktitel: `Nee.` werd een hoofdstuktitel (matrix #07). |
| …bold/italic/underline/strike | **Alleen directe opmaak** | `_run_signature` leest `run.bold` enz. (`docx_io.py:112-119`). Opmaak via tekenstijl (*Emphasis*/*Strong*) of alineastijl gaat **stil verloren** (matrix #04). |
| …lijsten | **Gedeeltelijk** | Alleen stijlnamen `List Bullet*`/`List Number*` (`docx_io.py:180-183`). Word's gewone lijst (`List Paragraph` + `w:numPr`) wordt platte tekst. |
| …hyperlinktekst | ✔ (tekst) | De URL verdwijnt **zonder waarschuwing** (matrix #08). |
| …hard line breaks | **✘ als claim** | `<w:br/>` wordt een broncode-newline en dus een **nieuwe alinea**. Binnen een vetgedrukte run breekt het de opmaak: export toont letterlijk `**Regel een` / `regel twee**` (matrix #05). |
| …style inheritance | **✘** | Geen overerving voor runopmaak, en eigen kopstijlen *gebaseerd op* Heading 1 worden niet herkend. Het hele document werd één hoofdstuk (matrix #13). |
| Tabellen/afbeeldingen niet geïmporteerd, met waarschuwing | ✔ | Het aantal afbeeldingen telt relaties, niet het gebruik: 3× dezelfde afbeelding geeft "1". |
| Export heeft al een abstraherende laag; opslag en uitvoer hoeven niet gelijk te zijn | **Half waar** | `ExportDocument` is een **snapshot**, geen semantisch model: `ExportChapter.markdown: str` (`exporting/models.py:25`). Iedere exporter parseert de brontekst opnieuw. Waar is het alleen voor *uitvoerformaten*, niet voor ontkoppeling van de *opslagsyntaxis*. |

**Feiten die het onderzoeksdocument mist maar die het besluit raken**

- **History = volledige `copytree` van de boekmap per snapshot**, inclusief `assets/` (`storage.py:645, 692, 756`). Dagelijkse, handmatige, conflict- en pre-migratiesnapshots dupliceren dus alle afbeeldingen. Bij beeldimport uit DOCX groeit History daardoor lineair met het aantal snapshots × de mediagrootte. Dit raakt §7/§9.6 van het document, los van het formaat.
- **Iedere hoofdstuk-save herschrijft `book.json`** (`storage.py:619-621`, `last_used`), en de revisie geldt per boek (`revisions.py`, `verify_book_unchanged`). Runtime bevestigd: pc2 kan een **ander** hoofdstuk niet opslaan nadat pc1 opsloeg (`ExternalModificationError: book.json, chapters/…md`). novelWriter heeft hetzelfde patroon (projectbestand met tijdstempel bij elke save, eigen documentatie `technical/storage.rst`).
- **Inline-parsing is niet eenduidig.** `parse_inline_spans` over de hele tekst koppelt markers **over regels heen** (`'Prijs 5*3 euro.\nEn 2*4 meter.'` → één cursieve span `3 euro.\nEn 2`). Per regel (editor, export) is er geen span. De hele-tekst-variant wordt gebruikt in de Darlings-validatie (`prepare_markdown_removal/insertion`) en in `source_selection_with_enclosing_markup`.
- **Woordtelling**: `***` telt als woord, `- ` (lijstprefix) telt als woord (`media/markup.py:163`).
- **Import is niet transactioneel**: `import_docx_book`/`import_markdown_book` schrijven meteen in `books/` (`storage.py:1184-1262`). Een crash halverwege laat een half boek zichtbaar achter. Dat strijdt met het eigen principe "conversie in tijdelijke locatie, validatie vóór commit".
- **DOCX-import draait op de UI-thread** (`ui/main_window.py:767`). Gemeten: 300k woorden ≈ 21,6 s parse (mammoth: 1,5 s). Een gewone roman (90k) zou ruwweg 6–7 s bevriezen. Dat is niet op Windows gemeten.
- **Positief en relevant**: onbekende `book.json`-sleutels blijven behouden (`storage.py:379-380`, `extra_manifest`). Daarop kan een compat/incompat-vlaggenmodel (§9) zonder risico voor 1.2.x worden gebouwd.

---

## 3. Stap 2 — externe projecten

Labels: **[B]** broncode in deze sessie gelezen · **[D]** projectdocumentatie · **[K]** algemene kennis, niet geverifieerd · **[I]** mijn inferentie.

| Project | Opslag | Relevante les voor QW |
|---|---|---|
| **NEO** (`hughhowey/neo`, MIT) | [B] Boek = map: `book.json` + `chapters/*.html` + `notes.html` + `outline.html` + `darlings.json` (`main.js:546`). Durable write: `.tmp` → fsync → rename, plus `.bak`-fallback bij lezen (`main.js:438-480`). **`book.json` wordt herbouwd uit de hoofdstukbestanden als het verloren is** (`main.js:489-512`), en iCloud-placeholders worden herkend (`main.js:601-603`). Editor: `contenteditable` + `document.execCommand`, geen ProseMirror (`app.js`). | [B] De DOCX-import is een eigen regex-OOXML-lezer: **escapet `* _ \`** uit Word-tekst (`main.js:1098`), **volgt `basedOn` voor bold/italic via stijlen** (`main.js:1114-1143`), splitst markers per regel bij `<w:br>` (`main.js:1191-1200`), en neemt runs binnen `w:ins` mee. [B] Geen tabellen of afbeeldingen in de import (geen `w:tbl`/`drawing` in `main.js`). [I] HTML-opslag werkt hier omdat de editor zelf een DOM is. Die voorwaarde heeft QW niet. |
| **novelWriter** (`vkbo/novelWriter`) | [B] `nwProject.nwx` (XML) + `content/*.nwd` (platte tekst) + `meta/` met `index.json` (herbouwbaar, `core/index.py`). Write via `.tmp` + replace, sha1-check bij wijziging op schijf (`core/document.py:229-310`). | [D] **Expliciete escapes `\*`, `\_`, `\~`** (`usage/basic_formatting.rst`). [D] **Voetnoten in hetzelfde tekstbestand**: shortcode `[footnote:key]` + bijbehorende commentaar (`usage/comments.rst`), dus geen sidecar. [D] Nadruk loopt niet over regeleinden. [D] Ook hier wordt het projectbestand bij elke save herschreven met een tijdstempel. Dit is het bewijs dat plain text ver meegroeit, mét een eigen, gedocumenteerd dialect. |
| **Manuskript** (`olivierkes/manuskript`) | [B] Twee modi: map met platte tekstbestanden (`outline/` met metadataheaders) of één gezipte `.msk` (`load_save/version_1.py:99-110`). Schrijft alleen gewijzigde bestanden via een cache (`:381`). Hernoemt bestanden mee met titels (`:360`). | [B] Pandoc voor importers. [I] Bestandsnamen afgeleid van titels geven sync-ruis bij hernoemen. QW's UUID-bestandsnamen zijn beter. |
| **bibisco** (GPL-3) | [B] LokiJS: in-memory JSON-database, als geheel opgeslagen per project (`ProjectDbConnectionService.js`). Rich text als HTML-strings, gesaneerd met een allowlist (`SanitizeHtmlService.js:26-27`). | [I] Blast radius = het hele project per save. Een sanitizer is nodig zodra HTML de bron is. |
| **Quoll Writer** | [B] H2 SQL-database (`db/ObjectManager.java:438`), hoofdstukken als tabel, 13 schema-updatescripts. | [I] Sterk in relaties, zwak in herstel buiten de app en riskant op Dropbox (DB + lock/journal-bestanden). |
| **python-mammoth** (BSD-2) — *toegevoegd* | [B]+getest: DOCX → semantische HTML via style maps, met berichten voor alles wat het niet herkent. | Zie §4. Kandidaat als importfront-end. Pure Python. |
| **Pandoc** — *toegevoegd* | [K] Intern AST (JSON) als tussenformaat tussen readers en writers. Markdown-extensies: fenced divs `:::`, bracketed spans `[x]{.sc}`, voetnoten `[^1]`, pipe tables. | [I] Het patroon "reader → AST → writer" is precies optie E. **Syntaxis lenen van Pandoc** voor nieuwe QWM-constructies maakt QW-bestanden begrijpelijker buiten QW. |
| **Scrivener** | [K] `.scriv`-bundel: XML-projectbestand + per item een RTF-bestand. | [K] Veel kleine bestanden + rijke metadata is robuust, maar RTF is voor mensen slecht leesbaar. |
| **Obsidian** | [K] Map met `.md`-bestanden; extensies (wikilinks, callouts) vormen een dialect. | [I] Bevestigt de "dialect"-les. Obsidian documenteert zijn dialect wel. |

**Synthese:** alle projecten die plain text als bron houden (novelWriter, Manuskript, Obsidian) hebben een **eigen, gedocumenteerde syntaxis met escaping**. Projecten met rijke opslag (NEO, bibisco) hebben een **DOM-editor** die bij die opslag past. Geen enkel project combineert een brontekst-editor met HTML/JSON-opslag. QW zou het eerste zijn, en dat is geen goed teken.

---

## 4. Stap 3 — DOCX voor de QuietWriter-doelgroep

### 4.1 Matrixresultaten (QW 1.2.13 vs mammoth, zelfde bestanden)

| # | Geval | QW 1.2.13 | mammoth |
|---|---|---|---|
| 01 | Roman, Heading 1 | ✔ | ✔ |
| 02 | H1 + H2 (sectie/hoofdstuk) | ✔ | ✔ |
| 03 | Directe b/i/u/s | ✔ | ✔ (u/s via style map) |
| 04 | Cursief/vet via *Emphasis*/*Strong*/alineastijl | **✘ stil verloren** | Strong ✔; Emphasis/alineastijl → **waarschuwing** (te mappen) |
| 05 | Shift+Enter (ook binnen vet, gedicht) | **✘** wordt alinea; vet breekt: letterlijk `**` in export | ✔ `<br/>` |
| 06 | Scènebreuk `***` / `* * *` / `#` / `⁂` | alleen `***`; `* * *` → **`<ul><li><em> </em></li></ul>`** | tekst (geen interpretatie) |
| 07 | Title + paginabreuken, geen koppen | Title → leeg hoofdstuk; `Nee.` → **hoofdstuktitel** | platte alinea's + waarschuwing |
| 08 | Hyperlink | tekst ✔, **URL stil weg** | ✔ `<a href>` |
| 09/10 | Afbeelding(en) | waarschuwing, niet geïmporteerd | ✔ |
| 11 | Eenvoudige tabel | waarschuwing, niet geïmporteerd | ✔ |
| 12 | Documenttaal nl-NL | ✔ | n.v.t. |
| 13 | Eigen kopstijl op basis van Heading 1 | **✘ één hoofdstuk, koppen als proza** | ✘ maar met **waarschuwing** |
| 14 | Proza die op syntaxis lijkt | **✘ dialoogstreepje → lijst, `1944.` → ol, `5*3…2*4` → cursief, `> `/`## ` → quote/kop** | ✔ letterlijk |
| 15 | Niet-geaccepteerde track changes | **✘ ingevoegde tekst stil verloren** (`Ze was moe.` i.p.v. `Ze was erg moe.`) | ✔ |
| 16 | Voetnootverwijzing | **stil verwijderd** | (mijn synthetische bestand mist `footnotes.xml`; mammoth crasht daarop, dus altijd met try/except aanroepen) |
| 17 | Content control (body + inline) | **✘ tekst stil verloren** | ✔ |
| 18 | `w:fldSimple` / `w:smartTag` | **✘ tekst stil verloren** | smartTag ✔, veld weg mét waarschuwing |
| 19 | NL-Word style-id `Kop1` | ✔ | ✔ |
| 20 | Tab, harde spatie | tab blijft letterlijk `\t` in de bron | idem |
| 21 | Vet over runs met spatie-run | ✔ | ✔ |
| 22 | Word-opmerking | genegeerd, geen melding | genegeerd |
| 24 | Heading 3 | wordt platte alinea (had `## ` kunnen worden) | ✔ `<h3>` |
| — | 300k woorden, 40 hoofdstukken | 21,6 s (UI-thread) | 1,5 s (alleen lezen naar HTML; QW-builder komt daar nog bij) |

### 4.2 Antwoorden op de vragen uit stap 3

**Noodzakelijke Word-constructies voor romans.** Kop(stijl) inclusief eigen stijlen met `basedOn`, alinea's, b/i/u/s **inclusief stijl-overerving**, soft line break (poëzie, brieven, adressen), scènebreukvarianten (`***`, `* * *`, `#`, `⁂`, lege alinea, gecentreerde sterretjes), page breaks, lijsten via `w:numPr`, hyperlinks met URL, afbeeldingen, eenvoudige tabellen, en **track changes en content controls zonder tekstverlies**. Voetnoten zijn voor fictie zeldzaam, maar moeten minstens gemeld worden.

**Wat python-docx goed kan.** Kernproperties, stijlen en `style.base_style`-ketens (de API kan de overerving zelf afleiden), runs op het hoogste niveau, hyperlinks (1.2), tabellen (`doc.tables`) en image-relaties. **Niet**: overerving van runopmaak automatisch oplossen, runs in `w:ins`/`w:sdt`/`w:fldSimple`/`w:smartTag`, voetnoten en de volgorde van tabellen tussen alinea's (`doc.paragraphs` slaat ze over; daarvoor moet je over `doc.element.body` lopen).

**Waar direct OOXML nodig is.** Body-volgorde (`w:p`/`w:tbl`/`w:sdt` door elkaar), `w:ins`/`w:del`/`w:moveTo`, `w:sdtContent`, velden, `w:numPr` + `numbering.xml`, `w:drawing`/`a:blip` → relatie → bytes, en `footnotes.xml`. Met python-docx is dat haalbaar via `._p`/xpath, maar dan bouw je in feite mammoth na.

**Kan het zonder opslagwijziging?**
- *Afbeeldingen:* **ja, zonder formaatwijziging.** Het bestaande image-block (`![alt](../assets/images/<uuid>.png "caption") <!-- qw:image … -->`) plus MediaStore dekt dit. Wel nodig: de import in een tijdelijke map laten plaatsvinden, en het History-groeiprobleem (§2) beseffen.
- *Tabellen:* **niet zonder syntaxisuitbreiding.** Er is nu geen tabelconstructie. Een tabel is wel uit te drukken in tekst (pipe table in een QWM-container, §7.2) zonder het opslag**model** te veranderen. Wel is een syntaxisversie nodig (§9).
- *Soft breaks, links, voetnoten:* idem, kleine syntaxisuitbreidingen.

**Wat alleen een waarschuwing hoort te geven** (maar **altijd** een waarschuwing, gegenereerd uit wat de parser *tegenkwam* en niet uit een vaste lijst): opmerkingen, tekstvakken/zwevende objecten, kop- en voetteksten, kolommen, SmartArt/grafieken, eindnoten (tot ondersteuning), onbekende velden (resultaattekst behouden), onbekende stijlen (tekst behouden, stijl gemeld), en verwijderingen uit track changes (genegeerd, gemeld). **Nooit stil tekst laten vallen.**

**Advies DOCX:** vervang de leeslaag van `docx_io.parse_docx_book` door mammoth (of een eigen lezer met dezelfde dekking) → **semantisch importmodel** → **QWM-builder met escaping** → verliesrapport. Het formaat hoeft daarvoor niet eerst te veranderen. Afbeeldingen kunnen direct. Tabellen, soft breaks en links wachten op QWM v2.

---

## 5. Hypothesen uit §11, aangevallen

**H1 — "Database als manuscriptbron past slecht."** *Houdt stand, met één terechte tegenwerping.* Het sterkste argument vóór een DB is **transacties over meerdere bestanden**. QW mist die nu echt: `add_chapter` = bestand + manifest, import = veel bestanden, niets is atomair als geheel. Maar dat los je op met staging-mappen en journaled operaties, niet met een DB als bron. bibisco (hele DB per save) en Quoll (H2 + journal op Dropbox) laten de keerzijde zien. QW gebruikt SQLite al correct: als weggooibare cache (`search.py`).

**H2 — "HTML is semantisch rijker maar slechter voor diffs/recovery."** *Grotendeels weerlegd, en voor de verkeerde reden.* Diff-ruis hangt af van de serializer, niet van HTML: een canonieke writer met één block per regel diffbaar maakt even goed als QW-tekst. Voor *recovery buiten de app* is HTML zelfs **beter** dan QW's huidige syntaxis: een browser toont alinea's correct, terwijl iedere Markdown-viewer een QW-hoofdstuk als één alinea rendert. De **echte** kosten van HTML zitten in de editor. QW toont brontekst met verborgen markers. Met HTML moet je naar een rich-text-`QTextDocument` plus serializer, waarmee Undo, offsets, Darlings, Open punten en beeldbescherming opnieuw moeten. `QTextDocument.toHtml()` is bovendien niet canoniek, dus dat moet je zelf schrijven. Herformuleer H2 als: *"HTML-opslag vereist een nieuwe editor."*

**H3 — "Een formeel DocumentModel levert meer op dan opslag vervangen."** *Bevestigd, sterker dan het document stelt.* Bewijs: vier levende parsers en één dode met andere semantiek, verschil tussen hele-tekst- en per-regel-parsing, woordtelling die syntaxis meetelt, en Open punten-afhandeling verspreid over zes modules, met een tweede, eigen todo-regex in de highlighter. Het eerdere besluit om dit vóór Open punten te bouwen is overgeslagen. Kanttekening: het model moet een **read-only view met source ranges** zijn voor editor/export/zoeken, en daarnaast een **builder** voor import. Er komt **geen** algemene `serialize(document)` die bestaande hoofdstukken herschrijft.

**H4 — "Semantische import + verliesrapport is belangrijker dan Word-fidelity."** *Bevestigd. De huidige implementatie haalt de voorwaarde niet.* Een verliesrapport is waardeloos als het alleen meldt wat je *wist* niet te ondersteunen (tabellen/afbeeldingen) en de rest stil laat vallen (#04, #08, #15–#18). Het rapport moet uit de parser komen: alles wat niet op een QW-concept gemapt wordt, telt.

**H5 — "Markdown kan beste opslag blijven als QW-syntaxis begrensd en formeel wordt."** *Bevestigd, onder twee correcties.* (a) Noem het geen Markdown meer in het ontwerp: het is **QuietWriter-tekst** (UTF-8, één alinea per regel, met Markdown-achtige markering). De waarde is "leesbaar in Kladblok", niet "rendert in Markdown-tools". (b) Zonder **escaping** is het geen formele taal. Escaping is nu de belangrijkste ontbrekende formaatfeature, niet tabellen.

**H6 — "Met een formeel DocumentModel kan het storagebesluit later vallen."** *Half waar. Dit is de belangrijkste correctie op het document.* Voor export, import, zoeken, spelling, AI en woordtelling: ja. Voor de **editor**: nee. Die is structureel aan brontekst-offsets gebonden (`manuscript_editor.py`, `presentation_highlighter.py`, `manuscript_markup.prepare_markdown_*`). "Uitstellen" betekent in de praktijk "tekstopslag houden zolang de huidige editor blijft". Dat kun je dan beter expliciet besluiten, met een tripwire (§9.8).

**H7 — "Semantische fidelity is belangrijker dan layout fidelity."** *Bevestigd, met een grensgeval.* Een deel van wat Word als "layout" opslaat, is voor fictie **semantiek**: regelbreuk binnen een alinea (poëzie, brieven), gecentreerde blokken (gedicht, brief, opschrift) en klein kapitaal (opening). QW heeft nu geen representatie voor een regelbreuk binnen een alinea. Dat is een echt semantisch gat, geen layoutdetail.

---

## 6. Weging en scores

**Aangepaste weging** (som 100), met motivering:

| Criterium | Origineel | Mijn | Waarom |
|---|---:|---:|---|
| Dataveiligheid en herstel (incl. **betekenis**veiligheid) | 20 | 20 | = |
| Veilige migratie bestaande gebruikers | 15 | 15 | = |
| Openheid / buiten QW leesbaar | 15 | 13 | Licht omlaag: alle kandidaten behalve D scoren hier vergelijkbaar. |
| **Editorcomplexiteit / source fidelity** | 5 | **12** | Het meest onderscheidende criterium: C/D vereisen een nieuwe editor. Met 5 werd dat weggemoffeld. |
| Semantische uitbreidbaarheid | 10 | 12 | Tabellen, voetnoten, soft breaks en typografie staan op de roadmap. |
| Filesync, conflicts, diffs | 10 | 8 | Wordt bepaald door granulariteit, niet door het formaat (§2). |
| DOCX-import normale romans | 15 | 8 | Importkwaliteit is een importerprobleem (§4). Het formaat onderscheidt hier weinig. |
| Implementatie / onderhoud | 2 | 6 | Solo-ontwikkelaar + AI-agent: parallelle parsers zijn al aantoonbaar een onderhoudsrisico. |
| Exportarchitectuur | 5 | 3 | Lost op via E, ongeacht de opslag. |
| Performance grote boeken | 3 | 3 | Geen knelpunt gemeten (§8). |

**Scores (1–5, mijn oordeel) en gewogen totaal (max 100):**

| Optie | Veilig | Migr. | Open | Editor | Sem. | Sync | DOCX | Onderh. | Export | Perf | **Mijn weging** | **Originele weging** |
|---|---|---|---|---|---|---|---|---|---|---|---:|---:|
| A huidig | 3 | 5 | 4 | 5 | 2 | 3 | 2 | 3 | 3 | 4 | 70,0 | 66,6 |
| B QWM | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 3 | 4 | 4 | 77,2 | 77,6 |
| C HTML+sidecars | 3 | 2 | 4 | 1 | 5 | 3 | 5 | 2 | 5 | 4 | 63,4 | 70,2 |
| D JSON/AST | 3 | 2 | 1 | 1 | 5 | 2 | 5 | 2 | 5 | 3 | 53,4 | 58,6 |
| E model, opslag ongemoeid | 4 | 5 | 4 | 4 | 3 | 3 | 4 | 4 | 5 | 4 | 79,6 | 80,0 |
| **E → B** | 5 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 5 | 4 | **83,0** | **83,0** |

De volgorde is **gelijk onder beide wegingen**. De conclusie hangt dus niet aan mijn herweging. C wint alleen als je het editorcriterium op 0 zet, dus als QW toch al naar een rich-text-editor zou gaan.

---

## 7. Stap 4 — de vijf opties

### 7.1 Kern per optie

- **A — huidig houden.** Nul migratierisico, maar de bestaande defecten blijven: geen escaping, versnipperde parsers en geen plek voor tabellen, links of soft breaks. Elke nieuwe feature voegt een regex toe op 4–6 plekken. Niet houdbaar als eindsituatie, wel als *startpunt* van E.
- **B — QWM.** Hetzelfde bestand, dezelfde editor, maar met een **gespecificeerde grammatica** (één document, versie), escaping, een canonieke builder voor *nieuwe* inhoud, en een compat/incompat-versiemodel. Risico: dialectgroei. Mitigatie: een vaste lijst blocktypes plus de regel dat nieuwe syntaxis alleen via de spec + DocumentView komt.
- **C — HTML + sidecars.** Semantisch het rijkst, en een browser is een goede exit. Maar: nieuwe editor, sanitization, canonicalisatie, en een migratie van ieder hoofdstuk (alle bytes veranderen). History-herstel van 1.2-snapshots vereist dan een converter. Hoge kosten, terwijl de voordelen ook via B+E te halen zijn.
- **D — JSON/AST.** Valideerbaar, maar slecht leesbaar en herstelbaar zonder app. Eén kapotte accolade kost het hele hoofdstuk, tenzij je per regel serialiseert. Strijdig met "lokaal en van jou". Afwijzen.
- **E — DocumentModel + open opslag.** Levert de meeste waarde per risico-eenheid en verandert geen bytes. Maar zie H6: het stelt de editorvraag niet uit, dus E alleen is geen eindantwoord.

### 7.2 QWM: custom blocks/sidecars versus embedded HTML (expliciet gevraagd)

| Aspect | Custom QWM-syntaxis | Embedded HTML in QWM |
|---|---|---|
| Leesbaarheid ruw bestand | Goed bij Pandoc-achtige vormen (`:::`, pipe tables) | Matig tot slecht (tags, attributen, entities) |
| Past in "één regel = één alinea" | Ja: container-open en -sluit op eigen regels, inhoud per regel | Nee: of multi-line HTML (breekt het regelmodel) of één lange regel (onleesbaar, diff van een hele tabel per celwijziging) |
| Tweede impliciet formaat | Nee, één grammatica | **Ja**: HTML-subset + classes/attributen = tweede taal die je moet specificeren, saneren en versioneren |
| Sanitization | Niet nodig (geen markup-passthrough) | Verplicht (allowlist zoals bibisco), anders XSS-achtige problemen in EPUB/PDF |
| Handmatige edits | Fout = zichtbare letterlijke tekst (fail-visible) | Fout = malformed DOM, met onvoorspelbare herstelpogingen per parser |
| Editor (verborgen markers) | Werkt met het bestaande patroon (prefix/marker op 1pt, of beschermd blok zoals afbeeldingen) | Tags zijn lang en genest; verbergen per teken wordt onbeheersbaar, dus altijd een beschermde kaart |
| Qt vs export-verschillen | Eén parser via DocumentView | Qt-HTML-subset ≠ EPUB-XHTML ≠ PDF-HTML: drie interpretaties van dezelfde tags |
| Exit buiten QW | Pandoc-achtige syntaxis is gedocumenteerd en deels door Pandoc leesbaar | Browser kan het lezen |

**Advies: custom QWM-blocks, met syntaxis geleend van Pandoc waar dat kan. Geen embedded HTML.** De bestaande `<u>` en `<!--qw:…-->` zijn erfenis. Bevries die, maar breid het HTML-gebruik niet uit.

**Sidecar-regel** (aanscherping van ARCHITECTURE_AND_DATA_SAFETY): *alles wat nodig is om de tekst correct te lezen of te exporteren, staat in het hoofdstukbestand.* Denk aan voetnoottekst, tabelinhoud, captions en links. Sidecars zijn alleen voor metadata waarvan verlies **degradeert maar geen tekst kost**: notities bij Open punten, status, asset-manifest. novelWriter kiest om dezelfde reden voor voetnoten in het document.

Concrete richting voor QWM v2 (ter discussie, niet bouwen vóór de spec):

```text
\- Kom je? vroeg ze.          ← escape: letterlijk streepje, geen lijst
Rozen zijn rood\              ← trailing backslash = regelbreuk binnen alinea
viooltjes blauw
Zie [mijn site](https://…).   ← link
Hij loog.[^a3f2]              ← voetnootreferentie
::: center                    ← container-blok (gedicht, brief, opschrift)
…
:::
::: table                     ← tabel als container met pipe-rijen
| Naam | Leeftijd |
| Anna | 42 |
:::
[^a3f2]: Dat dacht zij tenminste.   ← definitie onderaan hetzelfde hoofdstuk
```

---

## 8. Stap 5 — de architectuur onder druk

**Source offsets.** De offsets zijn nu één-op-één met de brontekst, en dat is QW's grote kracht (Darlings-validatie, beschermde ranges, zoeken/vervangen met maskering van gelijke lengte). Escapes voegen extra verborgen tekens toe. Dat past in het bestaande markerpatroon, maar dan moeten **alle** offset-consumenten de DocumentView gebruiken, anders zoekt "zoeken" straks op `\-`.

**Undo.** Escapes die de editor zelf invoegt (de gebruiker typt `- ` aan het begin van een alinea → opslag `\- `), moeten in hetzelfde undo-commando als de toetsaanslag. Er is precedent in `undo()/redo()` (`manuscript_editor.py:501-580`, `undo`/`redo`/`reset_undo_history`). Niet getest in de GUI.

**Sync / twee computers.** Het formaat doet er nauwelijks toe. Wat helpt: (1) `last_used` niet meer in `book.json` maar in een lokale, niet-gesyncte cache (bijv. `.cache/` of QSettings); (2) revisiecontrole **per bestand** voor hoofdstuk-saves, en per boek alleen voor structuurwijzigingen. Dit kan onafhankelijk van A–E en is waarschijnlijk de grootste winst in dagelijkse betrouwbaarheid voor jouw eigen Dropbox-gebruik.

**History.** Een volledige `copytree` per snapshot schaalt slecht met afbeeldingen. Advies, los van het formaat: assets in snapshots hardlinken of content-addressed opslaan (ze zijn al immutable en SHA-256-geverifieerd). Een formaatmigratie maakt een pre-migratiesnapshot van het hele boek. Prima, maar meet de grootte.

**Corruptie.** QWM faalt *zichtbaar*: een kapotte container wordt letterlijke tekst. HTML/JSON falen *structureel*: het hele hoofdstuk wordt onleesbaar of moet "gerepareerd" worden. Dit pleit voor B.

**Future format.** Hoofdstukbestanden dragen geen eigen versie. Dat is prima, zolang `book.json` de versie draagt. Introduceer **twee niveaus** (§9.4). Fix daarnaast nu al `open_points.json`: een hogere versie = future → read-only, niet corrupt.

**Partial writes.** Per bestand is het atomisch (goed). Over bestanden heen niet: import, `add_chapter` en een migratie van meerdere bestanden. Een migratie moet in een staging-map plaatsvinden met één commitstap (rename van de map of een manifestswitch).

**Performance.** Gemeten op een 25k-woordhoofdstuk (134 KB): `parse_inline_spans` 40 ms, `markdown_to_xhtml` 213 ms, `_source_style_map` 219 ms. Prima voor export. Een DocumentView per toetsaanslag over het hele hoofdstuk is waarschijnlijk te traag (~40–200 ms in pure Python), dus **incrementeel per QTextBlock** is nodig in de editor. Gelukkig is QWM regelgebaseerd. Uitzondering: containers (`:::`) over meerdere regels hebben blokstate nodig, zoals de highlighter nu al heeft voor Open punten over alinea's (`setCurrentBlockState`).

**Afbeeldingen/tabellen in de editor.** Afbeeldingen zijn al beschermde kaarten. Tabellen als beschermde kaart met een eigen bewerkingsdialoog zijn hetzelfde patroon. Inline cellen bewerken in de brontekst-editor: niet doen.

**Verborgen markers.** Iedere nieuwe verborgen syntaxis vergroot het "cursor springt over onzichtbare tekens"-probleem. De DocumentView moet daarom de *enige* bron zijn van `hidden_ranges` en `protected_ranges`.

---

## 9. Stap 6 — aanbeveling

### 9.1 Keuze
**"Eerst intern model invoeren" + nu expliciet besluiten: tekstopslag blijft en evolueert gecontroleerd tot QWM.** Dus de 4e optie uit §12 stap 6, gecombineerd met de 2e, en uitdrukkelijk niet de 3e.

### 9.2 Volgorde (iedere stap afzonderlijk releasebaar; stap 1–3 veranderen geen bytes van bestaande boeken)

1. **Specificatie `MANUSCRIPT_SYNTAX.md` (QWM v1 = huidige werkelijkheid).** Leg vast wat 1.2.13 *feitelijk* doet: één regel = alinea, exacte scènebreuk, blockprefixen, inline-regels **per regel** (verschil met hele-tekst-parsing beslechten), image-regel, todo-markers. Gebruik dit als testorakel.
2. **`document_view.py` (read-only), daarna migratie van de consumers.** `parse(source) → DocumentView(blocks[kind, source_range, content_ranges, attrs], inline_spans, hidden_ranges, protected_ranges, diagnostics)`. Eerst de exporters (pdf/epub/docx: drie parsers worden één), dan zoeken/spelling/woordtelling/AI, en als laatste `_block_kind` en de highlighter (incrementeel per blok). **Verwijder `exporting/xhtml.py`.**
3. **Nieuwe DOCX-importpijplijn.** Lezer (mammoth of gelijkwaardig) → `ImportDocument` → **QWM-builder** (canonieke serializer *alleen voor nieuw gegenereerde tekst*, met escaping zodra v2 er is) → verliesrapport. Afbeeldingen naar MediaStore. Alles in een **staging-map**, dan atomisch publiceren. In een worker-thread.
4. **Sync-granulariteit + History-assets** (los spoor, geen formaat): `last_used` uit `book.json`, revisie per hoofdstukbestand, assets in snapshots hardlinken/dedupliceren.
5. **QWM v2: escaping.** Daarna soft break, link, tabelcontainer en voetnoten, elk als aparte syntax-feature in de spec + DocumentView + tests, vóórdat een feature hem gebruikt.

### 9.3 Prototypes (vóór je iets besluit voor stap 5)
- **P1 differential test:** draai alle huidige parsers over een corpus (testboeken + gegenereerde randgevallen) en rapporteer verschillen. Dat levert de lijst die QWM v1 moet beslechten.
- **P2 DocumentView-spike:** alleen blockclassificatie + ranges. Doel: byte-identieke EPUB/PDF/DOCX-uitvoer vergeleken met 1.2.13 op het corpus.
- **P3 import-spike:** mammoth → ImportDocument → QWM-builder. Doel: alle 24 matrixgevallen zonder stil verlies, plus 3–5 **echte** manuscripten van testers.
- **P4 escape-UX-spike in de editor:** `- ` typen aan het begin van een alinea → `\- ` in de bron, verborgen weergave, één Undo-stap, en een lijst alleen via de toolbar. Hier zit het grootste UX-risico.

### 9.4 Migratie (alleen voor QWM v2)
- **Twee versievelden in `book.json`:** `format` (incompat: oudere versies blokkeren, bestaand mechanisme) en `syntax_features` (compat: oudere versies laten het staan). Dat laatste werkt al dankzij `extra_manifest`.
- **Escaping is in 1.2.x degradatieveilig:** 1.2 toont `\-` letterlijk en verwijdert het nooit. Escaping kan dus een *compat*-feature zijn. Tabellen/voetnoten waarschijnlijk ook: een container wordt letterlijke tekst in 1.2, wat lelijk maar verliesvrij is. Alleen iets dat 1.2 bij opslaan kapot zou maken, verdient een *incompat*-bump.
- **Luie bump, nooit stil:** pas wanneer een boek voor het eerst een v2-constructie krijgt, en met een expliciete melding ("Oudere QuietWriter-versies tonen dit als platte tekst") plus een pre-migratiecheckpoint. Geen migratie in de open-flow.
- **Conversie v1 → v2 behoudt de huidige interpretatie:** bestaande `- `-regels **blijven** lijsten (zo zag de gebruiker ze al). Alleen bestaande backslashes vóór escapebare tekens worden verdubbeld. In de praktijk zijn bijna alle bestanden daarna byte-identiek.
- **Rollback naar 1.2.x:** compat-features blijven leesbaar. Een incompat-boek wordt geblokkeerd met de bestaande `FutureBookFormatError`-route. Herstel zonder nieuwe versie via de pre-migratiesnapshot in History.

### 9.5 Niet bouwen
- Geen HTML- of JSON-opslag, geen SQLite als bron.
- Geen generieke `serialize(document)` die bestaande hoofdstukken herschrijft (dus geen "normaliseren bij openen").
- Geen CommonMark-bibliotheek als manuscriptparser (andere alinea-semantiek).
- Geen frontmatter of versieheader per hoofdstukbestand.
- Geen nieuwe embedded-HTML-constructies; `<u>` en `<!--qw:-->` bevriezen.
- Geen sidecar voor voetnoottekst, tabelinhoud of captions.
- Geen DOCX-roundtrip.
- Geen `QTextDocument.toHtml()` als persistentie.

### 9.6 Testplan
- **Syntaxcorpus** met golden files per blocktype en randgeval (inclusief de 10 regels uit matrix #14).
- **Property tests:** `parse` verliest nooit zichtbare tekens; `parse(build(model)) == model` voor importuitvoer; escapen is idempotent; de hidden/protected ranges van DocumentView liggen binnen de bron en overlappen niet ongeldig.
- **Differential tests:** DocumentView-export versus 1.2.13-export op het corpus (byte-gelijk, of verschillen expliciet geaccepteerd).
- **DOCX-matrix** (bijlage) als regressiesuite, aangevuld met echte, geanonimiseerde testersbestanden.
- **Compatibiliteit:** een boek met v2-features openen met de 1.2.13-code → leesbaar, niets verloren bij opslaan, of netjes geblokkeerd bij incompat.
- **Migratie met foutinjectie:** schijf vol, lock, crash tussen staging en commit, future-versie halverwege.
- **Twee-pc-scenario:** verschillende hoofdstukken mogen elkaar niet blokkeren (na stap 4); hetzelfde hoofdstuk wel.

### 9.7 Effect op DOCX en op bestaande 1.2.x-boeken
- **DOCX:** stap 3 lost het stille verlies op zonder formaatwijziging. Afbeeldingen direct. Tabellen/links/soft breaks pas na v2. Tot die tijd tabellen als tekst importeren *met* waarschuwing, of overslaan met waarschuwing (keuze voor Lucas).
- **Bestaande boeken:** stap 1–4 veranderen geen manuscriptbytes. Stap 5 alleen per boek, expliciet, met checkpoint, en voor de meeste bestanden byte-identiek.

### 9.8 Tripwires: wanneer dit besluit opnieuw open moet
- QW stapt over van een brontekst-editor naar een rich-text/WYSIWYG-editor. Dan wordt C serieus.
- Er zijn meer dan ~5 container-blocktypes nodig, of geneste structuren (tabellen in citaten, voetnoten in tabellen).
- Testers bewerken hun hoofdstukbestanden aantoonbaar nooit buiten QW **en** openheid blijkt in de praktijk geen rol te spelen.

---

## 10. Stap 7 — onzekerheden

**Onbekende feiten**
- Hoe vaak alinea's in echte boeken met `- `, `* `, `1944. ` of `> ` beginnen. Dat bepaalt hoe urgent escaping is. Te meten met een klein opt-in-scriptje bij testers (alleen tellingen, geen tekst).
- Hoe Word-bestanden van de doelgroep er echt uitzien: eigen stijlen, `List Paragraph`, track changes nog aan, content controls uit sjablonen, Google Docs-export.
- Of gebruikers hun hoofdstukbestanden ooit buiten QW openen. Dat bepaalt het gewicht van "openheid".
- De werkelijke grootte van History bij boeken met afbeeldingen.

**Benodigde benchmarks / prototypes**
- DocumentView incrementeel per blok in de highlighter: kosten per toetsaanslag op Windows.
- Import van 90k- en 150k-woordromans op een gewone Windows-laptop, zowel bestaand als met mammoth.
- PyInstaller-build met mammoth (pure Python, zal waarschijnlijk werken, maar niet getest).
- Escape-UX (P4) met echte schrijvers.

**Alleen te beantwoorden met echte gebruikersdocumenten**
- Welke scènebreukvarianten voorkomen, en of `* * *`/`#` automatisch herkend moeten worden of alleen gemeld.
- Of de page-break-heuristiek (`docx_io.py:327`) meer goed dan kwaad doet. Mijn matrix laat het kwaad zien (#07).
- Of voetnoten in fictie bij deze doelgroep voorkomen.

---

## 11. Losse bevindingen onderweg (direct bruikbaar, los van het formaatbesluit)

| Ernst | Bestand | Bevinding | Concrete oplossing |
|---|---|---|---|
| Hoog | `docx_io.py:143-159, 364-387` | Stil tekstverlies bij import: runs in `w:ins`, `w:sdt` (body én inline), `w:fldSimple`, `w:smartTag` | Over `body`/`w:p`-descendants lopen in plaats van `iter_inner_content`, of mammoth gebruiken. Altijd melden wat overgeslagen is. |
| Hoog | `manuscript_editor.py:1051-1067` e.a. | Getypte proza die op syntaxis lijkt (`- `, `1944. `, `* `) wordt lijst/quote/kop, zonder dat de schrijver dat koos | QWM v2-escaping (§9). Op korte termijn: bij DOCX-import zulke regels melden. |
| Midden | `storage.py:610-630` + `revisions.py` | Twee pc's blokkeren elkaar op verschillende hoofdstukken (`book.json`/`last_used`, revisie per boek) | `last_used` naar een lokale cache; revisie per hoofdstukbestand. |
| Midden | `open_points_storage.py:29-31`, `integrity.py:138-156` | Future-versie van `open_points.json` → "corrupt"; Integriteit ziet niets | `version > 1` → future-fout + read-only, analoog aan Planning; Integriteit `aux_json_newer`. |
| Midden | `docx_io.py:112-119, 162-186` | Opmaak via stijlen en eigen kopstijlen (`basedOn`) genegeerd | `style.base_style`-keten volgen voor b/i/u/s en heading-detectie. |
| Midden | `docx_io.py:122-140, 162-176` | `<w:br/>` binnen een opgemaakte run geeft letterlijke `**` in de export | Markers per regel zetten, zoals NEO (`main.js:1191-1200`). Later een echte soft break. |
| Midden | `storage.py:1184-1262` | Import niet transactioneel: half boek zichtbaar na crash | Bouwen in een staging-map, daarna één rename. |
| Midden | `storage.py:645, 692, 756` | History dupliceert alle assets per snapshot | Hardlinken of content-addressed opslaan. |
| Laag | `exporting/xhtml.py` | Dode parser met afwijkende semantiek | Verwijderen. |
| Laag | `manuscript_markup.py:46` vs editor/export | Inline-pairing over regels heen (hele tekst) ≠ per regel | In QWM v1-spec vastleggen: per regel. Darlings-validatie per regel laten parsen. |
| Laag | `media/markup.py:163` | `***` en het lijststreepje tellen als woord | Via DocumentView tellen. |
| Laag | `docx_io.py:313` | Afbeeldingstelling = relaties, niet het aantal keren gebruikt | `w:drawing`/`a:blip` tellen. |
| Laag | `exporting/markup.py:109-113` | Commentaar zegt dat een lege regel een "extra alinea" is, maar de code laat hem weg | Gedrag of commentaar in lijn brengen (spec v1). |
| Laag | `ui/main_window.py:767` | DOCX-import op de UI-thread | Worker-thread met voortgang. |
| Laag | `tests/current/test_1_0_release_metadata.py:17` | Faalt na herschrijving van de ROADMAP | Assertie verplaatsen naar `ROADMAP_HISTORY_TO_1_2_13.md`. |

---

### Bijlagen
- `docx_matrix.py` — genereert de 24 testbestanden en draait de QW-importer.
- `docx_matrix_out.txt` — volledige uitvoer, inclusief brontekst en XHTML per geval.
