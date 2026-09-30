# Reviewnotes 0.34.7 — hoofdstukplanning expliciet naar AI

## Verplicht eerst
1. Draai `pytest` met echte PySide6. Verwacht alle current-tests groen.
2. Draai `pytest tests/legacy`; alleen de twee bekende fonttests mogen falen.
3. Koude start via `python main.py`.

## Runtime: exacte AI-context
Maak één hoofdstuk met unieke Planning-markeringen, bijvoorbeeld `AUTO_SYNOPSIS_0347` en `AUTO_DOEL_0347`.

- Boek openen → AI → Context: **Planning van dit hoofdstuk gebruiken** is actief en standaard aangevinkt wanneer opgeslagen scènes bestaan.
- Samenvatting zegt `wordt meegestuurd`.
- **Context bekijken** toont exact de opgeslagen hoofdstukplanning.
- Onderschep met nep-provider de systeemprompt: unieke automatische markeringen staan onder `PLANNING VAN HET HUIDIGE HOOFDSTUK`.
- Zet de checkbox uit en verstuur opnieuw: geen automatische markering in de systeemprompt; samenvatting zegt `niet meegestuurd`.
- Een handmatig geselecteerde scène/personage via **Planning-context…** blijft in beide gevallen onder `GESELECTEERDE PLANNINGCONTEXT` aanwezig.

## Failsafe
- Geen gekoppelde scènes: checkbox disabled, AI-vraag gaat normaal door.
- Kapotte v1 Planning: checkbox disabled, reden zichtbaar, AI gaat zonder hoofdstukplanning door.
- Nieuwere v2 Planning: idem, bytes blijven identiek.
- Wissel hoofdstuk: preview, labels en meegestuurde tekst volgen het nieuwe actieve hoofdstuk.
- Boekenplank: Planning-contextknop en hoofdstukplanningcheckbox intern uit.

## Persistente voorkeur
- Checkbox uit → nieuw hoofdstuk / paneel dicht-open / app herstart: voorkeur blijft uit.
- Checkbox weer aan → herstart: voorkeur blijft aan.
- Tijdelijk onbeschikbare Planning mag de opgeslagen voorkeur niet overschrijven.

## Geen writes
Alle `planning/`-bestanden byte-identiek na preview, toggle en AI-vragen.
