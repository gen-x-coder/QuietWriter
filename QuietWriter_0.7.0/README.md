# QuietWriter 0.7.0

QuietWriter is een lokale Python-desktopapp voor het schrijven van boeken en verhalen met optionele Ollama-integratie. Manuscripten blijven gewone Markdown-bestanden. JSON en SQLite worden alleen gebruikt voor structuur, instellingen, metadata en zoekindexen.

## Belangrijkste functies

- moderne PySide6/Qt 6-interface;
- boekenplank als startscherm met omslagen, importeren en sorteren;
- boeken met secties en hoofdstukken;
- boekdetails met titel, slug, beschrijvingen, tags, auteur en omslag;
- rustige schrijfweergave met beperkte regelbreedte en woordtelling;
- autosave plus handmatig opslaan (`Ctrl+S`);
- dagelijkse herstelkopieën, handmatige versies, versiepreview/herstel en een prullenbak voor boeken;
- werkmap kan rechtstreeks in Dropbox staan;
- inklapbare linkernavigatie;
- aparte verhalenbibliotheek en schrijverspersona;
- zoeken en vervangen in hoofdstuk, sectie of volledig boek;
- veilige hoofdstuk-drag-and-drop via de zes-punts sleepgreep;
- hoofdstukken hernoemen, dupliceren en veilig verwijderen via rechtsklik;
- secties toevoegen, hernoemen en lege secties verwijderen;
- spellingsonderstreping en een stap-voor-stap spellingspaneel, inclusief hoofdstuktitels;
- automatische Hunspell-detectie via ONLYOFFICE, LibreOffice en OpenOffice;
- alle gevonden talen worden met een leesbare naam getoond;
- persoonlijk woordenboek én een aparte blijvende lijst `Altijd negeren`;
- instellingen verdeeld over Algemeen, Uiterlijk, Opslag, AI en Spelling;
- streaming Ollama-chat met schrijfpersona.

## Installeren

Python 3.12 of nieuwer wordt aanbevolen.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Spellingscontrole

QuietWriter bundelt bewust geen woordenboeken. Het zoekt automatisch in de eigen werkmap en in gangbare installaties van ONLYOFFICE, LibreOffice en OpenOffice. Daardoor kun je bestaande Hunspell-bestanden hergebruiken zonder ze opnieuw te distribueren.

In **Instellingen > Spelling** kun je:

- alle gevonden talen bekijken;
- opnieuw naar geïnstalleerde woordenboeken zoeken;
- een eigen `.dic` (en indien aanwezig de bijbehorende `.aff`) toevoegen;
- een door QuietWriter gekopieerd eigen woordenboek verwijderen;
- een algemene downloadsite voor OpenOffice-woordenboeken openen.

Woordenboeken uit Office-installaties worden alleen gelezen en nooit door QuietWriter verwijderd.

Het spellingspaneel kent vier verschillende acties:

- **Negeren** — alleen deze ene vindplaats overslaan;
- **Alles negeren** — dit woord voor de huidige QuietWriter-sessie negeren;
- **Altijd negeren** — blijvend negeren via `dictionaries/altijd_negeren.txt`, zonder het woord goed te keuren;
- **Toevoegen aan woordenboek** — blijvend toevoegen aan `dictionaries/persoonlijk.txt`.

Interactieve hover-suggesties zijn bewust verwijderd. Bij grote hoofdstukken veroorzaakten die te veel werk tijdens iedere muisbeweging. Suggesties worden nu alleen berekend wanneer het spellingspaneel ze nodig heeft.

## Versiegeschiedenis

Open **Versiegeschiedenis** via het klok-icoon in de rechter gereedschapsbalk. Automatische dagarchieven en handmatig gemaakte versies staan samen in één tijdlijn. Klik op een versie om het boek alleen-lezen te bekijken. Bovenaan verschijnt dan een duidelijke balk met **Deze versie herstellen** en **Afsluiten**.

Herstellen maakt altijd eerst een extra veiligheidsversie van de huidige toestand. Versies kunnen met een ster worden gemarkeerd en de tijdlijn kan op alleen gemarkeerde versies worden gefilterd.

QuietWriter maakt niet bij iedere autosave een nieuwe historische versie: de automatische basis blijft één dagarchief per gewijzigde dag. Met **Nieuwe versie maken** kun je zelf extra checkpoints bewaren wanneer je dat nuttig vindt.

## Werkmap

Standaard gebruikt QuietWriter:

```text
C:\Users\<naam>\QuietWriter
```

QuietWriter maakt daarin onder andere:

```text
QuietWriter/
├── books/
├── stories/
├── boekomslagen/
├── persona/
│   └── schrijver.md
├── archive/
├── trash/
├── dictionaries/
│   ├── persoonlijk.txt
│   └── altijd_negeren.txt
└── .cache/
```

## Boekomslagen

Een boek met slug `onder-de-linden` gebruikt bijvoorbeeld `boekomslagen/onder-de-linden.jpg`. Aanbevolen formaat: portret **1:1,6**, met minimaal **1024 pixels** op de lange zijde. De titel blijft echte interface-tekst en zit niet in het omslagbeeld.

## Oude verhalen en importeren

Plaats bestaande `.md`-verhalen in `stories/`. QuietWriter leest frontmattervelden zoals `title`, `description`, `meta`, `intro`, `tags`, `author`, `slug` en afbeeldingsvelden. Een regel `# Hoofdstuktitel` begint een nieuw hoofdstuk.

Op de Boekenplank kun je met **Importeren…** zo'n Markdown-bestand omzetten naar een bewerkbaar QuietWriter-boek. Het bronbestand blijft ongewijzigd.

## Tests

Voer de regressietests uit met:

```powershell
python -m unittest discover -s tests -v
```

0.7.0 bevat 22 tests voor onder andere:

- 1000 willekeurige drag-and-dropverplaatsingen zonder verlies of duplicatie;
- woordenboekdetectie in meerdere talen;
- toevoegen/verwijderen van eigen woordenboeken zonder Office-bestanden te wijzigen;
- spellingsscans van grote hoofdstukken;
- sessie-negeren versus blijvend negeren;
- hoofdstukken hernoemen, dupliceren en veilig verwijderen;
- robuuste opslag bij tijdelijke Windows/Dropbox file locks;
- volledige boekversies maken, markeren en herstellen.

Zie `ROADMAP.md` voor de volgende iteraties.
