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

## Code-review herstelprogramma — hogere prioriteit, gestart in 0.21.1

De bestaande productroadmap blijft actief. De volledige externe code-review vormt tijdelijk een **hogere-prioriteitslaag** vóór nieuwe featurebouw, omdat meerdere bevestigde bevindingen data-integriteit, hoofdstukbeheer, publicatiegegevens, AI-gesprekken en spelling raken. Iedere bevinding wordt eerst tegen de actuele releasecode getoetst; bevestigde fixes krijgen een regressietest en worden per samenhangend domein uitgebracht.

**Afgerond**
- **0.21.1:** ontbrekende `QMenu`-import gerepareerd en `CurrentPageStack` laat de actieve pagina zijn expliciete minimummaat afdwingen zonder verborgen pagina's weer de venstergrootte te laten bepalen.
- **0.21.2:** de afzonderlijk aangeleverde en geteste manuscript-Undo-patch is geïsoleerd geïntegreerd. Actieve lege vervolgalinea's gebruiken hetzelfde line-height/marge-format als hun toekomstige normale alinea, Undo/Redo onderdrukt formatting-scheduling tijdens de Qt-operatie en Ctrl+Z/Ctrl+Y wordt expliciet door de editor-overrides geleid.
- **0.21.3:** hoofdstuk-/sectiemutaties zijn rollback-safe gemaakt bij mislukte manifest-writes. `delete_chapter()` bewaart eerst een recoverable trashkopie en verwijdert de live bron pas na een geslaagde manifestcommit. Drag/reorder wordt na een opgelost extern conflict opnieuw tegen de actuele boekstructuur toegepast, zodat de actie niet meer stil verloren gaat.
- **0.21.4:** hoofdstuk-trash is nu zichtbaar, herstelbaar en definitief opruimbaar vanuit dezelfde Prullenbak als boeken. Nieuwe trashitems bewaren sectie/positie-metadata, legacy 0.21.3-items blijven herstelbaar, restore is rollback-safe en het definitief verwijderen/legen van de prullenbak ruimt ook hoofdstukinhoud op. De hoofdstuk-/sectie-tekstprompts zijn tegelijk gelokaliseerd naar Opslaan/Annuleren.
- **0.21.5:** publicatie- en planningdata zijn verder gehard: same-book publicatienavigatie bewaart pending wijzigingen, character/outline-writes gebruiken candidate/rollback-patronen, verweesde scènes blijven zichtbaar, personageverwijdering ruimt scèneverwijzingen op, nieuw-personage-drafts krijgen save/discard/cancel bij boekwissel en boekverwijdering wordt vóór de trash-move geblokkeerd als planning/manuscript niet veilig kunnen worden opgeslagen. Het hoofdstuk-contextmenu bevat nu ook Verwijderen en alle hoofdstuk-/sectie-tekstprompts gebruiken een eigen gelokaliseerde Opslaan/Annuleren-dialoog.
- **0.21.6:** AI-workers zijn geïsoleerd per boekgeneratie/request/worker, waardoor late callbacks nooit meer een ander boekgesprek kunnen muteren of opslaan. Boekwissels blokkeren niet meer op netwerkcancel; alle workers worden wel veilig bijgehouden voor afsluiten. Provider/model-keuzes zijn direct provider-specifiek gesynchroniseerd, AI-context heeft stale/read-error guards en de Toevoegen-flyout gebruikt subtielere hoeken.
- **0.21.7:** spellingcontrole behandelt hoofdletterwoorden weer via de echte woordenboekregels, leest `.dic` volgens de `SET`-encoding uit `.aff` met veilige fallback en navigeert na globale negeer-/woordenboekacties op tekstoffset zodat verschuivende foutlijsten geen woord meer overslaan.
- **0.21.8:** export valideert nu ook pass-through covers en quote YAML-gevoelige publicatiefrontmatter veilig; crashlogging valt bij een onschrijfbare workspace terug op de OS-tempmap en roteert bij 2 MiB; woordenboeklabels/inferentie tonen veel meer locales als nette **Taal — Land**-namen zonder half-vertaalde fallback.
- **0.21.9:** Ollama-timeout wordt daadwerkelijk gerespecteerd; OpenRouter toont API-foutdetails; mislukte image-replacement houdt het echte bestandslabel; dubbele scene-breaks naast de cursor zijn voorkomen en met regressietests afgedekt.
- **0.21.10:** AI-modelophalen geeft zichtbare voortgang/succesfeedback en de modelkeuze is selection-only. De cleanup verwijdert dode exportcode, voorkomt dubbele woordtelling en `QSettings`-constructie in paint-hotpaths, ruimt veilige lintbevindingen op en breidt AI/export/performance-regressiedekking uit. Het externe code-review herstelprogramma is hiermee afgerond.

