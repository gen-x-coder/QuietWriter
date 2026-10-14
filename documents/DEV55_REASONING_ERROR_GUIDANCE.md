# Dev.55 — duidelijke melding bij verplichte OpenRouter-reasoning

Gebaseerd op de ongewijzigde requestlogica van dev.53, niet op de automatische herstelpoging van dev.54.

## Gedrag

- Instelling **Thinking: Uitgeschakeld** blijft een bewuste gebruikerskeuze.
- Wanneer OpenRouter meldt dat reasoning verplicht is, verschijnt de uitleg om **Instellingen → AI Meelezer → Thinking → Modelstandaard** te kiezen en opnieuw te proberen.
- QuietWriter schakelt thinking niet zelf om en verstuurt niet automatisch een tweede verzoek.
- Andere API-fouten blijven door de bestaande foutafhandeling lopen.
- De Nederlandse en vier overige UI-vertalingen bevatten deze melding.

## Regressie

Controleer op Windows dat dezelfde modelaanvraag met Thinking op Uitgeschakeld de begrijpelijke melding geeft, en met Modelstandaard werkt. De automatische herstelpoging van dev.54 is expliciet niet overgenomen.

De volgende projecten moeten de complete AI-geheugenworkflow verder testen; deze release corrigeert alleen de foutafhandeling.
