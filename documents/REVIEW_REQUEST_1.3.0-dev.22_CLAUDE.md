# Reviewverzoek QuietWriter 1.3.0-dev.22

Wijzig **geen code**. Review en test deze build als onafhankelijke reviewer.

## Context

Publieke release blijft 1.2.32. Actieve ontwikkellijn is 1.3.0-dev.22.

Dev.22 maakt de bestaande Planningworkflow interactief tijdens het schrijven. Naast Tekstbreedte staat een subtiele Planning-knop met een tijdelijke overlay voor de scènes van het actieve hoofdstuk. De schrijver kan daar een open scène bewust als `geschreven` markeren. QuietWriter detecteert dit nooit automatisch.

Lees eerst:
- `documents/PLANNING_GHOST_PARAGRAPHS_DESIGN.md`
- `documents/PLANNING_WORKFLOW_NEXT_STEP.md`
- `documents/RELEASE_NOTES_1.3.0-dev.22.md`

## A. Volledige regressie

1. Draai volledige pytest met PySide6.
2. Draai `python main.py --smoke-test`.
3. Controleer locales.
4. Draai undefined-names/pyflakes en vergelijk met de vorige build.
5. Meld de uiteindelijke pytest-exitcode, inclusief de bekende Linux/Qt-teardown indien die nog optreedt.

## B. Planning-overlay

Test met een hoofdstuk met minstens drie gekoppelde scènes in verschillende statussen (`idee`, `uitgewerkt`, `geschreven`).

Controleer:
- knop **Planning** staat direct naast Tekstbreedte en is subtiel;
- zonder gekoppelde scènes is de knop niet bruikbaar;
- met gekoppelde scènes opent hij een tijdelijke overlay, ook als er al manuscripttekst staat;
- alle scènes blijven zichtbaar inclusief geschreven scènes;
- statussen zijn duidelijk;
- open scène -> **Klaar** schrijft uitsluitend `status=geschreven` in Planning;
- manuscripttekst, dirty-status, woordtelling, zoeken, export, AI-context en Undo veranderen niet;
- overlay sluit natuurlijk met Escape/klik buiten;
- veel scènes scrollen bruikbaar;
- licht/donker en indien mogelijk 125/150% DPI.

Test ook externe wijziging/conflict tijdens het opslaan van de status. De bestaande Planning-conflictbeveiliging mag niet worden omzeild.

## C. Ghosttekst

- Status verschijnt nu expliciet in de ghosttekst.
- `Locatie` en `Personages` blijven aparte regels.
- Een als Geschreven gemarkeerde scène blijft zichtbaar maar duidelijk als klaar herkenbaar.
- Ghosts blijven strikt presentation-only en blijven uit QTextDocument, bestand, tellers, zoeken, spelling, export, AI-context en Undo.

## D. Scene-editor

Status moet een echte gesloten `QComboBox` zijn: klikken ergens op het veld opent/selecteert de lijst; vrije tekst invoeren mag niet. Oude/onbekende opgeslagen statuswaarden mogen bij openen niet stil verloren gaan.

## E. Personages / hoofdstuklijst

- Planning > Personages selecteert bij openen automatisch het eerste opgeslagen personage en toont diens details.
- Bij geen personages blijft de lege toestand correct.
- Bij veel hoofdstukken gebruikt de track van de scrollbar dezelfde achtergrond als de Inhoud/pagina-achtergrond, in licht en donker thema.

## F. Versie-audit

Zoek actuele statusverwijzingen die nog foutief een oudere actieve dev-versie noemen. Historische changelog/release-notes blijven historisch. README.md en README_EN.md zijn bewust niet gewijzigd.

## Rapportage

Classificeer als blocker, vóór 1.3.0, backlog/polish of niet getest. Geef concrete reproductie en kleinste veilige oplossingsrichting. Wijzig geen code.
