# QuietWriter 1.3: advies over het gegevensmodel voor boekenplanken

**Reviewer:** Claude · **Datum:** 7 oktober 2026
**Codebasis:** de nieuwste broncode die ik heb is **1.2.31** (`QuietWriter-1.2.31.zip`, SHA-256 `6166c430…`). Voor 1.2.32
heb ik geen zip, dus alle codefeiten hieronder komen uit 1.2.31. Als 1.2.32 iets wijzigt in `storage.py` of
`qwbook_io.py`, kloppen de regelverwijzingen mogelijk niet meer.
**Status:** architectuurreview; er is geen code gewijzigd.

Legenda: **[code]** = vastgesteld in de broncode · **[advies]** = mijn ontwerpkeuze.

---

## 1. Besluit

**Model C: een centrale `book_id → shelf_id`-mapping in één bibliotheekbestand in de werkmap.**

De conclusie van ChatGPT klopt in de richting. De echte code maakt C **sterker** dan het document veronderstelt,
vooral door versieherstel en de inhoud van `.qwbook`-pakketten (§2). Ik voeg vier dingen toe die in de analyse
ontbreken of te licht wegen:

1. **Synchronisatie tussen twee computers.** De werkmap wordt in de praktijk via OneDrive of Dropbox gedeeld, en de
   code is daar overal op ingericht. Een centraal bestand heeft daarom een **revisieguard met operation replay**
   nodig, en QuietWriter mag het **nooit schrijven zonder gebruikersactie**.
2. **Mappings van boeken in de prullenbak** moeten blijven staan. Anders komt een hersteld privéboek op een publieke
   plank terecht.
3. **De standaardplank kan niet privé zijn.**
4. **Demo-modus** moet ook de lekken dichten die in het document ontbreken: de Bewaarplaats-herkomst, de prullenbak,
   kaarten van onleesbare boeken, de zoekindex en het gebruikerswoordenboek.

---

## 2. Codefeiten die het besluit bepalen

| # | Feit | Waar | Gevolg |
|---|---|---|---|
| F1 | Elk boek krijgt bij aanmaken een UUID4 als `id` in `book.json`. De mapnaam is `slug-<eerste 8 tekens>`, maar de **identiteit is `id`**, niet het pad. | `storage.create_book` (`:326`) | ✅ Er is een stabiele `book_id`. Hernoemen van de titel of de map verandert hem niet. |
| F2 | De boekenplank vindt boeken door `books/*/book.json` te scannen (verborgen mappen worden overgeslagen). Boeken die niet laden komen in `last_list_errors`. | `Library.list_books` | Er bestaat geen centrale boekindex. Een C-mapping is de eerste werkmap-brede relatie; kaarten van onleesbare boeken hebben geen betrouwbare `id`. |
| F3 | **QWBOOK-import behoudt de `book_id`** en **weigert** als dezelfde id al leeft of in de prullenbak staat (`QwBookConflictError`). Een "importeer als kopie" bestaat niet. | `qwbook_io.import_qwbook` (`:334–371`) | ✅ De id is uniek binnen een werkmap. Een herimport na definitief verwijderen krijgt dezelfde id terug. |
| F4 | **Versieherstel zet de volledige `metadata` en `extra_manifest` uit de snapshot terug** (alleen `last_used` wordt vernieuwd). | `_apply_snapshot_to_live` (`:980–983`), `restore_version` | ❌ **Bij Model A** verplaatst het herstellen van een oude versie het boek stil terug naar de plank van toen, mogelijk van een privé- naar een publieke plank. Dat is een privacyfout die alleen ontstaat als de relatie in het boek zit. |
| F5 | Een `.qwbook` bevat `book.json` **en** de geschiedenis met **historische `book.json`-kopieën**. `_sanitize_book_json` verwijdert alleen `source_file`. | `qwbook_io` (`:86–113`) | ❌ **Bij Model A** zou je `shelf_id` in de actuele én in alle historische `book.json`'s moeten filteren, bij export én bij import. Dat is precies het permanente onderscheid "intern versus exporteerbaar" waar het document voor waarschuwt. |
| F6 | Elke wijziging aan `book.json` loopt via de revisieguard (`verify_book_unchanged`). Een wijziging op een andere computer wordt dan een conflict met dialogen en herstelversies. | `storage.py`, `editor_page` | ❌ **Bij Model A** zou een boek verplaatsen een conflict kunnen geven met een open editor op een andere computer. Bij C raakt organisatie het boek nooit. |
| F7 | `book.json` bevat nu al lokale bibliotheekmetadata: `metadata.last_used`, geschreven bij elk openen (`touch_book`) en meegenomen in exports. | `touch_book`, `create_book` | Dat is het bestaande precedent van Model A. Een reden om het **niet** uit te breiden: `last_used` toont al hoe lokale ordening meereist en revisies aanraakt. |
| F8 | Werkmap-brede bestanden bestaan al en gebruiken patronen die je kunt hergebruiken: `persona/schrijver.md` met `expected_revision` en `file_revision`, en `fragments/` met één bestand per item om synchronisatieconflicten te beperken. | `save_persona` (`:1655`), `fragment_store.py` | ✅ Er is een bewezen patroon voor een centraal bestand met revisieguard. |
| F9 | Er is een algemeen hulpmiddel voor drieweg-merges. | `field_merge.merge_scalar_fields` | Bruikbaar, maar voor dit bestand is operation replay eenvoudiger (§5.4). |
| F10 | Prullenbak: een verwijderd boek wordt naar `trash/` verplaatst met **dezelfde id**. Herstel controleert op dubbele ids. | `delete_book`/`restore_trashed_book` (`:1210, :1234`) | Mapping-sleutels moeten de prullenbak overleven (§5.2). |
| F11 | Instellingen staan per computer in `QSettings`. De werkmap zelf wordt gesynchroniseerd. | `startup.py`, `workspace_path.py` | Plankindeling hoort in de **werkmap** (reist mee). De **Demo-modus**-vlag hoort in **QSettings**, per computer: demo op de laptop raakt de desktop niet. |

