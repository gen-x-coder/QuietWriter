# QuietWriter dev.20 — Windows health-check contract

Dit is een tussenstap, geen productie-activatie. `main.py --update-health-check <hex token> <nieuw markerpad>` voert de bestaande geïsoleerde `--smoke-test` uit, zonder de reguliere boekenplank te openen. Bij succes verschijnt een bevestiging met de unieke token. De controlefunctie `probe_executable` start een EXE en vergelijkt exitcode en bevestiging.

Nog open: een externe updater-EXE buiten de installatiemap, Windows-proceshandle, single-instance, hersteltrigger, productiehandtekeningen, manifesten, UI-koppeling en echte installatiewissel. Deze bron voert geen productie-updates uit. Test op Windows in een lege testomgeving met de volledige Windows-build, nooit op de hoofdinstallatie.
