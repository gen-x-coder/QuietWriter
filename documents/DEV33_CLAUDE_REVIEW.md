# QuietWriter 1.5.0-dev.33 — reviewkandidaat (13 oktober 2026)

## Herkomst en grenzen

Gebaseerd op de volledige `QuietWriter-1.5.0-dev.32-source-review.zip` en Claude’s `QUIETWRITER_REVIEW_1_5_0_DEV32_CLAUDE.md`.
Dit is een **broncode-reviewkandidaat**, niet een productierelease of een werkende automatische updater. Interne versie-/snapshotmetadata zijn nog niet naar dev.33 gezet: dat blijft een vrijgaveblokkade. Niets pushen naar GitHub zonder expliciete bevestiging.

## Veranderingen

1. `test_versioned_starter_safety_dev32.py`: relatieve testimport; verhelpt de `spylls`/`tests`-naamcollision bij verzamelen.
2. `storage.py`: `ChapterNotAvailableError` voor een gerefereerd hoofdstukbestand dat lokaal ontbreekt; voorkom zowel leeg lezen als opslaan op dat pad. Een echt bestaand leeg hoofdstuk blijft geldig. Dit is de hoogste prioriteit uit het Dropbox-scenario.
3. `editor_page.py`: rustige, vertaald beschikbare, alleen-lezenweergave bij een nog niet beschikbaar hoofdstuk; stop autosave. **Controleer expliciet op echte Windows/Qt** de focus, navigatie, herstel na opnieuw openen en mogelijk werk in het editordocument.
4. `versioned_install.py`: tijdelijk onleesbare pointers na korte retries als fout behandelen, **niet** als ongeldige JSON en dus geen stille terugval; padcomponenten op links controleren en strikte `size`-typecontrole. De starter toont een waarschuwing als een corrupte actieve applicatie alleen via `previous` te openen is. De pointer wordt niet gewijzigd.
5. `documents/ROADMAP_AND_IDEAS.md`: vijf geprioriteerde cloudsync-items, waarvan de ontbrekende hoofdstukblokkade in deze reviewbron is begonnen.
6. Twee meertalige editorsleutels toegevoegd voor nl/en/de/fr/es.

## Tests uitgevoerd in de ontwikkelcontainer

- Gerichte storage, pointer, historie, versiemappen: **33 passed**.
- Extra Qt-/locale-/releasegerelateerde tests: **22 passed, 1 skipped**.
- `tools/check_locales.py`: **1715 keys in 5 locales**.
- `tools/check_source_assets.py`: **9 branding assets, changed 0**.
- De **volledige suite is niet gedraaid**. Dit is geen GO voor productie.

## Onafhankelijk reviewwerk voor Claude

- Draai de **volledige suite zonder** `--continue-on-collection-errors`; vooral gerelateerde opslag-, export- en AI-paden die nu `ChapterNotAvailableError` ontvangen.
- Test `sync532.py` opnieuw: S2 (ontbrekend hoofdstuk) en S4 (erop schrijven) moeten nu veilig falen, S6 (boekenkast refresh) blijft backlog.
- Test `ud532.py` pointer-locked-slot en beschadigde actieve EXE en bevestig dat tijdelijk I/O-falen geen downgrade veroorzaakt; let op user-facing fallback en eventuele regressies.
- Qt-test van editor die een ontbrekend hoofdstuk opent, autosave en alleen-lezen na wisselen naar een bestaand hoofdstuk, in alle vijf talen.
- Check `update_release_preflight` netwerkimport in starter, openstaande foutcodes, Windows-native starter en ontbrekende Ed25519-sleutel: **allemaal nog NIET productiegeschikt**.
- Regels SignPath uit `PRIVACY.md` en oude release-instructies zijn nog documentatieschuld; gebruiker heeft SignPath bewust stopgezet.
- Controleer Dropbox/OneDrive Files-on-Demand op echte Windows-laptop, zonder te vertrouwen op een provider-specifieke 'sync klaar' API.

## Belangrijk voor de volgende iteratie

Automatisch verversen van de boekenkast (F5 en bij heractivering), detectie van cloud-placeholders en conflictkopieën staan expliciet in de backlog. Deze reviewbron implementeert dat **niet**. Test de introductie van de missing-chapter-exceptie grondig; externe exports en woordtellingen moeten bij ontbrekende data niet ten onrechte een compleet boek suggereren.
