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

**Status: afgerond in 0.7.1.**

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
- Voor het verwijderen van een hoofdstuk wordt automatisch een herstelversie in de tijdlijn gemaakt.
- Hoofdstukverwijdering zit als contextactie in de rechter gereedschapsbalk, niet in de manuscriptboom.

Later mogelijk:
- Visuele diff tussen twee versies.
- Eigen naam/notitie aan een handmatige versie geven.
- Herstelbare verwijdering van losse oude versies.

## Iteratie 8 — AI

**Status: grotendeels afgerond in 0.8.0.**

Opgeleverd:
- Provider-onafhankelijke AI-architectuur.
- Ollama en OpenRouter als losse providers.
- Hoofdmodel los van snel lokaal achtergrondmodel.
- Markdown-rendering in de chat.
- Streaming met gebufferde UI-updates.
- Persona altijd actief.
- Context voor selectie, hoofdstuk, sectie, boek en verhalenbibliotheek.
- Context en geraadpleegde verhalen zichtbaar in de UI.
- Gesprekken per boek bewaren.
- Tags + metadata + full-text als lokale RAG-laag.
- Klein model als bibliothecaris met batchgewijze catalogusselectie.
- Optionele semantische retrieval met Ollama-embeddings en persistente cache.
- Bronnen/gebruikte verhalen bij het antwoord tonen.
- Contextlimieten voor grote manuscripten en verhalen.

Mogelijke vervolgstappen binnen AI:
- Contextbudget baseren op echte modeltokens in plaats van alleen tekens.
- UI voor AI-indexstatus en expliciet opnieuw indexeren.
- Chats hernoemen/meerdere gesprekken per boek.
- Promptprofielen zoals 'Redacteur', 'Herschrijven', 'Continuïteit' en 'Brainstorm'.
- OpenRouter API-key later veiliger opslaan via Windows Credential Manager.

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


## Stabiliteitsfix 0.7.2

- QSplitter zijpanelen robuust herstellen bij openen/sluiten.
- Hoofdstukregels volledig uitlijnen met sleepgreep rechts.
- Passieve rode spellinghints loskoppelen van de actieve spellingscontrole-workflow.
