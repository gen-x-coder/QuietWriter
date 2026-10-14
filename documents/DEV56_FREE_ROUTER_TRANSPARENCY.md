# dev.56 – OpenRouter Free transparantie

- In AI-instellingen verschijnt bij `openrouter/free` een korte toelichting dat OpenRouter voor ieder API-verzoek een gratis model kan kiezen.
- De Meelezer leest de daadwerkelijke modelidentificatie uit OpenRouter streaming-events en toont die onder het afzonderlijke antwoord.
- Als de API geen model terugmeldt wordt geen modelnaam ingevuld. Bij verschillende modelmeldingen in één antwoord geldt de laatste gemelde naam.
- De modelnaam wordt alleen bij een voltooid antwoord opgenomen in de lokale gespreksgegevens, zodat ook expliciet bewaarde gesprekken hun herkomst behouden.
- Standaardinstellingen, reasoningfoutmeldingen van dev.55 en Boekgeheugen zijn niet gewijzigd.
- Test: `openrouter/free`, meerdere berichten, andere modellen vergelijken; een vast OpenRouter-model; annuleren; na opslaan gesprek opnieuw openen.
