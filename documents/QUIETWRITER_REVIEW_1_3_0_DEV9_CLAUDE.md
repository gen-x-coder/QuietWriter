# QuietWriter 1.3.0-dev.9: opvolgreview van N1 en N2

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.9.zip`, SHA-256 `cf2d47da1c3c768e300cd9cf3c01021c03477289f8260ede2e864d8c56e7bf89`
**Opdracht:** `documents/REVIEW_REQUEST_1.3.0-dev.9_CLAUDE.md`. Er is geen code gewijzigd.

**Verschil met dev.8:**
- Code: `ui/bookshelf.py` (sleutel = `sha256(pad)`; bij het laden alleen 64-hex-sleutels accepteren) en
  `tests/conftest.py` (`setTestModeEnabled(True)`).
- Tests: versie- en metadata-tests en het nieuwe `test_bookshelf_cache_130_dev9_qt.py`.
- Locales en `README.md` zijn byte-identiek.

---

## 0. Conclusie

**N1 en N2 zijn opgelost. Er zijn geen blockers en geen regressies.**

**De Boekenkast is functioneel releaseklaar voor 1.3.0, behoudens de Windows- en visuele acceptatietest.** Daarbij hoort
ook de beslissing over de covercache.

Er is één kanttekening bij N1 (§3): de testcachebestanden belanden nu in `~/.qttest`. Dat is de bedoelde
Qt-testlocatie, maar ze stapelen zich daar nog steeds op. Dit is backlog en geen blocker.

---

## 1. Regressie

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 | ✅ **761 geslaagd**, 304 subtests, 0 gefaald, 0 overgeslagen, 105 s |
| Exitcode | rc **139** na een volledig geslaagde suite. Ongewijzigd: de bekende teardown. |
| `python main.py --smoke-test` | ✅ rc 0 |
| locales | ✅ `OK: 1551 keys in 5 locales`; alle 5 bestanden byte-identiek aan dev.8 |
| undefined-names | ✅ OK |
| pyflakes | ✅ 32 meldingen, identiek aan dev.8; `tests/conftest.py` is schoon |

---

## 2. N2: gehashte cache-sleutels [test, `cache139.py`]

**Opzet:** 25 boeken, waarvan er 5 `GEHEIMTITEL nnn` heten en op een privéplank staan. Elke sessie draait als apart
proces met een geïsoleerde appdatamap.

| Controle | Resultaat |
|---|---|
| Cachebestand in de lokale appdata, buiten de werkmap; geen nieuwe bestanden in de werkmap; `library.json` byte-identiek | ✅ |
| Alle 300 sleutels zijn 64 hextekens | ✅ |
| Cachetekst bevat geen boektitel (ook geen `boek-0…`) en geen pad (geen werkmap, geen `/`, geen `chapters`, geen `.md`) | ✅. Het bestand is ook kleiner: 30 kB tegen 39 kB. |
| Tweede proces-sessie | ✅ 0 tellingen |
| Eén hoofdstuk gewijzigd | ✅ precies 1 telling; cache bijgewerkt; de sessie daarna 0 |
| Twee werkmappen | ✅ twee aparte bestanden |
| Corrupte JSON, JSON-lijst, verkeerde types, hash-sleutel in hoofdletters, leeg bestand | ✅ geen crash, opnieuw geteld, daarna een bruikbare cache |
| `XDG_DATA_HOME` is een bestand; het cachepad is een map | ✅ werkt (telt opnieuw) |

### Migratie vanaf dev.8 [test]

| Stap | Resultaat |
|---|---|
| Cachebestand in het dev.8-formaat aangemaakt: 300 pad-sleutels, met daarin `GEHEIMTITEL` | – |
| dev.9 start: pad-sleutels geven geen hit | ✅ alle 300 hoofdstukken opnieuw geteld |
| Inhoud na de refresh | ✅ **uitsluitend** SHA-256-sleutels (300 stuks) |
| Privétitel en padtekst | ✅ uit het bestand verdwenen |
| Volgende sessie | ✅ 0 tellingen |
| Gemengd bestand (half oud, half nieuw) | ✅ alleen de oude helft (150) opnieuw geteld, daarna alleen hashes |

---

## 3. N1: testisolatie [test, inspectie]

| Controle | Resultaat |
|---|---|
| `tests/conftest.py` zet `QStandardPaths.setTestModeEnabled(True)` als PySide6 aanwezig is (op moduleniveau, dus vóór elke test) | ✅ |
| Volledige suite met een geïsoleerde `HOME`: nieuwe `bookshelf-word-counts-*.json` in de **echte** appdatamap (`~/.local/share`) | ✅ **0** (dev.8: 50) |
| Testmodus beïnvloedt de app-runtime | ✅ nee. `setTestModeEnabled` komt alleen voor in `tests/conftest.py`, en `build_exe.cmd` weigert een release met `tests/` erin. De smoke-test schrijft geen cache. |

**Kanttekening (backlog):** testmodus verplaatst de bestanden naar Qt's testlocatie, maar ruimt ze niet op. Na één
suiterun stonden er **50 bestanden in `~/.qttest/share/test_ai_worker_state_qt.py/cache/`**. Elke run voegt nieuwe hashes
toe, omdat de tijdelijke werkmappen telkens anders heten. Op Windows staat `.qttest` ook onder de gebruikersmap.

Dit voldoet aan de opdracht ("niet de echte appdatamap"), maar het is niet helemaal schoon.

**Fix (één regel):** een autouse-fixture die `StartPage._word_count_cache_path` naar `tmp_path` zet, of
`QStandardPaths`-paden per sessie naar een tijdelijke map.

**Bijvangst, bestaand gedrag:** de suite maakt ook een lege `~/QuietWriter/dictionaries` aan in de echte gebruikersmap.
Dat komt door de standaardwerkmap van `settings_page` als `workspace` niet is ingesteld. Dat is precies de plek waar de
echte standaardwerkmap staat. Het is onschuldig (alleen `mkdir`), maar hoort in dezelfde opruiming.

---

## 4. Presentatiemodus [test]

Allemaal gelijk aan dev.8:

| Harnas | Resultaat |
|---|---|
| `demo137.py`, stable en dev-profiel | 36/37 in beide profielen. De enige FAIL is het bekende backlogpunt L1: verborgen exportlabels. |
| `demo138.py` (W1 en W2, foutpaden, logging) | 26/26 |
| `demo136b.py` | geen lekken na `DeferredDelete`; fail-closed bij een toekomstige of corrupte `library.json` |

---

## 5. Performance [meting]

| | dev.8 koud | dev.9 koud | dev.8 warm (2e sessie) | **dev.9 warm (2e sessie)** |
|---|---|---|---|---|
| 25 boeken (300 hoofdstukken) | 3916 ms | 4409 ms | 59 ms | **42 ms** |
| 100 boeken (1200 hoofdstukken) | 15 346 ms | 15 200 ms | 103 ms | **115 ms** |

De verschillen vallen binnen de meetruis; de koude sessie wordt volledig bepaald door `count_words`. SHA-256 over 1200
paden kost minder dan 1 ms. Er is geen regressie. Aan de covers is niets veranderd, dus die heb ik niet opnieuw
gemeten.

---

## 6. Packaging en documentatie

| Controle | Resultaat |
|---|---|
| `__version__`, `SNAPSHOT_INFO.txt`, metadata-tests | ✅ `1.3.0-dev.9` |
| `.pytest_cache` en `__pycache__` in de ZIP | ✅ geen van beide |
| `README.md` | ✅ byte-identiek aan dev.8 |
| `README_EN.md` | ✅ niet aanwezig en niet aangemaakt |
| `RELEASE_NOTES_1.3.0-dev.9.md` | ✅ beschrijft gehashte hoofdstukpaden, de migratie van dev.8-sleutels, ongewijzigde invalidatie, testmodus, en `library.json` als ongewijzigd |
| `CHANGELOG.md` | ✅ dev.9-sectie aanwezig en correct |

---

## 7. Bevindingen en classificatie

### Blocker

Geen.

### Vóór 1.3.0

**V1. Lockfile-headers** in `packaging/requirements-*.lock` noemen nog "QuietWriter 1.2.32 Windows RC". Puur cosmetisch;
bijwerken bij de release-build. Dit is resterend punt B6 uit dev.8.

### Backlog

| # | Punt |
|---|---|
| B1 | **Testcache in `~/.qttest`** stapelt zich op (§3). Ook de lege `~/QuietWriter/dictionaries` uit de suite. |
| B2 | **Cache-opschoning:** items van verwijderde boeken blijven staan (300 → 300). Nu alleen een kwestie van bestandsgrootte: ongeveer 100 bytes per hoofdstuk, zonder titels. |
| B3 | **Wees-cachebestanden in het dev.8-formaat** van werkmappen die dev.9 nooit meer opent (oude paden, testmappen op de ontwikkelmachine) houden hun pad-sleutels mét titels. Dat raakt alleen dev-testers. Optioneel: bij het opstarten `bookshelf-word-counts-*.json` verwijderen als het bestand niet-hex-sleutels bevat, of de bestandsnaam versioneren (`…-v2-<hash>.json`). |
| B4 | **Bestaande backlog uit dev.7 en dev.8:** L1 (exportlabels), L2 (stille weigering bij een fail-closed nieuw boek of import), L3 (`deleteLater`-flits), L4 (schaduwen), L5 (hergebruik van kaarten), L8 (cachegrenzen bij gelijke grootte en mtime), B2 (gedeeld `.tmp`-bestand), B3 (half gesloten toestand na een late exceptie), B5 (overige hardcoded `QSettings('QuietWriter','QuietWriter')`). |

### Afhankelijk van de Windows-acceptatietest

**W4 / P3: covercache.** Ongewijzigd ongeveer 0,2 s per warme actie bij covers van 1600×2400 (dev.8-meting).

---

## 8. Niet getest

- **Gelijktijdige processen** die dezelfde cache schrijven. Alleen geïnspecteerd; dat is ongewijzigd ten opzichte van
  dev.8.
- **Een niet-schrijfbare map via rechten.** Als root niet af te dwingen; getest met een bestand in plaats van een map, en
  met een map in plaats van een bestand.
- **Koude start bij 500 grote boeken.** Schaalt lineair met het aantal woorden.

### Bijlage

`cache139.py`: N2 (sleutelvorm, inhoud zonder titels of paden), migratie van dev.8 (volledig en gemengd), invalidatie,
twee werkmappen, corrupte en onbruikbare cache. Met de omgevingsvariabele `ALLEEN_TIMING=1` alleen de koude en warme
sessie.

**Aanroep:** `python3 cache139.py <pad-naar-zip> [boeken]`

**Ongewijzigd opnieuw gedraaid:** `demo137.py` (beide profielen), `demo138.py`, `demo136b.py` en `cache138.py` (alleen
de timing, tegen dev.8).
