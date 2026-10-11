# QuietWriter 1.3.0-dev.2: opvolgreview van het plankfundament

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.2.zip`, SHA-256 `a03eec95…42e84af785`, `__version__ = "1.3.0-dev.2"`
**Scope:** opvolging van de dev.1-review (B1, B2, H1, H2, M1–M3), multiprocessing, migratie, fail-closed gedrag bij
een toekomstig schema, herstel. Er is geen code gewijzigd.

Legenda: **[test]** = gereproduceerd (`shelf130.py`, `shelf130b.py`) · **[inspectie]** = code gelezen.

---

## 1. Conclusie

**Alle dev.1-bevindingen zijn werkelijk opgelost.** Concurrency is nu ook tussen processen correct.

Er blijft **één blocker vóór de Demo-UI**: de automatische migratie op een **tweede computer met een onvolledig
gesynchroniseerde werkmap** schrijft een nieuwe `library.json` waarin alles publiek is. Daarnaast twee kleine
API-punten. Alle drie zijn klein (§4).

De Neo-boekenkast in **normale modus** kan nu op deze laag worden gebouwd. **Demo-modus** pas na B3.

---

## 2. Controles

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 (Linux, Python 3.13, PySide6 6.11.2) | ✅ **739 geslaagd**, 0 gefaald, 0 overgeslagen, 304 subtests, 101 s |
| `--smoke-test` | ✅ rc 0 |
| undefined-names | ✅ |
| locales | ✅ 1527 sleutels |
| pyflakes | dezelfde 6 cosmetische meldingen als eerder |
| Nieuwe tests `test_bookshelf_model_130_dev2.py` | 23 tests, waaronder een echte `multiprocessing`-test (spawn) |

---

## 3. Verificatie van de dev.1-bevindingen [test]

| dev.1 | Status | Bewijs |
|---|---|---|
| **B1:** `library.json` weg leidt tot stille hermigratie en een privacylek | ✅ **opgelost** | met last-good aanwezig: geen write, `source=last_good`, Demo-modus toont niets, last-good onaangeroerd, plankbewerkingen geblokkeerd tot expliciet herstel |
| **B2:** half falende boekoperaties | ✅ **opgelost** | `create_book`, DOCX-import, QWBOOK-import, herstel uit de prullenbak, definitief verwijderen en de prullenbak legen slagen allemaal bij corrupte JSON, schema 2, een ongeldige mapping en een `PermissionError` op `library.json`. De waarschuwing staat in `pop_shelf_metadata_warnings()`. Geen duplicaten meer. |
| **H1:** stil verlies bij gelijktijdige schrijvers | ✅ **opgelost** | threads 80/80. **Multiprocessing:** 4 processen × 25 `create_shelf` gaf 100/100, 0 fouten, 0,6 s. 3 processen × 30 door elkaar `move_book`: elk boek op precies één geldige plank, bestand canonical. Lockfile opgeruimd. |
| **H2:** onafhankelijke migraties botsen | ✅ **opgelost** | `DEFAULT_SHELF_ID = uuid5(...)`. Twee migraties van dezelfde werkmap zijn **byte-identiek**. |
| **M1:** toekomstig schema gooit een exceptie in queries | ✅ **opgelost** | `source='future'`, geen exceptie; Demo-modus leeg (boeken én planken) |
| **M2:** geen herstel-API en te strenge validatie | ✅ **opgelost** | een ongeldige mapping is leesbaar (normaal: standaardplank, demo: verborgen) en blokkeert writes. `restore_from_last_good()`, `reset_to_default()` en `describe_problem()` zijn er. |
| **M3:** snapshot per render | ✅ **opgelost** | `loaded=`-parameter op alle queries |
| Versieherstel laat de plank ongemoeid; queries schrijven niet | ✅ | |

---

## 4. Resterende bevindingen

### B3 (blocker vóór de Demo-UI). Tweede computer met onvolledige sync: automatische migratie maakt alles publiek [test]

**Waar:** `ShelfLibraryStore.load()` (`library_shelves.py`, het pad zonder `library.json` én zonder last-good). Dit is
nog steeds een "sanctioned automatic write" bij de **eerste query**.

**Reproductie** (`shelf130b.py` §3):
1. PC1 heeft "Publiek" en "Geheim", met "Geheim" op een privéplank.
2. PC2 krijgt de werkmap zonder `library.json` en zonder `.cache`. Dat is precies de toestand van een nieuwe laptop
   waarop OneDrive nog bezig is, of waar `.cache` niet meesynchroniseert.
3. Op PC2 één query in Demo-modus.

| Verwacht | Werkelijk |
|---|---|
| geen write; Demo-modus toont niets tot de indeling bekend is | PC2 **schrijft** een `library.json` met één publieke plank. **Demo-modus toont "Geheim".** Het bestand is **nieuwer** dan dat van PC1 en wint dus bij last-writer-wins, waarna de privéplank ook op PC1 verdwijnt. |

De deterministische plank-id helpt hier niet: de inhoud verschilt, want PC1 heeft al een privéplank.

**Minimale fix:**
- Schrijf de migratie **nooit** vanuit een query. Ontbreken zowel `library.json` als last-good, dan geeft `load()` de
  migratie-indeling alleen in het geheugen terug met `source='pending_migration'`:
  - normale modus: alles op de standaardplank;
  - Demo-modus: **fail-closed**, want de bron is niet canonical.
- Schrijf de migratie pas in `_apply_operation`, dus bij de **eerste expliciete plankactie** (het pad bestaat al).

Een upgrade van een gewone 1.2-werkmap blijft zo volledig werken. Het enige verschil is dat Demo-modus pas iets toont
nadat er één keer een plankactie is gedaan, of na een expliciete "Indeling vastleggen"-knop bij het inschakelen van
Demo-modus. Dat laatste is een productkeuze voor de UI.

Test: kopie van een werkmap zonder `library.json` en zonder `.cache`, met queries in beide modi: geen write, en Demo
leeg.

### M4. Herstel-API overschrijft een nieuwer schema [test]

`restore_from_last_good()` en `reset_to_default()` schrijven onvoorwaardelijk. Bij `source='future'` (een nieuwere
1.3-build op een andere computer) vervangt een klik op "Herstellen" of "Opnieuw beginnen" de nieuwere indeling.
Bewezen: het veld `nieuw_in_v2` verdwijnt.

**Fix:** beide methoden weigeren als `library.json` bestaat en een schema heeft dat hoger is dan `SCHEMA_VERSION`. Ze
zijn alleen toegestaan als de canonieke versie ontbreekt of corrupt is.

### M5. Lockfile staat in de gesynchroniseerde werkmap [test]

`lock_path = <werkmap>/.cache/library.json.lock`. De lock is bedoeld voor lokale processen, maar wordt meegesynchroniseerd:
- Een lock die van PC1 binnenkomt (of een crashrest jonger dan 30 seconden) laat elke plankbewerking op PC2 **5 seconden
  wachten en dan falen** met `ShelfLibraryConflictError`.
- Sync-clients maken en verwijderen het bestand bij elke bewerking, wat ruis en mogelijke conflictkopieën geeft.

**Fix:** zet de lock **buiten** de werkmap, in een lokale map die niet synchroniseert:
- `QStandardPaths.AppLocalDataLocation`, of
- `tempfile.gettempdir()`, met een naam als `quietwriter-<sha1(werkmappad)>.lock`.

Voor lokale serialisatie is dat net zo effectief.

### L1. Kleine opmerkingen [inspectie]

- **Stale-lock-race.** Twee wachtende processen die allebei een verouderde lock zien, kunnen elkaars net aangemaakte
  lock verwijderen. Theoretisch; acceptabel. Met M5 (lokale map) en een PID-check wordt het nog kleiner.
- **Migratie buiten de lock.** `_write_initial_if_still_missing` draait buiten `_local_lock`. Na B3 verhuist de
  migratie naar `_apply_operation`, binnen de lock, en lost dit zich vanzelf op.
- **Waarschuwingen zonder consument.** `pop_shelf_metadata_warnings()` wordt nu alleen door het importpad uitgelezen.
  Waarschuwingen van aanmaken, herstel en verwijderen blijven in de lijst staan tot de UI ze ophaalt. Neem dat mee in
  de UI-laag: één centrale melding na elke boekactie.
- **Opnieuw importeren blijft dupliceren.** Een tweede DOCX-import van hetzelfde bestand maakt bewust een tweede boek.
  Dat is bestaand gedrag en hoort niet bij deze laag.

---

## 5. Advies voor de Neo-UI

| Onderdeel | Kan nu? |
|---|---|
| Boekenkast in normale modus: planken, hernoemen, verplaatsen, verwijderen, herstelmeldingen | ✅ ja |
| Demo-modus-UI | ⏸️ **na B3**. M4 meenemen in dezelfde ronde, want de herstelknoppen zitten in dezelfde UI. |
| M5 | kan los, vóór de eerste build voor twee computers |

Bouw in de UI vanaf het begin:
1. **één snapshot per render** (`loaded=`);
2. **één centrale melding** voor `pop_shelf_metadata_warnings()`;
3. herstelacties alleen tonen als `source` `last_good` of `emergency` is, **niet** bij `future`.

---

## 6. Niet getest

- Echte sync-clients (OneDrive of Dropbox), conflictkopieën en vertraagde sync. Gesimuleerd met kopieën, verwijderen
  en vervangen.
- Windows-bestandssemantiek van `O_EXCL`-locks, en `os.replace` op een geopend bestand.
- Processen op **verschillende machines** tegelijk. Daar helpt een lokale lock per definitie niet; de verificatie na
  het schrijven dekt alleen het eigen proces.
- UI.

### Bijlage

`shelf130.py` (dev.1-harnas, ongewijzigd) en `shelf130b.py` (multiprocessing, tweede computer, herstel bij een
toekomstig schema, lock, last-good-modus).

Aanroep: `python3 shelf130b.py <absoluut pad naar uitgepakte zip>` (gebruikt spawn-processen).
