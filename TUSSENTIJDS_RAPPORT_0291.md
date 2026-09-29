# Tussentijds rapport — QuietWriter 0.29.1

## Aanleiding

Claude vond in 0.29.0 één rode integratiefout: een correct hersteld hoofdstuk kon daarna door stale editorinhoud worden overschreven. Daarnaast moest een extern verdwenen bestand eerst via de Boekenplank opnieuw worden geopend voordat herstel praktisch bruikbaar werd.

## Oplossing

Integriteit gebruikt nu aan beide kanten van de audit/herstelgrens hetzelfde centrale patroon:

- vóór een audit: `load_book` → `MainWindow.adopt_active_book` → audit;
- na een geslaagd herstel: `load_book` → `MainWindow.adopt_active_book` → heraudit.

Het huidige hoofdstuk-id wordt daarbij doorgegeven zodat `EditorPage.adopt_live_book` precies dat hoofdstuk opnieuw van schijf laadt. De centrale adoptie herbindt ook de overige boekpagina's en vernieuwt revision tracking.

Een future-format, corrupt manifest of bewust geblokkeerd boek wordt niet geforceerd geadopteerd. Die situaties blijven voor de read-only checker zichtbaar. Een blokkade wordt dus niet door een integriteitsrefresh opgeheven.

Daarnaast heeft de integriteitspagina een recovery-cache per audit gekregen. Die wordt bij iedere nieuwe refresh geleegd.

## Scope

Geen editor-polish, autosavewijzigingen, spellingswerk of navigatieherontwerp in deze patch. Die blijven voor 0.30/0.31.

## Runtimefocus voor Claude

Zie `REVIEW_NOTES_0291.md`. Vooral scenario 1, 2, 4 en 7 zijn blockers voor groen.
