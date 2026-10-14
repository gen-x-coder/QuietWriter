# QuietWriter dev.39 — read-only replacement recovery overview

## Scope

Built from the dev.38 complete source archive. `quietwriter/recovery_overview.py` lists replacement journal folders under `archive/<book-id>/replace-recovery-*` without modifying manuscript data, journals, or recovery copies. `Integriteit & herstel` has a manual scan button and a button to open the selected recovery directory in the file manager. The list distinguishes pending, attention required, recovered and committed journals. Invalid/missing journals are displayed as needing attention and are **never** deleted.

## Tests

- `python -m pytest -q tests/current/test_recovery_overview_dev39.py tests/current/test_replace_batch_dev37.py tests/current/test_replace_crash_journal_dev38.py tests/current/test_sync_conflicts_dev36.py`: 16 passed in this environment.
- `python tools/check_locales.py`: 1733 keys in five locales.
- `python tools/check_source_assets.py`: nine branding images, unchanged.
- Full test suite and actual Windows UI rendering: not run/verified in this iteration.

## Restrictions / next work

- **No automatic restore or deletion** from the UI; opening a directory is the only action.
- The existing recovery engine is not modified in this iteration, and its safety under actual sudden power loss is not certified.
- An incomplete or inconsistent recovery should be inspected by the user or a qualified reviewer before changing files.
- The live two-computer Dropbox/OneDrive acceptance scenario remains deferred by user choice.
- Program updater/automatic installation remains disabled.
- Lab `versioned_install`/native launcher and signed release workflow are still not a production-ready update mechanism.
- A broad project release-number reconciliation remains necessary; the package is a dev.39 review snapshot, not a published installer.
