# Review request — QuietWriter 1.3.0-dev.26

**Wijzig geen code.** Dit is een onafhankelijke code-, runtime- en visuele review van de huidige ontwikkelbuild.

## Context en versie

- Publieke stabiele release: **1.2.32**.
- Actieve ontwikkellijn: **1.3.0-dev.26**.
- 1.3.0 wordt bewust nog niet gepubliceerd; ontwikkeling gaat door op dezelfde 1.3.0-dev-lijn.
- README.md en README_EN.md zijn bewust niet aangepast tijdens deze iteraties en moeten ook door jou niet worden gewijzigd.
- Controleer tijdens de review ook actuele versieverwijzingen. Historische changelog/release-notes mogen vanzelfsprekend oude versies blijven noemen.

## Wat er sinds je laatste brede review is gebeurd

### A. Schrijfdoelen en voortgang (dev.11–dev.17)

- Optioneel **Woorddoel** per boek.
- Optionele gewenste einddatum met neutraal afgeleid tempo.
- Opt-in **Vandaag geschreven bijhouden**; standaard uit.
- Dagtelling is lokaal op het apparaat en telt alleen positieve editor-save-groei; schrappen maakt het dagtotaal niet negatief.
- Uitzetten pauzeert meten maar wist bestaande telling niet; tijdens uitgeschakelde periode geschreven woorden worden later niet ingehaald.
- Woorddoel/einddatum blijven behouden bij versieherstel.
- Boekenkast toont rustige voortgangsbalk en `x van y woorden`.
- Boekdetails/Boekomslag zijn visueel geharmoniseerd.
- Instellingenpagina heeft een consistente label→control-opmaak gekregen; losse checkboxen zijn vervangen door normale keuzevelden.
- Schrijflettertype-preview is opgeschoond.

### B. Planning dichter bij schrijven (dev.18–dev.26)

- Leeg hoofdstuk met gekoppelde scènes toont **presentation-only Planninghulp/ghosttekst**.
- Die Planninghulp zit niet in QTextDocument/Markdown en mag dus niet meetellen, zoeken, spelling, export, AI-manuscriptcontext of undo vervuilen.
- Zodra echte manuscripttekst aanwezig is verdwijnt automatische Planninghulp; bij volledig leeg worden komt hij terug.
- Planning-scènes tonen titel/synopsis, locatie, personages, doel/conflict/uitkomst en status; afgekapt aantal scènes wordt expliciet gemeld.
- Planningpagina kreeg duidelijkere uitleg, grotere personageselectie en automatische selectie van het eerste personage.
- Scènestatus gebruikt vaste waarden `idee / uitgewerkt / geschreven`, visueel **Idee / Uitgewerkt / Geschreven**.
- Outline toont statusbadges.
- Editor heeft subtiele knop **Planning** naast Tekstbreedte.
- De Planning-flyout is on-demand en blijft beschikbaar terwijl manuscripttekst aanwezig is.
- Schrijver kan in de flyout zelf een scène bewust als `Geschreven` markeren; geen automatische detectie.
- Planning-knop verdwijnt volledig als `Planninghulp in editor` op Verbergen staat.
- Planning-knop blijft zichtbaar bij een normaal hoofdstuk zonder gekoppelde scènes en toont dan `Geen planning voor dit hoofdstuk.`
- Flyout is bewust smal/hoog om manuscript zo min mogelijk te bedekken.
- dev.26 corrigeert alleen de lege flyout: titel, uitleg en lege melding moeten compact **bovenaan** staan, niet verticaal verspreid.

### C. Losse editorbugs die recent zijn gerepareerd

1. **Zoeken/vervangen-layout**
   - resultatenzone blijft stabiel bij 0 of meer resultaten;
   - `Vervangen door` mag niet omhoog springen;
   - bij 0 treffers geen dubbele `0 resultaten` + `Geen resultaten gevonden`;
   - lege resultatenzone gebruikt dezelfde lichte achtergrond als normale resultaten.

2. **Ctrl+C / Ctrl+V**
   - intern kopiëren/plakken behoudt tekst/opmaak;
   - geplakte tekst mag na Ctrl+V niet geselecteerd blijven;
   - cursor hoort direct achter de geplakte tekst te staan.

### D. UI-consistentie

- Context-subnavigatie (Planning en hoofdstukken) gebruikt pagina-achtergrond; alleen selectie krijgt accent.
- Scrollbar-track van hoofdstuklijst moet dezelfde achtergrond hebben als de contextkolom/pagina, ook in thema's.
- Statusdropdown in Scène bewerken is een gesloten dropdown, geen vrij tekstveld.

## Reviewopdracht

### 1. Volledige regressiesuite

Draai minimaal:

- volledige pytest-suite;
- smoke-test;
- locale-keycontrole voor alle 5 talen;
- undefined-names-check / pyflakes volgens de bestaande projectworkflow;
- eventuele bestaande Qt-runtime/harnesses die relevant zijn.

Rapporteer aantallen en exitcodes. Als Linux na volledig geslaagde tests opnieuw met exitcode 139 afsluit, vergelijk expliciet met de eerdere bekende teardown-crash en meld of dit een regressie is.

### 2. Gerichte code-review

Lees minimaal:

- `quietwriter/ui/editor_page.py`
- `quietwriter/ui/manuscript_editor.py`
- `quietwriter/ui/search_panel.py`
- `quietwriter/ui/planning_page.py` / relevante Planning-UI
- `quietwriter/planning_models.py` / storage/validation voor status
- `quietwriter/ui/settings_page.py`
- `quietwriter/ui/book_details.py`
- `quietwriter/writing_progress.py`
- relevante theme/QSS-code

