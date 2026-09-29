# QuietWriter 0.28.0 — reviewnotities voor Claude

Deze release bouwt de niet-visuele basis voor integriteitscontrole, herstel en toekomstige datamigraties. De belangrijkste ontwerpkeuzes zijn bewust conservatief.

## 1. Audit is read-only en fail-closed

`BookIntegrityChecker.audit_folder()` schrijft nooit. Corrupte JSON in Planning/Publicatie wordt niet via de bestaande tolerant loaders als een lege datastructuur geïnterpreteerd; de auditor meldt dit expliciet als fout. De gewone loaders zijn niet aangepast, om geen brede gedragswijziging in 0.28.0 te introduceren.

Test vooral: afgekapt `book.json`, afgekapt Planning/Publicatie-JSON, invalid UTF-8, ontbrekend hoofdstuk, dubbele chapter-id/file en `../`-paden.

## 2. Media-integriteit gebruikt de bestaande SHA-256 als waarheid

Een manifestrecord moet naar `assets/images/...` wijzen. Ontbrekende binaries en hashverschillen zijn errors. Een ontbrekend `assets/manifest.json` is alleen een warning omdat pre-0.20-boeken legitiem zonder dit bestand kunnen bestaan.

## 3. Gericht herstel vervangt nooit book.json

`restore_file_from_history()` is bedoeld voor chapter/aux/media-bestanden. `book.json` bepaalt boekidentiteit en hoofdstukstructuur en wordt daarom niet als los bestand uit een willekeurige snapshot teruggezet. Manifestherstel hoort bij een volledige versie-restore.

Voor iedere gerichte reparatie:
1. revision guard;
2. zoek nieuwste daadwerkelijk leesbare History-kopie;
3. maak één volledige `pre_integrity_repair`-snapshot;
4. revision guard opnieuw;
5. schrijf alleen het gekozen bestand;
6. refresh revision.

De tweede guard is belangrijk voor Dropbox-timing tussen checkpoint en write.

## 4. Migraties zijn expliciet, niet stil tijdens load_book()

Het huidige formaat blijft 2. Een manifest zonder `format` wordt als legacy formaat 1 gezien. De pure migratie 1 -> 2 maakt `metadata` expliciet en voegt zo nodig alleen `slug` toe; onbekende velden blijven behouden.

Ik heb bewust geen automatische migratie in `load_book()` gezet. Alleen openen mag geen persistente wijziging veroorzaken. `Library.migrate_book_format()` maakt eerst een complete `pre_migration`-snapshot en gebruikt daarna een atomische manifestwrite. Een future format (>2) wordt geweigerd in plaats van best-effort geopend als migratiekandidaat.

## 5. Gewenste runtime/failure-injectiontests

- schoon 0.28-boek -> geen errors;
- half geschreven `book.json` -> nette auditfout, geen crash/write;
- ontbrekend hoofdstuk -> recoverable error;
- invalid UTF-8 hoofdstuk -> recoverable error;
- dubbele chapter-id en dubbel chapter-file -> errors;
- chapterpad `../outside.md` -> error en nooit buiten boekmap lezen;
- corrupt `planning/characters.json`, `outline.json`, `publication.json` -> errors;
- media binary ontbreekt / hash mismatch -> errors;
- legacy boek zonder media manifest -> warning, geen error;
- format 1 -> pure migratie naar 2, inputobject onveranderd, onbekende velden behouden;
- format 99 -> `FutureBookFormatError`;
- failure tijdens manifestwrite -> oorspronkelijke `book.json` bytes intact;
- `Library.migrate_book_format()` -> precies één `pre_migration` checkpoint;
- gericht herstel -> nieuwste bruikbare History-kopie + precies één `pre_integrity_repair` checkpoint;
- nieuwste History-kopie corrupt maar oudere goed -> oudere goede kopie kiezen;
- externe wijziging vóór herstel -> `ExternalModificationError`, geen checkpoint/write;
- externe wijziging tussen checkpoint en write -> tweede guard moet write blokkeren.

Let ook op regressies in bestaande History restore, Media Manager en conflict/revision tests.
