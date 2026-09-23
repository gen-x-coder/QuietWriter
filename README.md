# QuietWriter

QuietWriter is een lokale Python/PySide6-schrijfomgeving met boeken, secties, hoofdstukken, Markdown-opslag, versiegeschiedenis, spellingscontrole en een modulaire AI-assistent.


## Schrijfopmaak

QuietWriter bewaart hoofdstukken als leesbare Markdown, maar toont tijdens het schrijven een rustige manuscriptweergave. Selecteer tekst en wacht ongeveer één seconde om de compacte opmaakbalk te openen. Beschikbaar zijn onder meer vet, cursief, onderstrepen, doorhalen, tussenkoppen, lijsten en citaten.

Een scènebreuk blijft op schijf `***`, maar wordt in de editor als een subtiele horizontale scheiding weergegeven. In Instellingen > Uiterlijk zijn regelafstand, alinea-inspringing, alinearuimte en slimme aanhalingstekens afzonderlijk instelbaar.

## Eén documentmodel

QuietWriter gebruikt één eenvoudig model: alles wat je schrijft is een **boek**. Dat kan een roman zijn, een kort verhaal met één hoofdstuk of een verhalenbundel met secties en meerdere hoofdstukken. Een aparte verhalenbibliotheek bestaat niet meer.

Bestaande `.md`-verhalen open je via **Boekenplank → Importeren…**. QuietWriter maakt daar een normaal bewerkbaar boek van, zonder het bronbestand te wijzigen.

## Navigatie

Wanneer geen boek geopend is, is de Boekenplank het centrale startpunt. Na openen van een boek worden **Inhoud**, **Planning**, **Boekdetails** en **Exporteren** beschikbaar.

Globale functies staan onderaan de linkernavigatie:

- Schrijverspersona
- Instellingen
- Prullenbak

Boekdetails, Exporteren en Instellingen zijn centrale pagina's in de applicatie en geen losse popupvensters meer. Instellingen hebben een eigen linker categorienavigatie voor Algemeen, Uiterlijk, Opslag, AI en Spelling, met Over direct aansluitend onder Spelling. De rechter gereedschapsrail is uitsluitend bedoeld voor gereedschappen rond de huidige tekst, zoals Zoeken, AI, Spellingscontrole, Toevoegen en Versiegeschiedenis.

## Boekenplank

De boekenplank gebruikt een responsive raster: QuietWriter berekent hoeveel boekkaarten naast elkaar passen op basis van de beschikbare vensterbreedte. Een boek open je met **Openen**; metadata en omslag beheer je daarna via **Boekdetails**.

## Uiterlijk en typografie

Onder **Instellingen → Uiterlijk** toont QuietWriter eerst vier aanbevolen schrijftypografieën — Merriweather, Literata, Source Serif 4 en EB Garamond — en daarna de overige beschikbare systeemfonts. Meegeleverde fonts worden alleen binnen QuietWriter geregistreerd en niet in Windows geïnstalleerd. De tekstgrootte blijft een volledig onafhankelijke instelling.

De fontbronnen en SIL Open Font License 1.1-teksten staan onder `resources/fonts/`. In een source checkout kunnen de geverifieerde fontbinaries vóór starten/packagen worden opgehaald met `py tools/fetch_bundled_fonts.py`; een uiteindelijke distributiebundle bevat deze bestanden rechtstreeks.

Onder **Instellingen → Over** staan de QuietWriter-versie, een korte productintro, informatie over lokale opslag/privacy, copyright, een benoemde sectie **Technische omgeving** en de licentieteksten van de meegeleverde schrijftypografie.

Bij het starten blijft een themagekoppeld splashscherm zichtbaar totdat het hoofdvenster daadwerkelijk gereed en zichtbaar is. Het toont één duidelijke appnaam, tagline, versie/copyright en de actuele opstartfase; er is geen kunstmatige wachttijd.

De linker inhoudsstructuur kan worden getoond/verbergen met het kleine tabje aan de linkerrand van de schrijfruimte. De rechter gereedschapsrail kan zelf worden uitgevouwen om tekstlabels naast de iconen te tonen.

## Starten

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py main.py
```

## Markdown import

Op de boekenplank kies je **Importeren…** en selecteer je een `.md`-bestand. QuietWriter leest frontmatter zoals `title`, `date`, `slug`, `description`, `intro`, `meta`, `image`, `image_alt`, `author`, `tags`, `published` en `synopsis`. Onbekende velden worden bewaard.

Een top-level kop wordt een hoofdstuk:

```markdown
# Hoofdstuk 1
Tekst...

