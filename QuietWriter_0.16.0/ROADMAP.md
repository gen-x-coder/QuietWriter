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

### Iteratie 17 — Meegeleverde schrijftypografie

Een kleine set hoogwaardige editorfonts meeleveren zodat QuietWriter overal dezelfde goede basis heeft.

- Alleen fonts met een distributielicentie die bundeling toestaat; per font licentie opnieuw verifiëren vóór opname.
- Fontbestanden plus verplichte licentieteksten in een eigen resources/fonts-structuur.
- Fonts bij start lokaal registreren via Qt; geen systeeminstallatie nodig.
- Kandidaten om juridisch en visueel te beoordelen: Merriweather, Source Serif 4, Literata, EB Garamond/Lora of vergelijkbare rustige serifs.
- Gebruiker kan daarnaast altijd geïnstalleerde systeemfonts blijven kiezen.
- Geen fontbestand opnemen voordat de licentie expliciet is gecontroleerd.

### Iteratie 18 — AI-verfijning

De gewone schrijfchat blijft leidend.

- Alleen snelacties toevoegen die in echt gebruik vaak terugkomen, bijvoorbeeld Feedback, Herschrijf selectie of Persona-check.
- Snelacties zijn alleen vooraf ingevulde prompts; geen aparte AI-logica.
- OpenRouter uitgebreider testen.
- Geen RAG/bibliothecaris tenzij daar later opnieuw een duidelijke behoefte aan ontstaat.

### Iteratie 19 — UI/UX polish 2

- Screens op verschillende DPI's/resoluties nalopen.
- Boekenplank spacing en kaartmaten verder finetunen.
- Cursors, micro-interacties en flyouts nalopen.
- Scene-break interactie visueel afmaken.
- Toegankelijkheid: focus states, toetsenbordnavigatie en contrast.

### Iteratie 20 — Release en robuustheid

- Windows executable/installer.
- Migraties tussen QuietWriter-versies.
- Logging en crash recovery.
- Herstel na beschadigde instellingen of gedeeltelijke bestanden.
- Meer integratie- en GUI-smoketests.
- Releasecheck voor licenties van meegeleverde resources.
