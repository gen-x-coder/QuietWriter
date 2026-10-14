# QuietWriter 1.5.0-dev.29 — overdracht voor Claude

## Status
**REVIEW CANDIDATE — NO-GO voor productie-installatie.** Alle installerende productieacties blijven uitgeschakeld. Bestaande handmatige update blijft werken.

## Afgesproken gedrag
- Zonder marker: standaard updatecontrole en `GitHub openen`, verder niets.
- Met leeg, gewoon bestand `.quietwriter-update-pilot` direct in de **actieve boekenwerkmap** (`library.root`): extra knop `Nieuwe updater (proef)` bij een beschikbare versie, plus een zichtbare proefstatus in Instellingen.
- Marker als directory, symlink, niet-leeg bestand of in een andere map: geen opt-in.
- Verwijderen van de marker schakelt de proef uit bij de volgende updateweergave/instellingenpagina. Herstart aanbevolen voor duidelijkheid.
- Opt-in verandert géén update-instellingen, downloadt niets en machtigt geen installatie. Het is niet de security-grens.
- De eerdere instelling `auto_update_check` regelt uitsluitend het automatisch controleren op nieuwe versies; `auto_update_download` blijft uitgeschakeld.

## Bestaande techniek
- Frozen onedir-updater; Windows parent HANDLE + READY; mapwissel; EXE-gezondheidscontrole; commit en rollback in tijdelijke fixture.
- ZIP preflight: volledige ZIP SHA-256, bestandeninventaris, gevaarlijke namen, links, duplicaten en uitpaklimieten.
- Read-only install-readiness: ongewijzigde programmabestanden en geen onbekende bestanden in installatiewortel.
- Pinned production release keys zijn bewust leeg in `update_release_preflight.py`.

## Gevraagd aan Claude — maak GO/NO-GO oordeel
1. Controleer de marker gating op active workspace, symlinks/junctions, onverwachte werkmapwissel, bestandsmanipulatie en UI-relevante race conditions.
2. Controleer de volledige overgang van geauthenticeerde release (offline Ed25519) naar download, veilige extractie/staging, Windows handoff, journaling, gezondheid, commit/rollback en herstart. Identificeer gaten; laat automatische installatie uitgeschakeld totdat volledig.
3. Vergelijk `side_by_side_update.py` met `update_real_transaction_lab.py` — dubbele transaction-engine is een expliciet architectuurrisico.
4. Verifieer dat lokale install-inventarissen nooit als zelfstandig authenticiteitsbewijs gelden en dat junctions, user books en herstel na stroomuitval beschermd zijn.
5. Test Windows met volledige PyInstaller onedir inclusief nieuw updateproces, launcher UI, ongeldige handtekeningen/manifesten en afgebroken updates.
6. Controleer versiebeleid en GitHub signing/publicatieproces: nog geen officiële offline releasesleutel ingevoerd. Geen automatisch uitvoerende knoppen vrijgeven zonder die infrastructuur.
7. Controleer taalvertalingen, toegankelijkheid, status, herstart na boekenmapwissel, branding en standaardhandmatige updateflow.

## Geteste reeks in deze omgeving
`54 passed, 1 skipped, 1 warning` op geselecteerde update-/security-/gate-regressies. Waarschuwing betreft bewust dubbele ZIP-entry in kwaadaardige testdata. Dit is GEEN volledige Windows-testsuite en GEEN GO.

## Gebruik op testcomputers
Maak in de actieve boekenmap een **leeg bestand** met de naam `.quietwriter-update-pilot` (zonder `.txt`). Verwijder het om het proefpad te verbergen. Voor de actuele build is de proefknop alleen een informatiedialoog; hij installeert nog niet. Voor echte pilots vereist het veilig aansluiten van de geauthenticeerde updater aanvullende ontwikkeling en releaseondertekening.

## Voorwaarden productie-GO
Officiële public key pinnen in een gereviewde applicatierelease, private release signing offline organiseren, echte geauthenticeerde pakketketen koppelen aan één transactie-engine, veilige stager buiten installatiemap, betrouwbaar crashherstel, handmatige goedkeuring vóór sluiten/installatie, en schone Windows E2E van **twee verschillende** ondertekende binaries incl. persoonlijke data en rollback.
