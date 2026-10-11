# QuietWriter 1.4 — integrale review van boekback-ups

**Status:** reviewopdracht, nog niet als definitief veilig vrijgegeven. De externe reviewer wijzigt geen productcode.

## Te reviewen

Review de volledige actuele bronboom, niet uitsluitend de tests die eerder voor dev.3–dev.5 zijn gemaakt.

1. **Windows / OneDrive / Dropbox:** sharing violations, bestanden die op aanvraag geladen worden, open bestanden, junctions, netwerkstations, lange paden en verdwijnende schijven.
2. **Volledige round-trip:** back-up → beschadigd of gewijzigd boek → bestaand boek vervangen → manuscript, media, boekgeheugen, chats en alle zichtbare versies controleren; met behoud van plankregistratie en privacy.
3. **Mislukking op elk overgangspunt:** valideren, veiligheidskopie maken, wisselen van map, geschiedenis overzetten, registratie bijwerken, tijdelijke mappen opruimen; na iedere fout moet exact vaststaan welke versie actief is. Test gesimuleerde en (waar haalbaar) echte Windows-locks.
4. **Permanente veiligheid:** fsync met schrijfbare handle, atomische publicatie, crash/restart, bestandssysteem dat tijdens het schrijven wegvalt. Geen ongecontroleerde `.qwbook` met definitieve naam.
5. **Automatische planning:** alleen opt-in, alleen gewijzigde boeken, maximaal eenmaal per dag, geen race met editor of gelijktijdige handmatige back-up; correct afbreken bij sluiten.
6. **Retentie:** behoud van zeven dagelijkse en vier wekelijkse automatische exemplaren volgens ontwerp; handmatige en veiligheidskopieën nooit automatisch opruimen. Alleen aantoonbaar geslaagde bestanden tellen mee.
7. **Privacy:** geen privéboeken in back-upselectie of status in Presentatiemodus. Test wisselen van zichtbaarheid terwijl Instellingen geopend is.
8. **Grote boeken:** huidige `.qwbook`-grens van 2 GB en herhaalde media in history; maak- én herstelpad moeten dezelfde grenzen hebben. Geen onverklaarde successen voor te grote archieven.
9. **Gebruikerservaring:** herstel vraagt twee bewuste bevestigingen, toont de juiste datum, heeft gelokaliseerde knoppen, onthult geen technische bestandsnamen en mag een succesvol herstel niet foutief als mislukt melden.

## Bekende achtergrond

- Dev.3: ongecontroleerde publicatie, ontbrekende fsync en halve history; hersteld in dev.4.
- Dev.4: alleen-lezen fsync blokkeerde Windows; hersteld in dev.5 na echte Windows-reproductie.
- Dev.12: fout bij opruimen van `.restore-staging` nadat een boek al hersteld was; afhandeling aangepast in dev.13.
- Dev.15: standaardknoppen bij back-upmeldingen vervangen door vertaalde knop; dev.16 voert die regel ook door bij gewone meldingen elders in de app.

## Acceptatie

Lever blockers, must-fixes, overige punten en expliciet niet-geteste scenario's. Draai volledige Qt-suite, lokale locale- en statische controles, de bestaande back-upstressscripts en eigen regressieharnassen. Laat productcode ongemoeid; echte Windows-waarnemingen blijven noodzakelijk.
