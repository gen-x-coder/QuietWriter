# dev.47 — OpenRouter-verbindingsmethode

De instellingen tonen bij OpenRouter één keuze: **Verbinden via browser** of **API-sleutel invoeren**. Alleen de gekozen instellingenrij is zichtbaar. De bestaande QuietWriter-instellingenopmaak blijft behouden.

De provider gebruikt uitsluitend de gekozen sleutelbron; geen stille terugval naar een andere methode als de actieve sleutel faalt. Een oude handmatige sleutel blijft behouden wanneer browserlogin slaagt. Het verbreken van browserlogin verwijdert alleen de lokaal veilig opgeslagen browsersleutel.

Voor bestaande installaties zonder opgeslagen keuze blijft de vroegere prioriteit gelden (browser indien opgeslagen, anders handmatig). Bij opslaan wordt de expliciete keuze vastgelegd.

Windows-test: wissel tussen beide keuzes, controleer zichtbaarheid, kies een ongeldige handmatige sleutel terwijl browserlogin bestaat, bevestig dat er niet via browser wordt teruggevallen; wissel terug en controleer het correcte antwoord. Test vervolgens Opslaan, afsluiten, opnieuw starten, Modellen ophalen, en Verbinding verbreken.