Controleer specifiek:

- Planning-overlay lifecycle en toggle-state (`Qt.Popup`, hide/close, Escape, buiten klikken, tweede klik op knop);
- of signalen of focus gedrag onverwachte reopen/close-loops kunnen geven;
- lege overlay layout in dev.26 versus overlay met scènes;
- dat Planninghulp presentation-only blijft en niet per ongeluk in manuscriptdata terechtkomt;
- statuswijzigingen alleen Planning-data wijzigen;
- undo/redo, save/autosave, zoekfunctie, export en AI-context niet door ghost/overlay worden beïnvloed;
- opt-in schrijfvoortgang en profiel/QSettings-scheiding;
- regressies door vervangen van checkboxes door combo-keuzes;
- zoek/vervang-layout na 0 → resultaten → leeg → opnieuw zoeken;
- copy/paste met plain text, bold/italic en multiline tekst;
- versieherstel behoudt writing_goal velden;
- performance of event-loopproblemen door paint/overlay/Planning-refresh.

### 3. Visuele/runtime-tests in PySide6

Doe echte Qt-runs en, waar mogelijk, screenshots of nauwkeurige observaties voor minimaal deze scenario's:

#### Planning overlay

1. Hoofdstuk met 0 gekoppelde scènes: open Planning-flyout.
   - titel, uitleg en `Geen planning voor dit hoofdstuk.` direct bovenaan;
   - onderkant blijft leeg;
   - geen verticale spreiding zoals in dev.25.
2. Hoofdstuk met 1, 3 en veel scènes: flyout blijft smal/hoog en scrollbaar.
3. Tweede klik op Planning terwijl flyout open is: sluit betrouwbaar.
4. Escape sluit; volgende klik opent één keer normaal.
5. Buiten flyout klikken sluit; volgende klik opent één keer normaal.
6. Instelling Planninghulp → Verbergen: knop verdwijnt; Tonen: knop komt terug.
7. Hoofdstuk zonder planning houdt knop zichtbaar wanneer Planninghulp aan staat.
8. Markeer een scène als Klaar/Geschreven in flyout en controleer Outline + ghoststatus.
9. Licht en donker thema; controleer contrast en dat flyout niet onnodig manuscript bedekt.

#### Planninghulp/ghost

10. Leeg hoofdstuk met scènes toont hulp; woordtelling blijft 0.
11. Typ echte tekst: hulp verdwijnt.
12. Verwijder/undo terug naar volledig leeg: hulp komt terug.
13. Zoek naar uniek woord dat alleen in ghost staat: geen manuscriptresultaat.
14. Export/saven/reopen: ghosttekst komt nooit in hoofdstukbestand.
15. Locatie en Personages staan op aparte regels.
16. Veel scènes: expliciete `… nog N meer in Planning`-melding.

#### Planning UI

17. Personagespagina selecteert bij openen het eerste personage.
18. Lange rollen vervuilen personageselectie niet; selectie toont alleen namen.
19. Scene-status is overal een gesloten dropdown en visueel `Idee / Uitgewerkt / Geschreven`.
20. Planning/Personages/Outline uitleg is leesbaar en niet dubbelzinnig.

#### Zoek/vervangen

21. Zoekterm met 0 resultaten: paneelgeometrie blijft stabiel; witte/lichte resultaatzone; één lege melding.
22. Term met resultaten: resultaten komen in dezelfde zone; `Vervangen door` blijft onderaan.
23. Zoekveld leegmaken en opnieuw zoeken: geen layout-instorting.
24. Test bij verschillende paneelhoogtes/venstergroottes.

#### Kopiëren/plakken

25. Plain text Ctrl+C/Ctrl+V: na paste geen selectie, cursor achter tekst.
26. Vet/cursief gemengde tekst: opmaak blijft behouden, geen selectie.
27. Multiline en scènebreuk/Markdown-randgevallen voor zover ondersteund.
28. Direct typen na paste voegt toe en vervangt niet de geplakte tekst.

#### Schrijfdoelen

29. Opt-in staat standaard uit bij schoon profiel.
30. +10 woorden save, -2 save, +5 save → vandaag 15.
31. Bijhouden uit, schrijf +10, weer aan → oude dagtotaal blijft en +10 wordt niet ingehaald.
32. Woorddoel/einddatum blijven bij versieherstel behouden.
33. Boekenkastbalk en `x van y woorden` blijven correct.

### 4. Versie-audit

Zoek expliciet naar actuele, niet-historische verwijzingen die nog een verkeerde versie noemen. Verwacht:

- publieke release: `1.2.32`;
- actieve ontwikkellijn: `1.3.0-dev.26`.

Historische changelog/review/release notes moeten uiteraard hun oorspronkelijke versienummers behouden. Meld alleen werkelijk verouderde actuele verwijzingen.

### 5. Rapportage

Rapporteer compact maar volledig in deze volgorde:

1. **Blockers vóór verdere ontwikkeling**
2. **Moet vóór 1.3.0**
3. **Backlog/polish**
4. **Testresultaten en performance**
5. **Visuele bevindingen**
6. **Versie-audit**
7. **Niet getest / beperkingen**

Maak daarnaast een bestand `QUIETWRITER_REVIEW_1_3_0_DEV26_CLAUDE.md` met de volledige review en voeg eventuele losse testscripts toe. **Wijzig geen productcode.**