**Conclusie uit de code:** F4 en F5 maken Model A niet alleen minder zuiver, maar **onveilig voor privacy zonder
extra speciale gevallen**. F1 en F3 maken Model C direct haalbaar. Er is geen voorwerk aan de boekidentiteit nodig.

---

## 3. Vergelijking, aangescherpt met de codefeiten

| Onderwerp | A: `shelf_id` in boek | B: `book_ids` per plank | **C: centrale mapping** |
|---|---|---|---|
| Precies één plank | sterk | zwak (invariant over lijsten) | **sterk (dict-sleutel)** |
| Verplaatsen | één boekwrite, **maar met revisieguard en conflictrisico (F6)** | twee lijsten | **één sleutel** |
| Versieherstel | ❌ **verplaatst het boek terug (F4)** | ✅ ongemoeid | ✅ ongemoeid |
| `.qwbook`-export | ❌ filteren in actuele en historische `book.json` (F5) | ✅ schoon | ✅ schoon |
| Import | beleid nodig voor een vreemde shelf-id | standaardplank | **standaardplank** |
| Migratie 1.2 → 1.3 | **schrijft elke `book.json`** (revisies, synchronisatie) | één bestand | **één bestand** |
| Plank verwijderen | N boekwrites, niet atomair | één bestand | **één bestand, atomair** |
| Corruptie van centrale data | indeling overleeft | indeling weg | indeling weg, **opgevangen door een last-good-kopie (§5.5)** |
| Synchronisatie tussen twee computers | conflicten per boek, zwaar | één bestand | één bestand, **klein, met replay (§5.4)** |
| Scheiding boek en bibliotheek | ❌ | ✅ | ✅ |
| Testbaarheid | redelijk | veel randgevallen | **goed** |

**Het enige echte argument voor A** (de indeling overleeft beschadiging van het centrale bestand) los ik in C op met
een **last-good-kopie**. Dat is één extra bestand, veel minder complexiteit dan F4, F5 en F6 bij A.

**B** heeft geen voordeel boven C.

---

## 4. Antwoord op de tien vragen

