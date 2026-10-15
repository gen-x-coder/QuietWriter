# QuietWriter dev.34 — review van ontbrekende hoofdstukken

Bronbasis: volledige dev.33-source-review ZIP. Geen bestanden van lokale Windows-werkmap gewijzigd, geen commit of GitHub-publicatie. Dit is een reviewkandidaat; interne versiemetadata zijn nog niet omgezet naar een officiële dev.34-release.

## Gewijzigd

- `main_window.py`: bij voorbereid openen van het eerste hoofdstuk kan `ChapterNotAvailableError` de boekadoptie niet meer afbreken; de editor krijgt gelegenheid om zijn bestaande melding en alleen-lezenstatus te tonen.
- `storage.py`: dupliceren van een ontbrekend hoofdstuk weigert; conflict-snapshots met ontbrekend hoofdstuk weigeren in plaats van het bestand als lege tekst te bewaren. Een onvoltooide `.partial`-geschiedenismap kan overblijven en wordt niet als volledige revisie geregistreerd.
- `editor_page.py`: aparte `_chapter_unavailable`-status; melding telt niet meer als hoofdstukwoorden; zoeken vangt de nieuwe opslagexceptie af; 'Alles vervangen' weigert bij eerder herkende onleesbare of ontbrekende hoofdstukken. Bij synchronisatie tussen de voorcontrole en latere schrijftaken is volledige transactie-atomiciteit nog niet gegarandeerd.
- `ai/context.py`: bij ontbrekend actief hoofdstuk wordt een neutrale placeholder gebruikt in plaats van de zichtbare editorwaarschuwing, inclusief boek- en sectiecontext.
- Vijf vertaalbestanden: één nieuwe AI-contextsleutel.
- `tests/current/test_sync_missing_chapter_dev34.py`: twee nieuwe regressies voor duplicatie en conflict-snapshot.

## Lokaal uitgevoerd

- 18 passed, 1 skipped in gekozen testset (storage, context, versiestarter, taalhardening).
- `tools/check_locales.py`: 1716 keys, 5 locales.
- `tools/check_source_assets.py`: 9 screenshots, missing=0, changed=0.
- Python compileall op bijgewerkte code geslaagd.
- Volledige pytest en Claude's UI-harnas `sync533.py` zijn **nog niet** uitgevoerd; Windows/echte Dropbox evenmin.

## Kritieke reviewvragen

1. Herhaal `sync533.py` (M1/M2/M3/M6/M7/M9/M10) tegen deze kandidaat. Test ook klikken, focus en autosave in Qt.
2. Controleer of `update_counts` geen waarschuwing als manuscriptwoorden telt. Controleer ook andere AI-paden die de editor rechtstreeks lezen.
3. Onderzoek de zoek/vervang-flow bij simultane cloudbestandswijzigingen. Huidige beschermingen blokkeren ontbrekende bestanden vóór bevestiging, maar vervanging over meerdere bestanden is geen volledig atomaire transactie.
4. Controleer of gedeeltelijke `.partial`-geschiedenismappen na fout geen herstelproblemen veroorzaken.
5. Nog open: boekenkast automatisch verversen bij sync, zichtbaarheid conflictkopieën, integriteits-herstelwaarschuwingen, ontbrekende manuscriptbestanden in tellingen, extra heldere exportmelding en Nederlandse/Engelse statusnauwkeurigheid.
6. Los van deze iteratie: externe updater blijft uit; native starter en offline Ed25519-productieketen ontbreken. SignPath is bewust verlaten.

NO-GO voor automatische installaties en voor definitieve publicatie zonder onafhankelijke test en Windows-validatie.
