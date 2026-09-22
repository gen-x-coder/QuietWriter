# QuietWriter roadmap

## Afgerond

- Editorbasis: hoofdstukken/secties, drag-and-drop hoofdstukken, zoeken/vervangen en spellingscontrole.
- Versiegeschiedenis: dagarchief, handmatige versies, sterren, preview en herstel.
- AI-basis: modulaire providers, Ollama/OpenRouter, streaming chat, Markdown-output, persona en selectie/hoofdstuk/sectie/boek-context.
- Markdown import/export: volledige frontmatter, hoofdstukken, secties en round-trip.
- Scènebreuk invoegen als `***` via de rechter werkbalk.
- UI/UX polish: semantisch themesysteem, dynamische schrijftypografie, navigatierails, editor, AI-chat, responsive boekenplank en centrale pagina's.
- Informatiearchitectuur vereenvoudigd: één documentmodel voor boeken, korte verhalen en verhalenbundels; losse stories-bibliotheek verwijderd.
- Instellingen als centrale pagina met eigen linker categorienavigatie en inhoud rechts.
- Technische UI-refactor: de monolithische `app.py` is opgesplitst in zelfstandige UI-modules per pagina/paneel.

## Voorgestelde volgorde

### Iteratie 13 — Schrijfopmaak en manuscriptstijl — afgerond

- Selectie-toolbar met eenvoudige manuscriptopmaak.
- Markdown als bron blijft leidend; de editor toont een rustige visuele opmaaklaag.
- Vet, cursief, onderstrepen, doorhalen, code, tussenkop, citaat en lijsten.
- Scènebreuk `***` als visuele divider.
- Alinea-inspringing, regelafstand en alinearuimte als onafhankelijke instellingen.
- Optionele slimme dubbele aanhalingstekens tijdens typen.

### Iteratie 14 — Veilige externe wijzigingen — afgerond

- Optimistic concurrency per boek/bestand, zonder lockfiles of Dropbox-specifieke code.
- SHA-256 revisions vóór iedere schrijfactie; externe wijzigingen worden nooit stilletjes overschreven.
- Eenvoudige conflictkeuze: eigen versie of schijfversie, met automatische recovery in versiegeschiedenis.
- Tijdelijke sync-/bestandslocks apart behandelen van echte inhoudsconflicten.

### Iteratie 15 — Boekplanning en ideeën — MVP afgerond

Per boek bestaat nu een optionele planningslaag, volledig gescheiden van de uiteindelijke manuscripttekst.

**MVP aanwezig**
- Planning als zelfstandige modus met Personages, Outline en Notities.
- Gestructureerde personageprofielen met vaste, AI-vriendelijke karaktervelden.
- Klikbare, bidirectionele relaties tussen personages.
- Outline met scènes gegroepeerd onder de bestaande hoofdstukken en een bak voor Losse ideeën.
- Scènes met titel, synopsis, betrokken personages, locatie, doel, conflict, uitkomst, status en notities.
- Eén Markdown-notitiepagina per boek met dezelfde rustige editorcomponent.
- Planningdata in losse bestanden onder `planning/`, inclusief revision/conflictbeveiliging en versiegeschiedenis.

**Later / bewust niet in MVP**
- Scènes slepen en vrij herschikken tussen hoofdstukken.
- Inklapbare hoofdstukgroepen en compactere inline-scènebewerking.
- Portretten, eerste verschijning en expliciete belangrijke hoofdstukken op personagepagina's.
- Uitgebreidere relatiebeschrijvingen of een visuele relatieweergave.
- Wiki-achtige `[[links]]` tussen notities, personages en scènes.
- Locaties als eigen entiteit, tijdlijn of worldbuilding-database.
- Custom fields per genre en meerdere outline-weergaven (kanban/tijdlijn).
- AI-acties die planning/personageprofielen als gerichte context gebruiken.

### Iteratie 16 — Publicatiestructuur — MVP afgerond

QuietWriter kent nu een expliciete publicatiestructuur naast Planning: **Voorwerk → Manuscript → Achterwerk**.

**MVP aanwezig**
- Publicatiestructuur kiezen vanuit de bestaande Inhoud-editor; geen aparte dashboardmodus.
- Voorwerk: Titelpagina, Copyright, Opdracht, Epigraaf, Inhoudsopgave, Voorwoord en Inleiding.
- Achterwerk: Nawoord, Dankwoord en Over de auteur.
- Vrije tekstonderdelen blijven Markdown en gebruiken dezelfde editorcomponent.
- Titelpagina, Copyright en Epigraaf zijn gestructureerde formulieren.
- Copyright ondersteunt auteursnaam/pseudoniem, editie, jaar, uitgever, ISBNs per formaat en optionele aanpasbare clausules.
- Inhoudsopgave wordt uit de actuele hoofdstukstructuur gegenereerd, met optioneel tussenkoppen.
- Publicatiebestanden staan los onder `publication/` en vallen onder revision/conflictbeveiliging en versiegeschiedenis.
- Inhoud/semantiek zijn bewust losgekoppeld van exportvormgeving.