**Status reviewreeks**
- **Afgerond in 0.21.10.** Nieuwe featurebouw volgt weer de bestaande productroadmap hieronder; de actuele prioriteit staat bij Iteratie 21.

## Code-review ronde 3 — hogere prioriteit vanaf 0.22.1

De volledige 0.21.10-codebase is opnieuw extern doorgelicht. De eerdere 0.21.x-fixes functioneren zoals bedoeld, maar de nieuwe review vond vooral samenhangsproblemen **tussen** pagina's: Editor, Planning, Boekdetails en Export konden verschillende `Book`-instanties voor hetzelfde boek vasthouden terwijl revisiebewaking per boek-id centraal is. Voor een Dropbox/twee-computers-workflow kan dat tot stil dataverlies leiden. Deze ronde krijgt daarom opnieuw voorrang boven productfeatures; de bestaande productroadmap blijft hieronder volledig behouden.

**Afgerond**
- **0.22.1 — Centrale live-bookstate:** één gecoördineerde `adopt_active_book(...)`-route deelt het actuele `Book`-object met Editor, Planning, Boekdetails en Export. Boekenplank-Openen herlaadt eerst `book.json`, Planning-conflicten hebben een driewaardige `mine/disk/failed`-uitkomst en stale Boekdetails-referenties worden na reload/conflict vervangen. Hiermee zijn reviewbevindingen 1, 2, 3 en 6 aangepakt.
- **0.22.2 — History-preview isolatie:** history-preview is editor-only en wordt bij hoofdnavigatie verlaten; Zoeken/Vervangen en Spelling kunnen snapshots niet muteren; gewone conflictlogica draait nooit op een archive-`Book`; versieherstel bij externe wijziging sluit preview, adopteert de nieuwste live disk-state en laat het archief ongemoeid. Hiermee zijn reviewbevindingen 4 en 5 aangepakt.
- **0.22.3 — Tekstintegriteit:** Alles vervangen werkt uitsluitend op treffers uit de gemaskeerde zoektekst en kan image-paths/UUID-syntax niet meer wijzigen; Spelling → Wijzigen valideert/re-ankert stale offsets; structuurconflicten zonder actief hoofdstuk krijgen zichtbare, veilige conflict-UX; instellingenpreview schrijft geen manuscriptopmaak meer in Undo en een opgeslagen schrijflayout start bewust met een schone presentatie-Undo-historie. Hiermee zijn reviewbevindingen 7, 8, 13 en 14 aangepakt.
- **0.22.4 — Exportcorrectheid + typografie-refresh:** de na 0.22.3 handmatig gevonden fontrefresh-regressie is gesloten voor het reeds geopende hoofdstuk; één Enter blijft één EPUB-alinea, gekruiste inline-opmaak wordt geldig gebalanceerd, publieke Markdown is export/import-round-trip-safe en inhoudsopgave-diepte met tussenkoppen wordt in `contents.xhtml` én `nav.xhtml` uitgevoerd. Hiermee zijn reviewbevindingen 9–12 aangepakt.
- **0.22.5 — Cache/startup/legacy storage:** de FTS-zoekdatabase is expliciet wegwerp-cache en herstelt/fallbackt zonder startup- of saveblokkade; legacy globale omslagen worden alleen nog gekoppeld aan pre-0.20-manifests zonder `cover_file`; een onbereikbare werkmap krijgt zichtbare mapkeuze/afsluit-UX; mislukte boekverwijdering houdt revision-tracking actief; Boekdetails commit metadata/omslag via een kandidaat met rollback; en een mislukte `last_used`-manifestwrite veroorzaakt geen vals conflict na een geslaagde hoofdstuksave. Hiermee zijn reviewbevindingen 15, 16, 17, 21, 22 en 23 aangepakt.
- **0.22.6 — AI en scene-break randgevallen:** annuleren tijdens de provider-connectfase blijft behouden; Ollama/OpenRouter mid-stream foutpayloads gaan via de normale fout-/conversation-save-route; same-book conflict/herstel vervangt alleen de AI-store zonder de actieve worker/generatie te annuleren; en een scènebreuk midden in tekst wordt naar een veilige regelgrens verplaatst. Hiermee zijn reviewbevindingen 18, 19, 20 en 24 aangepakt.

