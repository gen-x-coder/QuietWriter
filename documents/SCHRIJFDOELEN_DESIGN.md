# QuietWriter — Schrijfdoelen en rustige voortgang

**Status:** canoniek ontwerp voor de 1.3.0-dev-lijn, gestart in **1.3.0-dev.11**.

## Doel
Schrijfdoelen moeten informatie geven zonder QuietWriter in een motivatiesysteem te veranderen. De schrijver kiest zelf of dagactiviteit wordt bijgehouden. Zonder opt-in verandert de dagelijkse schrijfervaring niet.

## V1
- Per boek een optioneel **Woorddoel**.
- Per boek een optionele **Gewenst klaar op**-datum, alleen zinvol bij een woorddoel.
- Een neutrale afgeleide regel: resterende woorden en ongeveer benodigde woorden per kalenderdag.
- Op de Boekenkast bij een doel: dunne voortgangsbalk en `x van y woorden`.
- In de editor bij een doel: `Boek: x van y woorden` en, alleen na expliciete opt-in en zodra groter dan nul, `vandaag n`.

## Volledig opt-in
De instelling `writing_progress_enabled` staat standaard **uit**.

De uitleg staat zowel bij het Schrijfdoel in Boekdetails als in Instellingen. De gebruiker moet de checkbox zelf inschakelen. Daarna wordt lokale positieve schrijfactiviteit per boek bijgehouden, ook als een boek nog geen woorddoel heeft; de UI toont `vandaag` in v1 alleen bij boeken mét een woorddoel. Dagvoortgang blijft lokaal op deze computer en wordt niet gesynchroniseerd.

Uitzetten:
- stopt onmiddellijk met nieuwe dagvoortgang verzamelen;
- verwijdert bestaande lokale dagvoortgang niet;
- telt tekst die tijdens de uitgeschakelde periode wordt geschreven later niet alsnog mee;
- opnieuw inschakelen gaat verder vanaf het laatst bewaarde dagtotaal.

Het woorddoel en de deadline blijven zichtbaar/bewaard wanneer dagtracking uit staat; die velden zijn expliciet door de gebruiker aan het boek toegevoegd en zijn geen activiteitstelemetrie.

## Wat telt als "vandaag geschreven"
Bij iedere **geslaagde editor-save** van hoofdstuk H:

`delta = woorden(H, huidige save) - woorden(H, vorige geslaagde save/laadmoment)`

Alleen `max(0, delta)` wordt toegevoegd.

Gevolgen:
- schrijven telt positief;
- schrappen verlaagt het dagtotaal niet;
- schrijven en daarna schrappen geeft dezelfde positieve schrijfproductie als schrappen en daarna schrijven, mits de stappen afzonderlijk zijn opgeslagen;
- import, synchronisatie en versieherstel tellen niet als lokaal geschreven activiteit;
- tekst geschreven terwijl tracking uit staat wordt niet achteraf meegeteld.

Bekende, geaccepteerde grenzen voor v1: verplaatsen/plakken van tekst tussen hoofdstukken kan na een opslag als positieve groei tellen; undo van eerder verwijderde tekst kan eveneens positief tellen. We meten tekstgroei, niet toetsaanslagen.

## Opslag
Boekintentie reist mee met het boek:
- `metadata.writing_goal_words`
- `metadata.writing_goal_date` (`YYYY-MM-DD`)

Lokale dagvoortgang staat buiten de werkmap in `AppLocalDataLocation/progress/`, per werkmap gehasht. Het bestand is niet nodig om een boek te openen of op te slaan. Ontbrekend/corrupt/onbeschrijfbaar betekent alleen dat lokale daghistorie niet beschikbaar is.

De lokale historie bewaart maximaal circa 60 dagen om latere rustige terugblik mogelijk te maken zonder nu al een dashboard te bouwen.

## Versiegeschiedenis
Woorddoel en deadline zijn **huidige intentie**, geen historische manuscriptinhoud. Bij versieherstel blijven daarom de live waarden staan, ook als de gekozen snapshot oudere of geen doelvelden bevat.

## UX-regels
- Geen streaks, badges, felicitaties, sprints of timers.
- Geen rood, "achter", schuld- of waarschuwingstaal.
- Geen dagdoel in v1.
- Geen nieuw dashboard of nieuwe hoofdpagina.
- `vandaag 0` wordt niet getoond.
- Doel gehaald: balk vol en gewoon het werkelijke aantal tonen; geen animatie/melding.
- Verstreken datum: alleen neutraal `verstreken`; geen nieuw dagtempo tonen.
- Daggrens: lokale middernacht.

## Latere opties, alleen bij echte vraag
- rustige lijst van recente dagen;
- configureerbare daggrens voor nachtschrijvers;
- dagdoel;
- gesommeerde activiteit over meerdere apparaten met conflictvrij apparaatbestand.
