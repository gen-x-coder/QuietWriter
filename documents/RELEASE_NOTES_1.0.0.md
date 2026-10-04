# QuietWriter 1.0.0

QuietWriter 1.0.0 is de eerste stabiele release.

Deze release bevat geen nieuwe productfunctionaliteit bovenop de gevalideerde RC5-baseline. De RC-fase draaide vooral om dataveiligheid, conflictgedrag, herstel, Windows-distributie, AI-context/privacy en overdraagbaarheid van de bron.

## Belangrijkste onderdelen

- rustige manuscripteditor met hoofdstukken en secties;
- Planning voor scènes, personages en notities;
- History, revisions en Integriteit/Herstel;
- spelling;
- Media Manager;
- EPUB, PDF en Markdown-export;
- optionele Meelezer via Ollama of OpenRouter;
- first-run wizard;
- portable Windows-build;
- Nederlands en Engels;
- reproduceerbare branding en releaseflow.

## Dataveiligheid

De 1.0-baseline bevat onder meer:

- atomische writes;
- revisioncontrole en conflictbeveiliging;
- transactionele active-book adoption;
- fail-closed gedrag bij corrupte bronnen;
- future-format bescherming;
- History-recovery;
- bron/presentatie-scheiding in de editor;
- persona-conflictbeveiliging;
- merge-before-write voor het persoonlijke woordenboek;
- corrupte persona en andere optionele AI-contextbronnen blokkeren de applicatie niet.

## Praktijkvalidatie

Voor 1.0 zijn onder meer gecontroleerd:

- groot boek van circa 150.000 woorden en 40 hoofdstukken;
- Windows op 150% schaal;
- Ollama cold start;
- echte OpenRouter-vraag;
- twee-computer/sync-conflict;
- clean release staging en executable smoke in de RC-rondes.

## AI

De AI-functie heet **Meelezer**. QuietWriter positioneert AI niet als ghostwriter of co-auteur.

De Meelezer kan feedback, persona-/stijlcontrole, feiten- en consistentiechecks geven. `Herschrijf selectie` bestaat bewust niet.

OpenRouter is extern en krijgt pas inhoud na een bewuste gebruikersvraag. Ollama kan lokaal in de achtergrond opwarmen.

## Na 1.0

Nieuwe productfunctionaliteit volgt via de v2-roadmap. De eerste geplande v2-feature is de bewaarplaats voor tekstfragmenten ("Darlings"). Het ontwerp daarvan bestaat al, maar er zit geen v2-code in deze 1.0-release.