# Hoofdstuk 2
Tekst...
```

Zonder `#`-kop wordt het hele bestand één hoofdstuk.

## Exporteren

Open een boek en kies **Exporteren** in de linkernavigatie. QuietWriter bouwt eerst één consistente momentopname van het opgeslagen manuscript en de ingestelde publicatiestructuur.

### EPUB 3

EPUB-export gebruikt geen extra e-booklibrary. QuietWriter maakt met de Python-standaardbibliotheek een EPUB 3-container met XHTML, CSS, metadata, navigatie en manifest/spine. Beschikbaar zijn de templates **Klassiek**, **Modern** en **Literair**.

Een eigen boekomslag kan op twee manieren worden gebruikt: als tekstloos artwork waarop QuietWriter automatisch titel en auteur plaatst, of als volledig ontworpen omslag die al tekst bevat. Nieuwe/vervangen omslagen worden vanaf 0.20.0 in de boekmap onder `assets/cover/` opgeslagen; bestaande globale omslagen blijven als legacy fallback werken.

### Afbeeldingen in het manuscript

Via **Toevoegen → Afbeelding** voeg je JPG/JPEG of PNG toe op de cursorpositie. QuietWriter kopieert het bronbestand pas na **Invoegen** naar `assets/images/` van het geopende boek, geeft het een UUID-bestandsnaam en bewaart integriteitsmetadata in `assets/manifest.json`. Alt-tekst is bedoeld voor toegankelijkheid; een onderschrift is optioneel. Op schijf blijft de verwijzing gewone Markdown.

Afbeeldingen zijn immutable assets: verwijderen uit de tekst verwijdert alleen de Markdown-verwijzing, niet meteen het bestand. Daardoor blijven historische versies herstelbaar. EPUB-export neemt gebruikte afbeeldingen mee in `EPUB/images/`, schrijft ze in het EPUB-manifest en rendert een semantische `figure` met alt-tekst en eventueel `figcaption`. Ontbrekende of buiten QuietWriter gewijzigde assets blokkeren EPUB-export in de preflight.

### Markdown

Markdown op **Exporteren** gebruikt het vaste publicatieformaat uit bestaande workflows. De header tussen `---` is verplicht en heeft altijd dezelfde volgorde: `title`, `date`, `slug`, `description`, `meta`, `intro`, `author`, `tags`. Bij één los verhaal waarvan hoofdstuk- en boektitel gelijk zijn begint de tekst direct na de header, zonder extra `#`-kop. Meerhoofdstukboeken behouden hoofdstukkoppen en onzichtbare sectiemarkeringen om structuur te bewaren.

In 0.20.0 wordt Markdown-export bewust geblokkeerd wanneer het manuscript inline afbeeldingen bevat. 0.20.3 voegt hiervoor een portable `<slug>-assets/` companionmap en link-rewriting toe; QuietWriter exporteert dus niet tijdelijk een `.md` met kapotte projectinterne paden.

De rijkere Markdown import/round-triplaag blijft hiervan losstaan en kan extra QuietWriter-metadata bewaren.

### PDF

PDF is bewust nog niet actief. QuietWriter onderzoekt eerst of nette vaste pagina-opmaak met de bestaande PySide6-stack haalbaar is; er wordt geen zware library of extra Windows-component toegevoegd alleen om PDF te kunnen maken.

## Scènebreuk

Gebruik de **+** knop in de rechter werkbalk en kies **Scènebreuk**. Op schijf blijft dat gewone Markdown:

```markdown
***
```
## Veilige externe wijzigingen

QuietWriter gebruikt geen `.lock`-bestanden en bevat geen Dropbox-specifieke synchronisatielaag. In plaats daarvan bewaakt de storage-laag de inhoudsrevision van ieder geopend boek. Vóór een schrijfactie worden `book.json`, hoofdstuk-/planning-/publicatiebestanden en het kleine `assets/manifest.json` opnieuw met SHA-256 gecontroleerd. Zware immutable afbeeldingsbinaries worden pas bij gebruik/export tegen hun opgeslagen SHA-256 gecontroleerd.

Als een bestand sinds het openen buiten QuietWriter is gewijzigd, wordt niet opgeslagen. Autosave pauzeert en de gebruiker kiest tussen **Mijn versie gebruiken** en **Versie op schijf gebruiken**. Voor beide keuzes maakt QuietWriter eerst automatisch een herstelversie in de bestaande versiegeschiedenis. Daardoor kan een wijziging door Dropbox, OneDrive, Git, een tweede QuietWriter-proces of een andere editor niet ongemerkt worden overschreven.

