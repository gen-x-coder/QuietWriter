# QuietWriter dev.41 — Bewaarplaats-paneel correctie

- Alleen het Bewaarplaats-paneel gebruikt de gedeelde PanelHelp zonder knop **Begrepen**.
- De knop rechtsboven met het vraagteken blijft de uitleg aan- en uitzetten.
- Andere panelen behouden hun bestaande knoppen en gedrag.
- De verwijderde focusmodus blijft verwijderd.
- Open punten blijft alleen in zijn eigen rechter menu beschikbaar.
- Nieuwe functies voor Planning en de AI Meelezer zijn niet gebouwd; bespreek hun gewenste gedrag eerst met de gebruiker.

## Visuele controle Windows
1. Open een boek, toon Bewaarplaats. De uitleg staat compact bovenaan en de actieknoppen volgen er direct onder.
2. Klik op het vraagteken en controleer het in- en uitklappen.
3. Open Toevoegen: geen extra Open punten-kaart en dezelfde paneelachtergrond als de andere onderdelen.
4. Controleer dat Ctrl+Shift+F geen focusmodus activeert.

## Teststatus
Python-syntaxis gecontroleerd. De nieuwe Qt-test moet op Windows/PySide6 worden uitgevoerd.
