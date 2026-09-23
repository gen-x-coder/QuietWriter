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

**Afgerond in 0.18.0–0.18.14**
- Designregels vastgelegd voor overzichts-, instellingen-, detail-, document- en setup-pagina's.
- Instellingen gebruiken een consistente tweekoloms settings-row taal met gerichte microcopy; vanaf 0.18.1 staan labels en controls in vaste onzichtbare kolommen.
- Font-preview staat naast de fontkeuze als volwaardige preview-card; Opslaan kent een echte dirty-state.
- De selectie-toolbar steelt geen keyboard focus meer.
- Scènebreuken hebben een hover-only verwijderactie; de gewone tekstselectie blijft ongemoeid.
- Het standaard editor-contextmenu bevat nu ook QuietWriter-opmaakacties; de zwevende toolbar heeft beschrijvende hover-uitleg voor alle acties.
- Lage schermhoogte en 125% DPI zijn structureel afgedekt door de layout-hardening uit 0.17.1; meerdere DPI's blijven onderdeel van de eind-smoketest.
- Nieuwe instellingen- en Over-teksten worden via locale-keys beheerd; `en.json` is toegevoegd als basis voor latere Engelstalige UI.
- Boekenplank spacing, kaartmaten en full-width hero zijn visueel afgerond; hoofdstukselectie in de Inhoud-boom vormt vanaf 0.18.6 één consistente rij.
- AI kan volledig uit de editor worden verborgen zonder configuratie te verliezen; de AI-instellingen benoemen expliciet de rol van Ollama/OpenRouter.
- Hoofdstuk-drag-and-drop is in 0.18.8 verder gehard: de guard begint al bij mouse-down, alle editor/publicatie-autosave wordt tijdens de native drag gepauzeerd en boomrefreshes worden als één uitgestelde transactie afgehandeld.
- In 0.18.9 is de via crashlogging gevonden Windows access violation in `ManuscriptTree.paintEvent()` aangepakt: één viewport-painter, geen `QTreeWidgetItem`-referenties tijdens de native drag-loop en alleen een eenvoudige drop-lijn als custom drag-overlay.
- De bestaande Nederlandse en Engelse locale kunnen vanaf 0.18.7 via Instellingen worden gekozen; de programmataal wordt bij de volgende start geladen.
- In 0.18.10 is de interactiebaseline geharmoniseerd: toetsenbordfocus is zichtbaar op buttons, navigatie, keuzecontrols en lijsten; borderless controls reserveren hun focusrand zonder layoutverspringing; cursorsemantiek en focusuitzonderingen zijn expliciet vastgelegd.
- In 0.18.11 is de editor/hoofdchrome-audit uitgevoerd: expliciete I-beam in de schrijfruimte, volledige hover/pressed-pariteit voor editor- en railknoppen, keyboard-activatie van de Inhoud-boom, Escape/focus-terugkeer voor flyouts en rechterpanelen en gerichte Tab-volgordes voor editor, zoeken en spelling.
- In 0.18.12 zijn de gevonden editor-interactieregressies hersteld (Undo/Redo-state, single-click zoeknavigatie en stabiele Inhoud-selectie bij slepen/structuurrijen). Boekdetails en de gemelde Planning-flows zijn tegelijk verder geharmoniseerd en aan de locale-laag gekoppeld; Boekenplank, Instellingen en Over zijn opnieuw gecontroleerd zonder aanvullende wijzigingen.
- In 0.18.13 is de themafamilie uitgebreid van zes naar veertien kleurenschema's, met vier nieuwe frisse lichte varianten, Nord Licht en drie duidelijk donkere richtingen. De contrastpass is geautomatiseerd: normale/muted tekst, focus, primaire acties en status-/hero-kleuren worden per thema op vaste minima getest.
- In 0.18.14 zijn de resterende Planning-, Publicatie-, Historie- en Prullenbakflows langs dezelfde interactie- en locale-regels gelegd. Publicatie heeft consistente zichtbare Opslaan-dirty-states, Historie/Prullenbak zijn volledig keyboard-bruikbaar en de Windows-schrijfruimte gebruikt kleur-neutrale grayscale font-antialiasing met volledige hinting.

**Nog open in deze polish-iteratie**
- Alleen de handmatige eind-smoketest op 100%, 125% en 150% DPI en op lage laptophoogte staat nog uitgesteld op verzoek; de structurele layout-hardening is eerder al getest.

### Iteratie 19 — Publicatie-export — gestart in 0.19.1

