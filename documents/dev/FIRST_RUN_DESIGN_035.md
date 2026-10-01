# QuietWriter 0.35 — ontwerp first run

De first-run wizard wordt in 0.36 gebouwd. 0.35 legt alleen het contract vast zodat de releasefundering niet tegelijk een nieuwe workflow introduceert.

## Trigger

- Gebruik een eigen instelling `first_run_done`; `workspace` is **geen** betrouwbare first-run-indicator.
- Bij de eerste start van een versie met de wizard: zet `first_run_done=True` zonder wizard als er al bestaande QuietWriter-instellingen zijn, of als de standaardwerkmap al bestaat.
- Alleen een werkelijk nieuwe installatie zonder bestaande QuietWriter-state én zonder bestaande standaardwerkmap krijgt de wizard.
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
- `first_run_done=True` → direct normale start.
- Bestaande QuietWriter-state maar nog geen `first_run_done` → markeer als bestaande gebruiker en start normaal.
- Geen bestaande state → toon de wizard en zet `first_run_done=True` zodra deze is afgerond of bewust overgeslagen.
- Afbreken verandert geen bestaande werkmap.
- AI blijft uit als de gebruiker niets kiest.
- Taalkeuze wordt pas na herstart toegepast als dat technisch nog nodig is; dit wordt duidelijk vermeld.
