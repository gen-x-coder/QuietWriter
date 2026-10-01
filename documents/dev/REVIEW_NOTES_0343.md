# Claude review — QuietWriter 0.34.3

## Verplicht eerst
1. Draai `pytest` met echte PySide6: current volledig groen.
2. Draai `pytest tests/legacy`: alleen de twee bekende fontresource-failures toegestaan.
3. Koude start via `python main.py`.

## A. AI Planning-context bij onbetrouwbare Planning
Test met reeds geselecteerde Planning-context en daarna extern: (a) v1 structureel corrupt `outline.json`, (b) v2 `outline.json`, (c) v2 `characters.json`.
- AI-paneel blijft werken; samenvatting ververst zonder traceback.
- Contextknop meldt zichtbaar `Planning niet beschikbaar`/reden.
- Dialoog Planning-context opent zonder crash, toont reden en kan de bestaande selectie niet stil leegmaken.
- Een AI-vraag gaat door met lege Planning-context; andere vaste/manuscriptcontext blijft intact.
- Live Planning-bytes blijven identiek.

## B. History versus nieuwere Planning
Maak v1 + handmatige History-versie, vervang live outline of characters door v2 en kies `Deze versie herstellen`.
- Herstel wordt volledig geweigerd met `Werk QuietWriter bij`.
- Geen hoofdstuk, manifest, Planning, publicatie, AI- of assetbestand mag door die poging veranderen.
- Geen `pre_restore`-versie mag onnodig worden aangemaakt vóór de guard.
- Corrupte v1 Planning blijft via History wel expliciet herstelbaar zoals vóór 0.34.3.

## C. Visueel
- Ingeklapte rail in minimaal Helder, Nacht en Aurora: separator fysiek 2 px inhoud en merkbaar duidelijker dan 0.34.2, zonder zware balk te worden.
- Uitgeklapte rail: geen separators.
- `In dit hoofdstuk`: scènetitel, Doel/Conflict/Uitkomst/Notities en waarden beginnen visueel op dezelfde x-lijn.
- Status: exact `1 woord` bij enkelvoud, `0 woorden` en `2 woorden` bij meervoud.

## D. Regressie
Herhaal minimaal ronde 38 voor nieuwere Planning/Integriteit, ronde 36 hoofdstukcontext, railselectie, History-preview en transactionele adopt.

## Buiten scope
- Echte Dropbox timing.
- Echte Windows DPI.
- Nieuwe automatische Planning→AI-context; 0.34.3 hardent alleen de bestaande expliciete Planning-selectie.
