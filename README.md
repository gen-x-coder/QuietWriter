# QuietWriter 0.3.0

QuietWriter is een lokale Python-desktopapp voor het schrijven van boeken en verhalen met optionele Ollama-integratie. Manuscripten blijven gewone Markdown-bestanden. JSON en SQLite worden alleen gebruikt voor structuur, instellingen en zoekindexen.

## Belangrijkste functies

- moderne PySide6/Qt 6-interface;
- boekenplank als startscherm;
- boeken met secties en hoofdstukken;
- rustige schrijfweergave met beperkte regelbreedte en woordtelling;
- autosave plus handmatig opslaan (`Ctrl+S`);
- dagelijkse herstelkopieën van oudere boekversies;
- werkmap kan rechtstreeks in Dropbox staan;
- zes lichte/donkere kleurenschema's;
- inklapbare linkernavigatie met compacte en uitgebreide stand;
- contextgevoelige navigatie: **Boekenplank** sluit het huidige boek, **Manuscript** keert terug naar het geladen boek;
- aparte **Verhalen**-bibliotheek voor bestaande Markdown-verhalen;
- aparte **Schrijverspersona**;
- zoeken door het geopende boek;
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
├── persona/
│   └── schrijver.md
├── dictionaries/
├── archive/
└── .cache/
```

## Verhalenbibliotheek

Bestaande `.md`-verhalen plaats je in `stories/`. QuietWriter ondersteunt YAML-frontmatter zoals:

```markdown
---
title: Aan mijn lezers
date: 2025-12-10T16:00
slug: aan-mijn-lezers
description: Beschrijving van het verhaal
meta: Korte metadataomschrijving
intro: Introductietekst
author: Auteur
tags: tag 1, tag 2, tag 3
---

Tekst van het verhaal.
```

Extra onbekende velden worden niet weggegooid. De index gebruikt momenteel vooral titel, description, synopsis, tags en inhoud.

### Meerdere hoofdstukken in een oud verhaal

Een regel met precies één Markdownkopniveau wordt als nieuw hoofdstuk gezien:

```markdown
# De aankomst

Tekst...

# De volgende ochtend

Tekst...
```

`##` en lagere koppen blijven onderdeel van het huidige hoofdstuk.

## Schrijverspersona

De meegeleverde `schrijver.md` is een opgeschoonde en compactere versie van de aangeleverde schrijfwijzer. In **Schrijverspersona** kun je via **Meegeleverde schrijfwijzer laden** de tekst in de editor plaatsen en daarna zelf opslaan.

QuietWriter voegt deze persona automatisch toe aan iedere AI-opdracht. De AI schrijft nooit rechtstreeks in het manuscript.

## Ollama

Standaard verwacht QuietWriter Ollama op:

```text
http://127.0.0.1:11434
```

Bij het opstarten worden de beschikbare modellen opgehaald. Als Ollama niet actief is, blijft de volledige schrijfapp bruikbaar.

## Ontwikkelrichting

De verhalenindex gebruikt nu SQLite FTS. De volgende AI-stap is een combinatie van tags, full-text search, embeddings en optioneel een klein achtergrondmodel dat relevante verhalen selecteert voordat het grotere schrijfmodel ze analyseert.