**Status reviewreeks**
- **Afgerond in 0.22.6.** Alle 24 bevindingen uit code-review ronde 3 zijn verwerkt.

## Code-review ronde 4 — stabiliteitsnaloop in 0.22.7

De volledige 0.22.6-codebase is opnieuw extern doorgelicht. Alle reproducties uit ronde 3 werken volgens de reviewer correct. De naloop vond nog vier afgebakende randgevallen rond legacy-omslagen, pending formulier/planningstate en de grens van beschermde afbeeldingssyntax.

**Afgerond**
- **0.22.7 — Pending-state en media-boundary hardening:** pre-0.20 globale omslagen met een later automatisch toegevoegd leeg `cover_file` blijven herkenbaar zonder nieuwe same-slug-boeken te besmetten; same-book Planning-adopt bewaart dirty notities en nieuwe personagedrafts buiten het conflictbestand; Boekdetails bewaart lokale velden en mergeert externe wijzigingen in onaangeraakte velden; en Zoeken/Vervangen weigert iedere treffer die beheerde image-syntax raakt, ook bij zoektermen met randspaties. Hiermee zijn alle vier bevindingen uit code-review ronde 4 aangepakt.

**Status reviewreeks**
- **Afgerond in 0.22.7.** Ronde 4 bevatte vier bevindingen; alle vier zijn verwerkt. De productroadmap is daarna herprioriteerd naar Iteratie 21: AI-profiel en boekgeheugen.

**Werkwijze per build**
- 🔴 bevestigde bevinding: eerst reproductie/regressietest, daarna gerichte fix.
- 🟡 vermoedelijke bevinding: eerst zelf reproduceren of expliciet als ontwerpbesluit beoordelen; niet blind wijzigen.
- ⚪ opschoning/efficiëntie: pas na de correctness- en data-integriteitsreeks, zodat functionele diffs klein en controleerbaar blijven.
- De bestaande roadmap hieronder blijft behouden. Zodra deze reviewreeks is afgerond, gaat de eerstvolgende open productiteratie gewoon verder.

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

**Afgerond in 0.20.3 / gecorrigeerd in 0.21.2**
- 0.20.3 bracht directe indent bij Enter en koppelde paragraph-layout aan de tekstbewerking, maar liet nog een Qt-undo-randgeval bestaan.
- 0.21.2 verwerkt de extern gereproduceerde root-cause-fix: actieve lege vervolgalinea en normale alinea hebben geen formattransitie meer bij de eerste letter, Undo/Redo onderdrukt formatting-scheduling tijdens de Qt-operatie en Ctrl+Z/Ctrl+Y wordt expliciet via de editor-overrides geleid.

### Iteratie 21 — AI-profiel en boekgeheugen — gestart in 0.23.0

De AI-laag krijgt voorrang boven de eerder geplande portable Markdown-media. De uitgangspunten zijn transparantie en gewone leesbare bestanden: geen verborgen geheugenlaag wanneer dezelfde informatie ook als Markdown inzichtelijk kan blijven.

**0.23.0 — Gestructureerde schrijverspersona — afgerond**
- `persona/schrijver.md` blijft de canonieke, human-readable bron.
- De app presenteert dezelfde inhoud als een profiel met vaste schrijfcategorieën.
- Legacy vrije persona-inhoud migreert zonder informatieverlies bij de eerstvolgende expliciete Opslaan.
- Drie bewerkbare voorbeeldpersona's als startpunt.
- AI blijft het complete Markdownbestand ongewijzigd als persona-context gebruiken.

