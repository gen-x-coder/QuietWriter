# QuietWriter 0.6.0

QuietWriter is een lokale Python-desktopapp voor het schrijven van boeken en verhalen met optionele Ollama-integratie. Manuscripten blijven gewone Markdown-bestanden. JSON en SQLite worden alleen gebruikt voor structuur, instellingen, metadata en zoekindexen.

## Belangrijkste functies

- moderne PySide6/Qt 6-interface;
- boekenplank als startscherm met omslagen, importeren en sorteren;
- boeken met secties en hoofdstukken;
- boekdetails met titel, slug, beschrijvingen, tags, auteur en omslag; een eigen omslag kan ook weer worden verwijderd;
- rustige schrijfweergave met beperkte regelbreedte en woordtelling;
- autosave plus handmatig opslaan (`Ctrl+S`);
- dagelijkse herstelkopieën van oudere boekversies;
- prullenbak met herstellen, selectie definitief verwijderen en alles legen;
- werkmap kan rechtstreeks in Dropbox staan;
- zes lichte/donkere kleurenschema's;
- inklapbare linkernavigatie met compacte en uitgebreide stand;
- contextgevoelige navigatie: **Boekenplank** sluit het huidige boek, **Manuscript** keert terug naar het geladen boek;
- aparte **Verhalen**-bibliotheek voor bestaande Markdown-verhalen;
- aparte **Schrijverspersona**;
- zoeken en vervangen in hoofdstuk, sectie of heel boek, inclusief hoofdlettergevoelig en heel woord;
- hoofdstukken via drag-and-drop ordenen en tussen secties verplaatsen;
- eerste spellingscontrole met rode onderstreping en stap-voor-stap rechterpaneel;
- centrale Nederlandse UI-termen in `quietwriter/locales/nl.json`;
- streaming Ollama-chat met schrijfpersona;
- zichtbaar `Denken…` tijdens AI-verwerking, zonder denklog in het uiteindelijke antwoord;
- oude verhalen kunnen door de AI als aanvullende context worden gebruikt.

## Installeren

Python 3.12 of nieuwer wordt aanbevolen.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Werkmap

Standaard gebruikt QuietWriter:

```text
C:\Users\<naam>\QuietWriter
```

Je kunt in **Instellingen** bijvoorbeeld een lokale Dropbox-map kiezen. QuietWriter maakt daarin automatisch:

```text
QuietWriter/
├── books/
├── stories/
├── boekomslagen/
├── persona/
│   └── schrijver.md
├── archive/
├── dictionaries/
└── .cache/
```

### Boekomslagen

De lokale omslagbestanden staan centraal in `boekomslagen/`. Een boek met slug `onder-de-linden` gebruikt bijvoorbeeld:

```text
boekomslagen/onder-de-linden.jpg
```

Aanbevolen formaat: portret **1:1,6**, met minimaal **1024 pixels** op de lange zijde. De omslag bevat alleen de foto; QuietWriter tekent de titel zelf als dynamische tekst.

Voor een algemene standaardomslag kun je een bestand plaatsen met een van deze namen:

```text
default-cover.jpg
default-cover.jpeg
default-cover.png
default-cover.webp
```

Als dat bestand ontbreekt, gebruikt QuietWriter een ingebouwde rustige fallback.

### Afbeeldingspad in Markdown-metadata

In **Instellingen** staat `Afbeeldingspad in metadata`. Standaard:

```text
/{slug}.jpg
```

Je kunt dit bijvoorbeeld veranderen in:

```text
/images/{slug}.jpg
```

QuietWriter kent bewust geen domeinnaam of website-adres. Het bewaart alleen het relatieve pad. De huidige boekmetadata wordt in `book.json` opgeslagen en kan bij een latere export naar Markdown als frontmatter worden geschreven.

## Oude verhalen

Plaats bestaande `.md`-verhalen in `stories/`. QuietWriter leest YAML/frontmatterachtige velden zoals `title`, `description`, `meta`, `intro`, `tags`, `author`, `slug` en afbeeldingsvelden. Een regel met één Markdownkop (`# Hoofdstuktitel`) begint een nieuw hoofdstuk in de verhalenlezer.


## Boek importeren

Kies op de Boekenplank **Importeren…** en selecteer een `.md`-bestand. QuietWriter leest de bestaande frontmatter en maakt er een bewerkbaar QuietWriter-boek van. Regels met één `#`, bijvoorbeeld `# Hoofdstuk 2`, beginnen een nieuw hoofdstuk. Het bronbestand blijft ongewijzigd; QuietWriter maakt een eigen kopie in `books/`.

## Nog gepland

Zie `ROADMAP.md` voor de geplande iteraties. De eerstvolgende grotere blokken zijn versiegeschiedenis, AI, import/export, bibliotheekverbeteringen en daarna een aparte UI/UX-polishronde.
