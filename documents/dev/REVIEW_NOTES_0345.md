# Reviewnotes 0.34.5 — ronde 41

0.34.5 is een kleine correctie-/UX-build bovenop de groene 0.34.4-basis.

## Verplicht eerst
1. Draai `pytest` met echte PySide6.
2. Draai `pytest tests/legacy`; alleen de twee bekende fontresource-tests mogen falen.
3. Koude start via `python main.py`.

## A. Planning-contextknop via echte route
- Nieuw venster, AI aan, boek nog niet open: **Planning-context…** uit.
- Open een boek via `MainWindow.open_book`/de echte boekenplankroute.
- Open het AI-paneel: **Planning-context… moet direct actief zijn**.
- Klik de knop; de dialoog moet echt openen en bestaande Planning-opties tonen.
- Herhaal na hoofdstukwissel, AI-paneel dicht/open en Nieuw gesprek. De knop mag niet opnieuw permanent grijs worden.

## B. Foutstatus Planning-context
Test met v1-structuurfout en v2 Planning:
- contextknop: `Context · Planning niet beschikbaar`;
- tooltip/dialoog bevat één keer de reden, dus geen `Planning-context niet beschikbaar: Planning-context niet beschikbaar`;
- AI-vraag gaat zonder Planning-context door; selectie blijft behouden.

## C. Context bekijken
- Geselecteerde Planning-context én hoofdstukpreview met meerdere velden.
- Binnen één scène/personage staan `- Doel`, `- Conflict`, `- Uitkomst`, enz. direct onder elkaar zonder lege regel tussen iedere veldregel.
- Tussen secties/scènes mag wel lucht blijven.
- Verifieer met nep-provider dat de hoofdstukpreview nog steeds niet automatisch in `send()` terechtkomt.

## D. Divider vóór PROGRAMMA
Rail ingeklapt, boek open, AI en Geavanceerd aan:
- ruim venster (bijv. 1280×1000) waarbij de middenrail niet scrollt: **geen extra divider vóór PROGRAMMA**;
- laag venster (bijv. 1280×520/700, afhankelijk van platform) waarbij middenrail overflow heeft: divider vóór PROGRAMMA zichtbaar;
- HUIDIG BOEK/AI-CONTEXT-separators blijven correct;
- uitgeklapte rail: geen separators, groepskoppen nemen over.
Meet dit ook kort in Helder en Nacht.

## E. Regressie
- 0.34.4 transparantie: hoofdstukplanning blijft preview-only.
- 0.34.3 History/AI failsafe.
- railselectie precies één actieve knop.
- statusbalk enkelvoud/meervoud.
- Planning corrupt/nieuwer/BOM-matrix.

## Niet gewijzigd
- Geen automatische hoofdstukplanning in AI-prompts.
- Geen Planning-schemawijziging.
