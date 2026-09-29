# QuietWriter 0.28.1 — tussentijds rapport

## Aanleiding
0.28.0 doorstond de transactietests (read-only audit, checkpoint, tweede revision guard en normale atomic write), maar Claude vond zes correctness-gaten in future-format bescherming, herstelbronselectie, History-volgorde, gedeelde validatie, byte-exact herstel en duplicate-detectie.

## Keuzes en waarom
1. **Future-format bescherming zit nu in `load_book`, niet alleen in audit/migratie.** Dit is de laatste veilige plek vóór een toekomstig format 3 bestaat. Een oude QuietWriter mag een nieuw boek nooit kunnen openen en vervolgens downgraden.
2. **Onbekende top-level velden blijven onderdeel van het in-memory Book.** Ze worden niet geïnterpreteerd, maar wel lossless teruggeschreven. Zo vernietigt een normale save geen metadata van een andere/nieuwere component.
3. **Audit en loader delen structurele validatie.** De audit mag nooit `ok=True` geven voor een manifest dat de loader vervolgens met `KeyError` afwijst.
4. **Herstel valideert semantisch, niet alleen op leesbaarheid.** JSON moet het verwachte objecttype hebben; media moet de live verwachte SHA-256 hebben; tekst moet UTF-8 zijn. `pre_integrity_repair` is expres geen bron omdat die snapshot juist de beschadigde toestand bewaart.
5. **Herstel is byte-exact.** History is een snapshot; herstel hoort dus geen CRLF/LF-normalisatie of andere teksttransformatie te doen.
6. **History krijgt een stabiele tie-breaker.** `created_at` blijft menselijk op seconden, de microseconde-version-id bepaalt de technische volgorde binnen dezelfde seconde.
7. **Duplicate-detectie is platform-conservatief.** Paden worden genormaliseerd en `casefold()` vergeleken. Daarmee beschermen we ook Windows/macOS zonder daarvoor op zo'n filesystem te hoeven draaien.
8. **Geen directe overwrite-fallback meer.** Bij een langdurige Windows/Dropbox lock geeft QuietWriter liever een fout en bewaart de oude bytes. Een fallback die live truncateert is niet atomisch en past niet bij de integriteitsgarantie.
9. **No-op migratie maakt geen checkpoint.** Eerst pure preview, alleen bij echte wijziging volgt de recovery snapshot.
10. **Niet-openbare boeken verdwijnen niet meer volledig stil.** `list_books()` bewaart de load-errors en de boekenplank vermeldt dat boeken niet konden worden geopend. Een uitgebreidere herstel-UI volgt pas nadat de backend groen is.

## Gericht opnieuw te testen door Claude
- format 99 + onbekend veld: `load_book` moet weigeren en bytes mogen niet wijzigen;
- format 2 + onbekende top-level velden: load + gewone chapter save moet ze behouden;
- goede media-snapshot, daarna corrupte nieuwere snapshots: herstel moet de goede hash kiezen;
- tweede herstelpoging na een `pre_integrity_repair`: die snapshot moet worden overgeslagen;
- aux JSON `[]` in nieuwere snapshot: moet worden overgeslagen ten gunste van een ouder JSON-object;
- twee snapshots in dezelfde seconde: hoogste/later gemaakte microseconde-id wint;
- ontbrekende section `id`/`title` en chapter `title`: audit én load moeten afwijzen;
- CRLF-hoofdstuk: herstel moet byte-voor-byte identiek zijn;
- `chapters/x.md` versus `chapters/./x.md` en casevariant: duplicate;
- `format=True`, `2.7`, `"2"`: alle drie ongeldig;
- format 2 migreren: geen checkpoint;
- `os.replace` permanent `PermissionError`: write faalt, oorspronkelijke bytes blijven intact en tempbestand wordt opgeruimd.

## Bewust nog niet gedaan
Geen Integriteit/Herstel-pagina. Eerst moet 0.28.1 opnieuw runtime groen zijn. Echte Dropbox-races, echte Windows-locks en stroomuitval blijven alleen benaderbaar via failure injection.
