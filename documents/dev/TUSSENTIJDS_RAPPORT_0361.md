# Tussentijds rapport 0.36.1

0.36.1 bouwt de first-run workflow en runtimeprofielen. Dezelfde portable release kan nu als productie of ontwikkeling draaien. Productie gebruikt de bestaande QuietWriter-instellingen en werkmap; development gebruikt eigen QSettings (`QuietWriter-Dev`), eigen standaardwerkmap (`QuietWriter-Dev`), eigen lokale loglocatie en een herkenbare `— DEV` venstertitel.

De first-run wizard is transactioneel: pas Voltooien of Overslaan schrijft instellingen. Nieuwe gebruikers krijgen vier korte stappen en AI staat standaard uit. Bestaande gebruikers worden niet lastiggevallen; bestaande instellingen of alleen het bestaan van de standaardwerkmap is genoeg om `first_run_done` stil te migreren. Voor testen is `--first-run` beschikbaar zonder eerst registrywaarden te verwijderen.

De portable Windows-build blijft allowlist-based en maakt twee launchers naast dezelfde exe: `QuietWriter PROD.cmd` en `QuietWriter DEV.cmd`.
