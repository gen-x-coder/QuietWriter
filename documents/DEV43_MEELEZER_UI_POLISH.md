# QuietWriter 1.5.0 — dev.43 Meelezer UI-polish

Gebaseerd op de door gebruiker aangeleverde dev.42-reviewbundle. Geen GitHub push, geen productie-release.

## Verbeteringen

- Meelezerknoppen hebben compacte labels: Pop-out (met venstericoon), Bewaren, Gesprekken; volledige betekenissen als tooltip.
- Pop-out blijft niet-modale werkruimte met dezelfde AIPanel, niet een lege kopie. Een tijdelijke placeholder bewaart de plek in de rechter QStackedWidget.
- Sluiten herstelt de originele widget op zijn positie. Selecteren van een ander rechterpaneel sluit de pop-out en houdt de nieuw gekozen tool actief.
- Opslaan zonder gebruikersvraag laat nu een begrijpelijke melding zien in plaats van stil niets te doen.
- Leeg gespreksarchief toont een beschrijving en Sluiten, geen blanco split-view.
- Export is alleen beschikbaar bij geselecteerde gesprekken. Fouten bij bestandsschrijven worden gemeld.
- Nieuwe vertalingen in NL, EN, DE, FR en ES. Dialoog heeft expliciete Nederlandstalige Sluiten-knop.

## Controle

- Python compileall geslaagd.
- `python -m pytest -q tests/current/test_meelezer_manual_archive_dev42.py`: 3 tests geslaagd.
- **Geen PySide6 in deze omgeving:** de nieuwe Qt-pop-out en de visuele Windows-regressies zijn nog niet daadwerkelijk gedraaid. Daarom eerst zelf controleren en pas na een grotere stabiele iteratie Claude inschakelen.

## Windows visueel te testen

1. Open Meelezer op normaal smal rechterpaneel: alle drie knoppen volledig leesbaar, Pop-out icoon aanwezig.
2. Klik Pop-out: dezelfde berichten en invoervelden zichtbaar in venster; rechterpaneel springt niet naar Spellingcontrole.
3. Sluit Pop-out met vensterkruis, en vervolgens met Terug: Meelezer staat één keer correct op zijn plek.
4. Open Pop-out en klik rechts op Spellingcontrole: pop-out sluit, Spellingcontrole staat normaal zichtbaar. Wissel terug naar Meelezer.
5. Klik Bewaren zonder gestelde vraag: er verschijnt een informatieve melding. Stel dan een vraag, bewaar het gesprek, open Gesprekken en exporteer het gesprek.
6. Test nieuw leeg boek zonder archief: Gesprekken toont lege-statusmelding, geen blanco split-view. Check donker thema en minimaal vensterformaat.