**1. Argumenten vóór C:**
- Organisatie is bibliotheekmetadata, geen boekinhoud.
- `.qwbook` blijft ongewijzigd en schoon (F5).
- Versieherstel kan een boek niet verplaatsen (F4).
- Verplaatsen raakt nooit een boekrevisie (F6).
- Exact één plank volgt uit de datastructuur.
- Migratie is één write.
- Plankoperaties zijn atomair.
- Privacy is volledig afleidbaar op plankniveau.

**2. Argumenten tegen C:**
- Eén centraal bestand is een single point of failure en een synchronisatiehotspot.
- Er ontstaan verweesde sleutels als boeken buiten QuietWriter om verdwijnen.
- Boeken die via synchronisatie binnenkomen kunnen tijdelijk zonder mapping zijn.

**3. Belangrijkste risico:** een **synchronisatieconflict** tussen twee computers, waarbij de laatste schrijver een
verplaatsing of privacystatus van de andere computer overschrijft. Of een gegenereerde automatische toewijzing die
een privétoewijzing van de andere computer overschrijft.

Mitigatie (§5.4):
- Nooit schrijven zonder gebruikersactie.
- Een revisieguard met replay van de enkele bewerking op de verse schijfversie.
- Ontbrekende mappings alleen in het geheugen oplossen.

**4. Export en import van `.qwbook`:**
- **Export:** ongewijzigd. Er gaat geen plankinformatie mee. `last_used` gaat al mee (F7); dat is los van dit besluit
  en optioneel te strippen.
- **Import:** de id blijft behouden (F3).
  - Bestaat er nog een mapping-sleutel voor die id (bijvoorbeeld na definitief verwijderen en herimport): plaats het
    boek **op die plank als die nog bestaat**.
  - Anders: zet het op `default_shelf_id`, met een write (de import is een gebruikersactie).
  - Een import neemt nooit een privéstatus over uit het pakket. Die staat er ook niet in.

**5. Bij corrupte metadata:** zie §5.5. Kort samengevat:
- Normale modus: het bestand nooit overschrijven; laden uit de last-good-kopie of een veilige noodindeling in het
  geheugen, met een melding.
- Demo-modus: **geen boeken tonen** zolang de indeling niet geldig is (fail-closed).

**6. Migratie vanaf 1.2.32:** bij de eerste start van 1.3, **alleen als `library.json` ontbreekt**:
1. maak de standaardplank "Werk in uitvoering";
2. map alle `book_id`'s die `list_books()` geldig laadt naar die plank;
3. schrijf één keer, atomair.

Dit is idempotent: bestaat het bestand al, dan wordt er niets geschreven. Er wordt geen enkel boekbestand aangeraakt.
Boeken in de prullenbak krijgen ook een sleutel naar de standaardplank, zodat herstel voorspelbaar is.

**7. Dataschema:** §5.1.

**8. Minimale codecomponenten:** §6.

**9. Minimale tests:** §7.

**10. Blockers vóór `1.3.0-dev.1`:** §8.

---

## 5. Implementatievoorstel

### 5.1 Opslag: `<werkmap>/library.json`

```json
{
  "schema_version": 1,
  "default_shelf_id": "9f1c…",
  "shelves": [
    {"id": "9f1c…", "name": "Werk in uitvoering", "private": false},
    {"id": "4b7a…", "name": "Privé",              "private": true}
  ],
  "book_shelves": {
    "e3a1…-book-uuid": "9f1c…",
    "77d0…-book-uuid": "4b7a…"
  }
}
```

- De **volgorde van de planken** is de volgorde in de lijst. Een apart `order`-veld kan dan niet tegenstrijdig zijn.
- **Geen volgorde van boeken per plank** in versie 1. De boeken sorteren zoals de huidige boekenplank: laatst gebruikt,
  titel of woorden. Handmatige volgorde is bloat tot er echt vraag naar is.
- **Last-good-kopie:** `<werkmap>/.cache/library.last-good.json`, geschreven na elke geslaagde, gevalideerde save.
  `.cache` is al gedefinieerd als afgeleide data (F2). Het is een vangnet, geen bron van waarheid.
