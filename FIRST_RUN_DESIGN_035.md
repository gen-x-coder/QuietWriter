# QuietWriter 0.35 — ontwerp first run

De first-run wizard wordt in 0.36 gebouwd. 0.35 legt alleen het contract vast zodat de releasefundering niet tegelijk een nieuwe workflow introduceert.

## Trigger

- Alleen tonen wanneer de instelling `workspace` nog niet bestaat.
- Een bestaande gebruiker ziet de wizard nooit automatisch.
- Iedere stap is over te slaan; alles blijft later wijzigbaar via Instellingen.

## Maximaal vier stappen

1. **Taal en uiterlijk** — Nederlands/English en thema.
2. **Werkmap** — standaardlocatie tonen, andere map kiezen, korte uitleg dat hier boeken en lokale hersteldata staan.
3. **Spelling** — gevonden Hunspell-woordenboeken tonen en eventueel spelling uit laten.
4. **AI** — standaard uit. Keuze: geen AI, lokale Ollama, of externe provider. Bij externe provider expliciet melden dat benodigde tekst/context de computer kan verlaten.

## UX-regels

- Geen tutorial-carrousel; de wizard configureert alleen basisinstellingen.
- Geen verplichte AI-configuratie.
- Geen netwerkverbinding noodzakelijk om de wizard af te ronden.
- `Vorige`, `Overslaan` en `Voltooien` zijn steeds duidelijk bereikbaar.
- Het hoofdvenster wordt pas na afronden/overslaan geopend; de splash blijft tijdens de technische start de feedback geven.

## Acceptatie voor 0.36

- Nieuwe instellingenmap → wizard verschijnt precies één keer.
- Bestaande `workspace` → direct normale start.
- Afbreken verandert geen bestaande werkmap.
- AI blijft uit als de gebruiker niets kiest.
- Taalkeuze wordt pas na herstart toegepast als dat technisch nog nodig is; dit wordt duidelijk vermeld.
