# QuietWriter 1.3.0-dev.11

Deze ontwikkelbuild start de schrijfdoelenfunctie bovenop de afgeronde Boekenkast.

## Schrijfdoel
- Boekdetails heeft nu een optioneel **Woorddoel** en een optionele gewenste einddatum.
- Bij een doel toont QuietWriter neutraal hoeveel woorden nog ontbreken en, met een toekomstige datum, ongeveer hoeveel woorden per kalenderdag nodig zijn.
- De Boekenkast toont bij boeken met een doel een dunne voortgangsbalk en `x van y woorden`.
- De editor toont bij een doel eveneens `x van y woorden`.

## Vandaag geschreven is volledig opt-in
- De instelling **Vandaag geschreven bijhouden** staat standaard uit.
- De uitleg en checkbox staan in Instellingen én bij Schrijfdoel in Boekdetails.
- Alleen positieve groei uit geslaagde editor-opslagen telt mee.
- Schrappen verlaagt het dagtotaal niet.
- De telling blijft lokaal op deze computer en wordt niet gesynchroniseerd.
- Uitzetten pauzeert het bijhouden zonder bestaande voortgang te wissen en zonder later tekst uit de uitgeschakelde periode alsnog mee te tellen.
- `vandaag 0` wordt niet getoond.

## Data en herstel
- Woorddoel en deadline staan als gewone boekmetadata in `book.json` en reizen daardoor mee in `.qwbook`.
- Lokale dagvoortgang staat buiten de werkmap in lokale appdata en bewaart maximaal ongeveer 60 dagen.
- Versieherstel herstelt manuscriptinhoud maar laat het huidige woorddoel en de huidige deadline ongemoeid.
- `library.json` is voor deze functie ongewijzigd.

## Niet in deze build
Geen dagdoelen, streaks, badges, sprints, timers, voortgangsgrafiek of meldingen. De feature blijft bewust rustig en opt-in.
