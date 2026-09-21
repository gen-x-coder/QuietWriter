# QuietWriter

QuietWriter is een lokale Python-desktopapp voor het schrijven van boeken en verhalen, met optionele Ollama-integratie. Manuscripten blijven gewone Markdown-bestanden; de applicatie gebruikt alleen aanvullende JSON/SQLite-bestanden voor structuur en zoeken.

## Wat deze eerste versie al bevat

- modern PySide6/Qt 6 venster;
- startscherm met bestaande boeken en nieuw boek;
- boeken, secties en hoofdstukken;
- rustige editor met woordtelling;
- linker manuscriptbalk en rechter gereedschapsbalk;
- beide zijpanelen afzonderlijk verberg-/toonbaar;
- zoekfunctie over alle hoofdstukken van het geopende boek via SQLite FTS5;
- handmatig opslaan (`Ctrl+S`) en autosave;
- dagelijkse archiefkopie van de laatst oudere boekversie;
- werkmap kan rechtstreeks naar een lokale Dropbox-map wijzen;
- zes ingebouwde lichte/donkere kleurenschema's;
- venstergrootte en splitterposities worden onthouden;
- aparte Persona-knop in de linker balk (`persona/schrijver.md`);
- Ollama wordt bij start gecontroleerd en lokale modellen worden opgehaald;
- streaming Ollama-chat in het rechterpaneel;
- AI gebruikt altijd `schrijver.md`;
- AI kan geselecteerde tekst, huidig hoofdstuk, huidige sectie, heel boek of relevante oude verhalen als context krijgen;
- `stories/*.md` wordt geïndexeerd op titel, beschrijving, synopsis, tags en tekst;
- eenvoudige voorbereidende ondersteuning voor Hunspell-achtige `.dic` woordenlijsten.

## Installatie

Python 3.12 of nieuwer wordt aanbevolen.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Op Linux/macOS gebruik je voor activeren doorgaans:

```bash
source .venv/bin/activate
```

## Werkmap

Standaard wordt `~/QuietWriter` gebruikt. In **Instellingen** kun je dit wijzigen, bijvoorbeeld naar:

```text
C:\Users\jij\Dropbox\QuietWriter
```

De structuur wordt automatisch aangemaakt:

```text
QuietWriter/
├── books/
├── stories/
├── persona/
│   └── schrijver.md
├── dictionaries/
├── archive/
└── .cache/
```

### Oude verhalen

Zet bestaande Markdown-verhalen in `stories/`. De parser accepteert nu zowel eenvoudige headers als YAML-frontmatter. Bijvoorbeeld:

```markdown
---
title: Dit is een titel
description: Beschrijving van het verhaal
synopsis: Korte samenvatting
tags: boerderij, familie, winter
---

# Dit is een titel

De tekst van het verhaal...
```

Ook zonder de `---`-regels worden eenvoudige `key: value` headers herkend. Extra velden kunnen later zonder probleem aan de parser worden toegevoegd.

## AI

QuietWriter verwacht standaard Ollama op:

```text
http://127.0.0.1:11434
```

Bij het starten wordt `/api/tags` gebruikt om de beschikbare modellen te controleren. Als Ollama uit staat, start QuietWriter gewoon door; alleen de AI-functie is dan tijdelijk niet beschikbaar.

In deze eerste versie gebruikt de verhalenbibliotheek SQLite FTS voor snelle voorselectie. De architectuur is bewust zo opgezet dat later een embedding-index en een klein achtergrondmodel als bibliothecaris kunnen worden toegevoegd vóór het grote schrijfmodel.

## Belangrijk ontwerpprincipe

De AI schrijft nooit zelfstandig in manuscriptbestanden. Herschrijvingen en suggesties verschijnen uitsluitend in het chatpaneel. De schrijver beslist wat er naar het manuscript wordt gekopieerd.

## Eerstvolgende logische uitbreidingen

- echte drag-and-drop van secties en hoofdstukken;
- volwaardige Hunspell/Spylls spellingscontrole met downloaden/verwijderen van woordenboeken en hover-suggesties;
- embedding-index voor de oude verhalen;
- optioneel klein Ollama-model voor classificatie, tags en bibliotheekselectie;
- AI-contextinspecteur: zichtbaar maken welke oude verhalen/fragmenten zijn meegestuurd;
- OpenRouter-provider;
- export naar DOCX/EPUB/PDF;
- herstelvenster voor dagarchieven;
- meer metadata-velden zodra voorbeelden van de bestaande Markdown-headers beschikbaar zijn;
- packaging naar Windows `.exe` met PyInstaller.
