# QuietWriter 1.5.0-dev.48 — OpenRouter instellingen

- Het Ollama-adres wordt alleen getoond bij provider Ollama.
- De status van browserautorisatie staat rechts van de verbindingsknoppen.
- Status: grijs = geen lokaal bewaarde browsersleutel; oranje = controle bezig; groen = OpenRouter heeft de sleutel geaccepteerd; rood = verificatie mislukt.
- Bij het openen van de instellingen wordt een eventueel opgeslagen browsersleutel op een achtergrondthread via OpenRouter gecontroleerd. De Qt-interface blijft bruikbaar.
- Gedetailleerde toelichting of fout staat als tooltip op de status.
- De geselecteerde browser/API-methode uit dev.47 blijft ongewijzigd; er vindt geen automatische fallback plaats.

Controle: negen gerichte OpenRouter-tests geslaagd. Visuele Qt-test op Windows nog vereist.