- Een onbekend `schema_version` hoger dan 1 betekent: alleen lezen, geen plankbewerkingen, en Demo-modus
  fail-closed. Hetzelfde patroon als `manuscript_syntax`.
- **Niet** in QSettings: de indeling moet met de werkmap meereizen (F11).
- **Demo-modus** staat **wel** in QSettings, per computer, en wordt bij het opstarten **niet** automatisch hersteld
  zonder bewuste keuze. Optioneel: Demo-modus aan houden tot hij expliciet uit wordt gezet.

### 5.2 Invarianten

1. Plank-id's zijn UUID's, uniek en onveranderlijk. De naam is alleen presentatie.
2. `default_shelf_id` wijst naar een bestaande plank die **niet privé** is. De standaardplank kan niet privé worden
   gemaakt en niet worden verwijderd.
3. `book_shelves` wijst elke sleutel naar precies één waarde. Een waarde moet een bestaande plank zijn, anders telt de
   mapping als ongeldig.
4. **QuietWriter schrijft `library.json` alleen bij een gebruikersactie:**
   - aanmaken, hernoemen, verwijderen en privé maken van een plank;
   - een boek verplaatsen;
   - een boek aanmaken, importeren of herstellen;
   - een boek definitief verwijderen;
   - de eenmalige migratie.

   Een boek weergeven, de boekenkast openen of iets automatisch herstellen leidt **nooit** tot een write.
5. Een boek in de prullenbak **houdt** zijn sleutel. Herstel uit de prullenbak brengt het terug op zijn plank (privé
   blijft privé). Pas bij definitief verwijderen verdwijnt de sleutel.
6. Een plank verwijderen verplaatst al zijn sleutels (ook die van boeken in de prullenbak) in dezelfde write naar
   `default_shelf_id`. Er worden nooit boeken verwijderd.
7. Er is precies één canonieke relatiebron. `shelf → boeken` wordt alleen in het geheugen afgeleid.

### 5.3 Zichtbaarheid: één centrale functie

Maak `library_view(library, store, demo_mode)` met de uitvoer `visible_shelves`, `visible_book_ids`,
`unassigned_book_ids` en `problems`.

| Situatie | Normale modus | **Demo-modus** |
|---|---|---|
| Geldige mapping naar een publieke plank | tonen | tonen |
| Geldige mapping naar een privéplank | tonen, met een subtiel slot | **plank en boek volledig afwezig** |
| Boek zonder mapping (bijvoorbeeld net binnengekomen via synchronisatie of door 1.2 gemaakt) | in het geheugen op de standaardplank, zonder write | **verborgen** |
| Mapping naar een onbekende plank-id | in het geheugen op de standaardplank, met melding | **verborgen** |
| Onleesbaar boek (`last_list_errors`) | foutkaart zoals nu | **verborgen** (id onbetrouwbaar) |
| `library.json` corrupt, onleesbaar of uit de toekomst | noodindeling (§5.5) | **geen enkel boek** en de melding "Demo-modus niet beschikbaar" |

**Elke** UI die boeken noemt gebruikt alleen `visible_book_ids`:
- boekenkast, aantallen en de zoekbalk op de boekenplank;
- de zoekindex (`search.py`): bouw voor verborgen boeken in Demo-modus niets op, of filter de resultaten op id;
- recente boeken, het venster- en recent-menu;
- de **Bewaarplaats**: fragmenten met een `source_book_id` van een verborgen boek verbergen, of in elk geval
  herkomsttitel en hoofdstuk weglaten;
- de **prullenbak** (verwijderde privéboeken en hoofdstukken);
- exportdialogen, de "Over"-statistiek en AI-gesprekken (per boek, dus vanzelf);
- **het gebruikerswoordenboek** kan privénamen bevatten. In Demo-modus de woordenboekpagina niet tonen. Dat is
  presentatieprivacy, dus geen filter op de spellingscontrole zelf nodig.

**Overgang naar Demo-modus terwijl een privéboek open is:** eerst opslaan, dan sluiten en naar de boekenkast.
**Covers:** laat thumbnails niet vooraf in cache laden voor verborgen boeken.