**Nog open rond publicatie**
- Echte PDF- en EPUB-rendering.
- Keuze uit enkele rustige boektemplates (bijv. klassiek, modern, literair).
- Boekformaat, marges, paginanummers, recto/verso-regels en hoofdstukstartpagina's voor print/PDF.
- EPUB-specifieke navigatie/metadata en validatie.
- Schutbladen, half-title en expliciete lege pagina's/pagina-einden voor print.
- Preview van de uiteindelijke opmaak per gekozen template.
- Meer inhoudsopgaveniveaus als de manuscriptstructuur daar later aanleiding toe geeft.
- Eventueel extra vrij definieerbare voor-/achterwerkonderdelen, pas als daar echte behoefte aan blijkt.

### Layout hardening — afgerond in 0.17.1

- Verborgen `QStackedWidget`-pagina's mogen de minimumhoogte van het hoofdvenster niet meer bepalen.
- Lange centrale formulieren en instellingen blijven binnen scrollbare viewports; vaste acties blijven bereikbaar op lage schermhoogtes.
- Geen custom Windows-geometryclamps: Qt blijft verantwoordelijk voor native restore/maximize-gedrag.

### Iteratie 17 — Meegeleverde schrijftypografie — afgerond

- Voorkeursset vastgesteld: Merriweather, Literata, Source Serif 4 en EB Garamond.
- Alle vier geverifieerd onder SIL Open Font License 1.1; licentieteksten en copyright notices worden per familie meegeleverd.
- Qt registreert de meegeleverde variable fonts alleen binnen QuietWriter; er is bewust geen Windows-installatiefunctie.
- Fontkeuze toont eerst **Aanbevolen**, daarna **Systeemfonts**, zonder dubbele families.
- Live voorbeeldregel toegevoegd aan Uiterlijk.
- Nieuwe Over-pagina bevat versie, project/makerinformatie en inklapbare fontlicenties.
- Build/source-helper haalt de geverifieerde upstream fontbinaries op uit Google Fonts vóór packaging.

### Iteratie 18 — UI/UX consistency & polish — gestart in 0.18.0

**Afgerond in 0.18.0**
- Designregels vastgelegd voor overzichts-, instellingen-, detail-, document- en setup-pagina's.
- Instellingen gebruiken een consistente tweekoloms settings-row taal met gerichte microcopy.
- Font-preview staat naast de fontkeuze; Opslaan kent een echte dirty-state.
- De selectie-toolbar steelt geen keyboard focus meer.
- Het standaard editor-contextmenu bevat nu ook QuietWriter-opmaakacties.
- Lage schermhoogte en 125% DPI zijn structureel afgedekt door de layout-hardening uit 0.17.1; meerdere DPI's blijven onderdeel van de eind-smoketest.

**Nog open in deze polish-iteratie**
- Boekenplank spacing en kaartmaten verder finetunen.
- Cursors, hover/pressed states, micro-interacties en flyouts scherm voor scherm nalopen.
- Scene-break interactie visueel afmaken.
- Focus states, Tab/Shift+Tab, toetsenbordnavigatie en contrast nalopen.
- Eind-smoketest op 100%, 125% en 150% DPI en op lage laptophoogte.

### Publicatie-export en templates

- PDF/EPUB-rendering bovenop het bestaande publication model.
- Rustige templates zoals Klassiek, Modern en Literair.
- Print-/EPUB-specifieke paginering, metadata en validatie.

### AI-verfijning — later

De gewone schrijfchat blijft leidend; deze iteratie is bewust naar beneden geschoven.

- Alleen snelacties toevoegen die in echt gebruik vaak terugkomen, bijvoorbeeld Feedback, Herschrijf selectie of Persona-check.
- Snelacties zijn alleen vooraf ingevulde prompts; geen aparte AI-logica.
- OpenRouter uitgebreider testen.
- Geen RAG/bibliothecaris tenzij daar later opnieuw een duidelijke behoefte aan ontstaat.

### Release en robuustheid

- Windows executable/installer.
- Migraties tussen QuietWriter-versies.
- Logging en crash recovery.
- Herstel na beschadigde instellingen of gedeeltelijke bestanden.
- Meer integratie- en GUI-smoketests.
- Releasecheck voor licenties van meegeleverde resources.


### Design language audit
- Planning collection pages use the same title/action hierarchy.
- Editable forms retain a bottom-right save action; collection actions live in the page header.
- Settings has one explicit commit action; navigation away discards unsaved values and restores live previews.
