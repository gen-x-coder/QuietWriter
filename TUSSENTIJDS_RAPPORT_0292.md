# Tussentijds rapport 0.29.2

## Aanleiding
Reviewronde 15 bevestigde 0.29.1 voor de normale herstelroute, maar vond dat ongeldige UTF-8 in het huidige hoofdstuk, Boekprofiel, Boekgeheugen of Planning-notities de Integriteit-pagina of het openen van een boek kon blokkeren.

## Wijzigingen
- Integriteit valt bij een mislukte centrale adopt terug op de read-only audit in plaats van de pagina te blokkeren.
- De editor behandelt een hoofdstuk met ongeldige UTF-8 als beschadigd en alleen-lezen. Er wordt nadrukkelijk niet naar lege tekst teruggevallen.
- Boekprofiel en Boekgeheugen tonen bij ongeldige UTF-8 een alleen-lezen foutstaat met verwijzing naar Integriteit.
- Planning-notities doen hetzelfde.
- Zodra een geldig/hersteld bestand opnieuw wordt geladen, wordt de editor weer normaal bewerkbaar.
- Extra regressietests bewaken dat ongeldige UTF-8 niet stil als lege inhoud wordt geïnterpreteerd.

## Bewuste grens
De grotere architectuurwijziging om `MainWindow.adopt_active_book()` volledig transactioneel/all-or-nothing te maken is niet in deze patch gestopt. Dat hoort bij 0.30.0, zoals Claude voorstelde. 0.29.2 beperkt zich tot het veilig bereikbaar houden van herstel en het voorkomen van overschrijven van corrupte tekstbestanden.
