# QuietWriter 1.5.0 — dev.36 synchronisatieverkenner (reviewbasis)

## Uitgangspunt
Volledige dev.35-bron (717 bestanden), niet de lokale Git-werkmap. Versiemetadata in de bron stonden nog op `1.5.0-dev.28`; dit archief heet dev.36 maar activeert geen productie-installatie. Geen GitHub-wijzigingen.

## Gebouwd
- `quietwriter/sync_conflicts.py`: read-only scan van `<werkmap>/books`, begrensd in aantal bestanden, geen volgen van directorysymlinks, geen schrijfacties. Herkent herkenbare Dropbox-namen `conflicted copy` en `conflictkopie`.
- `quietwriter/ui/integrity_page.py`: op de pagina Integriteit & herstel een handmatige scan, resultatenlijst en knop om de map in de Windows Verkenner (of bestandsbeheer) te openen. De scan voert **geen herstel** uit.
- 4 vertaalde sleutels in de vijf locales.
- `tests/current/test_sync_conflicts_dev36.py`: detectie, onveranderde manuscriptbestanden, scanlimieten en geen nieuwe werkmap.
- `documents/ROADMAP_AND_IDEAS.md`: feitelijke status en acceptatie met twee computers expliciet uitgesteld.

## Nog niet gedaan
- De meerhoofdstuksvervanging is niet atomair bij sync-races. Het is onveilig om te claimen dat deze volledig is opgelost; dit blijft een hoge prioriteit.
- De scan herkent geen universele OneDrive-conflictpatronen, en bevestigt niet of Dropbox klaar is.
- Geen echte Dropbox-/OneDrive-proef met twee computers. Die uitvoeren wanneer beide systemen beschikbaar zijn.
- Geen native starter, ondertekende productie-installatie of automatische updates; deze blijven uit.

## Windows-controle
1. Open een testboek; ga naar Integriteit & herstel en druk **Conflictkopieën zoeken**.
2. Maak in een *kopie van je werkmap* een tekstbestand met `conflicted copy` in de naam, druk opnieuw op zoeken en selecteer dit bestand.
3. Klik **Openen in Verkenner**; de juiste map opent. Controleer dat de inhoud van het manuscript niet veranderd is.
4. Gebruik bestaande herstel- en geschiedenisfuncties; die mogen door de nieuwe lijst niet worden gewijzigd.

## Validatie in deze omgeving
Gerichte pytest en locales/brandingcontroles groen. Geen volledige suite of echte Windows-GUI-acceptatie aangetoond.
