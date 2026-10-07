# QuietWriter 1.2.30: finale architectuur- en regressiereview

**Reviewer:** Claude · **Datum:** 7 oktober 2026 · **Snapshot:** `QuietWriter-1.2.30.zip` (`__version__ = "1.2.30"`)
**Er is geen productiecode gewijzigd.** Alle harnassen staan buiten de projectmap (zie bijlage).

Legenda: **[test]** = gereproduceerd met code of echte Qt-events · **[inspectie]** = vastgesteld door code te lezen ·
**[afgeleid]** = conclusie op basis van het voorgaande, niet apart uitgevoerd.

---

## 1. Executive summary

De refactor is **inhoudelijk geslaagd**:
- Van mijn 1.2.24-escapingmatrix is bijna alles groen: atomaire escapes, de structuurinvariant bij Delete en Enter,
  het klembord, zoeken via een zichtbare projectie, NBSP en vervangen als letterlijke tekst.
- PDF, DOCX en EPUB geven nog steeds identieke zichtbare tekst.
- DOCX-import verliest veel minder en degradeert netjes bij een kapot beeld.
- Markdown gaat nu via `ImportDocument` en houdt bij export de alineagrenzen vast.
- De syntaxmigratie maakt een checkpoint, rolt terug bij fouten en is fail-closed.
- Typen is 3–4× sneller en DOCX-import ~3× sneller.

Toch kan de refactor **nog niet worden afgesloten**. Er zijn twee blockers en twee high-bevindingen, allemaal met een
kleine, gerichte fix:

1. **Blocker:** de syntaxmigratie beschadigt boeken die met QuietWriter **1.2.19–1.2.29** zijn bewerkt. Deze boeken
   hebben geen `manuscript_syntax`-marker (die bestaat pas sinds 1.2.27, en alleen voor nieuwe boeken), maar bevatten
   al bewuste escapes. De migratie verdubbelt *alle* backslashes. Openen in 1.2.30 kan alleen ná migratie, dus
   precies de boeken van de recente testgebruikers worden bij het eerste openen zichtbaar veranderd:
   `5*3` wordt `5\3` en er ontstaat een onbedoelde cursieve span.
2. **Blocker:** structurele escapes worden wees en dus zichtbaar:
   - `- `, `> ` of `## ` typen en daarna alleen de spatie weghalen geeft een zichtbare `\-`;
   - tekst die met `1944. `, `- `, `## ` of `> ` begint **midden in een regel plakken** geeft `Begin 1944\. Het`.
3. **High:** Shift+Enter maakt weer een harde alinea in plaats van U+2028. De eigen Qt-test van het project faalt
   daarop. Jullie suite draait de Qt-tests niet, daarom was dit niet zichtbaar.
4. **High:** Zoek-en-vervang over een opmaakgrens laat een losse `**` zichtbaar achter (`was **heel** moe`, vervang
   `was heel` door `zij`, resultaat `zij** moe`). Met "Alles vervangen" kan dat boekbreed gebeuren.

**Advies: C, nog één kort hardeningblok.** De architectuur zelf is goed; zie §16–17.

---

## 2. Testomgeving

| | |
|---|---|
| OS | Linux 6.18 x86_64 (cloud-VM), Qt-platform `offscreen` |
| Python | 3.13.16 |
| PySide6 | 6.11.2 |
| python-docx | 1.2.0 |
| CommonMark-referentie | markdown-it-py (`commonmark`-preset) |
| UI-font | geen Segoe UI; Qt-fallback |

---

## 3. Volledige testresultaten

| Controle | Resultaat |
|---|---|
| `pytest` (volledig, PySide6 aanwezig) | ❌ **705 geslaagd, 1 gefaald, 0 overgeslagen**, 304 subtests, 106,8 s |
| Gefaalde test | `tests/current/test_review_1225_editor_qt.py::test_shift_enter_stays_inside_one_document_block` (zie H1) |
| Teardownwaarschuwing | `RuntimeError: libshiboken: Internal C++ object (ManuscriptEditor) already deleted` in `_layout_image_cards` (een timer vuurt na het verwijderen van de widget; onschuldig in tests, maar het wijst op een timer die niet wordt gestopt) |
| `main.py --smoke-test` | ✅ rc 0 |
| `tools/check_undefined_names.py` | ✅ OK |
| `tools/check_locales.py` | ✅ 1520 sleutels in 5 talen |
| `compileall` | ✅ |
| `pyflakes` (zonder "imported but unused") | 6 kleine meldingen: ongebruikte variabelen en `nonlocal` in `docx_io.py:554,663`, `markdown_io.py:91`, `main_window.py:514`, `settings_page.py:1071`, `characters_page.py:370` |

**Proceskanttekening:** jullie lokale run meldt 45 overgeslagen tests. Het project heeft 33 Qt-testbestanden met 96
tests. In een omgeving zonder PySide6 wordt dus juist de editorlaag, waar de escaping zit, niet getest. Dat verklaart
waarom H1 niet zichtbaar was. **Maak een PySide6-run verplicht als releasepoort.**

---

## 4. Blockers

### B1. De syntaxmigratie beschadigt boeken uit het escape-tijdperk (1.2.19–1.2.29) [test]

