# QuietWriter 1.2.31: laatste PySide6-run en verificatie van het hardeningblok

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Snapshot:** `QuietWriter-1.2.31.zip`, SHA-256 `6166c430c24dc8a874d25643755c84bc9e3b5a91935dfcffca058eea4c0b543d`
(✅ geverifieerd), `__version__ = "1.2.31"`. Er is geen productiecode gewijzigd.

Legenda: **[test]** = gereproduceerd met code of echte Qt-events · **[inspectie]** = code gelezen · **[afgeleid]** =
conclusie op basis van het voorgaande, niet apart uitgevoerd.

---

## 1. Conclusie: **A, refactor afgerond / releasecandidate**

Alle blockers en high-bevindingen uit de 1.2.30-review zijn verholpen. Ik heb dat geverifieerd met dezelfde
harnassen, opnieuw gedraaid en waar nodig uitgebreid. De volledige suite is groen **met** PySide6. Wat overblijft is
backlog die de manuscriptarchitectuur niet raakt (§6).

---

## 2. Volledige testresultaten

**Omgeving:** Linux x86_64, Python 3.13.16, PySide6 6.11.2 (offscreen), python-docx 1.2.0.

| Controle | Resultaat |
|---|---|
| `pytest` (volledig, met PySide6) | ✅ **714 geslaagd, 0 gefaald, 0 overgeslagen**, 304 subtests, 108,5 s |
| `main.py --smoke-test` | ✅ rc 0 |
| `check_undefined_names.py` | ✅ |
| `check_locales.py` | ✅ 1525 sleutels in 5 talen |
| `compileall` | ✅ |
| `pyflakes` | dezelfde 6 cosmetische meldingen als in 1.2.30 (ongebruikte variabelen en `nonlocal`) |

De 46 skips in jouw lokale run zijn de Qt-tests. Hier draaien ze allemaal, en ze slagen allemaal.

---

## 3. Verificatie van de 1.2.30-bevindingen

| 1.2.30-bevinding | 1.2.31 | Bewijs |
|---|---|---|
| **B1:** migratie beschadigt boeken uit het escape-tijdperk | ✅ **opgelost** | `mig130.py` scenario 2: alle 4 regels (`*31623455`, `5*3`, `2*4`, `- Kom`, `1944.`, `C:\pad`) zichtbaar gelijk; modus `escape-era` zet alleen de marker |
| Pre-escape-boek (golden corpus) | ✅ | alle 7 regels gelijk, inclusief `\\server\share`, `C:\Users\naam\.config`, `regex a\.b`, `\#tag` midden in de regel, `\->`, NBSP, U+2028, bullet, `3.`, scene. Er verandert nu nog maar **1** backslash (was 9): minimaal. |
| Checkpoint, herstel, opnieuw openen | ✅ | `pre_syntax_migration` staat in de geschiedenis; herstel geeft de originele bron met manifest zonder marker |
| Fout halverwege (met echte wijzigingen) | ✅ | `mig131.py`: alle 4 hoofdstukken byte-identiek terug, manifest zonder marker |
| Dubbelzinnig (alleen even backslash-runs) | ✅ | zonder keuze: `AmbiguousManuscriptSyntaxError`. "Huidige weergave behouden": zichtbaar gelijk. "Oude tekst beschermen": de legacy-lezing. In de UI krijg je de keuzedialoog. |
| Publicatieteksten gaan mee | ✅ | worden in dezelfde migratie meegenomen |
| Onbekende versie, feature of rommel | ✅ | niet geopend, bytes onaangeroerd |
| **B2:** spatie na `- `/`> `/`## ` weghalen | ✅ **opgelost** | `\-` blijft verborgen; zichtbaar `-`, `-Kom`, `>Kom`, `##Kom` |
| **B2:** plakken midden in een regel (`1944. Het jaar`, `- Kom mee`, `## kop`, `> citaat`) | ✅ **opgelost** | geen zichtbare backslash |
| **H1:** Shift+Enter | ✅ **opgelost** | bron `Regel\u2028- twee`, één alinea, `- twee` letterlijk; de eigen Qt-test is groen |
| **H2:** vervangen over een opmaakgrens | ✅ **opgelost** | `was **heel** moe` + vervang `was heel` slaat de match over; de bron blijft heel |
| **M6:** selectie die binnen een escape eindigt | ✅ opgelost | `a*b`, selectie tot binnen de escape + Delete geeft `*b` |
| **M1:** blok-SDT | ✅ opgelost | `BLOK-SDT-ALINEA` staat in documentvolgorde |
| **M2:** eindnoten | ✅ opgelost | expliciete melding "Eindnoten worden nog niet geïmporteerd." |
| **L6:** escapecontrole per blok | ✅ opgelost | zie §4 |

