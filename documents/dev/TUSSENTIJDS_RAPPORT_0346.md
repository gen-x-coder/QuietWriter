# Tussentijds rapport 0.34.6

0.34.6 corrigeert de laatste inconsistentie uit reviewronde 41. `AIPanel` past aan het eind van de constructor nu direct `_update_busy_buttons()` toe. Daardoor staat `Planning-context…` vóór het openen van een boek niet meer toevallig in de standaard actieve Qt-toestand. Na `set_book()` blijft de reeds bestaande update de knop activeren.

Daarnaast krijgt een Planning-fout die als lokaal contextstuk bij een AI-gesprek wordt vastgelegd opnieuw een zelfstandig label: `Planning niet beschikbaar — …`.

Lokale resultaten:
- current: 181 geslaagd, 12 overgeslagen;
- legacy: 422 geslaagd, 24 overgeslagen, 280 subtests geslaagd;
- de twee bekende fonttests zijn buiten deze runs gelaten.