Deze beveiliging is bewust generiek: er worden geen lockfiles achtergelaten en er is geen centrale syncservice nodig. Een theoretische gelijktijdige write op twee nog niet gesynchroniseerde computers blijft zonder centrale coördinatie mogelijk; syncsoftware kan in dat geval zelf een conflicted copy maken.

Bij een onverwachte harde crash schrijft QuietWriter diagnostiek naar `logs/crash.log` onder de ingestelde werkmap. Dit log bevat naast onverwerkte Python-exceptions ook `faulthandler`-informatie bij native/fatale crashes en is bedoeld om Qt/Windows-problemen reproduceerbaar te kunnen onderzoeken.

## Boekplanning en ideeën

Wanneer een boek geopend is, verschijnt **Planning** in de linker hoofdrail. Deze modus is optioneel en staat los van de manuscripttekst.

- **Personages** bevat vaste, gestructureerde velden voor rol, beschrijving, persoonlijkheid, motivatie, doelen, angsten, waarden, conflicten, achtergrond, stem/spreekwijze en gedrag onder druk. Relaties gebruiken stabiele personage-ID's.
- **Outline** toont scènes onder de bestaande hoofdstukken plus een sectie **Losse ideeën**. Scènes kunnen worden gekoppeld aan personages en bevatten onder meer synopsis, locatie, doel, conflict, uitkomst en status.
- **Notities** is één vrije Markdownpagina per boek en gebruikt dezelfde rustige schrijfeditor.

De planning wordt opgeslagen in een aparte `planning/`-map binnen het boek. Deze bestanden vallen onder dezelfde externe-wijzigingsbeveiliging en versiegeschiedenis als het manuscript.

## Publicatiestructuur

Via **Inhoud → + Toevoegen → Publicatiestructuur** kies je welke onderdelen vóór en na het manuscript bij het uiteindelijke boek horen. Geselecteerde onderdelen verschijnen in dezelfde inhoudsboom als **Voorwerk** en **Achterwerk**.

QuietWriter maakt daarbij bewust onderscheid tussen:

- **vrije tekst** zoals Opdracht, Voorwoord, Nawoord en Dankwoord;
- **gestructureerde onderdelen** zoals Titelpagina, Copyright en Epigraaf;
- **gegenereerde onderdelen** zoals de Inhoudsopgave.

De copyrightpagina bevat onder meer editie, jaar, uitgever/imprint, ISBNs per formaat en optionele bewerkbare clausules. De inhoudsopgave wordt uit de actuele hoofdstukstructuur opgebouwd en kan optioneel tussenkoppen meenemen.

Publicatiegegevens staan in een aparte `publication/`-map binnen het boek en vallen onder dezelfde externe-wijzigingsbeveiliging en versiegeschiedenis als manuscript en planning. PDF/EPUB en boektemplates zijn bewust een latere stap: de inhoudsstructuur is nu onafhankelijk van de uiteindelijke vormgeving.

## Code-architectuur

Sinds 0.12.1 is de UI niet meer geconcentreerd in één groot `app.py`-bestand. `app.py` bevat alleen de applicatiebootstrap. Media-opslag en Markdown-imageparsing staan vanaf 0.20.0 apart onder `quietwriter/media/` (`models.py`, `store.py`, `markup.py`), zodat editor en exporters niet zelf met assetpaden hoeven te werken. De Qt-interface staat onder `quietwriter/ui/` en is per verantwoordelijkheid opgesplitst:

```text
quietwriter/ui/
├── main_window.py
├── bookshelf.py
├── editor_page.py
├── manuscript_editor.py
├── manuscript_tree.py
├── book_details.py
├── settings_page.py
├── persona_page.py
├── planning/
│   ├── planning_page.py
│   ├── characters_page.py
│   ├── outline_page.py
│   └── notes_page.py
├── publication/
│   ├── publication_setup.py
│   ├── publication_editor.py
│   ├── copyright_page.py
│   └── contents_page.py
├── trash_page.py
├── search_panel.py
├── spell_panel.py
├── history_panel.py
├── splash.py
└── dialogs.py
```

Nieuwe UI-functionaliteit hoort bij voorkeur in de module van het betreffende scherm of paneel. `main_window.py` blijft de applicatieshell en `app.py` blijft alleen verantwoordelijk voor startup.

