# Review notes 0.29.2

Doel: het laatste bekende gat in Integriteit & Herstel sluiten: ongeldige UTF-8 mag herstel niet onbereikbaar maken en mag nooit als lege bewerkbare tekst worden behandeld.

## Runtimechecks voor Claude

1. Maak het huidige hoofdstuk ongeldig UTF-8 terwijl het boek open is. Open Integriteit. De pagina moet openen, het probleem melden en herstel aanbieden als History een geldige kopie heeft.
2. Open een boek waarvan het eerste hoofdstuk al ongeldig UTF-8 is. Het boek mag niet crashen. De editor toont een duidelijke melding, is alleen-lezen en autosave mag het bestand byte-voor-byte niet veranderen.
3. Herhaal voor `ai/memory.md`, `ai/boekprofiel.md` en `planning/notes.md`: pagina blijft bruikbaar, beschadigde editor is alleen-lezen, Integriteit blijft bereikbaar.
4. Herstel elk van bovenstaande bestanden via Integriteit. Na herstel moet de centrale reload de echte herstelde inhoud tonen en bewerken/opslaan weer normaal werken.
5. Controleer dat een geldig leeg bestand nog steeds als normale lege inhoud wordt behandeld; alleen decode-fouten activeren de foutstaat.
6. Guard-regressie: wijzig een bestand ná openen van Integriteit maar vóór Herstel. Herstel moet nog steeds worden geweigerd.
7. Controleer byte-hashes van de volledige boekmap vóór/na alleen openen van een beschadigd bestand: geen writes.
8. Regressie rondes 14 en 15 opnieuw uitvoeren.

## Specifiek aandachtspunt

`adopt_active_book()` is nog niet transactioneel/all-or-nothing gemaakt. Dat is bewust doorgeschoven naar 0.30.0. Probeer wel te bevestigen dat de vier nu afgevangen UTF-8-routes geen half-geadopteerde toestand meer veroorzaken.
