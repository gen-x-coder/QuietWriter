# Review notes — QuietWriter 0.29.0

Focus van deze review: de nieuwe Integriteit & herstel-UI moet een dunne laag blijven boven `BookIntegrityChecker`.

Controleer vooral:
- audit is werkelijk read-only;
- geen herstelactie zonder expliciete gebruikerbevestiging;
- herstelknop alleen bij een inhoudelijk geldige recovery source;
- revision guard blijft actief tussen audit en write;
- `pre_integrity_repair` wordt vóór iedere repair gemaakt;
- `book.json` wordt nooit via file-repair teruggezet;
- blocked/future-format/external-modification/write-error hebben elk een veilige uitweg;
- navigeren naar de pagina omzeilt geen bestaande dirty/save guards;
- migratie blijft expliciet en gebruikt de bestaande migration backend.

Gebruik waar mogelijk echte MainWindow/PySide6 runtime-tests in plaats van alleen broncode-stringchecks. Vergelijk bij read-only scenario's de hele boekmap byte-voor-byte.
