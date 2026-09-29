# Tussentijds rapport 0.28.2

## Aanleiding
De 0.28.1-backend is door Claude groen verklaard (523 tests, 280 subtests; alleen de twee bekende fonttests). De resterende rode fout zat aan de UI-grens: een blijvende lock kon de editorsave laten exploderen en `closeEvent` daardoor laten doorgaan met tekst die alleen nog in RAM stond.

## Ontwerpkeuzes
1. **Eén storage-domeinfout.** `_safe_atomic_write_text` en `_safe_atomic_write_bytes` vertalen `OSError` naar `StorageWriteError(path, cause)`. De storage bepaalt dus *wat* er fout ging; de UI bepaalt *wat de gebruiker mag doen*.
2. **Een mislukte manuscriptsave is geen crash.** `EditorPage.save()` houdt `dirty=True`, toont “Opslaan mislukt · bestand vergrendeld”, plant autosave opnieuw en retourneert `False`. Bestaande navigatieguards stoppen daardoor vanzelf.
3. **Afsluiten is fail-closed.** Ook een onverwachte save-exceptie in de laatste editorsave resulteert in `event.ignore()`. Geen save-exceptie mag het standaard geaccepteerde close-event laten passeren.
4. **Future format: eerst lokale recovery, dan loskoppelen.** Een oudere QuietWriter mag niet blijven proberen een format 3+-boek te muteren. Zodra `FutureBookFormatError` tijdens conflictresolutie verschijnt, wordt de lokale hoofdstuk/publicatietekst eerst als `conflict_local` in History gezet. Alleen als dat lukt wordt het boek via een expliciete no-save route gesloten en de boekenplank getoond.
5. **Geen geforceerde afsluiting als de recovery-snapshot mislukt.** Dan blijft het boek/editor open en krijgt de gebruiker de instructie de lokale tekst handmatig te kopiëren. Dit voorkomt dat onze veiligheidsroute zelf tekstverlies veroorzaakt.
6. **Metadata-contract voltooid.** `metadata` is afwezig/null/object; lijst/string/getal wordt door dezelfde validator geweigerd die audit en loader gebruiken.
7. **Binaire writes krijgen dezelfde lock-retry.** Gericht mediaherstel gebruikt dezelfde sibling-temp + retry + `os.replace`-garantie als tekst.
8. **Future extensies binnen section/chapter.** Nieuwe structurele velden binnen die objecten vereisen later een verhoging van het boekformaat. We voegen nu niet preventief overal `extra`-dicts toe; de future-format guard is de compatibiliteitsgrens.

## Wat Claude gericht moet testen
1. Manuscript dirty + permanente `PermissionError` op hoofdstukwrite: autosave faalt zonder crash, dirty blijft waar, tekst blijft in editor.
2. Daarna navigeren naar Planning/Boekprofiel: navigatie blijft op de editor zolang de lock bestaat.
3. Venster sluiten tijdens dezelfde lock: close-event wordt genegeerd en tekst blijft zichtbaar.
4. Lock verdwijnt: volgende autosave of handmatige save slaagt en dirty wordt false.
5. Onverwachte andere exceptie uit `editor_page.save()` tijdens `closeEvent`: venster blijft open.
6. Open format-2 boek wordt extern format 3; conflict → “Mijn versie”: exact lokale tekst bestaat in een `conflict_local` snapshot, boek wordt daarna gesloten naar boekenplank, live `book.json` blijft format 3 byte-identiek.
7. Hetzelfde met “Versie op schijf”: lokale tekst staat eveneens in History en er ontstaat geen terugkerende conflictdialoog.
8. Future-format conflict met dirty publicatietekst: lokale publicatiefile staat in `conflict_local`; daarna veilige terugkeer naar boekenplank.
9. Simuleer fout tijdens het maken van de lokale recovery-snapshot: boek blijft open, lokale tekst blijft in RAM en er wordt niet geforceerd losgekoppeld.
10. `metadata=[]`, `metadata="abc"`, `metadata=3`: audit en loader wijzen alle drie af; ontbrekend/null/object blijft geldig.
11. `_safe_atomic_write_bytes`: twee korte `PermissionError`s gevolgd door succes → herstel slaagt; permanente lock → `StorageWriteError`, originele bytes intact, geen tempbestand.
12. Controleer Planning, Boekprofiel, Boekgeheugen, Publicatie en Boekdetails bij `StorageWriteError`: geen paginawissel/close mag lokale dirty invoer stil verliezen. Generieke foutmeldingen zijn toegestaan; veiligheid en behoud zijn het contract.

## Bekende omgevingsgrens hier
PySide6 is in deze omgeving niet beschikbaar. De Qt/headless scenario's hierboven zijn daarom expliciet voor Claude; de niet-Qt regressies draaien hier wel.

## Teststatus in ChatGPT-omgeving
- Gerichte 0.28.2-tests: 5/5 geslaagd.
- Volledige suite zonder de twee bekende fontresource-tests: **498 geslaagd, 27 overgeslagen, 280 subtests geslaagd**.
- Volledige suite: **500 geslaagd, 27 overgeslagen, 280 subtests geslaagd, 2 bekende font-failures** (`resources/fonts/font_manifest.json` ontbreekt).
- De 27 skips zijn Qt/PySide6-tests; Claude kan deze runtime uitvoeren.
