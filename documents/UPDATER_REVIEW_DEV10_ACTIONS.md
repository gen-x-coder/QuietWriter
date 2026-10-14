# Dev.10 review → dev.11 follow-up

Claude found production blockers P1–P6. Dev.11 introduces an **isolated** side-by-side fixture-only engine, in addition to (not replacing) the legacy dev.10 test implementation.

Completed in dev.11 fixture lab: fresh staging, streaming extraction and file fsync, directory swap, recovery journal, retained prior version, removal of obsolete program files, refusal of actual executables.

Still open before production: durable crash recovery for every intermediate state, OS-level interprocess lock, Windows process handoff, signed production manifest and anti-replay, release ZIP compatibility, health check, data-location audit, Windows lock and junction tests. **Real installs remain blocked.**