### 5.4 Schrijven en synchronisatie (het belangrijkste dat in de analyse ontbreekt)

- Elke bewerking is een **kleine, herhaalbare operatie**: `move(book, shelf)`, `rename(shelf, naam)`,
  `create(shelf)`, `delete(shelf)`, `set_private(shelf, bool)`, `assign_new(book)` en `forget(book)`.
- Een save gebeurt zo:
  1. lees de schijfversie met `file_revision`;
  2. pas de operatie toe op die **verse** versie;
  3. valideer de invarianten;
  4. schrijf atomair met `expected_revision`;
  5. bij een revisieconflict: **opnieuw lezen en de operatie opnieuw toepassen** (maximaal drie keer).

  Een drieweg-merge is daarvoor niet nodig. Elke operatie is idempotent of commutatief genoeg.
- Bij een **conflictkopie van de sync-client** (bijvoorbeeld `library-DESKTOP.json`): die negeren en in de normale
  modus één keer een melding tonen. Nooit automatisch samenvoegen.
- Dankzij invariant 4 overschrijft de ene computer nooit een privétoewijzing van de andere met een automatisch
  gegenereerde toewijzing.

### 5.5 Ontbrekende of corrupte metadata

| Geval | Normale modus | Demo |
|---|---|---|
| `library.json` ontbreekt én er bestaan boeken | eenmalige migratie (§4.6) | pas na de migratie |
| Ongeldige JSON of schema | **niet overschrijven.** Laad `.cache/library.last-good.json` als die geldig is; anders een noodindeling (één standaardplank in het geheugen, alles erop). Toon een melding met "Indeling herstellen" (uit last-good) of "Opnieuw beginnen", allebei expliciet. Plankbewerkingen zijn geblokkeerd tot er een keuze is. | fail-closed: geen boeken |
| `default_shelf_id` ongeldig | in het geheugen: eerste publieke plank, anders een noodplank. Gerepareerd bij de volgende gebruikersactie. | ongewijzigd voor geldige mappings |
| Dubbele plank-id | het bestand is ongeldig, dus hetzelfde pad als bij corrupte JSON | fail-closed |
| Sleutel van een boek dat niet bestaat (niet levend, niet in de prullenbak) | laten staan. Opruimen alleen bij een expliciete "Indeling opschonen" in Integriteit & herstel. | n.v.t. |
| Herstel | raakt **nooit** boekbestanden | – |

### 5.6 Boekidentiteit (F1/F3): geen wijziging nodig

- De id is stabiel.
- QWBOOK-import weigert dubbele ids.
- Er bestaat geen functie om een boek te dupliceren. **Als** die er later komt, moet die een nieuwe UUID geven, en de
  kopie komt dan op de plank van het origineel (gebruikersactie, write).
- Een externe of originele id hoeft niet apart bewaard te worden.

---

## 6. Minimale codecomponenten

| Component | Wijziging |
|---|---|
| **Nieuw:** `quietwriter/library_shelves.py` | Een pure `ShelfLibrary`-dataclass, laden en valideren, de operaties uit §5.4, atomair schrijven met `expected_revision`, last-good-kopie, migratie en `library_view()`. Geen Qt. |
| `storage.Library` | Een accessor `self.shelves` (lazy). `create_book`, `import_docx_book`, `import_markdown_book` en `restore_trashed_book` roepen ná een geslaagde publicatie `assign_new` of herstel aan. Definitief verwijderen roept `forget` aan. **Geen** wijziging aan `book.json`. |
| `qwbook_io.import_qwbook` | Na een geslaagde import `assign_new(book_id)`, waarbij een bestaande sleutel voorrang krijgt. Export blijft ongewijzigd. |
| `ui/bookshelf.py` | Planken renderen vanuit `library_view`; inline hernoemen; verplaatsen via het contextmenu; het slot-icoon. |
| `ui/main_window.py` en `settings_page.py` | Demo-modus-schakelaar (QSettings); bij inschakelen een open privéboek opslaan en sluiten; recente boeken via `visible_book_ids`. |
| `search.py` en de zoekbalk op de boekenplank | Filteren op `visible_book_ids`. |
| `darlings_page.py`, `trash_page.py`, woordenboekpagina | Filters uit §5.3. |
| `integrity.py` / `integrity_page.py` | Problemen tonen (ongeldige mappings, verweesde sleutels, corrupt bestand) met expliciete herstelacties. |

