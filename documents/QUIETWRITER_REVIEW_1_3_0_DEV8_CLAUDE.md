# QuietWriter 1.3.0-dev.8: opvolgreview van W1, W2 en W3

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.8.zip`, SHA-256 `d384bfd7d2c4a08208bcec7530808da0a24b952f1cec5da4f2056c5068829f15`
**Opdracht:** `documents/REVIEW_REQUEST_1.3.0-dev.8_CLAUDE.md`. Er is geen code gewijzigd.

**Verschil met dev.7:**
- Code: alleen `ui/bookshelf.py` (settings meegeven, persistente cache) en `ui/main_window.py` (settings doorgeven,
  `try`/log/revert).
- Tests: versie- en metadata-tests, plus het nieuwe `test_bookshelf_presentation_130_dev8_qt.py`.

Legenda: **[test]** = gereproduceerd met harnas · **[meting]** = gemeten · **[inspectie]** = code gelezen.

---

## 0. Samenvatting

**W1, W2 en W3 zijn correct opgelost. Er zijn geen regressies en geen blockers vóór dev.9.**

**De Boekenkast is functioneel klaar voor de acceptatietest.** Een tweede sessie opent nu in 76 ms (25 boeken) of
109 ms (100 boeken) in plaats van 3,8 s of 15,3 s.

**Wel doen vóór 1.3.0** (twee kleine punten, §6):
- **N1:** de testsuite schrijft bij elke run ongeveer 50 cachebestanden naar de echte lokale appdatamap.
- **N2:** de cache-sleutels bevatten het boekmappad, dus ook **privé-boektitels**. Die blijven in de appdata staan,
  ook nadat het boek is verwijderd.

---

## 1. Regressie (A)

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 | ✅ **759 geslaagd**, 304 subtests, 0 gefaald, 0 overgeslagen, 108 s |
| Exitcode | rc **139** na een volledig geslaagde suite. Dit gedrag is **ongewijzigd** ten opzichte van dev.6 en dev.7: de bekende teardown bij het afsluiten. |
| `--smoke-test` | ✅ rc 0. Schrijft geen cachebestand. |
| locales | ✅ `OK: 1551 keys in 5 locales` |
| undefined-names | ✅ OK |
| pyflakes | 32 meldingen, **identiek aan dev.7**. De nieuwe code levert geen meldingen op. |

---

## 2. W1: runtimeprofiel en settings (B) [test, `demo138.py`, `demo137.py`]

| Controle | `QuietWriter` (stable) | `QuietWriter-Dev` |
|---|---|---|
| `StartPage.settings is MainWindow.settings` (dezelfde instantie) | ✅ | ✅ |
| Aanzetten schrijft alleen naar de eigen profielopslag; de andere blijft `None` | ✅ | ✅ |
| Na een herstart: aan, met de juiste knoptekst | ✅ | ✅ |
| Het andere profiel start met "uit" | ✅ | ✅ |
| Uitzetten wordt opgeslagen als `false` | ✅ | ✅ |
| Mislukt sluitpad (`save()` geeft `False`, of `StorageWriteError`): knop, `demo_mode_enabled()` en opslag staan alle drie **uit**, het boek blijft open | ✅ | ✅ |

`demo137.py` (dev.7-harnas): **36/37 in beide profielen** (in dev.7 was het dev-profiel 28/37). De enige FAIL is het
bekende backlogpunt L1: verborgen, achtergebleven exportlabels.

---

## 3. W2: onverwachte exceptie (C) [test, `demo138.py`]

| Scenario | Resultaat |
|---|---|
| Een `PermissionError` uit `save_chapter` tijdens het inschakelen | ✅ alle drie **uit**; het privéboek blijft open in de editor |
| Logging | ✅ in het crashlog onder het label "Presentatiemodus sluiten", met `PermissionError: [Errno 13] …`. Geen ontsnapte exceptie en geen dialoog (`notify=False`). |
| Recursie | ✅ geen. Het signaal `demo_mode_changed` vuurt precies 2 keer: aan, plus één geneste uit-revert. `_demo_mode_changed(False)` keert direct terug. |
| Een `RuntimeError` **laat** in `go_home`, nadat de editor al gesloten is | ✅ modus **uit**, gelogd. Zie de opmerking hieronder. |
| De bekende fouten (`False` en `StorageWriteError`) | ✅ geen regressie |

**Opmerking (backlog) bij de late exceptie:** een exceptie halverwege `go_home` laat een **half gesloten** toestand
achter:
- `active_book` is nog het privéboek, maar de editor en de planning zijn al leeg;
- "Schrijven" toont een lege editor;
- een volgende `go_home()` ruimt het netjes op.

Privacy is in orde: er is niets zichtbaar en de modus staat uit. Het gaat alleen om consistentie, en het is alleen
via een bug bereikbaar.

---

## 4. W3: persistente woordtellingcache (D) [test, meting, `cache138.py`]

Elke sessie is een **apart proces** met een geïsoleerde `XDG_DATA_HOME`, en de app- en organisatienaam staan zoals in
de echte app.

| Controle | Resultaat |
|---|---|
| Eerste koude sessie maakt een cachebestand aan | ✅ `<appdata>/QuietWriter/QuietWriter/cache/bookshelf-word-counts-<hash20>.json` (39 kB bij 300 hoofdstukken) |
| Cache staat buiten de werkmap; geen nieuwe bestanden in de werkmap; `library.json` byte-identiek | ✅ ✅ ✅ |
| Cache in `.qwbook` | ✅ kan niet: de export pakt alleen de boekmap in en de cache staat daar niet [inspectie] |
| Nieuwe proces-sessie zonder wijzigingen | ✅ **0** `count_words`-aanroepen |
| Eén hoofdstuk gewijzigd | ✅ precies **1** telling. Het cachebestand is bijgewerkt (nieuwe waarde 3); de sessie daarna telt weer 0. |
| Twee werkmappen | ✅ twee verschillende cachebestanden |
| Corrupte JSON, een JSON-lijst, verkeerde types, een leeg bestand | ✅ elk: geen crash, 300 hoofdstukken opnieuw geteld, daarna weer een bruikbare cache |
| `XDG_DATA_HOME` is een bestand, dus de map kan niet worden aangemaakt | ✅ werkt; telt elke sessie opnieuw |
| Het cachepad is een map | ✅ werkt |
| Opschoning | geen. Items van verwijderde boeken blijven staan (300 → 300) [test]. |

### Koude start [meting]

De tijd is de constructie van `StartPage`, dus tellen plus kaarten bouwen. Er is geen paint meegerekend.

| | dev.7, elke sessie | **dev.8, sessie 1 (koud)** | **dev.8, sessie 2 en verder** |
|---|---|---|---|
| 25 boeken (300 hoofdstukken, ongeveer 1 mln. woorden) | 4287 ms | 3788 ms | **76 ms** |
| 100 boeken (1200 hoofdstukken, ongeveer 4,2 mln. woorden) | 15 976 ms | 15 273 ms | **109 ms** |

De woordtelpiek is weg na de eerste sessie per werkmap, en ook na een hoofdstukwijziging (dan alleen dat ene
hoofdstuk).

---

## 5. Presentatiemodus-regressie (E) [test]

Opnieuw gedraaid: `demo137.py` in beide profielen, plus `demo136.py` en `demo136b.py`. Alle onderstaande punten zijn
ongewijzigd ten opzichte van dev.7.

| Punt | Resultaat |
|---|---|
| Privéboek sluiten bij het inschakelen | ✅ wijziging opgeslagen, Boekenkast getoond, geen enkele pagina houdt het boek vast |
| Publieke boeken blijven open en bereikbaar | ✅ |
| `open_book(privé)` | ✅ geweigerd |
| Corrupte of toekomstige `library.json` | ✅ fail-closed, ook bij `open_book` |
| Privégegevens in Boekenkast, Bewaarplaats en Prullenbak | ✅ geen; ook niet via zoeken of de telling |

---

## 6. Bevindingen en classificatie

### 1. Blocker vóór dev.9

Geen.

### 2. Wel doen vóór 1.3.0

**N1. De testsuite vervuilt de echte lokale appdata [test]**

Elke test die een `StartPage` met boeken bouwt, schrijft een cachebestand voor zijn tijdelijke werkmap. Na één
suiterun stonden er **50 bestanden** in `<appdata>/<naam van de eerste testmodule>/cache/`; zonder app-naam gebruikt Qt
`argv[0]`. Elke run komen er 50 nieuwe hashes bij, en die worden nooit opgeruimd. Op de ontwikkelmachine groeit dat
ongemerkt.

Alleen de nieuwe dev.8-test patcht `_word_count_cache_path`.

**Fix:** één regel in `conftest.py`: `QStandardPaths.setTestModeEnabled(True)`, of een autouse-fixture die
`_word_count_cache_path` naar `tmp_path` zet.

**N2. De cache bevat privé-boektitels en houdt ze vast na verwijdering [test]**

De sleutel is het volledige hoofdstukpad, en de boekmap heet `<slug(titel)>-<id8>`. Bij 25 boeken bevatten **60 sleutels
de privétitel**. Die staan in de lokale appdata, buiten de werkmap, en blijven staan nadat het boek is verwijderd,
omdat er niet wordt opgeschoond.

Dit is geen Presentatiemodus-lek; die is geen beveiliging en de werkmap zelf bevat de titels ook. Maar het is wel een
onnodige, blijvende kopie van privétitels op een plek waar de gebruiker die niet verwacht. De release notes zeggen
terecht "hoofdstukpad", maar niet dat daar de titel in zit.

**Fix (één regel):** gebruik als sleutel `sha256(str(path)).hexdigest()` in plaats van het pad. De invalidatie blijft
gelijk, want die loopt via `mtime_ns` en grootte. Bestaande caches worden daarna eenmalig koud; dat is geen probleem.

### 3. Alleen doen als de Windows- en visuele test dit bevestigt

**W4 / P3: covercache.**

| | 25 boeken | 100 boeken |
|---|---|---|
| Sorteeractie | 252 ms | 346 ms |
| ↳ `BookCover.paintEvent` | 196 ms | 191 ms |
| Warme refresh | 116 ms | 189 ms |
| 1 cover opnieuw schilderen | ongeveer 20 ms | ongeveer 20 ms |

Gemeten op dev.8 met een warme cache [meting]. Dit is gelijk aan dev.7: covers zijn nog steeds ongeveer 70 % van een
warme actie. De persistente cache verandert hier niets aan, want die raakt alleen de koude start.

**Mijn oordeel:** ja, de beslissing hoort terecht bij de test met echte covers. Het effect is reëel maar klein (ongeveer
0,2 s per actie), en hangt sterk af van het formaat van echte covers.

### 4. Backlog voor 1.4.x

| # | Punt |
|---|---|
| B1 | **Opschoning van de cache.** Bij een refresh zonder zoekfilter en buiten Presentatiemodus de items verwijderen die niet meer bestaan. Na N2 is het puur een kwestie van bestandsgrootte: ongeveer 130 bytes per hoofdstuk. |
| B2 | **Gedeeld `.tmp`-bestand.** Twee QuietWriter-processen op dezelfde werkmap delen hetzelfde tijdelijke bestand. In het slechtste geval wint één van beide of mislukt het schrijven stil, en wordt er opnieuw geteld. Onschuldig, want de laadcode valideert. |
| B3 | **Half gesloten toestand** na een exceptie laat in `go_home` (§3). |
| B4 | **Bestaande backlog uit dev.7:** L1 (exportlabels), L2 (stille weigering bij nieuw boek of import in een fail-closed toestand), L3 (`deleteLater`-flits), L4 (schaduwen), L5 (hergebruik van kaarten), L8 (cachegrenzen bij gelijke grootte en mtime). |
| B5 | **Overige hardcoded `QSettings('QuietWriter','QuietWriter')`** in `BookCover` (thema), `editor_page` (typografie), `manuscript_editor` en `manuscript_tree`. In het dev-profiel lezen die de stable-opslag. Het heeft niets met Presentatiemodus te maken en het is bestaand gedrag, maar dezelfde klasse fout als W1. |
| B6 | **Packaging-ruis:** de ZIP bevat een `.pytest_cache/`. `SNAPSHOT_INFO.txt` zegt nog "rerun … against dev.7". De `packaging/*.lock`-headers noemen nog "1.2.32 Windows RC". Bijwerken vóór de 1.3.0-release. |

---

## 7. Documentatie en packaging (G)

| Controle | Resultaat |
|---|---|
| `__version__` | ✅ `1.3.0-dev.8`. Ook `SNAPSHOT_INFO.txt` en de metadata-tests kloppen. |
| `README.md` | ✅ byte-identiek aan dev.7. `README_EN.md` is niet aanwezig. |
| `RELEASE_NOTES_1.3.0-dev.8.md` | ✅ beschrijft de cache als lokaal en persistent, in de appdatamap en niet in de werkmap, met een hash per werkmap en fouten die niet fataal zijn. Noemt `library.json` (ongewijzigd). Na N2 de zin "bewaart alleen hoofdstukpad" aanpassen naar "gehasht hoofdstukpad". |
| `CHANGELOG.md` | ✅ dev.8-sectie aanwezig en correct |

---

## 8. Niet getest

- **Echte gelijktijdige processen op één werkmap** die tegelijk de cache schrijven (B2). Alleen geïnspecteerd.
- **Een niet-schrijfbare map via rechten.** Als root zijn rechten niet af te dwingen. Wel getest met een bestand in
  plaats van een map, en met een map in plaats van een bestand.
- **Koude start bij 500 grote boeken.** Die schaalt lineair: ongeveer 3,6 µs per woord.
- **Een echte OneDrive-lock.** Gesimuleerd met `PermissionError` en `StorageWriteError` via monkeypatch.

### Bijlage

| Harnas | Inhoud |
|---|---|
| `demo138.py` | W1-profielscheiding (stable en dev), W2 (`PermissionError`, late `RuntimeError`, log, recursie), de bekende foutpaden |
| `cache138.py` | W3: aparte proces-sessies, cachelocatie, invalidatie, twee werkmappen, corrupte cache, ongeldige locaties, opschoning. Met de omgevingsvariabele `ALLEEN_TIMING=1` alleen de koude en warme sessie. |

**Aanroep:**
- `python3 demo138.py <pad-naar-zip>`
- `python3 cache138.py <pad-naar-zip> [boeken]`

**Ook opnieuw gedraaid:** `demo137.py` (met `QuietWriter` en `QuietWriter-Dev`), `shelfperf137.py` en
`shelfperf137b.py`. Let op: de regel "nieuwe StartPage begint met lege cache" in `shelfperf137.py` is voor dev.8
achterhaald; `cache138.py` meet dat nu correct.
