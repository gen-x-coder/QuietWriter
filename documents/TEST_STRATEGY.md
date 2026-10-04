# QuietWriter — teststrategie

## Doel
Tests bewaken blijvende product- en risicocontracten, niet oude reviewnummers.

## Testlagen
- **unit:** modellen, parsers, validators, merges, contextbouwers;
- **integratie:** storage/revisions/History/Planning/Publicatie/Media/Settings;
- **Qt-runtime:** signalen, timers, focus, modaliteit, parenting, layout, QTextDocument/Undo;
- **OS-specifiek:** Windows locks, SQLite handles, paths, PyInstaller, process exitcode;
- **executable smoke:** echte gebouwde app;
- **handmatig:** SmartScreen, visuele DPI, echte providers, grote/echte boeken.

## Blijvende risicodomeinen
1. storage/revisions en externe wijzigingen;
2. transactionele book adoption en failure injection;
3. corrupt UTF-8/JSON;
4. future-format no-downgrade;
5. History preview/restore;
6. Windows locks/filehandles;
7. editor source fidelity en false-dirty;
8. Undo/paragraph formatting;
9. Planning validatie;
10. publicatie/exportconflicten;
11. media protected blocks/cleanup;
12. AI stale workers/context/privacy;
13. i18n display vs canonieke opslag;
14. declaratieve navigatie/Settings preview;
15. startup/crash/smoke;
16. release staging/hygiene/version metadata.

## Organisatie
De langetermijnrichting is één actieve suite, per domein. Geen vergeten `legacy`-suite. Relevante oude regressies worden naar actief verplaatst; tests die alleen vervallen implementatiedetails bewaken worden verwijderd. Git-history is het archief.

Gewenste domeinnamen zijn bijvoorbeeld:
- `test_storage_safety.py`
- `test_book_adoption_and_conflicts.py`
- `test_integrity_and_recovery.py`
- `test_editor_source_fidelity.py`
- `test_planning.py`
- `test_publication_and_export.py`
- `test_media.py`
- `test_ai_reader.py`
- `test_navigation_and_settings.py`
- `test_i18n_and_accessibility.py`
- `test_startup_and_release.py`

## Test op contract
Een test moet liever het gebruikers-/veiligheidscontract bewaken dan een exacte codepositie. Source/AST is nuttig voor architecture gates zoals undefined names, imports of resourcewiring, maar niet als enige bewijs voor Qt-runtimegedrag.

## Qt
Gebruik `pytest -m qt`. Runtimebugs rond timers, signalen, focus, parent/reparent en modaliteit moeten echte PySide6/eventloop-testdekking hebben. Unexpected modals horen een test te laten falen, niet hangen.

## Failure injection
Blijvend gebruiken bij atomic writes, recovery snapshots, conflict_local, migratie, media-cleanup en caches. Controleer behalve exception ook live bytes, dirty state, History, Book identity en handles.

## Byte-identieke checks
Bij future formats, corruptie, History restore en presentation-only acties is bytevergelijking sterker dan alleen mtime/state.

## Windows
Windows CI blijft verplicht. SQLite/fileobjects/widgets/processen expliciet sluiten; niet op GC vertrouwen wanneer tempdirectorycleanup onderdeel is.

## AI-tests
Fake providers voor context, stale workers, no-warmup/privacy en requestparameters. Echte OpenRouter/Ollama blijven daarnaast praktijkchecks.

## Releasegates
Per push: static undefined-name, volledige actieve suite en Qt-subset op Windows + Ubuntu.  
Bij tag: Windows build, executable smoke, hygiene, tag/version check en assets/hash.

## Handmatige 1.0-matrix
- clean Windows zonder Python;
- first-run → boek maken → typen → sluiten/heropenen → export;
- 100/125/150% DPI;
- SmartScreen;
- echte Ollama/OpenRouter;
- oude boeken;
- groot boek;
- sync/conflict.

## Test verwijderen
Alleen als een sterker equivalent bestaat, de feature weg is, de test puur implementatiedetail is of hij echt duplicaat is zonder extra randgeval. 'Oud' of 'legacy' is geen reden op zichzelf.
