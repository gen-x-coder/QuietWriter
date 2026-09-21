# QuietWriter roadmap

Deze roadmap groepeert open werk in herkenbare iteraties. Daardoor kan later eenvoudig worden verwezen naar bijvoorbeeld **AI-iteratie** of **Versiegeschiedenis-iteratie**.

## Iteratie 6 — Editorbasis

Status: grotendeels uitgevoerd in 0.6.0.

- Zoeken en vervangen in huidig hoofdstuk, huidige sectie en hele boek.
- Opties voor hoofdlettergevoelig en heel woord.
- Volgende treffer, één vervangen en alles vervangen.
- Drag-and-drop voor hoofdstukken; hoofdstukken kunnen binnen en tussen secties worden verplaatst.
- Eerste bruikbare spellingscontrole met rode onderstreping en rechterpaneel.
- Nederlands taalbestand voor gedeelde UI-termen zoals Ja/Nee/Opslaan/Annuleren.

Nog af te maken binnen deze lijn:
- robuuster woordenboekbeheer: downloaden, toevoegen en verwijderen vanuit Instellingen;
- Hunspell `.aff`-regels gebruiken in plaats van alleen woorden uit `.dic`;
- spellingssuggesties ook via rechtermuisknop/hover in de editor;
- drag-and-drop van secties zelf;
- contextmenu voor hoofdstukken en secties: hernoemen, verwijderen, dupliceren en verplaatsen.

## Iteratie 7 — Versiegeschiedenis

- Dagarchieven zichtbaar maken in de UI.
- Overzicht met datum/tijd en woordenaantal.
- Oude versie alleen-lezen bekijken.
- Oude versie herstellen.
- Huidige versie eerst automatisch veiligstellen vóór herstel.
- Eventueel verschilweergave tussen twee versies.

## Iteratie 8 — AI

- Markdown in AI-antwoorden netjes renderen: koppen, vet, cursief, lijsten en codeblokken.
- Context zichtbaar maken: persona, hoofdstuk, sectie, boek en geraadpleegde oude verhalen.
- Selectie expliciet als AI-context kunnen gebruiken.
- Snelle achtergrondmodel-laag voor classificatie, selectie en samenvattingen.
- Bibliotheek-RAG met tags, metadata, full-text en embeddings.
- Bronvermelding van geraadpleegde verhalen in AI-paneel.
- Prompt/contextbeheer verbeteren voor grote boeken en verhalenbibliotheken.
- AI-gesprekken per boek eventueel kunnen bewaren.
- OpenRouter-provider naast Ollama.

## Iteratie 9 — Import & export

- QuietWriter-boek exporteren naar één Markdown-bestand met frontmatter.
- Secties/hoofdstukken correct terugvertalen naar Markdownkoppen.
- Afbeeldingspad uit instellingen meenemen in metadata.
- Bestaande Markdown-import verder robuust maken voor aanvullende headervelden.
- Later eventueel DOCX/EPUB-import en -export onderzoeken.

## Iteratie 10 — Bibliotheek en verhalen

- Verhalenbibliotheek verder uitbouwen als echte referentiebibliotheek.
- Tagbrowser en relaties tussen verhalen.
- Filters op tags, auteur, datum en andere metadata.
- AI-indexstatus en opnieuw indexeren vanuit UI.
- Eventueel verhalen vanuit `stories/` direct omzetten naar bewerkbare boeken.

## Iteratie 11 — UI/UX en visuele afwerking

Bewust later, zodat gedrag en schermstructuur eerst stabiel zijn.

- Eigen Windows/applicatie-icoon.
- Typografie van editor en interface verfijnen.
- Schaduwen, hoverstates, subtiele animaties en paneelovergangen.
- Kaarten en boekenplank visueel verfijnen.
- Consistente SVG-iconenset.
- Thema's verder uitwerken en contrast controleren.
- Splashscreen verfijnen.
- Toetsenbordnavigatie en toegankelijkheid nalopen.

## Iteratie 12 — Publicatie en robuustheid

- PyInstaller/Nuitka Windows-build.
- Migratie van instellingen en boekformaten tussen versies.
- Crash recovery en herstel van onafgemaakte autosaves.
- Logging en foutmeldingen voor eindgebruikers.
- Testset voor opslag, import, zoeken/vervangen, archieven en AI-context.
- Installer en automatische update-strategie onderzoeken.
