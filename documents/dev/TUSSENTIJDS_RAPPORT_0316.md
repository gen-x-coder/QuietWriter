# Tussentijds rapport 0.31.6

## Doel

Het laatste zeldzame dead-end uit reviewronde 24 sluiten: lokale dirty tekst mag niet vastlopen wanneer precies het bijbehorende Markdown-bronbestand extern onleesbaar wordt.

## Implementatie

- `BookMemoryPage.prepare_adoption()` en `BookProfilePage.prepare_adoption()` herkennen ongeldige UTF-8 tijdens de drie-wegs-preflight. De lokale complete invoer wordt eerst als `conflict_local` opgeslagen; de commit gebruikt daarna de bestaande alleen-lezen-corruptiestaat.
- Hun directe conflictflow detecteert een onleesbare eigen bron vóór de normale mine/disk-dialoog en routeert meteen via centrale adoptie. Daardoor bestaat er geen onveilige “overschrijf corrupt bestand”-keuze en ook geen cancel-dead-end.
- `MainWindow._prepare_active_book_adoption()` doet hetzelfde voor dirty Planning-notities. De commit markeert `planning/notes.md` als gewijzigd zodat pending tekst niet opnieuw over de read-only foutstaat wordt hersteld.
- `PlanningPage._resolve_external_change()` bypasset de normale keuze wanneer `planning/notes.md` zelf onleesbaar is.
- Alle recovery-writes blijven in de 0.31.5-preflight. Een snapshotfout gebeurt dus vóór de eerste UI-rebind.

## Tests lokaal

- Volledige suite: **551 geslaagd, 27 overgeslagen, 280 subtests geslaagd**.
- Alleen de **2 bekende fonttests** falen omdat `resources/fonts/font_manifest.json` en de fontresources in deze omgeving ontbreken.
- Nieuwe bron-/architectuurtests controleren de corrupt-preflight voor Boekgeheugen, Boekprofiel en Planning-notities, het ontbreken van recovery-writes in de commit, en het onderdrukken van pending Notes-herstel over een corrupte bron.

## Reviewfocus

Claude moet de echte PySide6-runtime gebruiken voor de drie corrupte-dirty scenario's, inclusief failure-injection op de nieuwe recovery-snapshots en herstel via Integriteit.
