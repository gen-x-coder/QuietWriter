# QuietWriter 1.3.0-dev.1: review van het plankfundament

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.1.zip`, SHA-256 `519b9944…3ec685f`, `__version__ = "1.3.0-dev.1"`
**Scope:** `library_shelves.py`, de integratie met aanmaken, import, prullenbak en QWBOOK, synchronisatie, migratie en
de nieuwe tests. Er is geen code gewijzigd.

Legenda: **[test]** = gereproduceerd (`shelf130.py`) · **[inspectie]** = code gelezen.

---

## 1. Conclusie

**Niet bouwen op deze laag voordat B1 en B2 zijn opgelost.** Het model zelf is goed uitgevoerd. Het volgt het advies
(centrale mapping, een standaardplank die niet privé kan, prullenbak behoudt de mapping, replay, last-good-kopie,
Demo-modus fail-closed bij een niet-canonieke bron) en de suite is groen.

Twee fouten raken precies de beloftes waar de UI op gaat leunen:
- **privacy in Demo-modus**: B1;
- **boekoperaties die nooit falen door plankmetadata**: B2.

Beide zijn lokaal op te lossen, in naar schatting een paar uur werk inclusief tests.

---

## 2. Controles

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 (Linux, Python 3.13, PySide6 6.11.2) | ✅ **729 geslaagd**, 0 gefaald, 0 overgeslagen, 304 subtests |
| `--smoke-test` | ✅ rc 0 |
| undefined-names | ✅ |
| locales | ✅ 1527 sleutels |
| pyflakes | dezelfde 6 cosmetische meldingen als in 1.2.31 |

---

## 3. Blockers

### B1. Ontbrekende `library.json` leidt tot een stille hermigratie, met privacylek en verlies van de last-good-kopie [test]

**Waar:** `ShelfLibraryStore.load()` (`library_shelves.py:84–90`) en `_apply_operation` (`:286–287`). Als `library.json`
ontbreekt, volgt **altijd** een nieuwe migratie: een nieuwe willekeurige standaardplank, alle boeken erop, en daarna
`_write_state` die **ook de last-good-kopie overschrijft**.

**Reproductie:**
1. Maak de boeken "Publiek" en "Geheim" aan, en zet "Geheim" op een privéplank.
2. Verwijder `library.json`. Dat doen sync-clients bij conflictafhandeling, en het gebeurt ook bij handmatig opruimen.
3. Roep één query aan: `visible_book_ids(…, demo_mode=True)`.

| Verwacht | Werkelijk |
|---|---|
| "Geheim" blijft verborgen; herstel uit last-good | **Demo-modus toont "Geheim"**. De privéplank is weg, de standaardplank-id is nieuw, en de last-good bevat de privéplank niet meer. |

Demo-modus is fail-closed voor een *corrupte* bron, maar een hermigratie levert een **geldige canonieke** bron op die
alles publiek maakt. Dat is precies het scenario waartegen fail-closed moest beschermen.

**Minimale fix:**
- Migreer alleen als **zowel** `library.json` **als** `.cache/library.last-good.json` ontbreken.
- Ontbreekt alleen de canonieke versie: `load()` geeft `source='last_good'` terug (Demo-modus fail-closed, normale
  modus toont die indeling), en schrijf **niets**. Herstel gebeurt via een expliciete actie (§5).
- Schrijf de last-good-kopie nooit vanuit de migratie.

### B2. Boekoperaties falen ná het vastleggen als de plankmetadata faalt: duplicaten bij import [test]

**Waar:** de aanroepen zitten **na** de echte operatie, en de fouten komen terug bij de aanroeper:
- `create_book` (`storage.py:370`);
- `restore_trashed_book` (`:1257`);
- `permanently_delete_trashed_book` (`:1272`);
- `empty_trash` (`:1291`);
- `_import_neutral_document` voor DOCX en Markdown (`:1466`, **binnen** de `try`);
- `import_qwbook` (`qwbook_io.py:437`, binnen de `try`).

| Toestand van `library.json` | Gevolg |
|---|---|
| corrupte JSON | `create_book` geeft `ShelfLibraryCorruptError`, **maar het boek bestaat** |
| schema 2 (nieuwere 1.3-build op de andere computer) | `ShelfLibraryFutureVersionError`, boek bestaat |
| één handmatige verwijzing naar een onbekende plank | heel bestand "corrupt", dus hetzelfde |
| `PermissionError` bij het schrijven (OneDrive-lock) | `create_book` faalt, boek bestaat, geen mapping |
| corrupt, plus **DOCX-import twee keer** proberen | de gebruiker ziet twee keer een fout en heeft **twee boeken "imp"** (elke DOCX-import maakt een nieuwe id) |
| corrupt, plus **QWBOOK-import twee keer** proberen | eerste poging: fout, maar het boek is geïmporteerd. Tweede poging: `QwBookConflictError: bestaat al` |

**Minimale fix:**
- Plankmetadata is altijd *best effort na* een geslaagde boekoperatie. Vang `ShelfLibraryError` en `OSError` rond
  `assign_new`, `forget` en `forget_many` af.
- Geef het resultaat terug als niet-blokkerende melding ("Boek aangemaakt; plankindeling kon niet worden bijgewerkt").
- Laat de import **slagen**.

Dat is veilig dankzij het eigen ontwerp: een boek zonder mapping staat in de normale modus op de standaardplank en is
verborgen in Demo-modus. Een vergeten `forget` laat alleen een onschuldige verweesde sleutel achter.

---

## 4. High / Medium

### H1. De replay is niet atomair: gelijktijdige schrijvers verliezen stil operaties [test]

**Waar:** `_apply_operation` (`:290–298`) en `_write_state` (`:303–307`). Eerst `file_revision(path) == revision`,
daarna pas schrijven: dat is check-then-act zonder lock. `_write_state` controleert opnieuw, maar ook niet atomair.

**Reproductie:** twee `ShelfLibraryStore`-instanties in twee threads, elk 40 keer `create_shelf`. Resultaat: **48 van
de 80 aangemaakt, 0 foutmeldingen, 32 stil verloren.** De bestaande test
`test_two_store_instances_replay_operations_on_latest_disk_state` test alleen *opeenvolgende* operaties.

Realistisch risico: twee QuietWriter-vensters of -processen op dezelfde werkmap, of een sync-client die het bestand
vervangt tijdens het schrijven. Klein venster, maar de garantie in de docstring klopt niet.

**Fix:**
1. Een lokale lockfile (`library.json.lock`, aangemaakt met `O_CREAT|O_EXCL`, met stale-timeout) rond lezen, muteren
   en schrijven. Dat lost de lokale meervoudige processen volledig op.
2. Na het schrijven opnieuw lezen en vergelijken met de kandidaat; bij een verschil `retry`. Dat dekt de sync-client
   grotendeels.
3. Vang de `ShelfLibraryConflictError` uit `_write_state` ook in de retry-lus (nu ontsnapt die direct).

### H2. Onafhankelijke migraties op twee computers botsen gegarandeerd [test]

`_initial_state` maakt de standaardplank aan met `uuid.uuid4()`. Twee computers die dezelfde (net gesynchroniseerde)
werkmap migreren, schrijven verschillende bestanden (`b4e1e8ca…` tegenover `783b0b79…`). De sync-client maakt dan een
conflictkopie, en een van de twee indelingen "wint" willekeurig.

**Fix:** een **deterministische** id voor de eerste standaardplank, bijvoorbeeld
`uuid5(NAMESPACE, 'quietwriter-default-shelf')`. Bij dezelfde boekenset zijn beide migraties dan byte-identiek
(`book_shelves` wordt al gesorteerd weggeschreven), en is er geen conflict.

### M1. Queries gooien een exceptie bij een nieuwere schemaversie [test]

`visible_book_ids` en `visible_shelf_ids` (demo) laten `ShelfLibraryFutureVersionError` door. Elke UI-aanroeper moet
dat zelf afvangen om fail-closed te blijven. Zo ontstaan verspreide privacyregels in de UI.

**Fix:** laat `load()` voor queries een resultaat met `source='future'` teruggeven. Demo-modus geeft dan leeg terug,
de normale modus de noodindeling met een melding en alleen-lezen.

### M2. Een corrupte bron blokkeert alle plankbewerkingen, zonder herstel-API [test]

Bij een corrupte canonieke bron (inclusief één verwijzing naar een onbekende plank) faalt elke `move`, `rename` en
`create` met `ShelfLibraryCorruptError`. Er bestaat geen methode om dat expliciet op te lossen. De UI heeft vóór
dev.2 minimaal nodig:
- `restore_from_last_good()`;
- `reset_to_default(book_ids)`: een expliciete noodindeling;
- `describe_problem()`.

Overweeg daarnaast een verwijzing naar een onbekende plank **niet** als corruptie van het hele bestand te behandelen.
`visible_book_ids` en `effective_shelf_id` vangen een ongeldige mapping al correct af (standaardplank in de normale
modus, verborgen in Demo-modus). Afkeuren hoeft alleen bij writes.

### M3. Elke query leest, hasht en valideert het bestand opnieuw [inspectie]

`effective_shelf_id`, `visible_*` en `state` roepen allemaal `load()` aan. Een UI die per boek `effective_shelf_id`
vraagt, doet dat N keer per render. Met honderden boeken is dat functioneel prima, maar het geeft per render
**verschillende snapshots** als het bestand tussendoor verandert. Er is dan geen consistent beeld meer: in Demo-modus
zou een plank zichtbaar kunnen zijn terwijl zijn boeken nog volgens een oudere versie worden gefilterd.

**Fix:** één `snapshot = store.load()` per render, met pure functies op die snapshot (`visible_*(snapshot, demo)`).

---

## 5. Wat goed is [test]

- Versieherstel laat de plank ongemoeid (regressie van F4 uit het advies).
- Gewone queries schrijven niets zodra `library.json` bestaat.
- De prullenbak behoudt de privémapping; definitief verwijderen en de prullenbak legen ruimen op.
- QWBOOK-export bevat geen `library.json`; import plaatst het boek op de lokale standaardplank (eigen tests).
- Opeenvolgende replay tussen twee instanties werkt.
- Een corrupte canonieke bron valt in de normale modus terug op last-good, in Demo-modus fail-closed. Zonder last-good
  wordt de bron niet overschreven.
- De migratie bij aanwezige boeken raakt `book.json` niet aan (eigen test).
- Markdown-import loopt via dezelfde `_import_neutral_document` en wordt dus ook gekoppeld.

---

## 6. Ontbrekende tests (toevoegen bij de fixes)

1. B1: `library.json` weg, last-good aanwezig. Privéboek blijft verborgen in Demo-modus, geen write, last-good
   onaangeroerd.
2. B2: voor elke boekoperatie (aanmaken, DOCX-, Markdown- en QWBOOK-import, herstel uit en definitief verwijderen uit
   de prullenbak, prullenbak legen) × elke metadatatoestand (corrupt, toekomstig schema, `PermissionError`):
   de boekoperatie slaagt, één melding, geen duplicaat bij een tweede poging.
3. H1: twee **processen** (`multiprocessing`) met elk 50 operaties. Alle operaties aanwezig, of een expliciete fout.
   Nooit stil verlies.
4. H2: twee onafhankelijke migraties van dezelfde werkmap zijn byte-identiek.
5. M1: queries bij schema 2: demo leeg, normale modus noodindeling, geen exceptie.
6. M3: consistent snapshotgedrag (één `load` per render).

---

## 7. Niet getest

- Echte sync-clients (OneDrive of Dropbox) en echte conflictkopieën. Gesimuleerd met het verwijderen of vervangen van
  het bestand en met threads.
- Meerdere **processen** (alleen threads; dezelfde TOCTOU, maar lokale bestandslocks gedragen zich per OS anders).
- Windows-bestandsgedrag (`os.replace` op een geopend bestand en dergelijke).
- UI. Die is er nog niet, en de Demo-UI volgt in dev.2.

### Bijlage

`shelf130.py`: 5 scenariogroepen. Aanroep: `python3 -I shelf130.py <pad-naar-uitgepakte-zip>`.