**Volgende stappen**
- **0.23.1 — Boekprofiel — afgerond:** per boek een transparant `ai/boekprofiel.md` met genre/doelgroep, premisse, perspectief/tijd, sfeer, thema’s, setting, tempo/spanningsboog, intensiteit, persona-afwijkingen en redactionele aandachtspunten. De laag is revision-bewaakt, gaat mee in History/herstel en wordt door AI na de globale persona als projectspecifiek kader gebruikt.
- **0.23.2 — Boekgeheugen — afgerond:** transparant `ai/memory.md` per boek met Canon & feiten, Stijl van dit boek, Besluiten, Terugkerende voorkeuren en Open aandachtspunten. Het bestand is volledig zichtbaar/bewerkbaar, revision-bewaakt en wordt als aparte AI-contextlaag meegestuurd; AI schrijft er in deze release nooit zelfstandig in.
- **0.23.3 — Geheugenvoorstellen — afgerond:** AI controleert relevant Boekgeheugen actiever tegen manuscriptcontext en kan maximaal twee duurzame geheugenregels voorstellen. Onthouden, Bewerken of Negeren blijft altijd een expliciete gebruikerskeuze; AI schrijft nooit autonoom naar `memory.md`.
- **0.23.4 — Planningcontext — afgerond:** specifieke personages, scènes en optioneel Planning-notities kunnen gericht als AI-context worden geselecteerd zonder Planning-data naar Boekgeheugen te dupliceren. Manuscript, Planning en Boekgeheugen hebben expliciet verschillende rollen.
- **0.23.5 — AI-context/geheugenactie hardening — afgerond:** geheugenvoorstellen geven deterministische opslagfeedback en binden eerst aan het actieve boek; Planning-context is letterlijk inspecteerbaar in Context bekijken en wordt als expliciet geselecteerde context sterker in de systeemprompt gepositioneerd.
- **0.23.6 — Onthouden hotfix — afgerond:** goedgekeurde geheugenvoorstellen worden als reeds samengestelde geheugenstate opgeslagen en kunnen niet meer vlak vóór de write door de stale Boekgeheugen-editor worden teruggedraaid.
- **0.23.7 — Geheugenbevestiging — afgerond:** geslaagde Onthouden-acties geven een subtiele, blijvende QuietWriter-bevestiging in de AI-chat; deze lokale notices worden niet terug naar het model gestuurd.
- **0.23.8 — AI-snelacties — afgerond:** vier bewerkbare prompttemplates in het AI-paneel: Feedback, Herschrijf selectie, Persona-check en Feitencheck. Snelacties versturen nooit automatisch; Herschrijf selectie is alleen actief bij echte manuscriptselectie.
- **0.23.9 — Compacte AI-zijbalk en thinking-regie — afgerond:** de chat krijgt weer de meeste ruimte; Context en Snelacties zijn inklapbare hulpmiddelen onder de composer, Huidig hoofdstuk is impliciet de standaardcontext, Context bekijken gebruikt een aparte inspectiedialoog en AI-instellingen kunnen provider-thinking expliciet uitschakelen.
- **0.23.10 — Thinking-capabilities zichtbaar — afgerond:** modeldetectie leest provider-metadata en markeert alleen modellen waarbij thinking aantoonbaar uitschakelbaar is met 🧠; model-id en presentatielabel blijven gescheiden en de thinking-instelling volgt bekende capability-state.
- **0.23.11 — Ollama thinking-capability fallback — afgerond:** `/api/show.capabilities` wordt gebruikt wanneer gedetailleerde thinking-controlmetadata ontbreekt; 🧠 staat voor thinking/reasoning-support en de UI onderscheidt bekende uitschakelbaarheid van een capability-only `think:false`-verzoek.
- **0.24.0 — Afbeeldingslayout — afgerond:** relatieve breedte, links/midden/rechts en eenvoudige tekstomloop zijn als leesbare Markdown-metadata toegevoegd; de editor geeft de intentie rustig weer en EPUB rendert de layout met relatieve CSS/float zonder een nieuwe custom-renderlaag.
- **0.25.0 — PDF-export MVP — afgerond:** de twee afzonderlijke Qt-spikes hebben vaste A5-paginering, running headers/paginanummers, hoofdstukstarts, afbeeldingslayout en paginagrensgedrag voldoende aangetoond. PDF is nu een echte exportkeuze met A5/A4, margepresets, templates en een veilige no-wrap fallback voor lange onderschriften.
- **0.25.1 — code-review ronde 5 — afgerond:** PDF-DPI en afbeelding/onderschrift-paginering gecorrigeerd; Planning bewaart lokale notities/personagebewerkingen conflict-aware zonder externe tekst stil te overschrijven; `##`-regels zijn round-trip-safe in Persona/Boekprofiel/Boekgeheugen; persona-afsluitguard en thinking-capabilityguard toegevoegd; verouderde AI-racetests bijgewerkt.
- **0.25.2 — code-review ronde 6 — afgerond:** Qt-racetestfixtures gecorrigeerd; PDF-documentmarge op nul; startup thinking-capability direct gecachet; drie-wegs same-field merge + herstelversie voor Boekprofiel/Boekgeheugen/Boekdetails; letterlijke backslashes vóór `##` volledig round-trip-safe.
- **0.26.0 — EPUB-validatie en reader-navigatie — afgerond:** verpakte EPUB wordt vóór commit intern op container/package/manifest/spine/nav en lokale resource-/fragmentverwijzingen gecontroleerd; reader-landmarks wijzen naar Inhoud en het begin van het manuscript.
- **0.27.0 — Media Manager — afgerond:** book-local afbeeldingen hebben een deterministische inventaris met gebruik/integriteit/history-status; ongebruikte manifestassets kunnen veilig in één cleanupbatch worden verwijderd na een automatisch herstelpunt, terwijl ongeregistreerde bestanden en onzekere historische afhankelijkheden conservatief blijven staan.
- **0.27.1 — Media Manager runtime-hardening — afgerond:** herstelbare prullenbakhoofdstukken beschermen hun assets; batch-cleanup ruimt alleen de expliciet veilige subset op; externe wijzigingen verlaten de Media-foutlus via de centrale live-book/conflictflow.
- **Volgende:** niet-visuele product-/releasehardening die volledig geautomatiseerd of headless getest kan worden; visuele polish alleen op basis van concrete praktijkfeedback.

