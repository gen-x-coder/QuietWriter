# Tussentijds rapport QuietWriter 0.28.3

## Aanleiding
Claude verklaarde de backend van 0.28.2 groen: 528 tests en 280 subtests, met alleen de twee bekende fontresource-failures. Elf van de twaalf gevraagde UI/storage-scenario's waren groen. Twee UI-randgevallen bleven over: future-format tijdens Planning/Boekprofiel/Boekgeheugen en verlies van pending Boekdetails bij afsluiten/boekenplank.

## Ontwerpkeuze 1 — future-format exit centraal
`MainWindow.preserve_local_and_close_future_book()` is nu de gemeenschappelijke grens. Een pagina levert de lokale recovery-inhoud aan; MainWindow bewaart die eerst als `conflict_local`. Alleen na een geslaagde snapshot volgt `force_return_to_bookshelf()`. Een mislukte snapshot laat de workspace open.

Waarom: een toekomstig formaat is geen gewoon mergeconflict. Deze QuietWriter mag het boek niet meer laden of schrijven. De enige veilige handeling is lokale invoer onafhankelijk veiligstellen en daarna stoppen met muteren.

Planning levert het actuele planningbestand plus andere pending planning-overrides aan. Boekprofiel en Boekgeheugen leveren hun actuele Markdown aan. Boekdetails bouwt een recovery-only Book met de actuele formulierwaarden en gebruikt `create_version_from_state`; het toekomstige live `book.json` wordt nooit aangepast.

## Ontwerpkeuze 2 — Boekdetails heeft een save-contract
`BookDetailsPage.save()` retourneert nu expliciet `True` of `False`. MainWindow controleert pending Boekdetails vóór boekenplank, afsluiten en hoofdnavigatie. Een mislukte write blokkeert de overgang.

Waarom: Boekdetails was de laatste formulierpagina waarvan pending state niet in de centrale leave/close-guard zat. Een synopsis mag niet verdwijnen alleen omdat de gebruiker de app sluit.

## Niet meegenomen
De Integriteit & Herstel-UI is bewust nog niet in deze patch gestopt. 0.28.3 is de laatste correctness-naloop van 0.28.x. Na runtimebevestiging kan 0.29.0 op een stabiele UI/storage-grens bouwen.

## Tests hier
- gerichte 0.28.3/package tests: 5 geslaagd;
- volledige suite zonder de twee bekende fonttests: 501 geslaagd, 27 overgeslagen, 280 subtests geslaagd;
- PySide6-runtimegedrag blijft voor Claude, omdat de 27 Qt-tests hier niet draaien.

## Runtimevragen voor Claude
1. Future format terwijl Planning-notities dirty zijn: lokale notities in `conflict_local`, terug naar boekenplank, future `book.json` byte-identiek.
2. Hetzelfde voor een pending nieuw/bewerkt personage.
3. Hetzelfde voor Boekprofiel.
4. Hetzelfde voor Boekgeheugen.
5. Forceer failure tijdens de recovery-snapshot: boek blijft open en lokale invoer blijft zichtbaar.
6. Boekdetails: wijzig synopsis, klik Boekenplank; synopsis moet eerst opgeslagen zijn.
7. Boekdetails: wijzig synopsis, sluit venster; synopsis moet eerst opgeslagen zijn.
8. Forceer een write-error vanuit Boekdetails; boekenplank/navigatie/close mogen niet doorgaan.
9. Future format terwijl Boekdetails dirty is: formulierstate in History, future manifest ongemoeid, daarna veilige detach.
10. Herhaal rondes 9–11 als regressie, met nadruk op de bestaande editor/publicatie future-format flow.
