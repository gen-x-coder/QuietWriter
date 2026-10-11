# Spellingscontrole loopt vast (1.3.0): analyse, oorzaak en oplossing

Datum: 9 oktober 2026
Onderzochte builds: 1.3.0-dev.29 (wat de gebruiker heeft) en 1.3.1-dev.2 (met ChatGPT's wijziging)

## 1. Samenvatting

- QuietWriter **crasht niet, maar blijft hangen**. De GUI-thread zit vast in `spylls`, dat suggesties zoekt voor één onbekend woord. Dat kan minuten duren, of praktisch eindeloos.
- Dat gebeurt **alleen als het spellingpaneel suggesties toont**: bij het openen van het paneel, bij *Negeren*/*Alles negeren*/*Toevoegen*, of als je de cursor in een onderstreept woord zet terwijl het paneel open is. Het rode onderstrepen tijdens het typen is snel en heeft hier niets mee te maken.
- Oorzaak: `spylls` (pure-Python Hunspell) heeft **geen tijdslimiet**. Het echte Hunspell (C++) heeft die wel. Met het meegeleverde OpenTaal-woordenboek ontploffen twee dingen:
  1. de **MAP-tabel** (`aáàäâå`, `eéèëê`, …) levert per klinker een aantal varianten op, dus het aantal te proberen woorden groeit exponentieel met het aantal klinkers;
  2. elke variant wordt ook nog als **samenstelling** gecontroleerd, en dat is traag.
- Het meegeleverde woordenboek (OpenTaal 2.20, 2021) is daarbij veel zwaarder dan dat van ONLYOFFICE (OpenTaal 2.00b2, 2010). Daarom zag jij het met ONLYOFFICE niet. Ook ONLYOFFICE loopt vast op de ergste woorden, alleen zeldzamer.
- ChatGPT's wijziging in 1.3.1-dev.2 laat `spell_engine.py` ongewijzigd. Er is alleen een keuzemenu voor het woordenboek bijgekomen, en de standaardkeuze blijft *Meegeleverd*. **Het probleem is daarmee niet opgelost.**
- Mijn patch zet een tijdsbudget van 1 s op het zoeken naar verbeteringen voor een woord. Daarna maakt spylls het af met zijn snelle suggesties op basis van woorddelen. In mijn tests (Linux) duurt elk woord daarna 1 tot 2 s, ook in een echte, offscreen gestarte QuietWriter-GUI.
- Bij jou hangt hij met de patch nog. Mijn belangrijkste vermoeden staat in §6: de kans is groot dat de patch niet geladen wordt. Het testscript laat dat zwart op wit zien.

## 2. Wat ik op de foto's zag

1. **Foto 1**: QuietWriter met de *Meelees-assistent* open. De knop van de spellingscontrole (I✓) in de rechterbalk heeft de focusrand, en midden in het venster staat de **zandloper**. Het venster reageert dus niet meer, maar is niet gesloten. Dat past bij een vastgelopen GUI-thread en niet bij een crash. Waarschijnlijk was dit het moment net na een klik op I✓ (`show_spell` → `refresh` → `show_current` → `suggest`).
2. **Foto 2**: Instellingen → Spelling: *Bron: Meegeleverd nl_NL · met .aff-regels*, met als pad `…\QuietWriter-1.3.0-windows-portable\QuietWriter-1.3.0\_internal\dictionaries\nl_NL.dic`. De gebruiker gebruikt dus het **meegeleverde** OpenTaal-woordenboek en heeft **spylls actief**: "met .aff-regels" betekent dat er een .aff is, dus wordt spylls gebruikt.

## 3. Hoe de spellingscontrole in QuietWriter werkt (relevante delen)

| Waar | Wat | Kosten |
|---|---|---|
| `presentation_highlighter._apply_spelling` | rood onderstrepen; per woord `WordDictionary.known()` → `spylls.lookup()` | snel (milliseconden), ook voor `Aaaaaaaaaaaaaaaaaaaa` |
| `SpellPanel.refresh` | `misspellings()` over het hele hoofdstuk (alleen `known()`) | snel |
| `SpellPanel.show_current` | `WordDictionary.suggest(word)` → `spylls.suggest()` voor het **getoonde** woord | **hier zit het probleem** |

`show_current()` wordt aangeroepen bij: het paneel openen, *Negeren*, *Alles negeren*, *Altijd negeren*, *Toevoegen*, *Wijzigen*, en `follow_editor_cursor()` (cursor in een onderstreept woord terwijl het paneel open is). Alles draait synchroon op de GUI-thread.

## 4. De oorzaak in detail

### 4.1 Hoe spylls suggesties maakt

`Suggest.suggestions(word)` doet in deze volgorde:

1. **Edit-fase zonder samenstellingen**: `edits(word)` levert kandidaten op (REP-vervangingen, twee woorden, **MAP-varianten**, letters wisselen, letter erbij/eraf, TRY-letters …). Elke kandidaat gaat door `lookup.good_forms()`.
2. **Edit-fase mét samenstellingen**: dezelfde kandidaten nog een keer, nu met de dure samenstellingscontrole.
3. **Ngram-fase**: vergelijkt met de woordenlijst. Snel: 0,1 tot 0,3 s.
4. (QuietWriter) als dat niets oplevert: `difflib` over de hele woordenlijst. Kost ongeveer 0,3 s.

### 4.2 Waarom stap 1 en 2 ontploffen

`permutations.mapchars()` probeert voor elke letter uit een MAP-groep alle alternatieven, recursief over het hele woord. Voor `Aaaaaaaaaaaaaaaaaaaa` met `MAP aáàäâå` zijn dat in de orde van 6^20 kandidaten. Die komt nooit tot een einde. Voor gewone lange woorden (`kinderboekenschrijfstr`) is het vooral de samenstellingscontrole per kandidaat die optelt tot minuten.

De Python-stack op het moment van hangen (uit het testscript) laat precies dat zien:

```
suggest.py  suggestions -> edit_suggestions -> filter_suggestions -> is_good_suggestion
lookup.py   good_forms -> affix_forms -> produce_affix_forms -> desuffix -> ...
permutations.py  mapchars_internal -> mapchars_internal -> ...
```

C++-Hunspell heeft hiervoor tijdslimieten in `suggestmgr.cxx`. spylls heeft die niet overgenomen.

### 4.3 Meetresultaten (Linux-container, Python 3.13, spylls 0.1.7)

Ongepatcht (gedrag van 1.3.0), tijd van `suggest()` voor één woord:

| Woord | Meegeleverd (OpenTaal 2.20) | ONLYOFFICE (OpenTaal 2.00b2) |
|---|---|---|
| hooofd | 0,7 s | 0,5 s |
| antwoorrde | 2,4 s | 1,4 s |
| Mariabeeldje | 21 s | – |
| Aurelianus | 34 s | – |
| Valentijnsdagkaart | > 60 s | – |
| kinderboekenschrijfstr | 113 s | 22 s |
| onvoorstelbaarhedenn | 88 s | 52 s |
| Aaaaaaaaaaaaaaaaaaaa | na 7 min nog niet klaar | na 4 min nog niet klaar |

Een gewone fantasienaam (*Aurelianus*) of één lange samenstelling met een typfout is dus al genoeg. Op een gemiddelde Windows-laptop zal het eerder langzamer dan sneller zijn.

### 4.4 Waarom meegeleverd erger is dan ONLYOFFICE

| | Meegeleverd | ONLYOFFICE |
|---|---|---|
| Versie | OpenTaal 2.20.21 (2021), via LibreOffice | OpenTaal 2.00b2 (2010) |
| MAP-groepen | 7, o.a. `aáàäâå` (6) | 5, o.a. `aáà` (3) |
| COMPOUNDRULE | 37 regels | 0 |
| Woorden | ~180.000 | ~150.000 |

Hetzelfde probleem dus, maar met ONLYOFFICE minder vaak en minder lang. Dat verklaart waarom jij het niet kon nabootsen tot je `Aaaaaaaaaaaaaaaaaaaa` probeerde.

Kanttekening: in dev.29 wint *Meegeleverd* (prioriteit 3) van *ONLYOFFICE* (2) als beide aanwezig zijn. Draai je de portable build, dan gebruik je dus het meegeleverde woordenboek, ook als ONLYOFFICE geïnstalleerd is. Controleer in Instellingen → Spelling welke bron er echt staat.

## 5. Wat ChatGPT deed (1.3.1-dev.2)

- `spell_engine.py` is **byte-voor-byte gelijk** aan dev.29.
- Wel nieuw: meerdere woordenboeken per taal, de instelling `spell_dictionary_source` en een keuzemenu in Spelling.
- Standaard (bestaande gebruikers zonder die instelling) sorteert `entries()` op label en dan op prioriteit, met *Meegeleverd* vóór *ONLYOFFICE*. De gebruiker uit de melding krijgt dus nog steeds het meegeleverde woordenboek en loopt op dezelfde manier vast.
- Overschakelen naar ONLYOFFICE is hooguit een omweg: het maakt het zeldzamer, maar lost het niet op (zie tabel), en de gebruiker moet ONLYOFFICE daarvoor geïnstalleerd hebben.

Het keuzemenu is op zich nuttig, maar het is geen oplossing voor deze melding.

## 6. Waarom het bij jou met mijn `spell_engine.py` nog kan hangen

Bij mij werkt de patch in alle drie de lagen: direct via spylls, via `WordDictionary` en in de echte QuietWriter-GUI (offscreen). Mogelijke verklaringen, de meest waarschijnlijke eerst:

1. **Je test de EXE / portable build.** PyInstaller laadt de modules uit zijn eigen archief (PYZ) in de exe, niet uit losse `.py`-bestanden. Een vervangen `spell_engine.py` in `_internal\` doet niets. De patch werkt pas na een nieuwe build met `build_exe.cmd`.
2. **Er wordt een andere kopie geladen.** Bijvoorbeeld een andere map, een andere checkout, of de 1.3.0-map terwijl je de 1.3.1-map hebt aangepast. Het script toont het pad en de hash van de geladen `spell_engine.py`. Mijn versie heeft sha256 `54368c6ae0a1e4f6…` met LF-regeleinden; met CRLF verschilt de hash. Kijk daarom vooral naar `budget_wrapper_active: True`.
3. **Een andere spylls-versie.** De patch vervangt `dictionary.suggester.edits`. Dat bestaat in spylls 0.1.7, de versie uit de lock-file. Het script toont de versie en of de vervanging echt actief is (`budget_wrapper_active`).
4. **Het hangt ergens anders.** Bijvoorbeeld in een codepad dat ik niet ken, of Windows-specifiek. De `--gui`-modus van het script doorloopt de echte UI-stappen en print bij een hang de Python-stack van precies die plek.
5. **Geen hang, maar traag.** Met de patch kost elk getoond woord bij mij 1 tot 2 s. Op een trage machine kan dat 3 tot 5 s worden, en dat voelt bij elke klik op *Negeren* als vastlopen. Het script meet dat per stap.

## 7. Het testscript

Bestanden:

- `tools\spell_diag.py`: het script (alleen stdlib + spylls; PySide6 alleen voor `--gui`)
- `spell_diag.cmd`: dubbelklikken in de QuietWriter-bronmap. Kiest eerst `.venv\Scripts\python.exe`, dan `py`/`python`, en draait `--all-dics --gui`.

Zet beide in de **bronmap** van QuietWriter (de map met `main.py` en `quietwriter\`), niet in de portable EXE-map.

### Gebruik

```
spell_diag.cmd                                  (alles, met GUI-test)
python tools\spell_diag.py                      (standaardwoorden, eerste woordenboek)
python tools\spell_diag.py --all-dics           (elk gevonden nl_NL-woordenboek)
python tools\spell_diag.py --gui                (ook de echte QuietWriter-UI offscreen)
python tools\spell_diag.py --word Aaaaaaaaaaaaaaaaaaaa --word Aurelianus
python tools\spell_diag.py --text hoofdstuk.txt (onbekende woorden uit een eigen tekst)
python tools\spell_diag.py --dic "C:\Program Files\ONLYOFFICE\DesktopEditors\dictionaries\nl_NL\nl_NL.dic"
python tools\spell_diag.py --timeout 60         (seconden per woord voordat het als hang telt; standaard 30)
python tools\spell_diag.py --mode qw --gui      (alleen de engine uit deze map + de GUI-test)
```

### Wat het doet

1. **Omgeving**: Python-versie en -pad, platform, spylls-versie, QuietWriter-versie, pad en hash van de geladen `spell_engine.py`, en of de budgetpatch erin zit. Waarschuwt als de map op een EXE-map lijkt.
2. **Woordenboeken**: dezelfde zoektocht als QuietWriter (`DictionaryCatalog`). Het eerste woordenboek in de lijst is wat QuietWriter standaard kiest. Per woordenboek: pad, grootte, hash, versie, MAP-groepen en het aantal COMPOUNDRULE-regels.
3. Per woordenboek, per modus, per woord: `lookup`-tijd en `suggest`-tijd plus de eerste suggesties:
   - `raw`: spylls zonder aanpassing (gedrag van 1.3.0);
   - `qw`: `quietwriter/spell_engine.py` uit déze map, precies wat het paneel aanroept;
   - `fixed`: spylls met het tijdsbudget uit het script zelf, los van `spell_engine.py`. Als `fixed` snel is en `qw` niet, dan wordt de patch niet geladen.
   - `gui` (met `--gui`): start de echte QuietWriter in een tijdelijke werkmap (je eigen boeken worden niet aangeraakt), typt de woorden, opent het spellingpaneel, klikt *Negeren* door alle woorden, typt met het paneel open en zet de cursor in het langste woord. Elke stap wordt getimed.
   - `difflib`: de terugvaloptie die `spell_engine` gebruikt als spylls niets vindt.
4. Elke meting draait in een **apart proces** met een harde time-out. Bij een hang print het script de **Python-stack van dat moment**, zie je `TIMEOUT … <-- hangs here`, en gaat het verder met het volgende woord.
5. Alles komt ook in `spell_diag_<datum>_<tijd>.log` in de huidige map. **Stuur dat bestand door.**

### Hoe je de uitvoer leest

| Je ziet | Betekenis |
|---|---|
| `raw` TIMEOUT, `fixed` snel, `qw` TIMEOUT, `budget patch: NO` | patch niet geladen: verkeerde map of EXE |
| `qw` snel, maar de app hangt wel | je draait een andere build/EXE dan deze map, of het hangt ergens buiten de spellingscode; dan `--gui` gebruiken |
| `gui` TIMEOUT met stack | precies de plek in QuietWriter waar het hangt: stuur de stack |
| alle tijden 3 tot 6 s | geen hang, maar een trage machine: zie §8, stap 2 |

Voorbeeld van mijn uitvoer (ingekort):

```
budget patch: YES, 1.0 s
Dictionary: Meegeleverd
  version line: # Date and version: 2021-07-03 20:32:13 2.20.21
  MAP groups: ['eéèëê', 'aáàäâå', 'iíìïî', 'oóòöô', 'uúùüû', 'nñ', 'cç']
  [raw]
    Aurelianus                   TIMEOUT  > 15 s  <-- hangs here
  [qw]
      budget_wrapper_active: True
    Aurelianus                   unknown  lookup 0.002 s  suggest   2.10 s  ['aurelius', 'aurelia', ...]
    Aaaaaaaaaaaaaaaaaaaa         unknown  lookup 0.002 s  suggest   1.38 s  []
  [gui]
    spellingpaneel openen                                  0.76 s
    Negeren -> volgende woord                              2.05 s
```

Met de ongepatchte engine geeft de GUI-test bij mij: `Negeren -> volgende woord  TIMEOUT > 20 s <-- hangs here`.

## 8. De oplossing die ik voorstel

### Stap 1: nu (1.3.1-hotfix): tijdsbudget in `spell_engine.py` (zit in de patch)

- `SUGGEST_BUDGET_SECONDS = 1.0`.
- Bij het laden wordt `dictionary.suggester.edits` per instantie vervangen door een wrapper. Die stopt met kandidaten opleveren zodra de deadline voorbij is. Alleen `suggest()` zet die deadline; `known()` merkt er niets van.
- spylls gaat daarna gewoon verder met de ngram-fase. Bij lange woorden blijven de suggesties dus goed (`kinderboekenschrijfstr` → `kinderboekenschrijfster`). Als alles leeg blijft, valt QuietWriter terug op difflib, zoals voorheen.
- Waarom de wrapper op `edits()` zit en niet op `good_forms()`: mijn eerste poging begrensde alleen de controle. Het **genereren** van MAP-varianten is zelf al eindeloos, dus de grens moet bij de bron liggen.
- Regressietest `tests/current/test_spell_suggest_budget_131.py`: een klein synthetisch woordenboek met een MAP-tabel. De test blijft hangen op de oude code en slaagt in een fractie van een seconde op de nieuwe.
- Volledige suite: 808 geslaagd. 3 tests falen, en die falen ook zonder de patch (versie-metadata en een undo-timingtest).

Beperking: de GUI-thread staat per getoond woord nog 1 tot 2 s stil, en op een langzame laptop mogelijk meer.

### Stap 2: daarna (1.4): suggesties buiten de GUI-thread

- Het paneel toont het woord direct, met "Suggesties zoeken…". De suggesties worden berekend in een `QThreadPool`-taak, of in één worker-thread met alleen het laatste verzoek.
- Komt een resultaat binnen voor een woord dat niet meer getoond wordt, dan wordt het weggegooid.
- Het tijdsbudget blijft nodig: een Python-thread kun je niet stoppen, dus zonder budget blijft een eindeloze berekening CPU en de GIL bezet houden.

### Stap 3: optioneel

- Een snellere Hunspell, zoals een C-binding (`cyhunspell`/`hunspell`-wheels). Op Windows met PyInstaller is dat merkbaar meer werk en risico. Pas overwegen als stap 1 en 2 niet genoeg zijn.
- **Niet** aanraden: alleen terug naar een ouder woordenboek. Dat verkleint het probleem maar lost het niet op.

### Uitlevering

- Na de patch **een nieuwe EXE bouwen**. Losse `.py`-bestanden in een portable map doen niets.
- Windows-test: de portable build met *Meegeleverd*, `Aaaaaaaaaaaaaaaaaaaa` en `Aurelianus` typen, het paneel openen en *Negeren* doorklikken. Dat mag geen zandloper van meer dan een paar seconden geven.

## 9. Wat ik niet heb kunnen testen

- **Windows** en de **echte EXE/portable build**: ik draai in Linux. Tijden op een Windows-laptop kunnen hoger liggen.
- De GUI alleen **offscreen** (`QT_QPA_PLATFORM=offscreen`), niet met een echt scherm, muis of DPI-schaal.
- De ONLYOFFICE-test gebruikt het nl_NL-woordenboek uit de GitHub-repo van ONLYOFFICE. Dat kan afwijken van wat jouw geïnstalleerde ONLYOFFICE meelevert.
- Waarom het bij jou met de patch nog hangt, kan ik zonder je uitvoer niet vaststellen. Het testscript is daarvoor bedoeld.
