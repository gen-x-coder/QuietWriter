# QuietWriter 1.3.0-dev.6: Boekenkast-performance, Demo-modus en naamgeving

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.6.zip`, SHA-256 `0d9c77e477634a10c90512b779fc8fd778d6ababfa560a06b13d9f99667dcca7`
**Opdracht:** `documents/REVIEW_REQUEST_1.3.0-dev.6_CLAUDE.md`. Er is geen code gewijzigd. De harnassen staan buiten het
project (bijlage).

Legenda: **[meting]** = gemeten met harnas · **[test]** = functioneel gereproduceerd · **[inspectie]** = code gelezen.

---

## 0. Samenvatting

- **De suite is groen.** Er is **één blocker** in Demo-modus: een privéboek dat al **open** staat, blijft open en
  bereikbaar nadat je Demo-modus aanzet (§2).
- **De Boekenkast is traag**: ongeveer **4 seconden per refresh bij 25 boeken**, en dat geldt ook **per toetsaanslag in
  het zoekveld**.
  - **Ongeveer 99 % daarvan is woordtelling.** Bij elke refresh wordt elk hoofdstuk van elk boek opnieuw gelezen en
    geparsed.
  - Met een woordtellingcache daalt een refresh naar **21 ms** (25 boeken), 81 ms (100) en 413 ms (500).
  - De rest van de pagina is daarna gezond. Een incrementele herbouw is tot ongeveer 100 boeken niet nodig.
- **Demo-modus filtert verder correct.** Er lekt niets via de Boekenkast, de telling, het zoeken, de Bewaarplaats of de
  Prullenbak. Fail-closed werkt bij een toekomstig schema en bij corrupte JSON, en de status blijft behouden na een
  herstart.
- **Naam:** gebruik **Presentatiemodus**. Vermijd **Privémodus**.

---

## 1. Testresultaten

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 (Linux, Python 3.13, PySide6 6.11.2) | ✅ **751 geslaagd**, 304 subtests, 0 gefaald, 0 overgeslagen, 110,6 s |
| `--smoke-test` | ✅ rc 0 |
| locales | ✅ 1551 sleutels in 5 talen |
| undefined-names | ✅ |
| pyflakes | dezelfde 6 cosmetische meldingen als eerder |
| Demo-modus functioneel (`demo136.py`, `demo136b.py`) | ✅ behalve **B4** (§2) |
| Performance (`shelfperf136.py`, `shelfperf136b.py`) | zie §3 |

---

## 2. Blockers

### B4. Demo-modus aanzetten terwijl een privéboek open staat: het boek blijft open [test]

**Waar:** `main_window.py` (rond regel 170–171). `demo_mode_changed` ververst alleen de Bewaarplaats en de Prullenbak.
Niets controleert het actieve boek.

**Reproductie** (`demo136.py`, laatste blok):
1. Open het boek "GEHEIMTITEL roman", dat op een privéplank staat.
2. Zet Demo-modus aan.

**Resultaat:**
- De editor houdt het boek geladen, met titel en tekst.
- Terugnavigeren naar de editor toont het privéboek volledig.
- Planning, profiel, geheugen en AI-pagina's van dat boek zijn ook nog bereikbaar [inspectie]. Ze hangen aan hetzelfde
  actieve boek.

Dit is precies het scenario waarvoor de functie bestaat: "even snel Demo aan voordat ik mijn scherm deel".

**Minimale fix:** bij het **inschakelen** van Demo-modus:
1. Controleer of het actieve boek in `visible_book_ids([actief.id], demo_mode=True)` zit.
2. Zo niet: sla het boek op en sluit het. Leeg de editor, planning, profiel, geheugen en AI-context.
3. Ga naar de Boekenkast.

Dezelfde controle is ook nodig bij **opstarten met Demo aan** als QuietWriter het laatst geopende boek automatisch
heropent [inspectie: controleer of dat pad bestaat].

Zorg ook dat in Demo-modus **geen route** een verborgen boek opent. Denk aan "recent geopend", een open-pad, of een
link vanuit een fragment in de Bewaarplaats. De Bewaarplaats verbergt die fragmenten nu al, dus dat lijkt gedekt, maar
een test is goedkoop.

**Test:** open een privéboek, zet Demo aan, en controleer dat de huidige pagina de Boekenkast is, dat de editor leeg
is, en dat geen enkele zichtbare widget de privétitel of -tekst bevat.

Er zijn geen andere blockers.

---

## 3. Performanceprofiel [meting]

**Opzet:** 25 boeken × 12 hoofdstukken × ongeveer 3500 woorden. 9 boeken hebben een echte JPEG-cover van 1600×2400.
Er zijn 3 planken (standaard, privé en "Serie"). Offscreen Qt, venster 1400×900. Alle tijden zijn wandkloktijd en de
beste van 3 pogingen.

### 3.1 Gebruikersacties bij 25 boeken (huidige code)

| Actie | Tijd |
|---|---|
| Eerste opbouw en tonen | **4206 ms** |
| `refresh()` zonder wijziging | **3786 ms** |
| Hele pagina schilderen | 403 ms |
| Demo aan | 3706 ms |
| Demo uit | 4354 ms |
| Sorteren op titel A→Z | 4624 ms |
| Sorteren op titel Z→A | 4915 ms |
| Sorteren op woorden | 5236 ms |
| Zoeken: "Boek 0" typen (6 toetsen) | **26 206 ms**, dus 4368 ms per toets |
| Breedte 1400→900→1400, met reflow en schilderen | 5158 ms |

### 3.2 Waar de tijd zit (cProfile op één refresh en schilderbeurt)

| Onderdeel | Aandeel |
|---|---|
| `count_words` (via `parse_document`) | **≈ 99 %** |
| `read_chapter` (alle hoofdstukken) | 65 ms |
| `list_books` | 8 ms |
| `book_activity` | 10 ms |
| `shelves.load()` (één snapshot) | ≈ 0 ms |
| `BookCover.paintEvent` | 1438 ms onder de profiler (168 aanroepen): JPEG decoderen en glad schalen bij **elke** paint |

### 3.3 Schaal, met een perfecte woordtellingcache (gestubd)

| | 25 boeken | 100 boeken | 500 boeken |
|---|---|---|---|
| `refresh()` | 21 ms | 81 ms | 413 ms |
| Pagina schilderen | 329 ms | 345 ms | 429 ms |
| Pagina schilderen zonder schaduweffecten | 272 ms | 292 ms | 319 ms |
| Eén kaart met cover opnieuw schilderen | 21 ms | – | – |

### 3.4 Knelpunten

**Huidige code bij 100 en 500 boeken:** extrapolatie. Woordtelling schaalt lineair met het totaal aantal woorden. Bij
100 boeken van deze omvang is dat ongeveer 15 seconden per refresh, en bij 500 boeken ruim een minuut.

| # | Knelpunt | Bijdrage | Ernst bij 25 / 100 / 500 | Simpelste veilige optimalisatie | Risico |
|---|---|---|---|---|---|
| P1 | **Woordtelling bij elke refresh**: elk hoofdstuk opnieuw lezen en parsen, en de cache leeft maar één refresh lang | ≈ 99 % van de refresh | hoog / onbruikbaar / onbruikbaar | Een cache per hoofdstuk met sleutel `(pad, mtime_ns, size)` → woorden, die blijft leven over refreshes heen (dict op `StartPage` of `Library`). Bij opslaan wordt het hoofdstuk vanzelf ongeldig door de nieuwe mtime. Optioneel: persistent in `.cache/`. | **Laag.** In het slechtste geval toont een kaart even een verouderde telling. |
| P2 | **`textChanged` → volledige `refresh()`** | elke toets kost een volledige refresh | hoog (door P1) / matig / matig | Een **debounce** van 200 ms met een `QTimer.singleShot`-herstart. Na P1 is dit vooral voor een rustig beeld. | Zeer laag |
| P3 | **Cover decoderen en schalen in `paintEvent`**, plus een nieuw `QSettings` per cover | 21 ms per cover-repaint, oplopend bij hover en scroll | laag / matig / matig | De geschaalde `QPixmap` cachen per `(pad, mtime, doelgrootte)`, in `QPixmapCache` of in een dict, en alleen bij resize opnieuw schalen. `QSettings` één keer lezen. | Laag |
| P4 | **`QGraphicsDropShadowEffect` per kaart** | ongeveer 15–25 % van de paint-tijd | laag / laag / matig | Het effect weglaten, of een vaste schaduw tekenen in de kaart (een rand of een gradient in `paintEvent`). Past ook beter bij "simpel en schrijven". | Laag. Puur visueel. |
| P5 | **Volledige herbouw van widgets** (`deleteLater` op alles) | na P1 21–413 ms | geen / laag / matig | Niet nu. Pas bij meer dan 300 boeken overwegen om kaarten te hergebruiken op `book_id`. | Matig. Niet doen zonder noodzaak. |
| P6 | **`_WrappingCardHost._reflow`** | klein; de resize-tijd komt vooral door repaint en covers | laag | Niets nodig na P3 en P4 | – |
| P7 | `list_books`, plank-snapshot, `book_activity`-sortering | < 20 ms | geen | Niets | – |
| P8 | Demo-filter in Bewaarplaats en Prullenbak (`visible_book_ids([id])` per rij) | niet meetbaar bij deze omvang; elke aanroep doet een `load()` | geen / laag / laag | Eén snapshot per refresh en `loaded=` doorgeven, net als de Boekenkast. Is vooral voor consistentie (M3). | Zeer laag |

---

## 4. Aanbevolen optimalisaties, in volgorde

1. **P1: woordtellingcache per hoofdstuk** met sleutel `(pad, mtime_ns, size)`, levend over refreshes heen. Dit is de
   enige ingreep die de Boekenkast van "traag" naar "direct" brengt. Een kleine diff in `bookshelf.py`.
2. **P2: debounce van het zoekveld** (200 ms). Een paar regels.
3. **P3: cache de geschaalde cover-pixmap** en lees `QSettings` één keer.
4. **P4: schaduweffecten weglaten of goedkoper tekenen.** Een productkeuze. Visueel klein, en rustiger.
5. **Polish:** verberg de oude widgets (`hide()`) vóór `deleteLater()` in `refresh()`. Nu staan ze één event-loop-ronde
   onder de nieuwe [test]. Er lekt niets, maar het kan heel kort flikkeren.
6. **P8:** één snapshot in de Bewaarplaats en de Prullenbak.

**Niet doen:** incrementele herbouw, virtualisatie of threads voor het tellen. Met P1 blijft een refresh tot 100
boeken onder de 100 ms en tot 500 boeken onder de halve seconde. Meer is bloat.

---

## 5. Oordeel over Demo-modus [test]

| Controle | Resultaat |
|---|---|
| Privéplank en privéboeken verdwijnen uit de Boekenkast | ✅ |
| De boekentelling bevat geen privéboeken | ✅ de telling verandert en noemt alleen zichtbare boeken |
| Zoeken op de privétitel vindt niets | ✅ |
| "Verplaats naar"-menu's tonen de privéplank niet | ✅ |
| De Bewaarplaats toont geen fragment uit een privéboek | ✅ |
| De Prullenbak toont geen verwijderd hoofdstuk of verwijderd boek van een privéplank | ✅ |
| Uitzetten herstelt alles direct | ✅ |
| Na een herstart is Demo nog aan, met de knoptekst "Demo-modus: aan" | ✅ |
| Taalwissel | ✅ de knoptekst volgt na een herstart (net als de rest van de UI) |
| Toekomstig schema in `library.json` | ✅ fail-closed: 0 boeken in Demo-modus, ook geen publieke, en niets in Bewaarplaats en Prullenbak |
| Corrupte `library.json` | ✅ fail-closed, net als bij een toekomstig schema |
| **Open privéboek bij het inschakelen** | ❌ **B4** |

**Oordeel:** na B4 is Demo-modus **productveilig als presentatiemiddel**. Het is geen beveiliging en dat claimt het
ook niet. De filtering zit centraal in `visible_book_ids` en `visible_shelf_ids`, en alle drie de pagina's gebruiken
die. Dat is de juiste opzet.

**Polish (geen blocker):**
- De `deleteLater`-flits uit §4, punt 5.
- Bij fail-closed staat de Boekenkast in Demo-modus leeg zonder uitleg. Een korte regel helpt: "Planindeling kon niet
  worden gelezen; Demo-modus toont daarom niets."
- Het venster toont geen zichtbaar signaal dat Demo aan staat, behalve de knop op de Boekenkast. Een klein label in de
  statusbalk of titelbalk voorkomt verwarring als je in een andere pagina zit.

---

## 6. Naamgevingsadvies

| Naam | Oordeel |
|---|---|
| **Presentatiemodus** | ✅ **voorkeur.** Beschrijft de situatie (presenteren, scherm delen, beurs, les) en niet een belofte. Vertaalt overal netjes: *Presentation mode* (EN), *Präsentationsmodus* (DE), *Mode présentation* (FR), *Modo presentación* (ES). Windows en Office gebruiken hetzelfde begrip, dus gebruikers herkennen het. |
| Demo-modus | Acceptabel, maar technisch. Suggereert dat je **demodata** of een voorbeeldboek te zien krijgt, niet "mijn eigen werk zonder privé". |
| **Privémodus** | ❌ **vermijden.** Klinkt als incognito, beveiliging of versleuteling, en belooft dus meer dan de functie doet. Ook verwarrend, omdat de knop privé juist *verbergt* terwijl de naam zegt dat je privé *bent*. |
| Presenteren | Werkwoord als knoplabel is dubbelzinnig: start de knop een diavoorstelling? Wel bruikbaar als menutekst ("Presenteren…"). |
| Eigen suggestie: *Deelmodus* / *Scherm delen* | Duidelijk, maar Presentatiemodus is breder (ook projector of meekijken) en vertaalt beter. |

**Knoptekst:** "Presentatiemodus: aan" / "uit". **Tooltip:** "Verbergt privéplanken en hun boeken in de Boekenkast,
Bewaarplaats en Prullenbak. Geen beveiliging." Een eerlijke tooltip voorkomt de verkeerde verwachting.

Hernoem alleen de **weergavetekst** in de locales. De instellingssleutel `bookshelf_demo_mode` kan blijven.

---

## 7. Vóór de volgende dev-build en backlog

**Vóór de volgende dev-build:**
1. **B4**: open privéboek sluiten bij het inschakelen, en bij het opstarten met Demo aan, plus de test.
2. **P1**: woordtellingcache.
3. **P2**: debounce van het zoekveld.

**Kan veilig op de backlog:**
- P3 (covercache), P4 (schaduwen), de `deleteLater`-flits en P8.
- De naamswijziging naar Presentatiemodus. Liefst wel vóór de eerste publieke 1.3, omdat locales en screenshots
  ermee meegaan.
- Een melding bij fail-closed en een zichtbaar Demo-signaal buiten de Boekenkast.
- Incrementele herbouw: alleen als iemand echt meer dan 300 boeken heeft.

---

## 8. Niet getest

- **Windows**: Segoe UI, DPI-schaling (125 % en 150 %), echte GPU-paint en echte hover- en scroll-beleving. Alle
  metingen zijn offscreen op Linux. Absolute tijden verschillen op Windows, maar de verhoudingen (woordtelling ≈ 99 %)
  niet.
- **Echte covers** uit Word of de browser (PNG met alpha, CMYK-JPEG, heel grote bestanden). Getest met gegenereerde
  JPEG's van 1600×2400.
- **Echte boekomvang en -verdeling.** Synthetische hoofdstukken met een vaste woordenschat. Markdown-intensieve tekst
  kan `parse_document` nog duurder maken.
- **100 en 500 boeken met de huidige code.** Alleen gemeten met een gestubde woordtelling; de huidige code is
  geëxtrapoleerd.
- **OneDrive of Dropbox** tijdens het wisselen van Demo-modus. Alleen kopieën en verwijderen zijn gesimuleerd (dev.2).
- **Taalwissel zonder herstart.** De UI past taal pas na een herstart toe, dus alleen dat pad is getest.
- **Schermlezer**: wat er in Demo-modus wordt voorgelezen. Alleen `accessibleName` is in de lektest meegenomen.
- **Automatisch heropenen van het laatste boek bij opstarten met Demo aan** (zie B4). Niet expliciet doorgelopen.

### Bijlage

| Harnas | Inhoud |
|---|---|
| `shelfperf136.py` | Setup van 25 boeken, alle gebruikersacties, cProfile |
| `shelfperf136b.py` | Woordtelling gestubd; schaal 25/100/500; met en zonder schaduwen; repaint van één kaart |
| `demo136.py` | Lektests in het MainWindow met de marker `GEHEIMTITEL`: plank, fragment, verwijderd hoofdstuk, verwijderd boek, herstart, toekomstig/corrupt, open privéboek |
| `demo136b.py` | Lokaliseert lekkende widgets, test de `DeferredDelete`-afhandeling en fail-closed |

**Aanroep:** `python3 <harnas> <absoluut pad naar uitgepakte zip> [boeken] [hoofdstukken] [woorden]`.
