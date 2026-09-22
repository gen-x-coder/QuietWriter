# Changelog

## 0.12.0

- Grote technische UI-refactor zonder bedoelde functionele wijzigingen.
- `quietwriter/app.py` is teruggebracht van ruim 2600 regels naar een kleine bootstrapmodule van circa 40 regels.
- `MainWindow` staat nu in `ui/main_window.py`; globale navigatie, themawissel en applicatieshell zijn daardoor geïsoleerd van startupcode.
- Boekenplank, boekdetails, instellingen, persona, prullenbak en splash staan elk in een eigen UI-module.
- De editor is verder opgesplitst in `editor_page.py`, `manuscript_editor.py`, `manuscript_tree.py`, `search_panel.py`, `spell_panel.py` en `history_panel.py`.
- De centrale Ja/Nee-dialoog staat nu in `ui/dialogs.py`.
- Geen tijdelijke compatibiliteitsmodule of dubbele oude UI-code behouden; de oude monolithische klassedefinities zijn uit `app.py` verwijderd.
- Persona-resources gebruiken na de verplaatsing opnieuw het juiste projectpad.
- Architectuurtests zijn aangepast zodat ze de nieuwe modulegrenzen bewaken in plaats van oude klasselocaties.
- 58 regressietests slagen en `compileall` is schoon.

## 0.11.1

- Instellingen hebben nu een eigen linker categorienavigatie in plaats van horizontale tabs.
- Algemeen, Uiterlijk, Opslag, AI en Spelling openen in één centraal inhoudsgebied rechts.
- Instellingselementen staan verticaal en links uitgelijnd, met labels boven de bediening.
- De instellingenpagina gebruikt dezelfde rustige navigatiehiërarchie als de rest van QuietWriter, zonder inklapbaar tabje.
- Roadmap uitgebreid met schrijfopmaak, boekplanning/ideeënbord, publicatiestructuur voor EPUB/PDF, meegeleverde fonts en verdere refactor/release-iteraties.
- 56 regressietests slagen.

## 0.11.0

- De boekenplank is responsive gemaakt: het aantal kolommen wordt uit de beschikbare breedte berekend, zodat vrije horizontale ruimte wordt benut voordat een tweede rij ontstaat.
- Boekkaarten zijn licht vergroot, terwijl omslagtiteltekst kleiner is gemaakt voor langere titels.
- De knop **Details** is van de boekenplank verwijderd. Boekdetails horen nu bij een geopend boek.
- **Boekdetails** is geen popup meer maar een volwaardige centrale pagina in QuietWriter.
- **Instellingen** is geen popup meer maar een volwaardige centrale pagina. Thema- en typografiepreview blijven werken; Annuleren herstelt de vorige preview.
- **Schrijverspersona**, **Instellingen** en **Prullenbak** staan als globale functies onderaan de linkernavigatie.
- De losse **Verhalen**-functie is volledig verwijderd uit UI, startup, opslag, indexering, iconen en broncode.
- QuietWriter maakt geen `stories`-map meer aan. Oude Markdownbestanden kunnen via **Importeren…** als normaal QuietWriter-boek worden geopend.
- De oude stories-index (`story_index.py`) en stories-icoon zijn verwijderd.
- De rechter gereedschapsrail verschijnt alleen bij de editor; Boekdetails en Instellingen gebruiken dezelfde centrale paginanavigatie als de rest van de app.
- 53 regressietests slagen.

## 0.10.9

- Alle QuietWriter-SVG-iconen worden via één thema-afhankelijke renderer ingekleurd.
- AI-rich-text wordt bij themawissels opnieuw opgebouwd met de actieve themakleuren.
