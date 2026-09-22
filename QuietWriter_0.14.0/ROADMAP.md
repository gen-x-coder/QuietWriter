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

### Iteratie 15 — Boekplanning en ideeën

Per boek een optionele planningslaag, volledig gescheiden van de uiteindelijke manuscripttekst.

- Algemene notitiepagina voor het boek.
- Ideeënbord / vrije kaarten voor scènes, onderzoek en losse gedachten.
- Hoofdstukraamwerk met per hoofdstuk een geplande synopsis, doel en status.
- Karakterpagina's: naam, rol, beschrijving, relaties, notities.
- Eventueel locaties en tijdlijn later toevoegen als daar echt behoefte aan is.
- Planning mag nooit verplicht worden voor gebruikers die alleen willen schrijven.

### Iteratie 16 — Publicatiestructuur

Eerst een documentmodel voor front matter, body en back matter ontwerpen; daarna pas PDF/EPUB.

**Front matter**
- Half-title/titelpagina.
- Copyrightpagina met templates én vrij bewerkbare tekst.
- Opdracht/dedicatie.
- Voorwoord/preface als apart front-matter-item, dus niet als "hoofdstuk 1".
- Automatische inhoudsopgave op basis van hoofdstukken/secties.
- Optionele lege pagina's/pagina-einden voor printopmaak.

**Body**
- Hoofdstukken en secties.
- Paginering/hoofdstukstartregels voor PDF.

**Back matter**
- Nawoord.
- Dankwoord.
- Over de auteur.
- Overige vrij definieerbare onderdelen.

Daarna:
- EPUB-export.
- PDF-export met gekozen boekformaat, marges, typografie en paginering.
- Inhoudsopgavegenerator delen tussen EPUB/PDF waar mogelijk.

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