**Waar:**
- `manuscript_profile.migrate_legacy_source_to_current` verdubbelt elke `\`.
- `Library.migrate_manuscript_syntax` (`storage.py:411`) doet dat voor elk boek zonder marker.
- `MainWindow.open_book` (`main_window.py:794–824`) vraagt erom bij openen; Annuleren betekent niet openen.

**Tijdlijn uit de CHANGELOG:**
- 1.2.19: het editor schrijft escapes (`\*`, `\- `, `1944\.`, `\\`).
- 1.2.27: de marker komt er, **alleen voor nieuwe boeken en DOCX-imports**.

Elk boek dat vóór 1.2.27 is aangemaakt en daarna in 1.2.19+ is bewerkt, is dus "unmarked" en bevat toch bewuste
escapes. Dat zijn waarschijnlijk precies de boeken waarmee je op Windows hebt getest.

**Reproductie** (`mig130.py`, scenario 2): een hoofdstuk zoals het in de 1.2.24-editor ontstaat, zonder marker:

```
bron vóór:  nummer \*31623455 en 5\*3 en 2\*4 = 8 / \- Kom je mee? / 1944\. Het was koud. / C:\\pad\\naar
zichtbaar:  nummer *31623455 en 5*3 en 2*4 = 8 / - Kom je mee? / 1944. Het was koud. / C:\pad\naar
na migratie zichtbaar:
            nummer \31623455 en 5\3 en 2\*4 = 8    (met een cursieve span van "31623455 … 5\")
            \- Kom je mee?
            1944\. Het was koud.
            C:\\pad\\naar
```

| | |
|---|---|
| **Verwacht** | gelijke zichtbare tekst |
| **Werkelijk** | zichtbare tekst gewijzigd, plus nieuwe semantiek (cursief) |
| **Herstel** | het checkpoint bestaat, maar de gebruiker merkt de schade pas bij het lezen |

**Echte pre-1.2.19-boeken** (`\\server\share`, `C:\Users\naam\.config`, `regex a\.b`, `\#tag`, `\->`, CRLF, BOM, NBSP,
U+2028, lijsten, scene breaks) migreren wel **correct**; zie §9.

### B2. Wees-structuurescapes worden zichtbare backslashes [test]

**Waar:**
- `manuscript_syntax.escape_ranges`: `\- `, `\> ` en `\## ` gelden alleen **mét** spatie erachter en alleen op de
  regelstart.
- `manuscript_markup.escape_literal_text`: escapet op basis van het begin van de **geplakte** tekst, niet van de
  invoegpositie.

| Reproductie (echte events) | Bron | Zichtbaar |
|---|---|---|
| typ `- `, Backspace | `\-` | **`\-`** |
| typ `- Kom`, Backspace op de spatie (of selecteer de spatie + Delete) | `\-Kom` | **`\-Kom`** |
| idem met `> ` en `## ` | `\>Kom`, `\##Kom` | **`\>Kom`**, **`\##Kom`** |
| typ `- `, 2× Backspace, `Kom` | `\Kom` | **`\Kom`** |
| typ `Begin `, plak `1944. Het jaar` | `Begin 1944\. Het jaar` | **`Begin 1944\. Het jaar`** |
| typ `Begin `, plak `- Kom mee` / `## kop` / `> citaat` | `Begin \- Kom mee`, … | **met backslash** |
| typ `aaa`, plak `1944. Het\n> geen citaat\n***` | `aaa1944\. Het` | **`aaa1944\. Het`** (regels 2–3 kloppen wel) |

`1. ` + Backspace gaat wel goed, want `N\.` is ook zonder spatie een escape.

**Waarom blocker:** gewone correcties en gewoon plakken zetten blijvend zichtbare tekens in het boek, die ook in elke
export terechtkomen. Dit is dezelfde klasse als de 1.2.24-blocker (`a\b`), alleen nauwer.

---

## 5. High

### H1. Shift+Enter maakt een harde alinea; de eigen Qt-test faalt [test]

**Waar:** `manuscript_editor.py` `keyPressEvent`, het typpad op ~933–957. Shift+Return levert `event.text() == '\r'`.
`plain_typing` sluit Shift niet uit, en `cursor.insertText('\r')` maakt in Qt een nieuw blok.

**Reproductie:** typ `Regel`, Shift+Enter, `- twee`.
- Bron: `'Regel\n\- twee'` (2 blokken).
- Verwacht (volgens de releasebelofte en de eigen test): één alinea met U+2028.

Escaping blijft wel goed: `- twee` blijft letterlijk. Het effect: zachte returns zijn in de editor niet meer te
maken, terwijl DOCX- en Markdown-import en de Markdown-export ze wel ondersteunen. Op Windows geeft Qt bij Shift+Enter
ook `'\r'`, dus ik verwacht hetzelfde gedrag [afgeleid].

### H2. Vervangen over een opmaakgrens laat losse opmaaktekens zichtbaar achter [test]

**Waar:** `media/markup.replace_searchable_text` (`:254`), en de editorvariant met dezelfde mapping. De zichtbare
projectie laat zoeken nu terecht over `**`-grenzen heen matchen, maar het bronbereik van de match bevat dan maar één
helft van een span.

**Reproductie:** `replace_searchable_text('was **heel** moe', re.compile('was heel'), 'zij')` geeft `'zij** moe'`,
zichtbaar **`zij** moe`**. Met "Alles vervangen" gebeurt dit in elk hoofdstuk.

Vervangen binnen een span gaat wel goed (`heel` → `erg` geeft `was **erg** moe`), net als letterlijke vervangtekst
(`*Bram*` en `- ` blijven letterlijk).

---

## 6. Medium

