# QuietWriter — afgesproken correcties op dev.41

Deze bundel is gebaseerd op de volledige dev.41-bron en is geen productie-release.

## Wijzigingen op uitdrukkelijk verzoek
- Focusmodus volledig verwijderd: knop, Ctrl+Shift+F, paneelherstelcode, vertalingen en uitsluitend de focusmodustest.
- Bewaarplaats: de uitleg houdt de eigen benodigde hoogte en rekt niet meer uit over het paneel; overige knoppen en logica behouden.
- Toevoegen: menuachtergrond krijgt dezelfde themakleur als de overige rechterpanelen, inclusief donkere thema's.
- Open punten: dubbele kaart uit Toevoegen verwijderd; zelfstandige knop/paneel voor Open punten behouden, inclusief toevoegen via dat paneel.

## Niet gewijzigd
- Meelezer-chatgeschiedenis of export (eerst bespreken), Planning, gewone handmatige updater, automatische updater (blijft uit).
- Geen vervanging van lokale projectmap of GitHub-push.

## Controles
- Python AST / compileall van betrokken modules; vertaalsets van vijf talen identiek.
- PySide6 en volledige pytest niet aanwezig in deze uitvoeromgeving; visuele Windows-acceptatie is nog nodig.

## Visuele controle op Windows
1. Open boek, controleer dat Focusmodus weg is en dat Ctrl+Shift+F niets extra's activeert.
2. Open Bewaarplaats in rechterpaneel: titel, helpvlak, selectietekst en knoppen compact bovenaan; geen reusachtig grijs vlak.
3. Open Toevoegen: achtergrond gelijk aan de andere rechterpanelen, ook na terugkeren van Afbeelding.
4. Open punten heeft zijn eigen ingang en werkt daar; er is geen tweede kaart onder Toevoegen.
5. Test licht en donker thema en venster op normale en smalle breedte.
