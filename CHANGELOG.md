# QuietWriter 0.10.0

## UI/UX polish

- Nieuw centraal semantisch designsysteem voor alle zes thema's. Hardcoded UI-kleuren in onder meer versiegeschiedenis en fallback-boekomslagen zijn verwijderd.
- Merriweather is nu het standaard schrijflettertype met Georgia als automatische fallback. In Instellingen > Uiterlijk kan tussen Merriweather en Georgia worden gekozen.
- Schrijftekst gebruikt een lichte font weight (300/Light) waar het platform/font dat ondersteunt.
- Primaire, secundaire en gevaarlijke acties hebben nu een duidelijke visuele hiërarchie.
- Focus-, hover-, pressed-, selected- en disabled-states zijn consistent gemaakt.
- Actieve navigatieknoppen krijgen een subtiele accentlijn; iconen en tooltips zijn consistenter gemaakt.
- De navigatierail klapt nu met een korte, rustige animatie in en uit.
- Splitter-hitboxes zijn groter zonder een dikke zichtbare scheidingsbalk te introduceren.
- Hoofdstuk drag-handles tonen een open hand en tijdens slepen een gesloten hand.
- Manuscriptsecties zijn visueel rustiger en duidelijker ondergeschikt aan hoofdstukken.
- Boekenkaarten hebben een lichte slagschaduw; primaire kaartacties zijn duidelijker.
- De editor toont bovenin een subtiele opslagstatus en onderin hoofdstukpositie + woordenaantal.
- `***`-regels worden in de editor als gecentreerde, rustige scènebreuk weergegeven, terwijl het Markdown-bestand ongewijzigd `***` blijft bevatten.
- AI-chat heeft een rustigere, moderne kaartweergave en een compacte compose-regel met geïntegreerde verzend/stop-knop.
- Instellingen-tabbladen, menu's, scrollbars en dialoogknoppen zijn visueel op hetzelfde designsysteem gebracht.
- Application/window icon gebruikt nu de bestaande rustige boek-SVG.

## Techniek

- De grote UI-structuur in `app.py` is bewust nog niet opgesplitst. Eerst is de look & feel gestabiliseerd; technische refactoring volgt als aparte iteratie.
- Bestaande functionaliteit en opslagformaten zijn ongewijzigd.
