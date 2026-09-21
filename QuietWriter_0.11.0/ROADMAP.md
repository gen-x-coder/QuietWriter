# QuietWriter roadmap

## Afgerond

- Editorbasis: hoofdstukken/secties, drag-and-drop hoofdstukken, zoeken/vervangen en spellingscontrole.
- Versiegeschiedenis: dagarchief, handmatige versies, sterren, preview en herstel.
- AI-basis: modulaire providers, Ollama/OpenRouter, streaming chat, Markdown-output, persona en selectie/hoofdstuk/sectie/boek-context.
- Markdown import/export: volledige frontmatter, hoofdstukken, secties en round-trip.
- Scènebreuk invoegen als `***` via de rechter werkbalk.
- UI/UX polish: semantisch themesysteem, dynamische schrijftypografie, navigatierails, editor, scene-break-weergave, AI-chat, boekenplank en centrale pagina's.
- Informatiearchitectuur vereenvoudigd: één documentmodel voor boeken, korte verhalen en verhalenbundels. Losse stories-bibliotheek verwijderd.

## Volgende logische iteraties

### Technische UI-refactor
- `app.py` opsplitsen nu de look & feel en pagina-architectuur stabieler zijn.
- Logische modules per scherm/paneel: bookshelf, editor shell/manuscript tree, book details, settings, history, spell/search en main window.
- Gedeelde widgetcomponenten voor panel headers, kaarten, flyouts en knoppen waar dat onderhoud vereenvoudigt.
- Geen functionele wijzigingen tijdens deze refactor; bestaande tests behouden en waar mogelijk GUI-smoketests toevoegen.

### UI/UX polish 2
- Nieuwe pagina's voor Boekdetails en Instellingen op echte Windows/DPI-schermen nalopen.
- Spacing, boekkaart-afmetingen en responsive boekenplank finetunen op screenshots.
- Scene-break interactie verder uitwerken: structureel selecteren/verwijderen zonder de Markdownbron te veranderen.
- Extra typografieopties alleen toevoegen als ze daadwerkelijk schrijfcomfort verbeteren.

### AI-verfijning
- Alleen bewezen nuttige snelacties/promptknoppen toevoegen.
- OpenRouter uitgebreider testen.
- Geen RAG/bibliothecaris zolang de gewone schrijfchat de primaire stabiele workflow is.

### Extra exportformaten
- EPUB/PDF pas nadat inhoudsopgave, front/back matter en publicatie-opmaak zijn ontworpen.

### Release en robuustheid
- Windows executable/installer.
- Migraties tussen QuietWriter-versies.
- Logging/crash recovery.
- Meer integratie- en GUI-smoketests.