Geschatte omvang: één nieuwe module van ±250 regels, de rest zijn kleine aanpassingen. Er hoeft geen bestaand formaat
te veranderen.

---

## 7. Minimale tests (aanvulling op de lijst in §21)

Jullie lijst is goed. Voeg toe:

**Code-specifiek**
- **Versieherstel van een boek verandert de plank niet** (regressie op F4).
- Het `.qwbook`, inclusief de geschiedenis, bevat geen `library.json`-gegevens. Na import in een lege werkmap staat
  het boek op de standaardplank.
- QWBOOK-herimport van een definitief verwijderd boek: een bestaande sleutel wint, en een verwijderde plank leidt naar
  de standaardplank.
- Prullenbak: verwijder een privéboek en herstel het. Het staat weer privé, en is tussendoor in Demo-modus nergens
  zichtbaar, ook niet in de prullenbak.

**Synchronisatie**
- Twee "computers" (twee `ShelfLibrary`-instanties op hetzelfde bestand): A verplaatst X naar privé, B hernoemt een
  plank. Beide operaties overleven (replay).
- Een boek dat via synchronisatie binnenkomt zonder mapping: verborgen in Demo-modus, op de standaardplank in de
  normale modus, en **geen write** bij het weergeven.
- Een conflictkopie `library-PC.json` naast `library.json`: wordt genegeerd, met één melding.

**Invarianten en corruptie**
- De standaardplank kan niet privé worden gemaakt of verwijderd.
- `schema_version` 2: alleen lezen, en Demo-modus fail-closed.
- Corrupte JSON: herstel uit last-good. Zonder last-good: een noodindeling zonder write. Boekbestanden byte-identiek.

**Demo-lekken** (één test die een privéboek met een unieke titel aanmaakt en alle oppervlakken controleert)
- boekenkast, aantallen, zoeken (boekenplank en zoekindex), recent-menu, Bewaarplaats-herkomst, prullenbak,
  foutkaarten, tooltips, venstertitel.
- Overschakelen naar Demo-modus terwijl een privéboek open is.

**Migratie**
- 1.2-werkmap met boeken in de prullenbak: alle sleutels naar de standaardplank, één write.
- Tweede start: geen write (vergelijk de mtime).
- 1.2.32 opent een 1.3-werkmap: negeert `library.json`, en nieuwe boeken uit 1.2 verschijnen in 1.3 op de
  standaardplank (normale modus) en zijn verborgen in Demo-modus.

---

## 8. Blockers vóór `1.3.0-dev.1`

Geen blockers in de bestaande code: de boekidentiteit (F1/F3) is in orde. Er zijn vier **besluiten** die vóór de
eerste build vast moeten liggen, omdat ze het bestandsformaat bepalen:

1. **De locatie `library.json` in de werkmap** (meesynchroniseren) en de Demo-vlag in QSettings (per computer).
   Bevestig dit productmatig.
2. **Invariant 4 (geen write zonder gebruikersactie)** en **replay bij revisieconflict.** Bouw dit in de eerste versie
   van de store. Achteraf toevoegen leidt tot synchronisatiebugs die al op schijf staan.
3. **Mappings van boeken in de prullenbak blijven staan** (invariant 5). Anders is het eerste herstel van een privéboek
   een privacylek.
4. **De standaardplank is niet privé.**

En één processpunt, op basis van de 1.2.30/1.2.31-ervaring: **draai de suite met PySide6.** Demo-modus is vooral
UI-gedrag. Zonder Qt-tests is juist dat ongetest.

---

### Kanttekening

Ik heb geen code geschreven of gedraaid voor dit advies, behalve het lezen van de broncode van 1.2.31.
