# Tussentijds rapport 0.31.3

Deze release sluit de twee regressies uit reviewronde 21 en maakt de corruptiebescherming af voor JSON en vrije publicatietekst.

## Opgelost

- **Export revision baseline:** `ExportSettingsStore` kan nu met de `Library` werken. Een save verifieert eerst dat het boek niet extern veranderde en ververst na de atomische write de revision baseline. De Exportpagina gebruikt deze store en schrijft tijdens `set_book()` niet terug via UI-signalen.
- **Spelling na typen:** `SpellPanel` bewaart de documentrevision waarop `rows` zijn berekend. Cursorvolging ververst de foutenlijst zonder editorselectie wanneer die revision niet meer klopt.
- **Eerste klik:** `EditorPage` markeert alleen echte tekstmutaties via `QTextDocument.contentsChange(position, removed, added)`. De eerdere revision-vergelijking, die ook op formattering/setPlainText reageerde, is verwijderd.
- **Afgekapte JSON:** `_guard_existing_json()` valideert bestaande JSON vóór normale writes. Planning `characters.json`/`outline.json`, `publication.json` en `export/settings.json` weigeren nu zowel ongeldige UTF-8 als syntactisch kapotte JSON.
- **Publicatietekst:** ongeldige UTF-8 in `publication/texts/*.md` wordt tolerant gedetecteerd. De free-text editor toont een alleen-lezen herstelmelding en `save_text()` heeft dezelfde UTF-8-guard als andere tekstbronnen.
- **Integriteit-witruimte:** zichtbaarheid van de 6 px scheiding is gekoppeld aan `has_book` in `_mode_changed()`, zodat ook gewone Boekenplank-navigatie hem opruimt.

## Bewust nog open

De resterende adoptiebevinding uit ronde 21 — een schrijffout tijdens conflict-snapshotting kan midden in de commit alsnog een gemengde UI-state achterlaten — is niet als paar-regelige fix behandeld. Hiervoor moeten drie-wegs merges, recovery snapshots en meldingen volledig naar de prepare/preflight-fase. Dat is een afzonderlijke transactionele wijziging en hoort in 0.31.4 met eigen failure-injectiontests.

## Tests in deze omgeving

- Gerichte 0.31.3 + relevante regressies: **32 passed, 1 skipped**.
- Volledige suite in deze Linux-sandbox: **538 passed, 27 skipped, 280 subtests passed** na versie-update; alleen de **2 bekende fonttests** falen omdat `resources/fonts/font_manifest.json`/gebundelde fontresources niet in deze aangeleverde ZIP aanwezig zijn.
- PySide6 is in deze sandbox niet geïnstalleerd. De Qt-runtimechecks voor klikken/typen blijven daarom expliciet onderdeel van Claude's review.
