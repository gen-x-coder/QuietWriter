# QuietWriter 1.3.0-dev.7: opvolgreview van B4, P1, P2 en Presentatiemodus

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.7.zip`, SHA-256 `33ce2b00c94ae71a572872d3715297ec7625dcb908b6f7e1e6b3982a041e0a4e`
**Opdracht:** `documents/REVIEW_REQUEST_1.3.0-dev.7_CLAUDE.md`. Er is geen code gewijzigd.

**Verschil met dev.6:**
- Code: alleen `ui/bookshelf.py`, `ui/main_window.py`, de 5 locales, versie- en metadata-tests, en twee nieuwe testbestanden.
- `README.md` is byte-identiek.

Legenda: **[test]** = gereproduceerd met harnas · **[meting]** = gemeten · **[inspectie]** = code gelezen.

---

## 0. Samenvatting

**Geen blockers vóór dev.8.**

- **B4 is opgelost.** Een open privéboek wordt opgeslagen en gesloten, en geen enkele boekgebonden pagina houdt het
  nog vast. `open_book()` weigert privéboeken fail-closed. Publieke boeken werken normaal.
- **P1 en P2 werken.**
  - Een warme refresh parseert niets opnieuw.
  - Na een wijziging wordt precies één hoofdstuk opnieuw geteld.
  - Tijdens het typen in het zoekveld vindt geen enkele refresh plaats.
  - Elke warme actie kost nu 0,2–0,4 s, waar dat in dev.6 4–5 s was.

**Wel doen vóór 1.3.0** (klein, zie §5):
1. Het foutpad zet Presentatiemodus in het **dev-profiel** terug in de verkeerde settings-opslag.
2. Een onverwachte exceptie tijdens het sluiten laat Presentatiemodus "aan" staan met het privéboek open.
3. De woordtellingcache is **niet persistent**, alleen per sessie. De eerste Boekenkast na het opstarten kost daardoor
   nog steeds 4,3 s (25 boeken) tot 16 s (100 boeken).
4. **P3 (covers)** is nu het grootste deel van elke warme actie (ongeveer 200 van 290 ms).

**Correctie op mijn dev.6-review [inspectie]:** B4 was in de echte UI vrijwel niet bereikbaar. De knop staat op de
Boekenkast, en naar de Boekenkast gaan (`go_home`) sluit het actieve boek altijd. Mijn dev.6-harnas zette de knop
programmatisch. De centrale guard in dev.7 is dus vooral verdediging in de diepte, wat terecht is voor een latere
sneltoets of menu-item. Dat verklaart ook waarom de foutpaden van §5 in de praktijk weinig voorkomen.

---

## 1. Regressie (A)

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 (Linux, Python 3.13, PySide6 6.11.2) | ✅ **755 geslaagd**, 304 subtests, 0 gefaald, 0 overgeslagen, ongeveer 100–113 s (twee keer gedraaid) |
| Exitcode van `pytest` | ⚠️ **139 (segfault) ná "755 passed"**. Dit gebeurt ook bij dev.6 (751 passed, rc 139), dus het is geen regressie. Het treedt op bij het afsluiten van de interpreter (Qt-teardown) en geeft geen faulthandler-trace. In dev.6 had ik dit niet gemeld. |
| `--smoke-test` | ✅ rc 0 |
| locales | ✅ `OK: 1551 keys in 5 locales` |
| undefined-names | ✅ OK |
| pyflakes | 32 meldingen, **identiek aan dev.6** (ongebruikte imports plus dezelfde 6 cosmetische) |
| Nieuwe tests | `test_bookshelf_presentation_130_dev7_qt.py` (4) en `test_bookshelf_demo_130_dev7.py` (5). Het foutpad is **niet** getest (§5). |

---

## 2. B4 / Presentatiemodus (B) [test]

**Harnassen:**
- `demo136.py` en `demo136b.py`: herhaald, zelfde uitkomst als dev.6. Er lekt niets, alleen de bekende
  `deleteLater`-flits (backlog).
- `demo137.py`: nieuw. Doorzoekt **het hele venster, ook verborgen pagina's**, op de privémarker. Score: 35/37 bij de
  standaard settings-naam.

| Scenario | Resultaat |
|---|---|
| Privéboek open, tekst getypt (dirty), Presentatiemodus aan | ✅ wijziging staat op schijf |
| Pagina na het inschakelen | ✅ Boekenkast |
| Verwijzingen naar het privéboek | ✅ geen. `active_book`, editor (boek en hoofdstuk), planning, profiel, geheugen, media, integriteit, export, boekdetails, AI en publicatie staan allemaal op `None` |
| Undo-geschiedenis van de editor | ✅ leeg; `undo()` haalt niets terug |
| Zichtbare widgets met de privétitel of -tekst | ✅ geen |
| Terugnavigeren via `show_editor`, `show_planning`, `show_book_profile`, `show_book_memory`, `show_media`, `show_integrity`, `show_export`, `show_open_points` | ✅ alle acht komen op de Boekenkast uit, zonder privéboek |
| `open_book(privé)` terwijl Presentatiemodus al aan staat | ✅ geweigerd, zonder melding (zie §5, L-punt) |
| `open_book(publiek op een niet-standaardplank)` | ✅ opent |
| Presentatiemodus aanzetten met een publiek boek open | ✅ het boek blijft open |
| Toekomstig schema of corrupte `library.json`, `open_book(publiek of privé)` | ✅ beide geweigerd (fail-closed) |
| Corrupte `library.json` en aanzetten met een privéboek open | ✅ het boek wordt gesloten |
| Foutpad: `editor.save()` geeft `False` | ✅ Presentatiemodus gaat terug naar **uit**; het boek blijft open |
| Foutpad: `save_chapter` gooit `StorageWriteError` (de echte OneDrive-lock-route) | ✅ terug naar **uit** |
| Foutpad: `planning.save_pending()` geeft `False` | ✅ terug naar **uit** |
| Foutpad: `save_chapter` gooit een **onverwachte** exceptie (`PermissionError`) | ❌ blijft **aan** met het privéboek open (§5, W2) |
| Foutpad in het **dev-profiel** (`QuietWriter-Dev`) | ❌ de knop zegt "uit", maar `demo_mode_enabled()` blijft `True` (§5, W1) |
| Automatisch heropenen bij het opstarten | ✅ bestaat niet [inspectie: `restore_state` herstelt alleen geometrie en splitters]. Opstarten met Presentatiemodus aan opent geen boek [test]. |
| Labels en tooltips in 5 talen | ✅ "Presentatiemodus: aan/uit", *Presentation mode*, *Präsentationsmodus*, *Mode présentation*, *Modo presentación*. De tooltip noemt in alle 5 talen "geen beveiliging" en gebruikt dezelfde paginanamen als de navigatie. Er staat nergens meer "Demo" in de UI. |

**Oordeel:** B4 is correct en centraal opgelost. De privacybelofte "niets zichtbaar" houdt in alle realistische
paden stand.

---

## 3. Performance (C) [meting]

**Opzet:** zoals in dev.6. Boeken van 12 hoofdstukken × ongeveer 3500 woorden; een derde heeft een JPEG-cover van
1600×2400. Offscreen Qt op Linux. De event-loop wordt inclusief `DeferredDelete` gepompt, zoals in de echte app.
Daardoor zijn de warme getallen realistischer dan mijn dev.6-getallen.

### 3.1 Gebruikersacties (`shelfperf137.py`)

| Actie | dev.6, 25 boeken | **dev.7, 25 boeken** | **dev.7, 100 boeken** |
|---|---|---|---|
| Eerste opbouw (koude cache) | 4206 ms | **4287 ms** (300 tellingen) | **15 976 ms** (1200 tellingen) |
| Tweede `refresh()` zonder wijziging | 3786 ms | **135 ms** (0 tellingen) | **209 ms** (0 tellingen) |
| Presentatiemodus aan | 3706 ms | **222 ms** | **312 ms** |
| Presentatiemodus uit | 4354 ms | **277 ms** | **346 ms** |
| Sorteren (4 varianten) | 4624–5236 ms | **286–311 ms** | **313–410 ms** |
| "Boek 0" typen, 6 toetsen met 40 ms ertussen | 4368 ms per toets | **82 ms per toets, 0 refreshes tijdens het typen**, daarna 1 refresh | idem |
| Refresh na het opslaan van 1 hoofdstuk | – | **113 ms** (precies 1 telling) | **390 ms** (1 telling) |
| Breedte 1400→900→1400 | 5158 ms | **189 ms** | **172 ms** |

### 3.2 Correctheid van de cache [test]

| Situatie | Resultaat |
|---|---|
| Normaal opslaan | ✅ telling direct juist |
| Externe wijziging met een andere grootte | ✅ juist |
| Zelfde inhoud opnieuw geschreven (nieuwe `mtime_ns`) | ✅ juist |
| Externe wijziging met **dezelfde grootte en een teruggezette `mtime_ns`** | verouderde telling. Dat is een bewuste grens van de sleutel en in de praktijk verwaarloosbaar. Op FAT32/exFAT (USB-stick, 2 s mtime-resolutie) kan een bewerking met gelijke grootte binnen 2 seconden ook gemist worden. Alleen cosmetisch: het gaat om een woordtelling. |
| Cache-items | 1 per hoofdstuk; nooit opgeruimd voor verwijderde boeken (verwaarloosbaar) |
| Nieuwe `StartPage`, dus een herstart | **lege cache**. De release notes noemen de cache "persistent", maar hij leeft alleen zolang het proces draait. |

### 3.3 Waar de tijd nu zit, per warme actie (`shelfperf137b.py`)

| | 25 boeken | 100 boeken | 500 boeken (12 hoofdstukken × 300 woorden) |
|---|---|---|---|
| Warme `refresh()` | 112 ms | 217 ms | 972 ms |
| Sorteeractie inclusief herbouw en paint | 256 ms | 346 ms | 1048 ms |
| ↳ `BookCover.paintEvent` (onder de profiler) | **201 ms** | **199 ms** | 174 ms |
| ↳ `BookCard.__init__` (widgets bouwen) | 38 ms | 160 ms | 844 ms |
| ↳ cache-lookups (`stat` per hoofdstuk) | 10 ms | 47 ms | 245 ms |
| Hele pagina schilderen / zonder schaduwen | 84 / 69 ms | 85 / 68 ms | 85 / 67 ms |
| 1 cover opnieuw schilderen (1600×2400 JPEG) | 18,9 ms | 20,1 ms | – |

**Conclusies:**
- **Cover-decodering (P3) is nu ongeveer 70 % van elke warme actie** bij 25 tot 100 boeken. Elke herbouw maakt nieuwe
  covers, en elke cover decodeert en schaalt het volledige JPEG-bestand in `paintEvent`.
- **Schaduwen (P4)** kosten ongeveer 15 ms per paint. Niet de moeite.
- **Widgets bouwen** domineert pas boven ongeveer 300 boeken. Incrementeel hergebruik blijft backlog.

**P3/P4 op Windows:** daar kon ik niet meten. Qt Widgets rastert op Windows ook op de CPU, en JPEG-decodering is CPU-werk.
Ik verwacht dus dezelfde verhouding: ongeveer 0,2 s extra per zoekresultaat, sortering of toggle bij echte covers.
Covers uit Word zijn vaak kleiner dan 1600×2400 en dan is de winst kleiner. **Advies:** laat de Windows-test met echte
covers beslissen. Voelt sorteren of zoeken daar trager aan dan ongeveer een kwart seconde, doe dan P3 vóór 1.3.0. P4 kan
in elk geval naar de backlog.

---

## 4. Windows en visueel (D)

**Niet getest.** Er is geen Windows-omgeving. Zie §7.

---

## 5. Bevindingen en classificatie

### Blocker vóór dev.8 / 1.3.0

Geen.

### Wel doen vóór 1.3.0

**W1. Het foutpad schrijft naar de verkeerde settings-opslag in het dev-profiel [test, inspectie]**

`StartPage` leest en schrijft `bookshelf_demo_mode` via de **hardcoded** opslag `QSettings('QuietWriter','QuietWriter')`
(`bookshelf.py:359`). Het foutpad in `_demo_mode_changed` schrijft naar `self.settings` van `MainWindow`
(`main_window.py:211`). In het dev-profiel is dat `QuietWriter-Dev`.

Gevolg in een dev-build:
- De knop toont "uit", maar `demo_mode_enabled()` blijft `True`.
- Privéboeken blijven verborgen en `open_book` blijft ze weigeren. Dat is fail-safe, maar inconsistent.
- Na een herstart staat Presentatiemodus weer "aan".

Daarnaast delen dev- en stable-installaties zo dezelfde Presentatiemodus-status.

**Fix (kies één):**
- Geef `StartPage` de settings van `MainWindow` mee.
- Of, het kleinst: zet in het foutpad gewoon `self.start.demo_toggle.setChecked(False)` **zonder** `blockSignals`. Dan
  schrijft `_set_demo_mode(False)` naar de juiste opslag, ververst de Boekenkast, en keert `_demo_mode_changed(False)`
  direct terug.

**W2. Een onverwachte exceptie tijdens het sluiten laat de modus "aan" [test]**

`go_home()` vangt alleen de bekende fouten af; die geven netjes `False` terug. Een andere exceptie, zoals een kale
`PermissionError` of een bug in een pagina-save, breekt `_demo_mode_changed` af ná het inschakelen. Gevolg: de
modus staat **aan** terwijl het privéboek open blijft.

- **Kans:** klein. Opslaan verpakt `OSError` al in `StorageWriteError`, en de knop is nu alleen bereikbaar zonder open
  boek.
- **Fix:** zet `try:` om `self.go_home()` heen, behandel `except Exception` als mislukking (dus de revert-tak), en log de
  fout. Ongeveer 3 regels.

**W3. De woordtellingcache is niet persistent [meting]**

De eerste Boekenkast na het opstarten telt alles opnieuw: 4,3 s bij 25 boeken en 16 s bij 100 boeken van ongeveer
42 000 woorden. Elke appstart blokkeert dus zo lang. Dit is geen regressie, want 1.2.31 telt ook alles [inspectie].
Het is wel de grootste resterende wachttijd, en de release notes beloven persistentie.

**Fix:** sla dezelfde dict `{pad: (mtime_ns, size, woorden)}` op als JSON in een lokale map, niet in de
gesynchroniseerde werkmap: `AppLocalDataLocation`, met één bestand per werkmap-hash. Laad het bij de constructie en
schrijf het na een refresh als er iets veranderd is. Een kapot of ontbrekend bestand betekent gewoon een lege cache.
Ongeveer 20 regels, en er is geen nieuwe invalidatielogica nodig.

**W4 (voorwaardelijk). P3, covercache**

Doe dit als de Windows-test met echte covers een merkbare vertraging laat zien (§3.3).

**Fix:** een dict of `QPixmapCache` op `(pad, mtime_ns, size, doelbreedte, doelhoogte)` → geschaalde pixmap, plus
`QSettings` één keer lezen per pagina.

### Veilig backlog voor 1.4.x

| # | Punt |
|---|---|
| L1 | **Achtergebleven labels op de Exportpagina.** Na het sluiten bevatten `exportHeader` ("Maak een publicatiebestand van "GEHEIMTITEL…") en het controlepaneel ("✓ Titel: GEHEIMTITEL roman") nog de titel. Ze zijn verborgen en worden overschreven zodra een ander boek wordt geopend; ze zijn niet zichtbaar te krijgen [test]. Netjes: leegmaken in `export_page.set_book(None)`. Dit is algemeen `go_home`-gedrag en niet specifiek voor Presentatiemodus. |
| L2 | **Stille weigering in `open_book`.** Bereikbaar via "Nieuw boek" of import bij een corrupte of toekomstige indeling terwijl Presentatiemodus aan staat. De gebruiker ziet "Boek aangemaakt; plankindeling kon niet worden bijgewerkt", daarna gebeurt er niets en is het boek onzichtbaar [test]. Een korte statusregel helpt: "Verborgen in Presentatiemodus". |
| L3 | **`deleteLater`-flits.** Oude kaarten staan één event-loop-ronde onder de nieuwe [test, dev.6 en dev.7]. Er lekt niets. Pas oppakken als het op Windows zichtbaar is. |
| L4 | **P4: schaduwen.** Ongeveer 15 ms per paint; niet nodig. |
| L5 | **Incrementeel hergebruik van kaarten.** Pas bij meer dan 300 boeken; widgets bouwen kost dan 0,8 s bij 500. |
| L6 | **Bewaarplaats en Prullenbak** blijven na een foutpad-revert gefilterd tot ze opnieuw getoond worden. Dat herstelt zich vanzelf, want `show_*` ververst. |
| L7 | **Segfault (rc 139)** bij het afsluiten van `pytest` op Linux; ook in dev.6. Alleen relevant als CI naar de exitcode kijkt. Controleer de exitcode eenmalig op Windows. |
| L8 | **Cache-grenzen:** gelijke grootte plus gelijke `mtime_ns` (FAT32 binnen 2 s), en geen opruiming van verwijderde paden. Cosmetisch. |

---

## 6. Advies voor dev.8

**Doen:** W1 en W2 (een paar regels, plus één test voor elk foutpad en elk profiel), en W3.

**Daarna:** Windows-test met echte covers.
- Voelt sorteren of zoeken trager dan ongeveer 0,25 s? Dan W4.
- Anders is de Boekenkast klaar voor 1.3.0.

Geen architectuurverbouwing nodig: cache plus debounce volstaan aantoonbaar tot ongeveer 300 boeken.

---

## 7. Niet getest

- **Alles uit D (Windows en visueel):**
  - de checked-stijl van de Presentatiemodus-knop;
  - de tooltip-weergave;
  - hoe het zoekveld voelt tijdens het typen;
  - de flits bij een refresh;
  - scrollen en hover met echte covers;
  - DPI-schaling van 125 % en 150 %.
  Alle metingen zijn offscreen op Linux. Absolute tijden op Windows verschillen.
- **Echte covers** uit Word of de browser (PNG met alpha, CMYK, kleinere formaten). Getest is alleen met gegenereerde
  JPEG's van 1600×2400.
- **Echte bibliotheken.** De tekst is synthetisch, met een vaste woordenschat en weinig markup.
- **Koude start van 500 grote boeken.** Alleen 500 kleine boeken zijn gemeten; de koude kosten schalen lineair met het
  aantal woorden (ongeveer 4 µs per woord).
- **Echte OneDrive-lock.** Gesimuleerd met `StorageWriteError` en `PermissionError` via monkeypatch.
- **Externe wijzigingsconflicten** (`ExternalModificationError`) op het moment van inschakelen. Die route geeft een
  dialoog; ik heb hem niet doorgelopen.
- **Schermlezer**: alleen `accessibleName` is gecontroleerd.
- **Exitcode 139 op Windows.**

### Bijlage

| Harnas | Inhoud |
|---|---|
| `demo137.py` | B4-scenario's, het hele venster doorzocht inclusief verborgen widgets, foutpaden, fail-closed, opstart. Optioneel tweede argument `QuietWriter-Dev` voor het dev-profiel. |
| `shelfperf137.py` | Gebruikersacties, telt `count_words`-aanroepen en refreshes, debounce, cache-correctheid |
| `shelfperf137b.py` | Profiel van een warme actie, aandeel van covers en schaduwen bij 25, 100 en 500 boeken. Moet naast `shelfperf137.py` staan. |

**Aanroep:** `python3 <harnas> <absoluut pad naar uitgepakte zip> [boeken] [hoofdstukken] [woorden]`.

- `demo136.py` en `demo136b.py` uit de dev.6-review zijn ongewijzigd opnieuw gedraaid.
- `shelfperf136.py` en `shelfperf136b.py` zijn vervangen door de 137-varianten. Die gebruiken dezelfde opzet, maar
  pompen ook `DeferredDelete` en meten het stubpad niet meer, omdat de echte cache nu bestaat.
