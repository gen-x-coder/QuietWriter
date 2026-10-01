# Review notes 0.36.4

Gerichte follow-up op Claude review 52.

## Te controleren

1. **Werkmapveiligheid**
   - First-run: typ handmatig `mijnboeken`; na afronden moet de opgeslagen werkmap onder de gebruikersmap staan, nooit naast `QuietWriter.exe`.
   - Instellingen: hetzelfde gedrag bij handmatig relatieve invoer.
   - Een absoluut gekozen pad via de mapkiezer moet exact behouden blijven.

2. **OpenRouter-warmup**
   - Nieuw gesprek/Open Reader toont direct de lokale welkomsttekst.
   - Bij alleen openen mag geen HTTP-call naar OpenRouter plaatsvinden.
   - Persona, boekprofiel, boekgeheugen en manuscript mogen bij alleen openen niet worden verstuurd.
   - Pas bij een echte vraag mag context naar OpenRouter.

3. **Ollama-warmup**
   - Openen van Meelezer blokkeert de Qt-thread niet.
   - Loadingtekst verschijnt direct.
   - Warmup-request draait in ProviderChatWorker.
   - Bij onbereikbaar Ollama valt de warmup terug op de lokale welkomsttekst en blijft de UI bruikbaar.

4. **Windows smoke**
   - `QuietWriter.exe --smoke-test` moet zonder first-runinteractie de volledige startup tot MainWindow uitvoeren en daarna met exitcode 0 afsluiten.
   - Startupfouten moeten een niet-nul exitcode opleveren.

5. **Portable release**
   - `LEESMIJ.txt` moet in de root van de portable map/ZIP staan.
   - `documents/dev` mag niet in de release voorkomen.
