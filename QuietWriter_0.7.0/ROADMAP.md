# QuietWriter roadmap

## Iteratie 6 — Editorbasis

**Status: afgerond in 0.6.3.**

Opgeleverd:
- Zoeken en vervangen in hoofdstuk, sectie en volledig boek.
- Hoofdlettergevoelig en heel woord.
- Volgende treffer, vervangen en alles vervangen.
- Veilige drag-and-drop voor hoofdstukken met uitsluitend de zes-punts sleepgreep.
- Secties bewust niet versleepbaar; nieuwe secties kunnen relatief aan de selectie worden ingevoegd.
- Secties hernoemen en lege secties verwijderen.
- Hoofdstukken hernoemen, dupliceren en veilig verwijderen.
- Spellingsonderstreping plus een apart spellingscontrolepaneel.
- Negeren, alles negeren voor de sessie, blijvend negeren en toevoegen aan persoonlijk woordenboek.
- Automatische woordenboekdetectie bij ONLYOFFICE, LibreOffice en OpenOffice.
- Alle gevonden talen zichtbaar met leesbare locale-namen.
- Eigen Hunspell-woordenboeken toevoegen en weer verwijderen.
- Instellingen verdeeld over categorieën/tabs met uitleg en woordenboek-downloadlink.
- Nederlandse gedeelde UI-termen centraal in `nl.json`.
- Geautomatiseerde regressietests voor drag-and-drop, hoofdstukbeheer, woordenboeken en spellingsengine.

Bewust doorgeschoven:
- Interactieve suggesties direct in de tekst (hover/rechtsklik). De hoverimplementatie bleek te veel werk tijdens muisbewegingen te veroorzaken. Dit komt pas terug wanneer het zonder invloed op de schrijfervaring kan worden ontworpen.

## Iteratie 7 — Versiegeschiedenis

**Status: basis afgerond in 0.7.0.**

Opgeleverd:
- Dagarchieven zichtbaar in de rechter tijdlijn.
- Handmatige versies naast het automatische dagarchief.
- Datum/tijd, type versie, hoofdstukken en woordenaantal tonen.
- Oude versie alleen-lezen bekijken.
- Duidelijke previewbalk met herstellen/afsluiten.
- Oude versie herstellen; huidige toestand wordt eerst automatisch veiliggesteld.
- Best-effort rollback bij een mislukte herstelactie.
- Versies markeren met ster en filteren op ster.
- Bestaande 0.6.x dagarchieven blijven bruikbaar.

Later mogelijk:
- Visuele diff tussen twee versies.
- Eigen naam/notitie aan een handmatige versie geven.
- Herstelbare verwijdering van losse oude versies.

## Iteratie 8 — AI
- Markdown in AI-antwoorden renderen: koppen, vet, cursief, lijsten en codeblokken.
- Context zichtbaar maken: persona, selectie, hoofdstuk, sectie, boek en geraadpleegde verhalen.
- Snelle achtergrondmodel-laag voor classificatie, selectie en samenvattingen.
- Bibliotheek-RAG met tags, metadata, full-text en embeddings.
- Bronvermelding van geraadpleegde verhalen in AI-paneel.
- Prompt/contextbeheer voor grote boeken en verhalenbibliotheken.
- AI-gesprekken per boek eventueel bewaren.
- OpenRouter-provider naast Ollama.

## Iteratie 9 — Import & export
- QuietWriter-boek exporteren naar één Markdown-bestand met frontmatter.
- Secties/hoofdstukken naar Markdownkoppen vertalen.
- Afbeeldingspad uit instellingen meenemen.
- Markdown-import robuuster maken voor extra headervelden.
- Later eventueel DOCX/EPUB onderzoeken.

## Iteratie 10 — Bibliotheek en verhalen
- Verhalenbibliotheek verder uitbouwen.
- Tagbrowser en relaties tussen verhalen.
- Filters op tags, auteur, datum en metadata.
- AI-indexstatus en opnieuw indexeren vanuit UI.
- Stories direct omzetten naar bewerkbare boeken.

## Iteratie 11 — UI/UX en visuele afwerking
- Eigen Windows/applicatie-icoon.
- Typografie van editor en interface verfijnen.
- Schaduwen, hoverstates, subtiele animaties en paneelovergangen.
- Kaarten en boekenplank visueel verfijnen.
- Consistente SVG-iconenset.
- Thema's verder uitwerken en contrast controleren.
- Splashscreen verfijnen.
- Toetsenbordnavigatie en toegankelijkheid nalopen.
- Interactieve spellingssuggesties in de tekst opnieuw ontwerpen, alleen als dit zonder vertraging kan.
- `***` als echt scene-break-element weergeven (gecentreerde markering, selectie en verwijderen) terwijl Markdown-opslag `***` blijft.

## Iteratie 12 — Publicatie en robuustheid
- PyInstaller/Nuitka Windows-build.
- Migratie van instellingen en boekformaten tussen versies.
- Crash recovery en herstel van onafgemaakte autosaves.
- Logging en foutmeldingen voor eindgebruikers.
- Uitgebreide testset voor opslag, import, zoeken/vervangen, archieven en AI-context.
- Installer en automatische update-strategie onderzoeken.
