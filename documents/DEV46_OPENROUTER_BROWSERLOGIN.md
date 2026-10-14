# QuietWriter 1.5.0 – dev.46: OpenRouter-browserkoppeling

- Nieuw: verbinden met OpenRouter via de officiële PKCE-browserflow vanuit Instellingen > AI Meelezer.
- Windows Credential Manager bewaart de ontvangen API-sleutel; deze wordt niet getoond of in QSettings gekopieerd.
- De bestaande handmatige API-sleutel blijft beschikbaar als alternatief. Als er een browsersleutel aanwezig is, krijgt deze voorrang.
- Modellen ophalen en de AI Meelezer gebruiken beide dezelfde providerfactory en daarmee dezelfde sleutel.
- Verbinding verbreken verwijdert uitsluitend de lokale browsersleutel. De externe sleutel moet desgewenst apart worden ingetrokken bij OpenRouter.
- Instellingen herstellen verwijdert de lokale browsersleutel waar mogelijk.
- Autorisatie verloopt in een achtergrondthread zodat het instellingenvenster niet blokkeert.
- De browserflow controleert de `state`-waarde en de ontvangen sleutel voordat die wordt opgeslagen.
- `keyring` toegevoegd aan requirements, Windows-backends aan PyInstaller-hiddenimports.

## Testen op Windows

1. Installeer bijgewerkte dependencies met `python -m pip install -r requirements.txt` in de bestaande venv.
2. Open AI Meelezer-instellingen, kies OpenRouter, klik Verbinden met OpenRouter.
3. Autoriseer via browser; controleer dat QuietWriter de verbinding bevestigt.
4. Haal modellen op, selecteer een model, sla de instellingen op en test één Meelezer-bericht.
5. Sluit QuietWriter, open opnieuw en test een nieuw bericht zonder inloggen.
6. Gebruik Verbinding verbreken; controleer dat opnieuw inloggen nodig is (tenzij er nog een handmatige sleutel ingevuld is).
7. Trek eventueel ongebruikte sleutels in via https://openrouter.ai/settings/keys.

## Grenzen

De browserflow is getest als afzonderlijk Windows-programma. De Qt-integratie is in deze build nog niet interactief op Windows getest. Geen wijzigingen aangebracht aan streaming, geheugen of bestaande chatfunctionaliteit.