**Editormatrix (`esc130.py`, echte Qt-events):** 66 van 67 OK. De ene "FAIL" is mijn verouderde verwachting voor
Shift+Enter (twee alinea's). Het nieuwe gedrag (één alinea met U+2028) is juist het gewenste.

De vijf 1.2.24-harnassen zijn ook allemaal groen.

**De vijf punten uit de Windows-checklijst**, hier getest met echte Qt-toetsevents (offscreen):

| Punt | Resultaat |
|---|---|
| `- ` typen en de spatie weghalen | ✅ alleen `-` |
| `1944. Het jaar` plakken na `Begin ` | ✅ geen backslash |
| Shift+Enter | ✅ U+2028 binnen dezelfde alinea |
| Vervangen van `was heel` in `was **heel** moe` | ✅ bron onbeschadigd (match overgeslagen) |
| Boek uit 1.2.24/1.2.29 openen | ✅ gesimuleerd met een realistisch escape-tijdperkhoofdstuk; zichtbaar gelijk. Jouw echte boeken heb ik niet gezien (§7). |

---

## 4. Performance [test]

| Hoofdstuk | 1.2.24 | 1.2.30 | **1.2.31** |
|---|---|---|---|
| 10k woorden, ms per toets | 26 | 8,8 | **1,2** |
| 30k woorden | 93 | 24,7 | **1,5** |
| 100k woorden | 294 | 73,4 | **3,5** |
| DOCX 85k woorden + 20 beelden | 16 s | 5,8 s | 5,8 s (ongewijzigd) |

De dirty-state is correct: na typen is het document dirty, na het terugdraaien van alle toetsen weer schoon. Typen
voelt nu ook in een extreem hoofdstuk direct aan. Er is geen O(n²)-route gevonden.

---

## 5. Resterende grens van de migratie (bewust, laag risico) [test]

De beslisregel "vingerafdruk betekent escape-tijdperk" geldt per boek. Pre-1.2.19-tekst die **toevallig** zelf een
vingerafdruk bevat, wordt daarom als escape-tijdperk gelezen en verliest één zichtbare backslash:

| Pre-1.2.19-bron | Na migratie zichtbaar |
|---|---|
| `\-> pijl aan regelstart` | `-> pijl …` |
| `regex a\*b` | `a*b` |
| `\#tag` **aan de regelstart** (midden in de regel blijft het goed) | `#tag` |
| `\! uitroep` | `! uitroep` |
| `C:\Users en \<tag>` | `\<` wordt `<` |

Een gemengd boek (een oud hoofdstuk met `\\server` en een nieuw hoofdstuk met `\*`) wordt in zijn geheel als
escape-tijdperk gezien.

**Oordeel:** dit is zonder bewerkingsgeschiedenis niet te onderscheiden. De gevallen zijn zeldzaam in proza, het
checkpoint vangt ze op, en de keuze voor de escape-tijdperklezing beschermt juist de recente boeken. **Geen
blocker.** Twee optionele verbeteringen voor de backlog:

1. Maak de structurele vingerafdruk strenger. Neem alleen op wat de 1.2.19–1.2.29-editor echt schreef: `^\\- `,
   `^\\> `, `^\\## `, `^\\\* `, `^\\!\[`. Laat losse `^\\#` en `^\\-` zonder spatie weg.
2. Toon na migratie in escape-tijdperkmodus het aantal regels met een "geïnterpreteerde backslash", met een link naar
   het checkpoint.

---

## 6. Backlog (blokkeert afsluiten niet; ongewijzigd sinds 1.2.30) [test]

| # | Punt |
|---|---|
| M3 | Echte lijstnummers (`3.`, `7.`) gaan verloren in PDF, EPUB en DOCX (`<ol>` zonder `start`). CommonMark rendert 3, 4. Word `List Number` wordt bij import twee keer `1.`. Alleen de AI-context behoudt de nummers. |
| M4 | U+2028 komt als ruw teken in PDF, EPUB en DOCX. Moet `<br/>` en `<w:br/>` worden. Markdown en AI zijn wel correct. |
| M5 | Markdown-export is niet CommonMark-veilig voor gewone proza: `_x_`, `[a](b)`, `# `, `+ `, `1) `, vier spaties inspringing, `&amp;`. (7 gevallen, `md130b.py`) |
| M7 | Een boek met een toekomstige syntax verdwijnt van de boekenplank. Toon het als vergrendelde kaart. |
| M8 | Markdown-import: onbekende frontmattervelden en YAML-lijsttypen blijven niet behouden. |
| M9 | De interne klembord-MIME draagt beeldregels mee. Tussen boeken plakken geeft een verwijzing naar een niet-bestaand bestand. |
| L5 | Bij een fout tijdens het aanmaken van de staging (vóór de `try`) blijft `.import-*` staan, totdat de 24-uursopruiming die weghaalt. |
| – | De 6 pyflakes-meldingen, dode helpers en `SNAPSHOT_INFO.txt` (1.2.13). |

Advies: neem M4 en M3 mee met de linkfeature, omdat die dezelfde exportlagen raakt. M5 hoort bij een volgende ronde
voor Markdown-publicatie.

---

## 7. Wat ik niet heb kunnen testen

- **Windows zelf.** Een echt toetsenbord, Shift+Enter via de Windows-invoerstack, IME en dode toetsen (die lopen via
  `inputMethodEvent` en kunnen in theorie de escaping omzeilen [afgeleid]), en Segoe UI.
- **Jouw echte 1.2.24/1.2.29-boeken.** Ik heb een realistisch escape-tijdperkhoofdstuk gesimuleerd. Één keer openen
  van een echt testboek op Windows blijft zinvol, juist omdat dat de migratiedialoog doorloopt.
- **De dubbelzinnigheidsdialoog in de UI.** Alleen de API-route is getest, beide keuzes.
- **Echte Word-bestanden.** Het corpus is gemaakt met python-docx en handmatige OOXML.
- **Echt slepen en neerzetten**, een schermlezer, OneDrive en virusscanners tijdens migratie of import.

---

### Bijlage: harnassen

Nieuw: `mig131.py` (fout halverwege met echte wijzigingen, dubbelzinnige keuze, publicatieteksten, adversaire
pre-escape-tekst). Daarnaast de ongewijzigde 1.2.30-harnassen (`esc130.py`, `mig130.py`, `parity130*.py`,
`docx124/130.py`, `md130b.py`, `perf130.py`).
