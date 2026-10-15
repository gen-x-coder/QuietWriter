# QuietWriter 1.5.0-dev.45 — Bewaren en Boekgeheugen

Op basis van dev.44.

- Bewaren tijdens generatie: melding om op het antwoord van de Meelezer te wachten.
- Bewaren zonder een gebruikersvraag: de bestaande melding wordt altijd getoond, ook als nog geen archiefobject bestaat.
- Bewaren zonder een open boek: expliciete melding.
- Na goedkeuring van een AI-geheugenvoorstel controleert QuietWriter het geschreven bestand `ai/memory.md` opnieuw; bevestiging van opslag komt alleen bij aantoonbaar aanwezige inhoud.
- Vijf talen bijgewerkt.

**Belangrijk:** een geheugenvoorstel wordt niet automatisch opgeslagen. De gebruiker moet op **Onthouden** (of in het bewerkingsscherm op **Onthouden**) klikken. Na succesvolle opslag volgt een melding in de chat. De chat zelf wordt niet automatisch tussen boeksessies bewaard; het Boekgeheugen wel.

## Handmatige Windows-check

1. Open een boek en klik direct op Bewaren zonder iets te vragen: een melding verschijnt.
2. Stel een vraag en klik terwijl de Meelezer antwoordt op Bewaren: wachtmelding verschijnt.
3. Na voltooiing: Bewaren opent de dialoog met Nederlandstalige knoppen.
4. Laat de Meelezer een geheugenvoorstel doen, klik op **Onthouden**. Controleer de bevestiging en het juiste onderdeel van Boekgeheugen. Sluit en heropen het boek om het resultaat opnieuw te controleren.

Geen Claude-review nodig voor deze kleine iteratie. PySide6 GUI-runtime kan niet worden uitgevoerd in deze Linux-omgeving.
