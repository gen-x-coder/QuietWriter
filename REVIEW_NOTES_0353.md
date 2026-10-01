# Review 0.35.3 — afsluiter 0.35

0.35.3 bevat de startfix uit 0.35.2 én de resterende releasefundamenten uit reviewronde 49.

## Verplicht met echte PySide6

1. `python main.py` — koude start.
2. `pytest`
3. `pytest -m qt`
4. `pytest tests/legacy`
5. `pytest tests/legacy -m qt`
6. `python -m pyflakes quietwriter`

CI installeert `pyflakes` en voert dezelfde undefined-namecontrole uit vóór de suites.

## Specifiek reproduceren

### Startblokker 0.35.2
- `AIPanel` moet zonder `NameError: tr` construeren.
- Start via de echte `MainWindow`-route en open daarna het AI-paneel.

### Engelse schermrondgang
Zet taal op Engels en controleer in ieder geval:
- statusbalk met boek-/hoofdstukwoordtelling;
- rechtsklikmenu in de manuscripteditor inclusief Formatting/Paragraph style;
- label YOU in AI-chat;
- spellingteller;
- Replace all-dialoog;
- conflicttekst met “and N more”;
- beschadigde-hoofdstukmeldingen;
- boekenplankmelding voor niet-geopende boeken;
- Planning-scènestatussen;
- Planning-relatietypen;
- nieuw boek: standaardtitel “Chapter 1”.

Planning-statussen en relatietypen mogen alleen in de UI vertaald zijn. Controleer byte-/JSON-inhoud: bekende waarden blijven canoniek Nederlands (`idee`, `uitgewerkt`, `geschreven`, `ouder van`, enz.). Een eigen/custom waarde moet ongewijzigd blijven.

### Voorwerk / Front matter
- Controleer dat `wijzig` / `edit` niet meer onder het inklaptabje valt.
- Controleer ook Achterwerk / Back matter.

### Fonts/licenties
- `tools/fetch_bundled_fonts.py` haalt 8 TTF-bestanden op.
- De 4 fontfamilies registreren.
- Alle fonttests zijn groen; er is geen permanente font-uitzondering meer.
- Geen `<Copyright Holder>`, `<Reserved Font Name>` of andere OFL-sjabloonregel in de meegeleverde `OFL.txt`-bestanden.

### Crash-cooldown
Herhaal de ronde-48-test: vijf exceptions van hetzelfde type en dezelfde bronregel met verschillende berichttekst mogen na sluiten niet onmiddellijk vijf nieuwe meldingen geven. Alle vijf moeten wel in het log staan.

## Verwachte basislijn

Er zijn vanaf 0.35.3 **geen bekende fontfailures** meer. Een niet-groene current/legacy/Qt-run is dus opnieuw een echte bevinding.