**Productstappen na 0.25.0**
- **PDF-export MVP — afgerond:** Qt-route bewezen en geïntegreerd met A5/A4, margepresets, templates, headers/footers, publicatiestructuur en afbeeldingen. Verdere printfijninstellingen alleen op basis van praktijkgebruik.
- **EPUB-reader-validatie — 0.26.0 technisch afgerond:** interne archive-/linkvalidatie en minimale reader-landmarks toegevoegd. Calibre blijft eerste praktijkreferentie; andere readers alleen gericht testen en alleen concrete compatibiliteitsproblemen oplossen.
- **Editor-image polish:** alleen verdere verfijning wanneer praktijkgebruik daar aanleiding toe geeft; geen complexe DTP-/custom-renderlaag.
- **Media-inspectie/ongebruikte-assets opruimen — afgerond in 0.27.0.** Eventuele automatische e-bookoptimalisatie voor zeer grote afbeeldingen blijft later en alleen bij concrete behoefte.
- Markdown-export blijft technisch beschikbaar maar is geen actieve productprioriteit; portable companion-assets worden pas heroverwogen bij concrete behoefte.
- OpenRouter uitgebreider blijven testen binnen de gewone schrijfchat.

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

### 0.28.0–0.28.4 — Integriteit & migratiebasis — reviewfase
- Read-only boekaudit voor structurele/inhoudelijke beschadiging zonder silent fallback.
- Gericht History-herstel met checkpoint en revision guard.
- Expliciete, atomische en opeenvolgende boekformaatmigraties; geen stille migratie tijdens openen.
- **0.28.1:** runtime/failure-injectionbevindingen verwerkt: future-format guard bij werkelijk openen, onbekende manifestvelden round-trip-safe, gedeelde load/audit-validatie, inhoudelijk gevalideerde herstelbronnen, byte-exact herstel, deterministische History-volgorde, genormaliseerde duplicate-detectie en strikt atomische writes zonder directe-overwritefallback.
- **0.28.2:** UI/storage-grens gehard: één `StorageWriteError`, dirty/autosave/close-failsafes bij locks, future-format conflict bewaart lokale tekst en sluit het incompatibele boek veilig, metadata-validatie voltooid en binaire herstelwrites delen de retrylogica.
- **0.28.3:** future-format veilig loskoppelen gecentraliseerd en Boekdetails-saveguards toegevoegd.
- **0.28.4:** detach is write-blocked en save-vrij; Boekdetails heeft nu ook de normale external-change merge/uitweg.
- **Status:** afgerond en runtime groen bevonden door Claude; 0.29.0 bouwt hierop voort.

