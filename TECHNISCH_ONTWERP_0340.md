# Technisch ontwerp 0.34.0 — Planning tijdens schrijven

## Doel
Planning dichter bij het manuscript brengen zonder een tweede bron van waarheid te introduceren. De eerste slice toont uitsluitend bestaande, opgeslagen Planning-data voor het actieve hoofdstuk.

## Plaats
**In dit hoofdstuk** is een eigen rechterpaneel in dezelfde familie als Zoeken, AI, Spelling, Toevoegen en Versiegeschiedenis. Dit kost geen hoogte in de hoofdstukboom en hergebruikt het bestaande paneelgedrag.

## Bron en viewmodel
- `PlanningStore` blijft de enige persistente bron.
- `quietwriter.chapter_context.build_chapter_context()` is een pure builder van hoofdstuk-id + scènes + personages naar een alleen-lezen viewmodel.
- Geen kopieën in hoofdstukmetadata, geen nieuw bestandsformaat en geen writes vanuit het paneel.
- Alleen scènes met `scene.chapter_id == current_chapter.id` worden getoond.
- Personages worden uitsluitend afgeleid uit `scene.character_ids`; ontbrekende/verwijderde ids worden stil overgeslagen.

## Vastgelegde randgevallen
1. Het paneel toont de **opgeslagen** Planning. Niet-opgeslagen Planning-state wordt pas zichtbaar nadat die succesvol is opgeslagen.
2. Bij Voorwoord/Nawoord, publicatie-instellingen, geschiedenis-preview of geen actief hoofdstuk is de functie niet beschikbaar.
3. Bij een beschadigd hoofdstuk is de functie niet beschikbaar.
4. Corrupte `planning/outline.json` of `planning/characters.json` geeft een korte foutmelding; de manuscripteditor blijft volledig bruikbaar.
5. AI uit verandert niets: dit paneel hoort bij Planning.
6. `Planning openen` gebruikt de bestaande centrale `show_planning()`-route.
7. Centrale adoptie/hoofdstukwissel ververst de context; er is geen polling.

## Navigatiecorrecties die met 0.34.0 meekomen
- Alle linkerrailknoppen zitten in één `QButtonGroup`, ook wanneer hun widgets verschillende parents hebben (scrollgebied versus vast PROGRAMMA-blok).
- `_sync_nav_selection()` gebruikt één doelknop en `ensureWidgetVisible()` voor programmatic navigation.

## Expliciet niet in 0.34.0
- geen automatische personageherkenning;
- geen lokale aliasherkenning;
- geen AI-voorstellen;
- geen automatische uitbreiding van AI-prompts met Planning;
- geen Planning-integriteitsrepair.
