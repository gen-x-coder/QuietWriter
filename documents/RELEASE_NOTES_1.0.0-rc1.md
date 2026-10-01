# QuietWriter 1.0.0-rc1

Dit is de eerste release candidate van QuietWriter voor een kleine testgroep. De functieset is vanaf deze versie bevroren: tot de definitieve 1.0.0 worden alleen regressies en releaseblokkades opgelost.

## Wat deze RC bevat

- Een portable Windows-build met first-run wizard, Nederlands/Engels, gescheiden DEV/PROD-profielen en een schone releaseflow met smoketest.
- Een schrijfomgeving met globale editorweergave, spelling, history/herstel, boek- en hoofdstukbeheer en export.
- **AI Meelezer** als optionele tweede lezer voor feedback, persona-/stijlcontrole, feiten, continuïteit en consistentie. De Meelezer is niet bedoeld als co-auteur of herschrijver.
- Ollama voor lokaal gebruik en OpenRouter als externe provider. Bij OpenRouter verstuurt alleen een bewuste vraag tekst/context; het openen van de Meelezer doet geen warmup-request.
- OpenRouter-modelkeuze met gratis-markering en een filter voor gratis modellen.
- Globale tekstbreedte **Extra smal / Smal / Normaal / Breed / Extra breed**. Dit verandert alleen de editorweergave, nooit manuscript of export.

## Bekende beperking

- Als **Alleen gratis modellen tonen** aanstaat terwijl vóór het filter een betaald OpenRouter-model was opgeslagen, kan de keuzelijst een gratis model tonen terwijl het betaalde model bewaard blijft totdat je bewust een ander model kiest. Er gaat geen instelling verloren, maar wat zichtbaar is kan in dat ene scenario afwijken van het bewaarde model. Dit is niet releaseblokkerend en staat gepland voor na de RC.

## Nog te valideren tijdens de RC

Deze punten zijn bewust onderdeel van de praktijktest en zijn nog geen afgeronde 1.0-garantie:

- starten van de uitgepakte portable ZIP op een schone Windows-pc zonder Python;
- SmartScreen-flow op een machine waarop QuietWriter nog niet eerder is gestart;
- weergave op 150% Windows-schaal en waar mogelijk meerdere DPI-instellingen;
- een echte koude Ollama-start van de Meelezer;
- dagelijks schrijven gedurende 2–3 weken zonder data-incident;
- grote-boektest en de resterende Windows-praktijkmatrix uit `PLAN_1_0.md`.

## Testen en back-up

Pak de ZIP volledig uit voordat je QuietWriter start. Maak tijdens de RC-periode regelmatig een kopie van de volledige QuietWriter-werkmap. Bij een fout kun je via de foutmelding **Logbestand openen** gebruiken; het crashlog staat normaal onder `%LOCALAPPDATA%\QuietWriter\QuietWriter\logs\crash.log`.

Feedback uit deze RC wordt verwerkt voordat `1.0.0` als definitieve eerste publieke versie wordt uitgebracht.
