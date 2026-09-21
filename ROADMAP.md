# QuietWriter roadmap

## Afgerond

- Editorbasis: hoofdstukken/secties, drag-and-drop hoofdstukken, zoeken/vervangen en spellingscontrole.
- Versiegeschiedenis: dagarchief, handmatige versies, sterren, preview en herstel.
- AI-basis: modulaire providers, Ollama/OpenRouter, streaming chat, Markdown-output, persona en selectie/hoofdstuk/sectie/boek-context.
- Markdown import/export: volledige frontmatter, hoofdstukken, secties en round-trip.
- Scènebreuk invoegen als `***` via de rechter werkbalk.
- UI/UX polish 1: semantisch themesysteem, Merriweather/Georgia, states, navigatie, editor, scènebreukweergave, AI-chat en micro-polish.

## Volgende logische iteraties

### Technische UI-refactor
- `app.py` opsplitsen nadat de nieuwe look & feel in de praktijk is goedgekeurd.
- Logische modules per scherm/paneel: bookshelf, editor shell/manuscript tree, settings, history, spell/search en dialogs.
- Gedeelde widgetcomponenten voor knoppen, panel headers en kaarten waar dat onderhoud echt vereenvoudigt.
- Geen functionele wijzigingen tijdens deze refactor; bestaande tests uitbreiden met GUI-smoketests waar mogelijk.

### UI/UX polish 2
- Nieuwe look & feel op echte Windows/DPI-schermen nalopen.
- Eventuele spacing/font-size correcties op basis van screenshots en gebruik.
- Scene-break interactie verder uitwerken (selecteren/verwijderen als structureel element) als dat prettig blijkt.
- Eventueel meer editorfonts aanbieden zonder fonts mee te distribueren.

### Verhalenbibliotheek
- Metadata van losse stories bekijken en bewerken.
- Tags/filtering verfijnen.
- Verhaal vanuit de bibliotheek omzetten/importeren naar een bewerkbaar QuietWriter-boek.
- Mogelijk bulkbeheer van metadata.

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