| # | Bevinding | Waar | Soort |
|---|---|---|---|
| M1 | **Blok-SDT-tekst gaat verloren.** `_top_level_sdt_blocks` roept `child.xpath('.//w:sdtContent/w:p')` aan op een kaal lxml-`_Element`. Dat geeft `XPathEvalError: Undefined namespace prefix`, wat `except Exception` inslikt. De herstelcode werkt dus bij geen enkel echt document. Ook niet ingelezen: Word-voorbladen en -inhoudsopgaven, die SDT's zijn. Er is alleen een vage melding ("kan niet volledig"). Bovendien zou herstelde tekst naar het **einde** van het laatste hoofdstuk worden verplaatst. | `docx_io.py:462–476, 718–726` | [test] |
| M2 | **Eindnoten verdwijnen zonder melding.** Alleen de relatie `/footnotes` wordt gedetecteerd. Voetnoottekst verdwijnt ook, maar dan met melding. | `docx_io.py:632–636` | [test] |
| M3 | **Echte lijstnummers gaan verloren in exports.** Bron `3. derde` / `7. zevende`: PDF en EPUB geven `<ol>` zonder `start` (zichtbaar 1, 2), DOCX heeft geen nummer, CommonMark rendert 3, 4. Alleen de AI-context behoudt 3 en 7. DOCX-import van Word `List Number` geeft twee keer `1.` in de editor. | exporters, `docx_io` | [test] |
| M4 | **U+2028 wordt niet gemapt in PDF, EPUB en DOCX.** Het ruwe teken komt in `<p>` en `<w:t>` (`zacht\u2028afgebroken`) in plaats van `<br/>` of `<w:br/>`. Markdown (`\`+newline) en AI doen het wel goed. Hoe e-readers en Word het ruwe teken tonen, heb ik niet getest. | `exporting/markup.py`, `pdf_exporter.py`, `docx_io._append_markdown` | [test] |
| M5 | **Markdown-export is niet CommonMark-veilig voor gewone proza.** Getypte tekst die na het renderen verandert: `__init__ en _nadruk_` (strong/em), `[de site](https://x.nl)` (link), `# Geen kop` (h1), `+ geen lijst` en `1) geen lijst` (lijsten), vier inspringspaties (codeblok), `&amp;` (wordt `&`). | `exporting/markdown_exporter.py` | [test] |
| M6 | **Een selectie die binnen een escape eindigt, verwijdert het volgende zichtbare teken.** `a*b`, selecteer bron 0–2 (eindigt tussen `\` en `*`, visueel ná `a`), Delete of typen geeft `b` in plaats van `*b`. `_normalise_selection_around_escapes` schuift het einde naar `pair_end` in plaats van naar de escapestart. | `manuscript_editor.py:705–722` | [test] |
| M7 | **Boeken met een toekomstige of onbekende syntax verdwijnen stil van de boekenplank** (`list_books` slaat ze over). Fail-closed is correct (bytes onaangeroerd, niet geopend), maar de gebruiker denkt dat het boek weg is. Toon een vergrendelde kaart met uitleg. | `storage.list_books` / `profile_from_manifest` | [test] |
| M8 | **Onbekende frontmattervelden blijven niet behouden** bij Markdown-import (`custom_field: behoud mij` is weg na import en export). `tags: [a, b]` wordt de string `"[a, b]"`. De releasebelofte zegt het tegenovergestelde. | `markdown_io` | [test] |
| M9 | **Intern plakken van een afbeeldingsregel tussen boeken.** De interne MIME draagt `![…](../assets/images/<uuid>.png)` mee. In een ander boek bestaat dat bestand niet, dus de exportpreflight blokkeert later. Getest: de regel wordt ingevoegd. De verwijzing naar een ander boek is afgeleid. | `createMimeDataFromSelection`/`insertFromMimeData` | [test]/[afgeleid] |

---

## 7. Low

| # | Bevinding | Soort |
|---|---|---|
| L1 | De migratie dekt alleen hoofdstukken. Vrije publicatieteksten (`planning/texts/*.md`, Voorwerk/Achterwerk) en Bewaarplaats-fragmenten (op werkmapniveau) zijn manuscriptachtig, worden met dezelfde grammatica gerenderd en worden niet gemigreerd. Oude backslashes daarin kunnen anders gelezen worden (zeldzaam). | [inspectie] |
| L2 | `qwbook_io` kent geen syntaxprofiel. Een QWBOOK-back-up uit 1.2.19–1.2.26 komt binnen zonder marker en volgt daarna het B1-pad. | [afgeleid] |
| L3 | Unmarked boeken worden vóór migratie al met de huidige grammatica gelezen door woordtelling op de boekenplank en de zoekindex (bijvoorbeeld `\\server` wordt `\server`). Alleen weergave, geen data. | [test] |
| L4 | Markdown-import: een citaat over twee bronregels wordt twee citaatalinea's (gewone alinea's worden wél samengevoegd). `_x_`, `+ `, `### ` blijven zonder melding letterlijk. | [test] |
| L5 | Een staging-map blijft staan als de fout optreedt in `_new_staged_import_book` (vóór de `try`). Dat wordt na 24 uur alsnog opgeruimd door `_cleanup_stale_import_staging`. Een echte publish-rename-fout ruimt wél correct op. | [test] |
| L6 | Typen en cursorbeweging doen per toets twee keer `source_text()` plus `escape_ranges()` over het **hele** hoofdstuk (`_escape_pair_at`). Zie §13. | [test] |
| L7 | Dode of alleen-in-tests gebruikte code; zie §14. | [inspectie] |
| L8 | `SNAPSHOT_INFO.txt` zegt nog "Application version: 1.2.13". De README is wél bijgewerkt. | [inspectie] |
| L9 | Vervangtekst ingevoegd bij een escape-grens: `searchable_matches` corrigeert de start met −1 bij een escape. Getest en correct, maar het is een subtiele uitzondering zonder eigen test. | [inspectie] |

---

## 8. Escaping en editor: resultaten

**`esc130.py`: 67 scenario's met echte Qt-events; 50 OK, 17 FAIL.** Alle FAIL's vallen onder B2, H1 en M6, plus mijn
bewust strenge verwachtingen bij plakken. Daarnaast heb ik de vijf 1.2.24-harnassen ongewijzigd opnieuw gedraaid.

| Groep | Resultaat |
|---|---|
| Typen van alle 14 gevraagde invoeren (inclusief `~~literal~~`, `` `literal` ``, `<u>literal</u>`, `***`, Windows-paden, `\\server\share`, `pijl \->`) | ✅ alle letterlijk; bron, zichtbare tekst en DocumentView kloppen |
| `a*`, Backspace, `b` | ✅ `ab` (de 1.2.24-blocker is opgelost) |
| Cursor ←/→ over een escape | ✅ springt over het paar heen (posities 1 → 3) |
| Delete of Backspace vóór en na een escape; typen op of naast een escape | ✅ alle 6 |
| Delete twee keer vóór `*nadruk*` | ✅ verwijdert zichtbare sterren als paar; geen cursief meer ontstaan |
| Selectie over escapes plus typen; selectie die **binnen** een escape **begint** | ✅ |
| Selectie die binnen een escape **eindigt** | ❌ M6 |
| Undo/Redo na Backspace-reeksen, Ctrl+B, plakken, `- `-prefix | ✅ |
| Delete, Backspace en Enter die een prefix vormen (`1944.`, `- Kom`, `## kop`) | ✅ blijven letterlijk |
| Selecteren plus typen dat `12000. Daarna` vormt | ✅ |
| Simulatie van slepen en neerzetten (`QDropEvent`) van `- ` op de regelstart | ✅ letterlijk |
| Plakken op de regelstart | ✅ |
| Plakken midden in een regel | ❌ B2 |
| Spatie na een prefix weghalen | ❌ B2 |
| Shift+Enter | ❌ H1 (de escaping zelf klopt) |
| NBSP bij Ctrl+B | ✅ behouden |
| `setPlainText(source)` → `source_text()` | ✅ bytes identiek |

### Klembord [test]

| Controle | Resultaat |
|---|---|
| text/plain van een vet/cursief/onderstreept/escaped corpus | ✅ `Hij was heel moe en erg stil, en dit en *31623455 en **letterlijk**.`: geen markers, geen escapes |
| Interne plak | ✅ opmaak behouden; letterlijke `**letterlijk**` blijft letterlijk (`\*\*letterlijk\*\*`) |
| text/plain "van buiten" teruggeplakt | ✅ letterlijke zichtbare tekst |
| Open-puntmarkers | ✅ lekken niet (plain én intern) |
| Beeld in plain text | ✅ alleen de alt-tekst (`Een kat`) |
| Beeld in de interne MIME | ⚠️ volledige beeldregel (M9) |

---

## 9. Legacy en syntaxmigratie

**Golden corpus** (`mig130.py`): een pre-escape-hoofdstuk met BOM en CRLF, met daarin `\\server\share`,
`C:\Users\naam\.config`, `regex a\.b`, `\#tag`, `\->`, gewone `*nadruk*`/`**vet**`, `5 * 3`, een bullet, `3.`,
`***`, NBSP, U+2028, `![geen echt beeld](foto.png)` en een open-puntmarker.

| Stap | Pre-1.2.19-boek | Boek uit 1.2.19–1.2.29 |
|---|---|---|
| 1. openen zonder migratie | ✅ geen stille wijziging. In de UI kun je niet openen zonder migratie: Annuleren betekent niet openen. | idem |
| 2. zichtbare tekst vóór migratie | `\\server` wordt al als `\server` gelezen door de woordtelling op de boekenplank (L3) | = wat de auteur zag |
| 3. expliciete migratie | ✅ | ❌ **zichtbare tekst verandert (B1)** |
| 4. checkpoint/revisie | ✅ `pre_syntax_migration` staat in de geschiedenis | ✅ |
| 5. bytes mogen veranderen, zichtbare tekst niet | ✅ alle 7 regels gelijk. CRLF wordt LF, BOM blijft. | ❌ |
| 6. semantiek gelijk (bullet, numbered, scene, inline) | ✅ | ❌ (nieuwe cursieve span) |
| 7. opnieuw openen na migratie | ✅ identieke bron | n.v.t. |
| 8. herstel uit het checkpoint | ✅ originele bron en manifest zonder marker terug | n.v.t. |
| 9. fout halverwege (2e hoofdstuk) | ✅ alle hoofdstukken byte-identiek terug, manifest zonder marker | n.v.t. |
| 10. onbekende versie, feature of rommel | ✅ niet geopend, `book.json` en hoofdstukken onaangeroerd | ⚠️ boek verdwijnt van de plank (M7) |

**Harde conclusie: nee, de migratiestrategie is in deze vorm niet veilig genoeg voor echte gebruikers.** Het
mechanisme (expliciet, checkpoint, rollback, fail-closed) is goed. De **beslisregel** "geen marker = pre-escape" is
feitelijk onjuist voor alle boeken die met 1.2.19–1.2.29 zijn bewerkt. Na de fix uit §17.1 is ze wel veilig.

---

## 10. Consumer-pariteit

**Corpus** (`parity130.py`): escapes, `C:\\pad`, letterlijke `**`/`<u>`/`~~`, vet/cursief, NBSP, U+2028, `***`,
bullet, `3.` en `7.`, citaat, `pijl \\->`.

| Consumer | Zichtbare tekst | Afwijking |
|---|---|---|
| Editor / DocumentView | ✅ | U+2028 blijft één alinea (12 blokken, correct) |
| Zoeken (`5*3`, `was heel moe`, `C:\pad`, `**literal**`, `tien procent` met NBSP, `pijl \->`) | ✅ alle gevonden | |
| Vervangen | ✅ letterlijk | ❌ over opmaakgrens (H2) |
| Woordtelling | ✅ 45 = 45 | |
| Spelling (`text_for_language_tools`) | ✅ offset-stabiel, markers gemaskeerd | |
| AI-context | ✅ | behoudt `3.` en `7.`, toont `[Scènebreuk]` |
| Bewaarplaats-preview | ✅ (`visible_text`) | |
| Klembord text/plain | ✅ | |
| PDF | ✅ tekst | ❌ `<ol>` zonder start (M3), ruwe U+2028 (M4) |
| DOCX-export | ✅ tekst | ❌ geen lijstnummers (M3), ruwe U+2028 (M4) |
| EPUB | ✅ tekst | ❌ `<ol>` zonder start (M3), ruwe U+2028 (M4) |
| Markdown → CommonMark | ✅ escapes onzichtbaar, alinea's los, `<hr>`, `<blockquote>`, hard break `\` | ❌ 7 wordt 4 (M3); gewone proza niet veilig (M5) |

---

## 11. DOCX-import

**Getest via `Library.import_docx_book`:** `docx124.py` (ongewijzigd) en `docx130.py` (nieuw).

| Geval | 1.2.24 | **1.2.30** |
|---|---|---|
| H1/H2 → sectie en hoofdstuk, vet/cursief, Strong/Emphasis, afgeleide stijl | ✅ | ✅ |
| Letterlijke markuptekens | ✅ | ✅ geëscaped |
| Bullet | ✅ | ✅ |
| Genummerd (`List Number`) | n.t. | ⚠️ twee keer `1.` (M3) |
| Zachte return | ❌ stil nieuwe alinea | ✅ U+2028 |
| Pagina-einde midden in een run | ❌ tekst geplakt, stil | ✅ U+2028 met melding |
| Hyperlink | tekst + melding | idem (URL weg, gemeld) |
| Tabel | tekst weg | ✅ rijen als tekst (`A1 · B2`) met melding. Lege cellen geven bungelende `·`. |
| PNG/JPEG, herhaald beeld (dedup), alt-tekst | ✅ | ✅ |
| GIF | gemeld | gemeld |
| Corrupte PNG of afgekapte JPEG | ❌ hele import faalt | ✅ overgeslagen met melding, tekst behouden |
| Tracked insertion | tekst weg | ✅ behouden met melding |
| Veldresultaat | weg, foute melding | ✅ "7" behouden |
| Inline-SDT | weg | ✅ behouden |
| **Blok-SDT** | weg | ❌ **weg** (M1) |
| Tekstvak | stil weg | ✅ behouden met melding |
| Voetnoot | weg, gemeld | weg, gemeld |
| **Eindnoot** | – | ❌ **stil weg** (M2) |
| Fout bij het schrijven van een hoofdstuk, mediafout | rollback ✅ | ✅ |
| Fout bij de publish-rename (`os.replace` van de map) | – | ✅ geen resten, geen boek |
| Bestaand doelpad | ✅ | ✅ |
| Fout in `_new_staged_import_book` | – | ⚠️ staging blijft staan (L5) |
| Oude `.import-*` | – | ✅ ouder dan 24 uur wordt opgeruimd, een verse map blijft staan |

**Hoofdregel "geen zichtbare tekst stil kwijt":** bijna gehaald. Er blijven twee gaten: eindnoten (stil) en blok-SDT
(vage melding, terwijl de herstelcode bedoeld was maar niet werkt).

---

## 12. Markdown-import en -export [test]

Extern bestand met frontmatter (inclusief een onbekend veld en een YAML-lijst), soft-wrapped alinea's, `**`/`*`/
`_`/`__`, hard breaks (twee spaties en backslash), een citaat over twee regels, bullets, `3.`/`4.`, letterlijke
escapes en backslashes, `##`, `***` en twee `#`-hoofdstukken.

| Controle | Resultaat |
|---|---|
| Soft-wrapped alinea's worden één QuietWriter-alinea | ✅ |
| Hard breaks worden U+2028 | ✅ beide vormen |
| `#` wordt een hoofdstuk, `##` een tussenkop, `***` een scene | ✅ |
| Lijsten met `3.`/`4.` | ✅ bron behoudt de nummers |
| `\*geen cursief\*`, `C:\\pad`, `\\` | ✅ letterlijk en correct zichtbaar |
| `_cursief_`, `__vet__` | ⚠️ letterlijke underscores, geen melding (L4); bij export weer opmaak (M5) |
| Citaat over twee regels | ⚠️ twee citaatalinea's (L4) |
| Frontmatter: titel en auteur | ✅ |
| Frontmatter: onbekend veld en lijsttype | ❌ M8 |
| Export → CommonMark: alineagrenzen | ✅ elke alinea een eigen `<p>` |
| Export → CommonMark: escapes onzichtbaar | ✅ |
| Export → CommonMark: hard breaks | ✅ `<br />` |
| Export → CommonMark: lijsten | ⚠️ "loose" (`<p>` in `<li>`): cosmetisch |
| Gewone proza → CommonMark | ❌ M5 |

---

## 13. Performance [test]

| Meting | 1.2.24 | **1.2.30** |
|---|---|---|
| Toetslatentie 10k woorden | 26 ms | **8,8 ms** |
| Toetslatentie 30k woorden | 93 ms | **24,7 ms** |
| Toetslatentie 100k woorden | 294 ms | **73,4 ms** |
| `parse_document` 30k / 100k | 82 / 186 ms | 49 / 159 ms |
| Woordtelling 30k / 100k | 97 / 254 ms | 86 / 306 ms (nu gedebounced, niet per toets) |
| Zichtbare projectie 30k / 100k | – | 76 / 250 ms |
| AI-context 30k / 100k | 211 / 743 ms | 95 / 307 ms |
| `inline_runs`, 20k tekens met 800 spans | 627 ms | **5,5 ms** |
| DOCX 85k woorden + 20 beelden | 16 s | **5,8 s** (met en zonder koppen) |
| Dirty-check | stringvergelijking per toets | ✅ modified-state; 5× Undo maakt weer schoon |

**Wat nu dominant is (cProfile, 100k woorden):** per toets en per cursorbeweging roept `_escape_pair_at` twee keer
`source_text()` plus `escape_ranges()` aan over het **hele** document (`_escape_cursor_changed` en
`_normalise_selection_around_escapes`). Dat is ~70 ms van de 73 ms. Escapes zijn per regel, dus dit kan per blok;
dat is een kleine, relevante fix. `parse_document` per toets is verwaarloosbaar geworden.

**Oordeel:** bij normale hoofdstukken (≤ 30k woorden) voelt typen nu goed. Bij een extreem hoofdstuk (100k woorden, wat
je krijgt bij import zonder koppen) is 70 ms per toets en per pijltoets merkbaar maar bruikbaar. Er is geen O(n²)
meer gevonden.

**Niet gemeten:** de korte pauze wanneer de gedebouncede woordtelling bij 100k woorden afgaat (~300 ms eenmalig na een
typpauze) [afgeleid uit de functietijd].

---

## 14. Architectuur

### Echt problematisch

Geen structurele problemen meer. De blockers zitten in **beslisregels** (B1) en **contextgevoeligheid** (B2), niet in
de lagenindeling.

### Technisch lelijk maar acceptabel

| Punt | Toelichting |
|---|---|
| Structurele escapes op drie plekken | `manuscript_syntax.escape_ranges` (structurele regels), `document_view.classify_block_line:105–108` (een tweede, net andere lijst) en `manuscript_markup.escape_literal_space_prefix`. B2 komt precies uit deze asymmetrie. Bij de fix: één tabel met prefixdefinities gebruiken voor alle drie. |
| Tweede zichtbare projectie | `manuscript_markup._visible_projection`/`_visible_text_with_styles` naast `document_view.visible_projection`, voor insert/remove-validatie. |
| Lui import-cyclus | `document_view` → `media.markup` (top-level), `media.markup` → `document_view`/`manuscript_markup` (lui). De cyclus `document_view` ↔ `manuscript_markup` is weg; `manuscript_syntax` is puur. |
| Zoeken en vervangen in `media/markup.py` | Ze horen in `manuscript_text.py`. Woordtelling en AI staan daar al. |
| Eigen regels in `markdown_io` voor `***`, `## `, `> `, `[-*]` | Acceptabel: dit is een lezer van *extern* Markdown, geen QuietWriter-semantiek. |

### Veilig later opruimen

- Dode code:
  - `pdf_exporter._BULLET_RE`/`_NUMBER_RE` (`:49–50`);
  - `docx_io._effective_run_bool`, `_run_is_code`;
  - `manuscript_syntax.unescape_literal_text` (ongebruikt);
  - `media.markup.text_without_image_blocks`.
- Alleen door tests gebruikt: `parse_docx_book` (6 testbestanden), `paragraph_to_markdown`, `parse_markdown_book`. Laat
  die tests de productieroutes testen.
- De 6 pyflakes-meldingen.
- `SNAPSHOT_INFO.txt`.

### Antwoord op de deelvragen

- **Zelfstandige regexes voor manuscriptsemantiek:** alleen de dode PDF-regexes, de externe Markdown-lezer en de
  scene-dedup in `markdown_io.py:362`. Geen consumer interpreteert zelfstandig QuietWriter-bron.
- **Consumers die ruwe bron gebruiken waar zichtbare tekst nodig is:** geen meer gevonden. De Bewaarplaats, het
  klembord, zoeken en AI gebruiken allemaal projecties.
- **Dubbele syntaxdefinities:** ja, de structurele escapes (zie hierboven).

---

## 15. Antwoord op de Markdown- en opslagvraag

1. **Is platte tekst als canonieke opslag nog juist?** Ja. Deze review bevestigt het. Elk probleem bleek met
   bytes-in-hand te diagnosticeren, en de migratie is herstelbaar met een gewoon checkpoint.
2. **Is het QuietWriter-profiel formeel genoeg?** Bijna. De grammatica is centraal, maar de structurele escaperegels
   zijn niet symmetrisch (B2), en `MANUSCRIPT_SYNTAX.md` moet de leesregels voor `\-`, `\>`, `\##`, `N\.` en `\\`
   exact vastleggen.
3. **Zijn syntaxversie en featureflags voldoende?** Het mechanisme wel (fail-closed, onbekende features geweigerd).
   De **legacy-detectie** niet: "geen marker" omvat twee verschillende grammatica's (B1).
4. **Is de grens tussen schrijverstekst en bron robuust?** Voor typen, Delete/Backspace en Enter: ja. Voor de
   spatie na een prefix, plakken midden in een regel, Shift+Enter en vervangen over een opmaakgrens: nog niet.
5. **Is `DocumentView` voldoende centraal?** Ja, voor alle consumers.
6. **Kunnen we afsluiten?** Na één kort hardeningblok wel (§16–17).

---

## 16. Advies: **C, nog één (kort) hardeningblok**

Geen D: de architectuur is goed, en alle problemen hebben een lokale fix.

Geen B: B1 beschadigt bij het **eerste openen** precies de boeken van recente gebruikers. B2 zet zichtbare tekens in
proza bij gewone handelingen. En de releasepoort (pytest met PySide6) is rood. Dat zijn geen "kleine fixes na
afsluiten".

Het blok is klein: naar schatting vijf gerichte wijzigingen plus tests. Daarna is het **A**.

---

## 17. Exacte minimale fixes vóór afsluiten

1. **B1, migratiebeslissing.** Bepaal per boek of de bron uit het escape-tijdperk komt.
   - **Vingerafdruk** = elke reeks die alleen de 1.2.19+-editor schrijft: `\*`, `\~`, `` \` ``, `\<`, en op de
     regelstart `\- `, `\> `, `\## `, `\* `, `N\. `.
   - **Vingerafdruk gevonden** → het boek is escape-tijdperk: zet alleen de marker en wijzig geen bytes.
   - **Geen vingerafdruk** → pre-escape: verdubbel alleen backslashes **binnen huidige `escape_ranges`**. Andere
     backslashes tonen in beide grammatica's hetzelfde, dus die verdubbelen geeft alleen onnodige bytewijzigingen.
   - **Gemengd of twijfel** (alleen `\\` aanwezig) → toon in de dialoog het aantal en enkele voorbeeldregels in beide
     lezingen, en laat de gebruiker kiezen.
   - Neem `planning/texts/*.md` mee (L1).
   - Test met beide corpora uit `mig130.py`.
2. **B2, wees-structuurescapes.**
   - Lees `\-`, `\>`, `\#` op de regelstart als escape, **ongeacht** wat erop volgt. Dat is veilig: migratie dekt de
     legacy-gevallen af.
   - Laat `escape_literal_text` de invoegcontext meekrijgen: escape een structuurprefix alleen als de geplakte regel
     op een regelstart belandt. Of strip na het invoegen in de geraakte blokken structuurescapes die niet op de
     regelstart staan.
   - Gebruik één gedeelde prefixtabel voor `escape_ranges`, `classify_block_line` en de schrijfkant.
3. **H1, Shift+Enter.** Behandel Shift+Return expliciet als `insertText('\u2028')` in één edit-block, en sluit `'\r'`
   en `'\n'` uit van het letterlijke typpad. De bestaande test wordt dan groen.
4. **H2, vervangen over een opmaakgrens.** Sla matches over waarvan het bronbereik een marker van een inline-span maar
   gedeeltelijk bevat. Zoeken mag ze blijven vinden; vervangen meldt "N overgeslagen (over opmaakgrens)". Liever dat
   dan een slimme herschrijving.
5. **M1 en M2, DOCX zonder stil verlies.**
   - Gebruik namespace-bewuste xpath in `_top_level_sdt_blocks` (`child.xpath(..., namespaces={'w': W_NS})`) of
     `iter`, en plaats de blokken in documentvolgorde.
   - Detecteer `w:endnoteReference` en `w:footnoteReference` (niet de relatie) en geef een specifieke melding.
6. **Releasepoort.** Laat de suite met PySide6 draaien, met 0 overgeslagen editortests.

Optioneel in hetzelfde blok, omdat het klein is en direct waarde heeft:
- M6: schuif het selectie-einde naar de escapestart.
- L6: `_escape_pair_at` per blok in plaats van per document.

**Na dit blok af te handelen als gewone backlog (blokkeert afsluiten niet):** M3 lijstnummers, M4 U+2028 in exports,
M5 CommonMark-veilige export, M7 vergrendelde kaart, M8 frontmatter, M9 beelden in de interne MIME, L2–L9.

---

## 18. Advies voor Boekenkast en planken

**Datamodel**
- `shelves.json` op werkmapniveau: `[{id, name, kind: series|genre|pen_name|custom, order, hidden: bool, sort: …}]`.
- Lidmaatschap staat **in de plank** (`book_ids`, met een volgorde voor series), niet in `book.json`. Zo blijven
  boekmappen onafhankelijk van de kast, en hoeft een QWBOOK-export van een boek geen privacy-informatie mee te dragen.
- Een boek mag **op meerdere planken** staan (een serie én een pseudoniem).
- Een virtuele plank **"Niet ingedeeld"** toont alle boeken zonder plank. Dat is de standaardplank en kan nooit
  verborgen worden.

**Verbergen: de regel die de eis afdwingt**
- Een boek is **verborgen zodra het op minstens één verborgen plank staat.** Verbergen wint van zichtbaarheid; anders
  lekt een boek via een tweede, zichtbare plank.
- Pas het filter toe op **één centrale plek**: een `visible_books(library, mode)`-dienst. Alle UI moet daardoor:
  boekenkast, "laatst gebruikt", zoekresultaten (inclusief de SQLite-index: verborgen boeken niet indexeren of de
  resultaten filteren), aantallen ("5 boeken"), badges, Bewaarplaats-herkomst ("uit boek X"), de prullenbak,
  exportdialogen en het venster- en recent-menu.
- Cover-thumbnails en caches van verborgen boeken niet vooraf laden.
- Schrijf een test die alle UI-oppervlakken langsloopt met een verborgen boek met een unieke titel, en op geen enkele
  label- of tooltiptekst die titel mag vinden.

**Demo-modus**
- Een sessievlag ("Demo-modus aan") die verborgen planken volledig weglaat, **inclusief het bestaan van de plank**:
  geen "1 verborgen plank". Uitzetten vraagt een bewuste actie in Instellingen.
- Het is geen beveiliging. Zeg dat eerlijk in de UI: de bestanden staan gewoon in de werkmap. Wie echte privacy wil,
  heeft een aparte werkmap nodig. Leg dat uit.
- Bij het openen van een boek uit een verborgen plank buiten de demo-modus: geen extra drempel nodig.

**Sorteren:** per plank (handmatig of serievolgorde, titel, laatst gebruikt, woorden). De kast zelf sorteert de
planken handmatig.

**Migratie:** geen bytewijziging aan boeken. Bij de eerste start ontstaat `shelves.json` leeg; alles staat in "Niet
ingedeeld". Optioneel kan één expliciete actie een plank per auteur of per serie voorstellen.

**UX-risico's**
- Een verborgen boek "kwijt" denken. Toon daarom buiten de demo-modus wel een teller of een ingeklapte plank.
- Dubbele weergave van een boek op meerdere planken. Maak duidelijk dat het hetzelfde boek is (zelfde
  kaartinteractie, geen kopie).
- Lege planken.
- Synchronisatieconflicten in `shelves.json` tussen twee computers. Gebruik hetzelfde revisieguardpatroon als
  `book.json`.

---

## 19. Advies voor links

**`[tekst](url)` blijft na 1.2.30 logisch.** Het past in het profiel, en de grammatica- en serializerlagen zijn er nu
klaar voor. Minimale veilige implementatie:

1. **Feature-flag `link-v1`** in `manuscript_syntax`. Oudere 1.2.30-builds weigeren het boek dan netjes (fail-closed,
   al getest).
2. **Lezen:** inline-link alleen in de vorm `[tekst](<url>)` of `[tekst](url)` zonder spaties, alleen als volledige
   span binnen één regel, en nooit over een andere span-grens.
3. **Schrijven:** links ontstaan alleen via een expliciete actie (Ctrl+K of een dialoog). Gewoon typen en plakken
   escapen `[` (alleen `[`; dat is genoeg). Plakken van `[a](b)` blijft daarmee letterlijk. Leer van B2: escape
   contextvrij, want `[` is overal inline.
4. **Editor:** de URL is een **beschermd, verborgen bereik**, net als een beeldpad. Bewerken gaat via een dialoog. Het
   klembord draagt in text/plain alleen de linktekst; de interne MIME draagt de link mee.
5. **Model:** `ImportInlineRun.attrs = {'href': …}`, niet als stijl.
   - DOCX-import: `w:hyperlink r:id` → href. Interne ankers en `HYPERLINK`-velden → tekst plus melding (of het veld
     parsen).
   - Exports: EPUB `<a>`, PDF-anker, DOCX-relatie, Markdown verbatim.
6. **Valideer schemes** bij export (`http`, `https`, `mailto`).

Doe dit pas ná het hardeningblok. Tabellen: geen sterke reden gezien; de huidige "tabel als leesbare tekst" bij import
is voor romans voldoende.

---

## 20. Wat ik niet heb kunnen testen

- **Windows zelf:** Segoe UI, DirectWrite, het echte toetsenbord. In het bijzonder **IME en dode toetsen** (die via
  `inputMethodEvent` binnenkomen en niet via `keyPressEvent`): mogelijk een route langs de escaping [afgeleid]. Of
  Shift+Enter op Windows hetzelfde doet (H1) is afgeleid uit Qt-gedrag, niet gezien.
- **Echt slepen en neerzetten met de muis.** Alleen `QDropEvent` is gesimuleerd.
- **Echte Word-bestanden.** Het corpus is gemaakt met python-docx en handmatige OOXML. Word-voorbladen, complexe velden
  en tracked deletions met opmaak heb ik niet getest.
- **Hoe e-readers en Word ruwe U+2028 tonen** (M4).
- **QWBOOK-import van een unmarked pakket** (L2): afgeleid uit code, niet uitgevoerd.
- **De eenmalige UI-pauze bij de gedebouncede woordtelling** van 100k woorden (alleen de functietijd gemeten).
- **OneDrive en virusscanners** tijdens migratie of import.
- **Een schermlezer.**
- **Meerdere QuietWriter-processen op dezelfde werkmap** (de 24-uursregel voor staging).

---

### Bijlage: harnassen (buiten het project, meegeleverd als zip)

| Bestand | Inhoud |
|---|---|
| `esc130.py` | 67 editorscenario's met echte Qt-events: typen, correcties, structuurinvariant, slepen en neerzetten, klembord, zoeken, vervangen, plakken midden in een regel, interne beeldplak |
| `esc124*.py` | de 1.2.24-matrix, ongewijzigd |
| `mig130.py` | golden corpus pre-escape en escape-tijdperk; migratie, checkpoint, herstel, fout halverwege, fail-closed |
| `parity130.py`, `parity130b.py` | consumer-pariteit en uitsplitsing per formaat |
| `docx124.py`, `docx130.py`, `docx130b.py` | DOCX-corpus, foutinjectie, SDT-xpathdiagnose, publish-fout, staging-opruiming |
| `md130.py`, `md130b.py` | Markdown-roundtrip en CommonMark-veiligheid van gewone proza |
| `perf130.py`, `prof130.py`, `docxperf124.py` | performance en profielen |

Aanroep: `QT_QPA_PLATFORM=offscreen python3 -I <script> <pad-naar-uitgepakte-zip>`.