**Afgerond in 0.19.1**
- Aparte Exporteren-pagina direct onder Boekdetails met EPUB, Markdown en een gereserveerde PDF-kaart.
- Eén immutable ExportDocument-snapshot als grens tussen opslag/publicatie-inhoud en renderers.
- Lichte EPUB 3-renderer zonder nieuwe dependency, inclusief package/nav/XHTML/CSS, metadata, publicatiestructuur en atomische uitvoer.
- Templates Klassiek, Modern en Literair.
- Omslagmodi: QuietWriter zet titel/auteur op tekstloos artwork, of gebruikt een reeds complete omslag zonder extra tekst.
- Generiek assetmodel voorbereid op toekomstige inline afbeeldingen.
- Boektaal als aparte metadata en EPUB-preflight voor essentiële publicatiegegevens.
- Bestaande Markdown-export verhuisd van Boekdetails naar Exporteren.
- In 0.19.2 is Markdown vastgezet op het bestaande publicatiecontract (`title/date/slug/description/meta/intro/author/tags`) en zijn de optionele frontmatter-/sectietoggles verwijderd. Een los enkelhoofdstukverhaal krijgt geen redundante H1.

**Volgende stappen**
- EPUB in echte readers blijven valideren (Calibre/Kobo/Apple Books indien beschikbaar) en gevonden compatibiliteitsdetails aanscherpen.
- PDF-spike uitvoeren met de bestaande PySide6-stack. Alleen toevoegen als nette vaste pagina-opmaak zonder zware nieuwe library of Windows-component mogelijk blijkt.
- Later: echte exportpreview en aanvullende print-/EPUB-fijninstellingen als daar praktische behoefte aan ontstaat.

### Iteratie 20 — Media & afbeeldingen — gestart in 0.20.0

**Afgerond in 0.20.0**
- Book-local `assets/`-structuur met gescheiden `images/` en `cover/` plus een klein `manifest.json`.
- UUID-bestandsnamen, SHA-256-integriteitsmetadata en deduplicatie; inline JPG/JPEG en PNG als eerste ondersteunde formaten.
- Afbeelding toevoegen vanuit de bestaande rechterrail met preview, alt-tekst en optioneel onderschrift; bron blijft standaard Markdown en de afbeelding is altijd een eigen blok.
- Image-aware woordtelling, spelling, zoeken en AI-context zodat opslagpaden geen prozestatistieken of taaltools vervuilen.
- `ExportDocument` verzamelt inline media als immutable assets; EPUB embedt ze met semantische figure/caption-markup en preflight detecteert ontbrekende of gewijzigde media.
- Historie/snapshots nemen assets mee zonder nieuwere immutable UUID-binaries automatisch te verwijderen.
- Nieuwe covers zijn book-local; bestaande globale covers blijven als legacy fallback werken.

**Afgerond in 0.20.1**
- Kritieke editorhotfix voor dubbele Enter: gewone Return/Enter gebruikt expliciete block-insertie en lege paragrafen krijgen een volledige minimum-regelhoogte zodat lege alinea's niet meer visueel inklappen.

**Afgerond in 0.20.2**
- Beschermde visuele afbeeldingsblokken in de manuscriptruimte: thumbnail/placeholder in plaats van ruwe Markdown, met expliciete Bewerken/Verwijderen-acties.
- Het bewezen prototypepatroon gebruikt echte gereserveerde QTextBlock-hoogte en `blockBoundingRect()` voor stabiele positionering zonder nieuwe custom-paintlaag.
- Kaartklik selecteert alleen; Enter/Bewerken opent het bestaande Afbeelding-paneel in editmodus. Verwijderen volgt de gelokaliseerde Ja/Nee-dialogen.
- Imageblokken zijn beschermd tegen directe tekstmutaties, selecties, paste/cut en drag/drop terwijl de Markdown-bron ongewijzigd de source of truth blijft.

**Volgende stappen**
- 0.20.3: portable Markdown-export met `<slug>-assets/` companionmap en herschreven relatieve links.
- Daarna: editor-image UX verder verfijnen op basis van praktijkgebruik; geen nieuwe renderinglaag tenzij daar een concrete behoefte uit volgt.
- Later: media-inspectie/ongebruikte-assets opruimen met historie-awareness en eventueel expliciete e-bookoptimalisatie voor zeer grote afbeeldingen.

### AI-verfijning — later

De gewone schrijfchat blijft leidend; deze iteratie is bewust naar beneden geschoven.

- Alleen snelacties toevoegen die in echt gebruik vaak terugkomen, bijvoorbeeld Feedback, Herschrijf selectie of Persona-check.
- Snelacties zijn alleen vooraf ingevulde prompts; geen aparte AI-logica.
- OpenRouter uitgebreider testen.
- Geen RAG/bibliothecaris tenzij daar later opnieuw een duidelijke behoefte aan ontstaat.

### Release en robuustheid

- In 0.19.3 is de startup-flow afgerond met een splash die pas sluit zodra het hoofdvenster werkelijk zichtbaar is. In 0.19.4 is de presentatie teruggebracht tot één QuietWriter-titel en is Over compacter gemaakt: intro, privacy, copyright, benoemde technische omgeving en fontlicenties; Over staat direct onder Spelling in de instellingen-navigatie.
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
