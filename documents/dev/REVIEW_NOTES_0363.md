# Review notes 0.36.3

## Doel

Deze release maakt de AI-positionering releaseklaar: QuietWriter gebruikt AI als **Meelezer**, niet als schrijver of co-auteur.

## Gewijzigd

- `quietwriter/ai/quick_actions.py`
  - `rewrite_selection` volledig verwijderd.
  - Alleen Feedback, Persona-check en Feitencheck blijven over.
  - Feedbackprompts vragen om advies, niet om vervangende proza.
- `quietwriter/ai/prompting.py`
  - Basisrol gewijzigd naar meelees-assistent / kritische tweede lezer.
  - Expliciet contract: geen manuscripttekst schrijven of herschrijven, ook niet op verzoek.
  - Geen kant-en-klare vervangende passages.
- `quietwriter/ai/ui.py`
  - Nieuw gesprek kan bij openen een provider-warmup uitvoeren.
  - Tijdens warmup: `De meelees-assistent wordt geladen…`; invoer en snelacties zijn tijdelijk niet beschikbaar.
  - Warmup stuurt geen manuscripttekst. Persona, boekprofiel en boekgeheugen blijven onderdeel van de basiscontext.
  - Warmup-intro wordt als eerste assistant-bericht opgeslagen, maar de verborgen warmup-opdracht niet.
  - Warmup-output wordt niet als Boekgeheugenvoorstel geïnterpreteerd.
- `quietwriter/ui/editor_page.py`
  - Warmup start pas wanneer de gebruiker de Meelezer opent.
- `quietwriter/locales/nl.json` en `en.json`
  - Instellingen → AI Meelezer / AI Reader.
  - Editoractie Meelezer / Reader.
  - Paneeltitel Meelees-assistent / Reading assistant.
  - First-run, Schrijverspersona en AI-uitleg herschreven naar dezelfde productrol.
- `quietwriter/persona_profile.py`
  - Redactionele persona-uitleg niet langer gekoppeld aan herschrijven.
- `documents/ROADMAP.md`
  - 1.0 AI-productcontract vastgelegd; historische Herschrijf-selectie gemarkeerd als verwijderd in 0.36.3.

## Belangrijke ontwerpkeuzes voor review

1. **Geen automatische provider-call bij boek openen.** Warmup wordt alleen gestart als het Meelezer-paneel daadwerkelijk wordt geopend of de gebruiker `Nieuw gesprek` kiest.
2. **Geen manuscript in warmup.** Dit voorkomt dat enkel het openen van de Meelezer manuscripttekst naar een externe provider stuurt.
3. **Input blijft tijdens warmup uit.** Zodra modeloutput binnenkomt verdwijnt de laadmelding; na afronden van de stream wordt input weer actief.
4. **Anti-ghostwriting zit in gedrag én UI.** Niet alleen de knop is weg; het systeempromptcontract verbiedt vervangende manuscripttekst.

## Geautomatiseerde teststatus

- Current suite: 233 passed, 18 skipped.
- Legacy suite na contractupdate: 426 passed, 24 skipped, 284 subtests passed.
- De overgeslagen tests zijn Qt/runtime-afhankelijk in deze Linux-omgeving.

## Gericht door Claude te controleren

- Qt-runtime: opent een leeg nieuw gesprek zichtbaar met de laadmelding en is composer tijdelijk disabled?
- Verschijnt de gegenereerde intro exact één keer en wordt de verborgen warmup-opdracht nergens zichtbaar/opgeslagen?
- Blijft bestaand gesprek bij opnieuw openen intact zonder nieuwe warmup?
- `Nieuw gesprek` wist het oude gesprek en start precies één nieuwe warmup?
- Geeft provider/model niet beschikbaar geen onverwachte modal tijdens enkel het openen van het paneel?
- Staat nergens in de actuele gebruikersinterface nog een uitnodiging om AI manuscripttekst te laten schrijven/herschrijven?
- Controleer dat de warmup geen manuscripttekst of Planning-context meestuurt.