**Vervolg na integriteits-UI — Planning dichter bij schrijven (ideeën uit reviewronde 10):** eerst een inklapbaar “In dit hoofdstuk”-blok met gekoppelde scènes/personages, daarna zichtbare automatische AI-context en planning-referenties in de integriteitsaudit. Lokale aliasherkenning kan daarna volgen. Hoofdstukvolgorde blijft bewust op één plek muteerbaar; de outline krijgt geen tweede drag-and-drop structuurbron.
- Volgende stap na groen: een rustige Integriteit/Herstel-UI bovenop deze service; daarna alleen aanvullende herstelgevallen wanneer runtime-tests concrete gaten tonen.


## Na 0.29.0

### 0.30 — Editor polish
- Spellingscontrole samen met Claude technisch herontwerpen: selectie/cursor, suggesties en robuuste contextinteractie; hover alleen als dat betrouwbaar blijkt.
- Automatisch opslaan altijd aan; instelling verwijderen. `Ctrl+S` blijft als expliciete directe save.
- Woordtelling in Inhoud verduidelijken naar bijvoorbeeld **Boek bevat 12.345 woorden**.

### 0.31 — Rustigere navigatiestructuur
- Met kleine tussenkoppen/visuele scheiding onderscheid maken tussen Boekenplank, onderdelen van het geopende boek en algemene functies.
- Schrijverspersona blijft een zelfstandige schrijffunctie en verhuist niet naar Instellingen.
- Geen grote navigatie-herbouw; rust en herkenbaarheid behouden.

### 0.32 — Planning tijdens het schrijven
- Pas na stabiliteit en UI-polish: rustig blok **In dit hoofdstuk** met gekoppelde scènes/personages.
- Daarna zichtbare AI-context en planning-integriteit verder uitbouwen.

### Later onderzoek
- Reedsy en vergelijkbare schrijfsystemen systematisch vergelijken voordat nieuwe grote schrijf-/publicatiefuncties worden gekozen.

## 0.29.1 — Integriteit/live-workspace aansluiting

- Centrale reload vóór audit en na herstel.
- Stale editorstate mag herstelde inhoud niet meer overschrijven.
- Extern verdwenen/beschadigde bestanden zijn direct vanuit Integriteit herstelbaar zonder omweg via Boekenplank.
- Geblokkeerde en future-format boeken blijven fail-closed/read-only.
- Recovery lookup per audit gecachet.
- Daarna: 0.30 Editor polish (autosave altijd aan, woordtelling, spelling eerst technisch ontwerpen met Claude).


## 0.29.2–0.29.4 — Corrupte tekst fail-closed
- 0.29.2 maakte Integriteit bereikbaar bij ongeldige UTF-8 en gaf betrokken pagina's een alleen-lezen foutstaat.
- 0.29.3 verplaatst de doorslaggevende bescherming naar storage: gewone saves mogen een bestaande corrupte tekstbron nooit vervangen.
- UI-flags voorkomen daarnaast zinloze/misleidende mutatieacties op een beschadigd hoofdstuk, Boekgeheugen of Boekprofiel.
- Expliciet herstel via Integriteit blijft de enige route die corrupte bronbytes mag vervangen.
- 0.29.4 voorkomt dat de hoofdstuk-corruptievlag naar Voorwerk/Achterwerk lekt en maakt zoeken/vervangen/dupliceren bestand tegen corrupte andere hoofdstukken.
- Na runtime-groen kan 0.29.x worden afgesloten; de transactionele `adopt_active_book()`-verbetering blijft bewust voor 0.30.0.

### 0.30.0 extra stabiliteit
- Maak `adopt_active_book()` transactioneel/all-or-nothing zodat een mislukte reload nooit pagina’s met verschillende Book-instanties achterlaat.


## 0.31.0 — Navigatie en kleine editorpolish

Afgerond in deze release: subtiele navigatiegroepen, autosave altijd aan en expliciete boektelling. Schrijverspersona blijft een zelfstandige globale schrijffunctie en is niet onder Instellingen geplaatst.

Vervolg: transactionele/all-or-nothing adoptie van een live boek en daarna de spellingsarchitectuur technisch laten beoordelen vóór wijzigingen aan de spellings-UX.
