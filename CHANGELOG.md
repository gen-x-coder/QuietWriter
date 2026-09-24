# Changelog

## 0.23.0 — Gestructureerde schrijverspersona

- De Schrijverspersona is opnieuw ontworpen als een begrijpelijk profiel met twaalf vaste onderdelen: Stem & toon, Vertelstijl, Taal & woordkeuze, Zinnen & ritme, Beschrijving & zintuigen, Dialoog & interactie, Emotie/spanning/intimiteit, Scènes & verteltempo, Redactionele voorkeuren, Vermijden, Voorbeeldteksten en Aanvullende instructies.
- `persona/schrijver.md` blijft de enige bron voor AI en blijft gewone, buiten QuietWriter leesbare Markdown. De nieuwe UI is uitsluitend een presentatie- en bewerkingslaag boven dat bestand.
- Bestaande vrije persona's worden zonder inhoudsverlies ingelezen. Zolang zij de nieuwe koppen nog niet gebruiken, staat de volledige oude inhoud in Aanvullende instructies; bij Opslaan wordt het bestand naar de nieuwe gestructureerde Markdownvorm geschreven.
- Drie bewerkbare voorbeeldpersona's toegevoegd: Jane Austen (sociale observatie/ironie), Arthur Conan Doyle (observatie/mysterie/voortgang) en Virginia Woolf (innerlijke waarneming/associatief ritme). De voorbeelden gebruiken brede stijlkenmerken en bevatten geen overgenomen auteurstekst.
- De persona-pagina toont expliciet het pad naar `schrijver.md`, heeft een zichtbare dirty-state en schrijft pas bij Opslaan naar schijf. Wisselen tussen onderdelen bewaart lokale invoer in het formulier.
- Nieuwe werkmappen starten direct met het gestructureerde Markdowncontract; bestaande werkmappen worden niet automatisch herschreven.
- De AI-promptsemantiek is bewust niet gewijzigd: AI leest nog steeds exact het complete `schrijver.md` als schrijversprofiel.
- Pakketversie naar 0.23.0 verhoogd.

## 0.22.7 — pending-state en media-boundary hardening

- De legacy-omslagdetectie uit 0.22.5 gebruikt niet langer alleen het ontbreken van `cover_file`. Oude pre-0.20-boeken die door 0.20–0.22 al eens zijn geopend en daardoor inmiddels `"cover_file": ""` bevatten, kunnen hun globale `boekomslagen/<slug>.*` weer eenmalig adopteren zolang de 0.20+ book-local `assets/manifest.json`-marker ontbreekt. Nieuwe boeken met dezelfde slug blijven geïsoleerd.
- Same-book adopt/reload in Planning bewaart dirty Notities en een nog niet opgeslagen nieuw-personage-concept wanneer het conflict in een ander planningsbestand zit. Dirty notities worden vóór de reload bovendien in de lokale conflictversie opgenomen, zodat ze niet alleen in RAM overleven. Het planningbestand waarover de gebruiker expliciet een conflictkeuze maakte blijft wel autoritatief herladen.
- Navigeren naar Boekdetails forceert eerst de pending editor/publicatie-save, zodat een achterlopende autosave niet pas bovenop een reeds bewerkt formulier een conflict opent. Als een same-book adopt toch plaatsvindt terwijl Boekdetails lokale wijzigingen bevat, blijft dezelfde pagina bestaan en worden alleen onaangeraakte velden met de nieuwste externe waarden gemerged; lokale velden en een pending omslag blijven staan.
- Zoeken/Vervangen gebruikt naast de lengtevaste image-maskering nu expliciete beschermde bronranges. Een treffer met een begin- of eindspatie mag daardoor niet meer over de grens tussen alt-/captiontekst en beheerde Markdown-image-syntax lopen. `Vervangen`, `Alles vervangen` en het getoonde resultaataantal gebruiken dezelfde veilige matchset.
- Nieuwe regressietests dekken de vier bevindingen uit code-review ronde 4, inclusief een pre-0.20-omslag met reeds aanwezige lege `cover_file`, image-boundary zoektermen en source-invariants voor pending-state adopt.
- Pakketversie naar 0.22.7 verhoogd.

## 0.22.6 — AI-streamintegriteit en scènebreuk-randgevallen

- **Stop AI** blijft nu geldig wanneer de gebruiker annuleert terwijl Ollama of OpenRouter nog in `requests.post()` wacht op modelstart/responseheaders. De cancelstatus wordt vóór de aanvraag gereset en `_set_active()` wist hem niet meer zodra de response later beschikbaar komt; de response wordt dan direct gesloten zonder alsnog tokens te verwerken.
- Ollama- en OpenRouter-streams herkennen providerfouten die met HTTP 200 midden in een stream worden meegestuurd. Een `error`-payload wordt als `RuntimeError` met de providerdetails doorgegeven aan de bestaande AI-foutafhandeling, zodat de gebruikersvraag plus foutmelding bewaard blijven in plaats van als een leeg, zogenaamd geslaagd antwoord te verdwijnen.
- `AIPanel.set_book()` maakt onderscheid tussen een echt ander boek en een nieuw `Book`-object met hetzelfde boek-id. Conflictresolutie of versieherstel van hetzelfde live boek ververst alleen het `ConversationStore`-pad; een lopende AI-worker, boekgeneratie, chatbuffer en nog niet opgeslagen gebruikersvraag blijven intact. Een echte boekwissel houdt de bestaande strikte worker-isolatie uit 0.21.6.
- Scènebreuk invoegen knipt nooit meer midden door een lopende regel. Staat de cursor midden in tekst, dan wordt `***` na het einde van die regel geplaatst; staat de cursor al aan het begin van een regel/alinea, dan komt de breuk ervoor. Voorloopspaties aan de rechterkant van de invoeggrens worden genormaliseerd en de bestaande bescherming tegen dubbele aangrenzende scènebreuken blijft actief.
- Nieuwe regressietests dekken annuleren tijdens de verbindingsfase voor beide providers, mid-stream foutpayloads, scènebreuken midden in een zin en — waar PySide6 beschikbaar is — AI-continuïteit tijdens same-book adopt/reload.
- Code-review ronde 3 (bevindingen 1–24) is hiermee volledig verwerkt; de productroadmap kan weer worden hervat.
- Pakketversie naar 0.22.6 verhoogd.

## 0.22.5 — cache, startup en legacy-storage hardening

- `.cache/book_search.db` is nu expliciet een wegwerp-cache. Een corrupte/half-gesynchroniseerde SQLite-database wordt verwijderd en opnieuw opgebouwd; als zelfs de schijfcache niet bruikbaar is, valt QuietWriter terug op een in-memory index. Cacheproblemen mogen startup of manuscript-save daardoor niet meer blokkeren.
- Legacy globale omslagen worden niet langer op basis van alleen de huidige slug gevonden. Alleen een manifest van vóór 0.20 dat het veld `cover_file` nog niet bevat kan bij laden een bestaande `boekomslagen/<slug>.*` als expliciete legacy-omslag adopteren. Nieuwe boeken met dezelfde titel erven die omslag dus niet, en **Omslag verwijderen** verwijdert nooit meer een toevallig gelijknamige globale omslag van een ander boek.
- Een onbereikbare werkmap veroorzaakt bij startup geen stille `pythonw`-crash meer. QuietWriter toont de betreffende map en fout en biedt **Andere map kiezen…** of **Afsluiten**; een succesvol gekozen alternatief wordt als nieuwe werkmap opgeslagen.
- `delete_book()` schakelt revision-tracking pas uit nadat de verplaatsing naar de prullenbak werkelijk is geslaagd. Een Windows-/Dropbox-lock laat een niet-verwijderd boek dus beschermd en getrackt achter.
- Boekdetails bouwt titel/metadata voortaan in een deep-copy kandidaat op. Coverwijzigingen worden als één guarded transactie voorbereid en bij een mislukte manifestcommit teruggedraaid; pas na volledig succes worden titel/metadata in het gedeelde live `Book`-object overgenomen. Een mislukte Boekdetails-save kan daardoor niet later via editor-autosave alsnog stil worden weggeschreven.
- `save_chapter()` behandelt `last_used` als best-effort metadata. Als de hoofdstuktekst wel is opgeslagen maar `book.json` tijdelijk niet kan worden bijgewerkt, blijft de tekstsave geldig en wordt de revision-baseline meteen naar de werkelijk opgeslagen hoofdstukinhoud verzet. De volgende save ziet daardoor geen vals extern conflict over de eigen tekst.
- Nieuwe regressietests dekken reviewbevindingen 15, 16, 17, 21, 22 en 23, inclusief corrupte cache, same-slug legacy covers, delete-tracking en coverrollback bij mislukte Boekdetails-persistentie.
- Pakketversie naar 0.22.5 verhoogd.

## 0.22.4 — exportcorrectheid en directe typografie-refresh

- Een opgeslagen wijziging van schrijflettertype of tekstgrootte wordt nu ook expliciet op alle reeds aanwezige tekens van het **al geopende hoofdstuk** toegepast. Alleen widget/document-defaults wijzigen bleek onvoldoende: bestaande `QTextCharFormat` kon de vorige font blijven tonen tot een hoofdstuk opnieuw werd geladen. Na de basisfont-pass legt de manuscript-highlighter koppen, inline-opmaak, code en verborgen Markdown-markers opnieuw aan.
- EPUB-rendering volgt nu QuietWriter's documentmodel: iedere niet-lege manuscriptregel / ieder `QTextBlock` wordt een eigen `<p>`. Eén Enter blijft daardoor één alinea in de EPUB in plaats van door CommonMark-achtige soft-line folding met de volgende regel te worden samengevoegd.
- Overlappende selectie-opmaak wordt bij EPUB-export stack-gebaseerd gebalanceerd. Gekruiste combinaties zoals `**een *twee** drie*` en vet + doorhalen produceren geldige geneste XHTML doordat doorlopende binnenste tags zo nodig tijdelijk worden gesloten en heropend.
- De Markdown-importer decodeert nu de double-quoted JSON/YAML-scalars die de publieke Markdown-export sinds 0.21.8 bewust schrijft. Ook eenvoudige single-quoted YAML-scalars worden ontquote. Titel, beschrijving, tags en andere scalars stapelen daardoor geen letterlijke quotes/escapes meer op bij export → import → export.
- `##`-tussenkoppen krijgen in EPUB-hoofdstukken stabiele `h-1`, `h-2`, … anchors. Staat de publicatie-inhoudsopgave op **Hoofdstukken + tussenkoppen**, dan verschijnen die koppen als geneste links in zowel `contents.xhtml` als EPUB 3 `nav.xhtml`; bij **Alleen hoofdstuktitels** blijven ze bewust afwezig.
- De ingebouwde XML-controle vermeldt bij eventuele resterende ongeldige EPUB-XHTML het betreffende document/hoofdstuk in plaats van alleen een kale parserfout.
- Nieuwe regressietests dekken de handmatig gevonden 0.22.3-fontrefresh-regressie en reviewbevindingen 9–12.
- Pakketversie naar 0.22.4 verhoogd.

## 0.22.3 — tekstintegriteit, stale spelling en conflict-UX

- **Alles vervangen** gebruikt nu exact dezelfde lengtevaste image-maskering als Zoeken. Alleen treffers die in de gemaskeerde tekst zichtbaar zijn worden op de corresponderende offsets van de originele Markdown vervangen; beheerde image-paths, UUID-bestandsnamen en Markdown-syntax blijven daardoor byte-for-byte intact. Alt-tekst en onderschriften blijven bewust gewone zoekbare tekst.
- **Spelling → Wijzigen** controleert vóór iedere mutatie of de opgeslagen `start:end`-offset nog steeds exact naar hetzelfde fout gespelde woord wijst. Is de editor of hoofdstuktitel intussen gewijzigd, dan wordt de foutenlijst ververst en de dichtstbijzijnde gelijke treffer opnieuw geankerd; bestaat die niet meer, dan wordt niets gewijzigd.
- Structuuracties vanuit Voorwerk/Achterwerk mislukken niet langer stil wanneer `self.chapter is None`. QuietWriter toont een expliciete externe-wijzigingsdialoog, kan de nieuwste live boekstate centraal adopteren en meldt dat de oorspronkelijke structuuractie niet is uitgevoerd. Niet-opgeslagen publicatievelden worden daarbij nooit stil weggegooid: die moeten eerst via hun eigen conflictpad worden opgeslagen/opgelost.
- De instellingenpagina past schrijflettertype, tekstgrootte, regelafstand, inspringing en alinearuimte tijdens het wijzigen niet meer op de verborgen manuscripteditor toe. De bestaande fontkaart blijft de lokale preview; thema blijft wel live previewen. Na **Opslaan** wordt de schrijflayout één keer toegepast en alleen bij een echte layoutwijziging wordt de presentatie-Undo-historie opgeschoond, zodat Ctrl+Z geen onzichtbare font-/blokopmaakstappen meer tegenkomt.
- `UI_GUIDE.md` is weer onderdeel van de releasebron en documenteert dat instellingenpreview de manuscript-Undo-stack niet mag muteren.
- Nieuwe regressietests dekken beschermde image-paths, stale spellingsposities, publicatiecontext-conflictgedrag en de Undo-grens rond opgeslagen manuscriptstijl.
- Pakketversie naar 0.22.3 verhoogd.

## 0.22.2 — history-preview isolatie en veilig versieherstel

- History-preview is nu expliciet editor-only. Zodra de gebruiker naar Planning, Boekdetails, Export, Instellingen of een andere hoofdpagina navigeert, verlaat de editor de historische weergave en koppelt hij terug naar het live boek. Andere pagina's kunnen daardoor nooit een `archive/`-snapshot als actief werkboek erven.
- **Huidige treffer vervangen**, **Alles vervangen** en **Spelling → Wijzigen** hebben een extra read-only guard tijdens history-preview. Programmatic text mutations kunnen daardoor ook buiten de normale read-only-widgetbeveiliging geen archiefhoofdstuk aanpassen.
- De normale editor-conflictafhandeling weigert nu expliciet te draaien zolang `self.book` een historische snapshot is. De preview wordt eerst veilig verlaten; de gewone conflictresolver kan daardoor nooit een archive-pad tracken of beschrijven alsof het live is.
- **Deze versie herstellen** heeft een eigen conflictpad gekregen. Als het live boek tijdens de preview extern is gewijzigd, wordt herstel niet uitgevoerd, de preview gesloten, de nieuwste live schijfversie geladen en een gerichte melding getoond. De archive-snapshot blijft byte-for-byte ongemoeid.
- Een tijdelijke revision-verificatiefout tijdens herstel sluit eveneens veilig de preview zonder de gewone conflictroute op de snapshot los te laten.
- Normaal verlaten van history-preview verzet de revision-baseline bewust niet. Als Dropbox tijdens de preview iets wijzigde, blijft dat bij de eerstvolgende schrijfactie detecteerbaar; alleen een succesvol opnieuw van schijf geladen live boek wordt opnieuw centraal getrackt.
- Nieuwe regressietests dekken read-only guards, preview-exit bij hoofdnavigatie, de dedicated restore-conflictroute en — waar PySide6 beschikbaar is — echte MainWindow-scenario's waarin Planning/Export en een extern restore-conflict het archief niet wijzigen.
- Pakketversie naar 0.22.2 verhoogd.

## 0.22.1 — centrale live-bookstate en conflictintegriteit

- QuietWriter heeft nu één centrale live-bookreferentie in `MainWindow`. Een vers geladen boek wordt via `adopt_active_book(...)` in één stap gedeeld met Editor, Planning, Boekdetails en Export; de editor koppelt daarbij het open hoofdstuk opnieuw aan het nieuwe `Book`-object.
- Conflictoplossing in Planning en Publicatie gebruikt dezelfde centrale adopt-route. Een verschoven revision-baseline kan daardoor niet meer samengaan met een editor die nog oude hoofdstuktekst of een verweesd `Chapter`-object vasthoudt.
- Planning-persistentie rapporteert voortaan expliciet `mine`, `disk` of `failed`. Alleen bij `failed` wordt een lokale kandidaat teruggerold; de keuze **Versie op schijf gebruiken** wordt niet meer achteraf door de oude in-memory lijst overschreven.
- **Openen** vanaf de boekenplank werkt altijd met een opnieuw van schijf geladen manifest. `Library.touch_book()` schrijft alleen `last_used` naar die actuele structuur en kan een stale bookshelf-object dus niet meer gebruiken om extern toegevoegde hoofdstukken uit `book.json` te verwijderen.
- Boekdetails wordt bij iedere centrale live-book-adopt opnieuw aan exact hetzelfde object gekoppeld. Na een conflict of versieherstel kan de pagina daardoor geen oude boekstructuur/metadata meer terugschrijven die de editor later weer ongedaan maakt.
- `PublicationEditor` heeft een expliciete `adopt_book()`-route die na een gecoördineerde reload niet probeert het oude object opnieuw op te slaan, maar het huidige publicatie-item veilig opnieuw laadt.
- Nieuwe regressietests dekken stale-bookshelf `touch_book`, de centrale identity-invariant, drie-uitkomsten Planning-conflicten en — waar PySide6 beschikbaar is — een echte MainWindow-adopt met extern toegevoegd hoofdstuk.
- Pakketversie naar 0.22.1 verhoogd.

## 0.21.10 — Cleanup, performance, testdekking en AI-instellingen-UX

- **Modellen ophalen** geeft nu direct inline voortgang (`Modellen ophalen…`) en daarna een expliciete succesmelding met het aantal gevonden modellen. Een fout blijft zowel inline als via de bestaande foutdialoog zichtbaar.
- De AI-modelkeuze is nu een echte niet-bewerkbare combobox. De gebruiker kiest uitsluitend uit de opgehaalde/provider-specifieke modellen; klikken op het veld zelf opent de keuzelijst en modelnamen kunnen niet meer per ongeluk handmatig worden gewijzigd.
- De boekenplank berekent woordenaantallen per refresh maximaal één keer per boek en hergebruikt die waarde zowel voor sortering als voor de kaart. Sorteren op woordenaantal veroorzaakt daardoor geen dubbele hoofdstuk-I/O meer.
- `BookCover.paintEvent()` maakt niet langer bij iedere repaint nieuwe `QSettings`-instanties; één settingsobject wordt per coverwidget hergebruikt.
- De oude, niet meer aangeroepen Markdown-exportmethode in `BookDetailsPage` is verwijderd. Export loopt uitsluitend via de modulaire `Exporteren`-pagina en `exporting/markdown_exporter.py`.
- Veilige cleanup uitgevoerd op aantoonbaar ongebruikte imports/lokalen. `zip()`-semantiek is expliciet gemaakt: `strict=True` waar EPUB-secties en paden exact één-op-één moeten lopen, en `strict=False` bij bewust overlappende buurparen in de UI.
- Extra regressiedekking toegevoegd voor AI-modelstatus/selection-only gedrag, OpenRouter streaming-foutdetails, de enige actieve Markdown-exportroute en de boekenplank-hotpaths.
- Het hogere-prioriteit externe code-review herstelprogramma 0.21.1–0.21.10 is hiermee afgerond. De bestaande productroadmap wordt hervat; portable Markdown-media is de eerstvolgende productstap.
- Pakketversie naar 0.21.10 verhoogd.

## 0.21.9 — kleine correctness/UX

- Ollama-modeldetectie respecteert nu daadwerkelijk de door de caller gevraagde timeout; de compatibiliteitslaag geeft `timeout` door aan `OllamaProvider.list_models()`.
- OpenRouter geeft bij HTTP-fouten de foutmelding uit de JSON-response door in plaats van alleen een generieke `401/429 Client Error`.
- Bij een ongeldige vervangingsafbeelding blijft in bewerkmodus de naam van het werkelijk gekoppelde bestand zichtbaar; QuietWriter suggereert niet langer dat de mislukte vervanging is geaccepteerd.
- Scene-break invoegen is symmetrisch beveiligd: staat direct links of rechts van de cursor al een `***`-blok, dan wordt geen tweede scene-break aangemaakt. De eerder vermoedelijke bevinding is hiermee gereproduceerd en bevestigd.
- Nieuwe gerichte regressietests voor timeout-doorgifte, OpenRouter-foutdetails, image-label en dubbele scene-breaks.


## 0.21.8 — Exportvalidatie, crash-infrastructuur en woordenboeklabels

- EPUB-coverrendering valideert nu iedere omslag met Qt vóór een JPEG/PNG in `artwork_with_text`-modus ongewijzigd wordt doorgegeven. Lege of corrupte coverbytes kunnen daardoor niet meer ongemerkt in een structureel geldige maar visueel kapotte EPUB terechtkomen.
- De vaste publicatie-Markdown blijft dezelfde frontmattervelden en volgorde gebruiken, maar quote YAML-gevoelige scalars deterministisch. Titels met `: `, meerregelige beschrijvingen, commenttekens en YAML-achtige waarden zoals `Yes` blijven daardoor geldige strings zonder een nieuwe runtime-dependency.
- Crashlogging is best-effort gemaakt: een onschrijfbare workspace-logmap kan de applicatie niet meer vóór installatie van het vangnet laten crashen. QuietWriter probeert automatisch een tijdelijke OS-map en start zonder crashlog als zelfs die niet beschikbaar is.
- `crash.log` wordt bij 2 MiB geroteerd naar één `crash.log.1`; als rename door sync/antivirus geblokkeerd wordt, probeert QuietWriter het actieve log veilig af te kappen. Crashlogging kan zo niet onbeperkt blijven groeien.
- Woordenboeklabels zijn uitgebreid met veel meer Nederlandse taal- en landnamen en gebruiken consequent **Taal — Land** als beide codes bekend zijn. Bij onbekende codes wordt de complete genormaliseerde locale getoond in plaats van een verwarrende half-vertaalde combinatie.
- Dictionary discovery verkiest nu een specifieke locale uit de bovenliggende Office-map boven een kale bestandsnaam. Een `nl.dic` onder `nl-NL/` wordt bijvoorbeeld als `nl_NL` / **Nederlands — Nederland** aangeboden.
- Nieuwe regressietests dekken YAML-escaping/parsing, lege en corrupte covers, crashlogrotatie/fallback en locale-label/inferentiegedrag.
- Roadmap: 0.21.8 is afgerond; 0.21.9 (Kleine correctness/UX) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.8 verhoogd.

## 0.21.7 — Spellingcorrectheid en woordenboekencoding

- Spellingscontrole accepteert woorden met een hoofdletter niet langer automatisch als correct. De normale Hunspell-regels worden gebruikt; zonder Hunspell blijft de eenvoudige woordenlijst case-insensitive, zodat bekende woorden aan het begin van een zin gewoon geldig blijven terwijl echte hoofdletter-tikfouten wel worden gemeld.
- De known-word cache bewaart bij actieve Hunspell-dictionaries de exacte woordvorm als sleutel, zodat hoofdletterregels niet door een eerder gecachte lowercase/uppercase variant worden omzeild.
- Hunspell `.dic`-bestanden worden niet meer hardcoded als UTF-8 met `errors='ignore'` gelezen. QuietWriter leest eerst `SET <ENCODING>` uit het bijbehorende `.aff`-bestand en decodeert daarmee strikt; zonder bruikbare declaratie volgt een gecontroleerde UTF-8 → Latin-1 fallback zonder diakrieten stil te verwijderen.
- **Alles negeren**, **Altijd negeren** en **Toevoegen aan woordenboek** hervatten nu op basis van de tekstpositie van de zojuist behandelde fout. Als dezelfde fout eerder in het hoofdstuk ook verdwijnt, kan de volgende overgebleven fout daardoor niet meer door een verschoven lijstindex worden overgeslagen.
- Nieuwe regressietests dekken hoofdletter-tikfouten, case-insensitive fallback, Latin-1 Hunspellwoordenboeken en — waar PySide6 beschikbaar is — de indexverschuiving van alle drie globale spellingacties.
- Roadmap: 0.21.7 is afgerond; 0.21.8 (Export & crash-infrastructuur) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.7 verhoogd.

## 0.21.6 — AI state-isolatie en provider/model-synchronisatie

- AI-aanvragen zijn nu gekoppeld aan zowel een oplopende boekgeneratie als een request-id en de concrete `ProviderChatWorker`. Tokens, thinking-output, success, failure en cancellation van een oude worker worden genegeerd zodra het zichtbare boek of de actieve aanvraag niet meer overeenkomt.
- Boekwisselen tijdens een lopende AI-aanvraag blokkeert de GUI niet langer maximaal 2,5 seconde. De oude worker wordt geannuleerd en als achtergrondworker aangehouden tot zijn `finished`-signaal; de nieuwe boekcontext kan direct worden geladen.
- Een laat `finished`-signaal van een oude worker kan `self.worker` van een nieuwere aanvraag niet meer leegmaken of de nieuwe worker per ongeluk `deleteLater()` geven. Alle nog levende workers worden sterk bijgehouden en bij afsluiten gezamenlijk gestopt/afgewacht.
- Hierdoor kan een stale cancel/done/fail van Boek A de berichtenlijst of `ConversationStore` van Boek B niet meer muteren of naar schijf schrijven. De bestaande `ConversationStore` hoeft daarvoor zelf geen cross-book heuristiek te krijgen: alleen callbacks van de nog actuele request-context mogen hem aanroepen.
- De AI-instellingen houden provider en model nu als één samenhangende formulierstate bij. Wisselen Ollama ↔ OpenRouter leegt/ververst de modelcombo direct vanuit de live providerselectie; een model van de vorige provider kan niet meer onder de nieuwe provider worden opgeslagen. Niet-opgeslagen modelkeuzes worden per provider apart onthouden tot Opslaan.
- `ContextBuilder` vangt een stale hoofdstukreferentie bij **Huidige sectie** defensief af en laat een onleesbaar niet-actief hoofdstuk in sectie/boek-context als duidelijke placeholder staan in plaats van de hele AI-aanvraag te laten crashen.
- De **+ Toevoegen**-flyout en zijn keuzes gebruiken subtielere 4px-hoeken in plaats van de opvallende 10/8px afronding.
- Nieuwe regressietests bewaken request/book-isolatie, worker-identity bij cleanup, live provider/model-synchronisatie, context-fallbacks en de flyout-stijl. Een aanvullende Qt-runtime-test reproduceert, waar PySide6 beschikbaar is, de late-cancel race tussen Boek A en Boek B.
- Roadmap: 0.21.6 is afgerond; 0.21.7 (Spellingcorrectheid) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.6 verhoogd.

## 0.21.5 — Publicatie & Planning data-integriteit

- Hoofdstuk-contextmenu uitgebreid met **Verwijderen** naast Hernoemen en Dupliceren. De bestaande verwijderactie in de rechter werkbalk blijft beschikbaar; beide routes gebruiken dezelfde bevestigde, herstelbare hoofdstukverwijdering.
- De hoofdstuk-/sectie-tekstprompt is niet langer gebaseerd op `QInputDialog`. QuietWriter gebruikt nu een eigen klein dialoog met betrouwbare **Opslaan / Annuleren**-knoppen op Windows, voor zowel Hernoemen als Nieuw hoofdstuk/sectie.
- `PublicationEditor.set_book()` reset bij navigatie binnen hetzelfde boek niet langer `key`, dirty-state en geladen data vóór `open_item()` de vorige publicatiepagina kan opslaan. Onopgeslagen structured en vrije-tekst-publicatiegegevens gaan daardoor niet meer stil verloren bij wisselen tussen Voorwerk/Achterwerk-items.
- Bestaande personages worden voortaan via een kandidaat-kopie bijgewerkt. Een mislukte `persist_characters()` kan daardoor geen in-memory mutatie achterlaten die bij een latere, andere save alsnog stil naar schijf wordt geschreven.
- Nieuwe en bewerkte outline-scènes gebruiken hetzelfde snapshot/rollback-patroon als verwijderen: faalt de persist, dan wordt de in-memory scènecollectie teruggezet.
- Scènes die nog verwijzen naar een inmiddels verwijderd hoofdstuk worden niet langer onzichtbaar. De Outline toont ze onder **Verweesde scènes**; openen/bewerken maakt herstel of herplaatsing mogelijk.
- Bij het verwijderen van een personage worden na de geslaagde personage-save ook diens `character_ids` uit scènes verwijderd. Als die tweede save door een extern conflict niet lukt, meldt QuietWriter dit expliciet in plaats van oude scènegegevens blind terug te schrijven.
- Een ingevuld maar nog niet opgeslagen nieuw-personage-concept wordt bij boekwissel niet meer stil weggegooid: de gebruiker kiest **Opslaan / Niet opslaan / Annuleren**. `PlanningPage.save_pending()` omvat daardoor nu zowel personagedrafts als notities.
- Boekverwijdering heeft een echte pre-delete guard gekregen: actieve planning én manuscripttekst moeten eerst succesvol kunnen worden opgeslagen voordat de boekmap naar de prullenbak verhuist. De oude post-delete `save_pending()`-aanroep is verwijderd.
- De geneste f-string in de personagerelatieweergave is herschreven zodat `characters_page.py` ook onder Python 3.11 parseert; QuietWriter zelf blijft op Python 3.12 gericht.
- Nieuwe regressietests bewaken de gelokaliseerde prompt, hoofdstuk-contextdelete, publicatie same-book guard, candidate/rollback-patronen, verweesde scènes, draft-save-pending, pre-delete saveguard en Python-3.11-syntaxcompatibiliteit.
- Roadmap: 0.21.5 is afgerond; 0.21.6 (AI state-isolatie) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.5 verhoogd.

## 0.21.4 — Prullenbak & herstelbaarheid

- De prullenbak toont voortaan zowel verwijderde boeken als verwijderde hoofdstukken in één chronologische lijst, met duidelijk onderscheid tussen boek en hoofdstuk plus het bijbehorende boek.
- Nieuwe hoofdstukverwijderingen bewaren naast de recoverable `.md`-kopie een kleine JSON-sidecar met boek-, sectie-, titel- en positiegegevens. Daardoor kan een hoofdstuk terugkeren op zijn oorspronkelijke plek; als de oorspronkelijke sectie intussen is verwijderd, wordt die sectie bij herstel opnieuw aangemaakt.
- Hoofdstukken die al in 0.21.3 naar `trash/chapters/` zijn verplaatst zonder metadata blijven als legacy-item zichtbaar en herstelbaar; ze vallen terug op de eerste beschikbare sectie.
- `Library.restore_trashed_chapter()` is rollback-safe: een mislukte manifest-write verwijdert de tijdelijk teruggeschreven live file en herstelt het in-memory model, terwijl de trashkopie beschikbaar blijft.
- Een boek en één of meer van zijn verwijderde hoofdstukken kunnen in één herstelactie worden geselecteerd; boeken worden bewust eerst hersteld en daarna pas hoofdstukken.
- Definitief verwijderen van een weggegooid boek ruimt nu ook `trash/chapters/<book_id>` op. **Prullenbak legen** verwijdert zowel boek- als hoofdstuk-trash, zodat verwijderde hoofdstukinhoud niet onzichtbaar op schijf blijft staan.
- Definitief verwijderen verwerkt items afzonderlijk met foutafhandeling; een fout op één item voorkomt niet dat de lijst wordt ververst of dat andere geselecteerde items worden afgehandeld. Ook een gedeeltelijk mislukte `Prullenbak legen`-actie geeft een normale waarschuwing en ververst daarna altijd de UI.
- Hernoemen en aanmaken van hoofdstukken/secties gebruiken nu één gelokaliseerde tekstprompt met **Opslaan / Annuleren** in plaats van Qt's native OK/CANCEL-labels.
- Nieuwe regressietests dekken metadata, herstelpositie, herstel van een verdwenen sectie, legacy-trash uit 0.21.3, rollback bij mislukte restore, boek+chapter-herstel, purge bij definitief boek verwijderen en volledige lege-prullenbaksemantiek.
- Roadmap: 0.21.4 is afgerond; 0.21.5 (Publicatie & Planning data-integriteit) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.4 verhoogd.

## 0.21.3 — Hoofdstuk- en storage-integriteit

- Hoofdstuk-drag-and-drop bewaart de oorspronkelijke verplaatsingsintentie nu ook bij een `ExternalModificationError`: na een succesvol opgelost extern conflict wordt de reorder opnieuw berekend tegen het vers geladen boek en één keer opnieuw opgeslagen. De oude situatie waarin het conflict wel werd opgelost maar de drag stil verloren ging is daarmee gesloten.
- Als de boekstructuur tijdens conflictresolutie zó is veranderd dat bronhoofdstuk of doel niet meer bestaat, wordt de verplaatsing niet geforceerd en krijgt de gebruiker een gerichte waarschuwing. Een tweede extern conflict tijdens de retry veroorzaakt geen oneindige herhaal-/dialooglus.
- `Library.delete_chapter()` verplaatst niet langer de enige live hoofdstukkopie vóórdat `book.json` veilig is bijgewerkt. Eerst wordt een recoverable kopie in chapter-trash gemaakt, daarna wordt de manifestmutatie gecommit en pas na succes wordt het live bestand best-effort verwijderd. Bij een mislukte manifest-write worden model en tijdelijke trashkopie teruggedraaid.
- Dezelfde rollback-regel is doorgetrokken naar `add_section()`, `add_chapter()`, `rename_chapter()`, `rename_section()` en `duplicate_chapter()`: een mislukte manifest-write laat het live model niet meer half-gemuteerd achter; nieuw aangemaakte UUID-hoofdstukbestanden worden waar mogelijk weer opgeruimd.
- Nieuwe regressietests forceren manifest-write failures en controleren dat model, bronbestand, manifest en tijdelijke trashstatus consistent blijven. De drag-retrylogica heeft daarnaast een broncontracttest; Qt-runtime-interactie blijft aanvullend handmatig/optioneel getest.
- De externe code-review is voor dit domein opnieuw getoetst: het contextloze conflictgedrag bij rename/add/delete/duplicate is verwarrend maar veroorzaakt vóór de mutatie geen bevestigd dataverlies; contextuele structurele conflictdialogen blijven daarom buiten deze data-integriteitshotfix.
- Roadmap: 0.21.3 is afgerond; 0.21.4 (hoofdstuk-prullenbak & herstelbaarheid) is de volgende hogere-prioriteitsbuild.
- Pakketversie naar 0.21.3 verhoogd.

## 0.21.2 — Undo/Redo root-cause hotfix

- De extern aangeleverde en vooraf gereproduceerde `manuscript_editor`-Undo-patch is geïsoleerd op de 0.21.1-codebasis toegepast; de resulterende file is byte-voor-byte gelijk aan het meegeleverde `manuscript_editor.py.fixed`.
- Actieve lege vervolgalinea's gebruiken voor line-height en bottom-margin voortaan hetzelfde blockformat als de normale alinea waarin ze na de eerste letter veranderen. Alleen duurzame lege separator-alinea's krijgen nog `MinimumHeight` en de compacte lege-regelmarge. Daardoor ontstaat bij het typen van de eerste letter geen extra block-formattransitie meer die als los Qt-undo-commando kan eindigen.
- `ManuscriptEditor.undo()` en `redo()` onderdrukken formatting-scheduling zolang Qt de eigenlijke undo/redo uitvoert en wissen daarna `_format_join_previous`; een undo/redo-trigger kan daardoor geen nieuwe formatteringspass meer aan de zojuist gewijzigde undo-stack vastplakken.
- Ctrl+Z/Ctrl+Y worden in `keyPressEvent()` expliciet via deze editor-overrides geleid met `QKeySequence.StandardKey.Undo/Redo`, omdat Qt's standaard `QTextEdit`-keypad de Python-level overrides anders kan omzeilen.
- Nieuwe regressietests bewaken de broncontracten én, waar PySide6 beschikbaar is, toetsenbordgedreven Ctrl+Z-convergentie, Undo→Redo→Undo-stabiliteit en formatgelijkheid van een actieve lege vervolgalinea.
- De roadmap bevat nu de volledige externe code-review als hogere-prioriteitsreeks 0.21.3–0.21.10 vóór nieuwe featurebouw; bestaande productroadmapitems blijven behouden.
- Pakketversie naar 0.21.2 verhoogd.

## 0.21.1 — Eerste externe code-review fixes

- `EditorPage.tree_context_menu()` importeert `QMenu` nu expliciet. Rechtsklikken in de manuscriptboom kan daardoor niet meer op een `NameError` stuklopen.
- `CurrentPageStack.minimumSizeHint()` en `sizeHint()` respecteren nu ook een expliciete `setMinimumSize()` van de zichtbare pagina via `expandedTo(page.minimumSize())`. Verborgen pagina's blijven de hoofdvensterhoogte niet bepalen, maar de actieve pagina mag wel zijn eigen minimum afdwingen.
- Nieuwe regressietests leggen beide fixes vast.
- De eerste externe code-review is vergeleken met de werkelijk uitgegeven 0.20.3-code. De genoemde undo-refactorpunten (`reset_undo_history`, één formatting-schedule, `_make_block_format` en `joinPreviousEditBlock`) waren daar al aanwezig en zijn daarom niet nogmaals gewijzigd; de resterende alinea/Undo-bug vraagt een andere oorzaak.
- Pakketversie naar 0.21.1 verhoogd.

## 0.20.3 — Alinea-inspringing en Undo-hotfix

- De alinea-inspringing wordt niet langer pas 90 ms na het eerste zichtbare karakter toegevoegd. Een gewone Enter maakt de nieuwe `QTextBlock` direct met de juiste vervolg-alinea-opmaak, zodat de cursor al vóór het typen op de ingesprongen positie staat.
- Enter en de bijbehorende paragraph-layout zijn één undo-transactie. De visuele `QTextBlockFormat` kan daardoor niet meer als los undo-item tussen de eerste letter en de rest van de zin komen te staan.
- Tekstgedreven formatteringscorrecties gebruiken `QTextCursor.joinPreviousEditBlock()` wanneer werkelijk een blockformat moet veranderen. Presentatie-opmaak vervuilt daardoor de tekstuele undo-keten niet meer.
- Een tweede Enter normaliseert de eerste lege vervolgregel tot een echte blanco alinea en maakt daarna een flush-left nieuwe alinea; de 0.20.1-fix voor zichtbare lege regels blijft behouden.
- Lege/whitespace-only actieve vervolgalinea's behouden hun inspringing. Een spatie typen laat de cursor dus niet terugvallen naar de linkermarge.
- Na het laden en de initiële manuscript-layout wordt de setup-only undo-historie expliciet leeggemaakt; een vers geopend hoofdstuk heeft geen verborgen formatteringsactie om ongedaan te maken.
- De dubbele formatteringsschedule vanuit `EditorPage.on_text_changed()` is verwijderd; de manuscripteditor bezit voortaan zelf de text-driven layoutcyclus.
- Nieuwe Qt-runtime-regressies dekken directe inspringing na Enter, whitespace op een lege vervolgalinea en herhaald Undo over tweede zin, eerste letter en Enter.
- Portable Markdown-media schuift door naar 0.20.4; de beschermde imageblokken van 0.20.2 zijn inhoudelijk ongewijzigd.

## 0.20.2 — Beschermde afbeeldingsblokken in de editor

- Inline media blijft op schijf gewone Markdown, maar beheerde image-regels zijn in de manuscriptruimte niet meer als ruwe `![...](../assets/images/...)`-syntaxis zichtbaar of rechtstreeks bewerkbaar.
- Nieuwe modulaire `ImageBlockCard` toont thumbnail/placeholder, alt-tekst, onderschrift en expliciete **Bewerken**/**Verwijderen**-acties bovenop een echt gereserveerd QTextBlock. De kaart wordt gepositioneerd via Qt's `blockBoundingRect()` zodat invoegen, laden, scrollen en resizen dezelfde uitlijning houden.
- Klikken op de kaart selecteert alleen het mediablok; bewerken start uitsluitend via **Bewerken**, Enter/Return op een geselecteerd blok of het beschermde contextmenu.
- Het bestaande Afbeelding-scherm in de rechterrail heeft nu een echte editmodus: huidige preview, alt-tekst en onderschrift worden geladen, **Afbeelding vervangen…** importeert alleen bij expliciete vervanging en **Opslaan** wijzigt het bestaande Markdown-blok.
- Afbeeldingsblokken zijn atomair beschermd tegen typen, Enter, Delete/Backspace, Cut/Paste, tekst-drag/drop en opmaakacties die een selectie over het mediablok heen zouden wijzigen.
- Verwijderen gebruikt QuietWriter's centrale gelokaliseerde bevestiging met **Ja/Nee** en verwijdert alleen de manuscriptverwijzing; de immutable asset blijft bewaard voor historie/herstel.
- Historische/read-only weergave toont de media-kaarten zonder bewerk/verwijder-acties.
- De ruwe Markdownregel wordt visueel ingeklapt door de presentatie-highlighter; de bron blijft wel volledig round-tripbaar voor opslag, historie en export.
- 0.20.2 is bewust vóór portable Markdown-media geplaatst; de `<slug>-assets/` companionmap en link-rewriting schuiven door naar 0.20.4.

## 0.20.1 — Hotfix lege alinea's in de editor

- Een gewone Enter/Return wordt in de manuscripteditor nu expliciet als `QTextCursor.insertBlock()` ingevoegd. Dit omzeilt een Qt-randgeval waarbij Return op een lege paragraaf met custom `QTextBlockFormat` de opmaak kan resetten/reflowen en de cursor visueel terug omhoog springt.
- Lege manuscriptblokken gebruiken een expliciete `MinimumHeight` op basis van het ingestelde schrijflettertype en de regelafstand. Een bewuste dubbele Enter blijft daardoor een zichtbare lege alinea, ook nadat de 90-ms visuele formatteringspass is uitgevoerd.
- Shift+Enter en modifier-combinaties blijven aan Qt zelf overgelaten; alleen gewone Enter/Return wordt door QuietWriter beheerd.
- Runtime-regressietest toegevoegd die twee Enters invoert, de formattering uitvoert en controleert dat de bron `\n\n`, drie tekstblokken en een niet-ingeklapte lege paragraaf behoudt.
- De geplande portable Markdown-media-export schuift door naar 0.20.4; de EPUB/mediafunctionaliteit van 0.20.0 is inhoudelijk ongewijzigd.

## 0.20.0 — Book-local media en afbeeldingen in EPUB

- Nieuwe modulaire `quietwriter/media/`-laag voor book-local assets. Ieder nieuw boek heeft `assets/images/`, `assets/cover/` en een klein revision-guarded `assets/manifest.json`; bestaande boeken worden zonder verplichte migratie ondersteund.
- Afbeeldingen worden bij import gekopieerd naar een UUID-bestandsnaam, blijven immutable en worden op SHA-256 gededupliceerd. De oorspronkelijke naam, media type, afmetingen, bestandsgrootte en hash staan in het manifest; JPG/JPEG en PNG zijn de eerste ondersteunde inlineformaten.
- De rechterrail **Toevoegen** bevat nu **Afbeelding** met preview, alt-tekst en optioneel onderschrift. Annuleren kopieert niets; pas **Invoegen** importeert het bestand en voegt één standaard Markdown-imageblok op de cursorpositie in.
- Manuscriptstatistieken tellen imageblokken niet als woorden. Spelling en zoeken negeren de beheerde UUID-/padsyntaxis, terwijl alt-tekst en onderschrift wel natuurlijke tekst blijven. AI-context vervangt het pad door een compacte `[Afbeelding: …]`-beschrijving.
- Export snapshots verzamelen alle gebruikte media via hetzelfde bestaande `ExportAsset`-model. EPUB kopieert inline assets naar `EPUB/images/`, neemt ze op in `package.opf` en rendert imageblokken als semantische `<figure><img/><figcaption>…</figcaption></figure>`.
- EPUB-preflight blokkeert ontbrekende of gewijzigde assets; zware binaries worden niet bij iedere editor-save gehasht, maar hun bytes worden bij export tegen de manifest-SHA gecontroleerd.
- Historieversies nemen `assets/` volledig mee. Bij herstel worden benodigde snapshot-assets teruggezet, maar nieuwere UUID-binaries nooit automatisch verwijderd; expliciete ongebruikte-media-opruiming is een latere functie.
- Nieuwe/vervangen boekomslagen worden voortaan in `assets/cover/` van het boek opgeslagen. Oude globale omslagen onder `boekomslagen/` blijven volledig leesbaar als backward-compatible fallback.
- Markdown-export met inline afbeeldingen wordt in 0.20.0 bewust door preflight geblokkeerd: 0.20.4 voegt de afgesproken portable `-assets` companionmap en link-rewriting toe in plaats van nu kapotte paden te exporteren.

## 0.19.4 — Rustiger splash en compactere Over-pagina

- Het splashscherm toont nog maar één QuietWriter-naam; de kleine dubbele merkregel boven de grote titel is verwijderd. De bestaande startup-status, voortgang, versie en copyright blijven ongewijzigd.
- De Over-pagina is teruggebracht tot productintro, lokale opslag/privacy, copyright, technische omgeving en fontlicenties. De drie ontwerpprincipe-kaarten en de grotendeels dubbele Maker-tekst zijn verwijderd.
- Runtime-informatie heeft nu de expliciete sectietitel **Technische omgeving** in plaats van als losse diagnostische regel tussen de overige inhoud te staan.
- **Over** staat in de instellingen-navigatie direct onder **Spelling**. De flexibele lege ruimte staat voortaan onder Over, zodat de pagina niet meer visueel los onderaan de sidebar hangt.

## 0.19.3 — Volwaardig opstartscherm en vernieuwde Over-pagina

- Het oude 450-ms splashvenster is vervangen door een echte startup-flow: de splash blijft zichtbaar terwijl lettertypen, werkmap, AI-provider en hoofdinterface worden voorbereid en sluit pas wanneer Qt/Windows het hoofdvenster daadwerkelijk heeft blootgelegd. Er is geen kunstmatige minimumduur.
- De splash volgt het actieve QuietWriter-thema en toont appnaam, tagline, actuele opstartstatus, een subtiele onbepaalde voortgangsbalk, versie en copyright. Alle zichtbare teksten lopen via `nl.json`/`en.json`.
- De Over-pagina heeft een compacte QuietWriter-hero gekregen en geeft naast versie/maker nu ook de ontwerpprincipes **Tekst centraal**, **Lokaal als basis** en **Lichtgewicht** weer.
- Een aparte privacytekst legt uit dat manuscripten in de gekozen werkmap worden bewaard, Ollama lokaal kan draaien en dat tekst/context bij gebruik van een externe AI-provider naar die provider kan worden verzonden.
- Runtime-informatie (Python, PySide6, Qt en platform) staat subtiel op de Over-pagina voor diagnose/support; de bestaande uitklapbare fontlicenties blijven behouden.

## 0.19.2 — Vaste publicatie-Markdown

- Markdown op **Exporteren** volgt nu het vaste publicatieformaat uit de bestaande bestanden: een verplichte header tussen `---` met `title`, `date`, `slug`, `description`, `meta`, `intro`, `author` en `tags` in stabiele volgorde.
- De 0.19.1-opties om frontmatter of sectiemarkeringen uit te schakelen zijn verwijderd; de publicatieheader is onderdeel van het formaat en kan niet per ongeluk verdwijnen.
- Een los verhaal met precies één hoofdstuk dat dezelfde titel heeft als het boek krijgt geen redundante `# Titel` meer. De tekst begint direct na de header, zoals in bestaande publicatiebestanden.
- Meerhoofdstukboeken behouden wel hoofdstukkoppen en onzichtbare sectiemarkeringen om hun structuur te bewaren.
- De rijkere Markdown import/round-triplaag blijft apart bestaan en bewaart extra QuietWriter-metadata; deze wijziging raakt EPUB niet.

## 0.19.1 — Exporteren-pagina en EPUB 3

- Nieuwe modulaire **Exporteren**-pagina direct onder Boekdetails. EPUB en Markdown zijn beschikbaar; PDF is zichtbaar als latere, bewust nog uitgeschakelde optie zonder extra dependency.
- Export bouwt eerst één immutable `ExportDocument`-snapshot uit opgeslagen boek-, hoofdstuk- en publicatiegegevens. EPUB en Markdown lezen daardoor niet ieder afzonderlijk uit live editorstate.
- Volledige lichte EPUB 3-pipeline toegevoegd met alleen Python-standaardbibliotheek plus de al aanwezige PySide6-stack: `mimetype`, container, package/manifest/spine, EPUB 3-nav, XHTML-hoofdstukken, CSS-templates en metadata.
- Drie rustige exporttemplates toegevoegd: Klassiek, Modern en Literair. De templates zijn gewone CSS-bestanden onder `quietwriter/export_templates/`.
- Boekomslag ondersteunt twee expliciete modi: **artwork zonder tekst**, waarbij QuietWriter zelf titel en auteur toevoegt, en **artwork met tekst**, waarbij de afbeelding inhoudelijk ongewijzigd wordt gebruikt. Hiervoor is geen extra beeldlibrary toegevoegd.
- Het exportassetmodel is generiek (`ExportAsset`) zodat toekomstige afbeeldingen in hoofdstukken via dezelfde snapshot/pipeline kunnen reizen; 0.19.1 gebruikt dit model nog alleen voor de omslag.
- Boekdetails bevat nu een aparte **Boektaal**-metadatawaarde. UI-taal en boektaal blijven bewust gescheiden; EPUB gebruikt de boektaal.
- De oude Markdown-exportactie is uit Boekdetails gehaald en verhuisd naar Exporteren. Per boek worden alleen exportvoorkeuren in `export/settings.json` bewaard; de uitvoermap blijft een lokale app-instelling.
- EPUB wordt eerst naar een tijdelijk bestand geschreven en pas na volledige opbouw atomair op de doelnaam geplaatst. Preflight controleert minimaal titel, auteur, boektaal, hoofdstukken, omslag en EPUB-ISBN.
- Nieuwe regressietests controleren de EPUB-containerstructuur, ongecomprimeerde eerste `mimetype`-entry, parseerbare XML/XHTML, navigation/spine, relatieve inhoudslinks, snapshotbuilder en QuietWriter-markupconversie.

## 0.18.14 — Windows-tekstweergave en afronding interactiepolish

- De manuscripttypografie gebruikt op Windows nu volledige font hinting met grayscale-antialiasing in plaats van subpixel-antialiasing. Dit is gericht op de schrijfruimte en font-preview, zodat lichte seriftekst op donkere thema's geen rode/cyaan ClearType-randjes krijgt; de rest van de applicatie houdt de platformstandaard.
- De font-preview in Instellingen gebruikt exact dezelfde `WritingTypography`-route als de editor, zodat familie, gewicht, hinting en antialiasing representatief zijn voor de echte schrijfruimte.
- De resterende Planning-details zijn aan de locale- en interactiebaseline gekoppeld: Personages-navigatie, veldlabels, relatieteksten en conflict/save-meldingen volgen `nl.json`/`en.json`; niet-klikbare Outline-kaarten adverteren geen hoverinteractie meer.
- Publicatie is consequent gemaakt als detail/document-flow: setup, publicatiestructuur en gestructureerde velden volgen de app-locale; Titelpagina, Epigraaf, Inhoud en Copyright hebben een zichtbare Opslaan-knop met dirty-state; vrije publicatietekst heeft dezelfde expliciete Opslaan-lijn naast autosave.
- Versiegeschiedenis volgt de app-locale voor koppen, types, datumtaal en getalnotatie. Enter/Return activeert dezelfde versie als een muisklik; de steractie blijft selectie-afhankelijk.
- Prullenbak heeft selectie-afhankelijke Herstellen/Definitief verwijderen-acties, gelokaliseerde bevestigingen en keyboard-activatie via Enter/Return. Destructieve acties blijven expliciet bevestigd.
- De resterende hover/pressed/focus- en toetsenbordpass van Iteratie 18 is hiermee functioneel afgerond. De eerder uitgevoerde contrasttests over alle veertien thema's blijven automatisch bewaakt; de handmatige DPI/lage-hoogte-smoketest blijft op verzoek uitgesteld.

## 0.18.13 — Uitgebreide themafamilie en contrastpass

- Acht nieuwe kleurenschema's toegevoegd: **Porselein**, **Nevel**, **Salie**, **Lavendel**, **Nord Licht**, **Inkt**, **Diepblauw** en **Aurora**. De bestaande zes thema's blijven beschikbaar; Instellingen toont nu veertien live-preview thema's.
- **Nord Licht** en **Aurora** zijn geïnspireerd op de officiële Nord-families Snow Storm/Polar Night/Frost/Aurora, vertaald naar QuietWriter's eigen semantische UI-tokens.
- Nieuwe semantische token `accent_text` scheidt primaire-knoptekst van `hero_text`. Donkere thema's kunnen daardoor donkere tekst op heldere accentknoppen gebruiken zonder de hero-kleuren te misbruiken.
- Contrast van bestaande thema's is centraal aangescherpt, met name `muted`, focus en enkele statuskleuren in Helder, Warm, Papier, Nacht, Grafiet en Middernacht.
- Geautomatiseerde contrasttests bewaken vanaf nu AA-contrast voor normale en secundaire tekst op alle gangbare oppervlakken, primaire knoppen normaal/hover, status- en hero/history-tekst en minimaal 3:1 voor focusindicatoren.
- De donkere uitbreiding is bewust gespreid: **Inkt** is vrijwel zwart, **Diepblauw** is diep navy en **Aurora** combineert een donkere Nord-basis met de kleurrijkere Aurora/Frost-accenten.

## 0.18.12 — Editor-state, directe zoeknavigatie en planning/detail-consistentie

- Undo/Redo gebruikt nu de actuele `QTextDocument`-state als bron van waarheid en synchroniseert opnieuw na de visuele formatteringspass; de knoppen blijven daardoor niet meer ten onrechte uitgeschakeld.
- Zoekresultaten navigeren met één muisklik naar het gevonden woord; Enter/Return blijft hetzelfde resultaat activeren. Bij een match in een ander hoofdstuk loopt ook de Inhoud-selectie mee met het werkelijk geopende hoofdstuk.
- Slepen van een hoofdstuk verandert niet langer de actieve Inhoud-selectie wanneer de editor een ander hoofdstuk toont. De sleepgreep en gewone klikken op structurele rijen (secties, Voorwerk, Boek, Achterwerk) laten de actieve tekstselectie ongemoeid; alleen de expliciete `wijzig`-actie bij Voorwerk/Achterwerk navigeert naar publicatie-instellingen.
- Outline-dialoogknoppen Opslaan/Annuleren en verwijderbevestigingen volgen de actieve QuietWriter-locale in plaats van de systeemtaal van Qt. Dezelfde gelokaliseerde Ja/Nee-confirmatie wordt nu ook voor personageverwijdering gebruikt.
- Notities heeft naast de bestaande veilige autosave nu een zichtbare primaire Opslaan-knop met dirty-state, in lijn met Personages en Outline.
- Boekdetails is verder aan `nl.json`/`en.json` gekoppeld. `Gepubliceerd` toont gelokaliseerd Ja/Nee of Yes/No, maar bewaart intern bewust de bestaande canonieke metadatawaarden `Yes`/`No`.
- Boekenplank, Instellingen en Over zijn in deze pass opnieuw op cursor/focus/hover-baseline gecontroleerd; daar waren geen aanvullende codewijzigingen nodig.

## 0.18.11 — Editor- en hoofdchrome-polish

- De manuscripteditor gebruikt op Windows expliciet de I-beam tekstcursor. De scènebreuk-hover zet de viewportcursor niet langer via `unsetCursor()` terug naar een overgeërfde pijlcursor; alleen de kleine verwijderactie gebruikt bewust de handcursor.
- De object-specifieke buttonstijlen van de hoofdrail, gereedschapsrail, compacte editorbuttons, secundaire acties, suggesties en geschiedenisbanner hebben nu eigen hover/pressed/focus-states. Daarmee kunnen hun specifiekere QSS-selectors de globale interactiestates niet meer stil overschrijven.
- De niet-klikbare kaart rond **Toevoegen → Scènebreuk** heeft geen hover-highlight meer; alleen de echte Toevoegen-knop communiceert interactie.
- De hoofdstukkenboom ondersteunt nu een expliciete keyboard-activatie: Enter/Return opent een hoofdstuk of publicatie-item; op sectie-/groepsrijen klapt Enter de groep open of dicht. De bestaande single-click-muisbediening blijft ongewijzigd.
- De **+ Toevoegen**-flyout geeft na openen focus aan de eerste keuze, ondersteunt Tab/Shift+Tab en sluit met Escape; Escape brengt focus terug naar de opener.
- Rechter editorpanelen (Zoeken, AI, Spelling, Toevoegen, Versiegeschiedenis) kunnen met Escape worden gesloten; focus keert dan terug naar het bijbehorende rail-icoon.
- Zoek/vervang heeft een expliciete Tab-volgorde die de visuele leesrichting volgt. De spellingscontrole focust bij openen de eerste suggestie/actie en ordent dynamische suggesties vóór de vaste acties.
- Undo/Redo zijn alleen actief wanneer de editor die actie daadwerkelijk kan uitvoeren en hebben expliciete toegankelijke namen. Bij hoofdstukwissel, publicatiecontext en boek sluiten wordt hun status opnieuw gesynchroniseerd.
- Icon-only hoofd- en gereedschapsrailknoppen hebben expliciete accessible names; het Inhoud-randtabje houdt tooltip en accessible name synchroon.

## 0.18.10 — Interaction baseline

- Eerste stap van de resterende UI/UX-polish uitgevoerd: één consistente basis voor hover, pressed, focus en disabled states.
- Alle normale `QPushButton`-varianten krijgen een zichtbare keyboard-focus; borderless navigatie-, compact-, flyout-, formatting- en chipknoppen reserveren transparante borders zodat focus geen layoutverspringing veroorzaakt.
- Hoofdrail, gereedschapsrail, Planning- en Instellingen-navigatie houden checked/selected en focus visueel uit elkaar.
- Checkboxes, radiobuttons, lijsten en bomen krijgen een expliciete focus-state; tekstvelden en combo/spin controls behouden hun bestaande focusrand.
- Flyout-, compact-, relation-chip-, inhoudrand- en primaire/destructieve knoppen hebben nu expliciete focus/pressed-pariteit waar hun specifiekere QSS-regels de globale button-state eerder konden overschrijven.
- UI-richtlijnen uitgebreid met cursorsemantiek, focusuitzonderingen en Tab/Shift+Tab/flyout-regels. Gewone desktopknoppen houden bewust de normale pijlcursor; handcursors blijven voor linkachtige/inline acties en sleepgrepen.
- De DPI/lage-hoogte eind-smoketest is op verzoek voorlopig uitgesteld; eerdere structurele layout-hardening blijft behouden.

## 0.18.9 — Windows drag/drop crash: QPainter fix

- Crashdiagnostiek uit 0.18.8 heeft de harde crash gelokaliseerd: Windows rapporteerde een native access violation in `ManuscriptTree.paintEvent()` tijdens `QDrag.exec()`.
- De custom tree-overlay gebruikt nu maximaal één `QPainter` tegelijk op het viewport. In 0.18.8 konden de selectie-accent en drop-lijn ieder een painter openen terwijl de eerste nog actief was.
- Tijdens een native drag wordt de extra selectie-accent niet meer custom geschilderd; alleen de drop-lijn wordt getekend. De gewone Qt-selectieachtergrond blijft zichtbaar.
- De drag bewaart geen `QTreeWidgetItem` meer als drop-target. `dragMoveEvent()` zet het doel direct om naar gewone waarden (`type`, `id`, `y`) zodat `paintEvent()` geen Shiboken/C++ itemwrapper hoeft te derefereren tijdens de native drag-loop.
- Ook de bron-`QTreeWidgetItem` wordt losgelaten vóór `QDrag.exec()`; alleen hoofdstuk-id, titel en drag-pixmap blijven over.
- `paintEvent()` controleert of de painter actief is en beëindigt hem expliciet via `try/finally`.
- Nieuwe regressietests bewaken dat er maar één viewport-painter bestaat en dat geen tree-itemwrapper de native drag-loop overleeft.


## 0.18.8 — Drag/drop hardening en crashdiagnostiek

- De drag-beveiliging start nu al bij mouse-down op de hoofdstukgreep, vóór `QTreeWidget.mousePressEvent()`. Daardoor kan een focuswissel naar de boom niet meer via `chapter_title.editingFinished` → `rename_current()` de Inhoud-boom herbouwen terwijl Qt het aangeklikte item nog verwerkt.
- Hoofdstuk-autosave én de aparte publicatie-free-text-autosave worden tijdens de volledige drag-interactie gepauzeerd. Opslaan/conflictafhandeling kan daardoor niet meer in de geneste event-loop van `QDrag.exec()` terechtkomen.
- `ManuscriptTree` heeft expliciete `dragStarted`/`dragFinished`-signalen en houdt de drag-guard via `try/finally` actief tot één event-loop-turn ná het terugkeren uit de native drag. Ook een geannuleerde drag of alleen klikken op de greep geeft de guard betrouwbaar vrij.
- `populate_tree()` is een gecoalesceerde refresh-transactie: tijdens een drag wordt `tree.clear()` nooit uitgevoerd. Vervolgacties die een verse boom nodig hebben (zoals selectie/openen) kunnen samen met de refresh worden uitgesteld, zodat geen oud boommodel tegen een nieuw boekmodel wordt gebruikt.
- Externe-wijzigingsdialoog en publicatie-conflictafhandeling krijgen een tweede drag-guard, zodat een toekomstige/directe call tijdens slepen veilig wordt uitgesteld in plaats van een modale dialoog te openen.
- Na een hoofdstukverplaatsing wordt `self.chapter` opnieuw gekoppeld aan het Chapter-object uit de nieuw geordende (deep-copied) secties.
- Navigatie/afsluiten respecteert voortaan een geweigerde editor-save; een boek of venster kan daardoor niet worden gesloten terwijl een drag nog actief is.
- Permanente crashdiagnostiek toegevoegd in `<werkmap>/logs/crash.log`: `faulthandler` schrijft native/fatale Python-stacks en `sys.excepthook`/`threading.excepthook` schrijven onverwerkte Python-exceptions.
- Nieuwe regressietests bewaken de vroege drag-guard, timerpauzes, deferred tree-refresh, Chapter-rebinding en crashlogging.


## 0.18.7 — Drag-and-drop stabiliteit, AI-verbergen en programmataal

- Hoofdstukken slepen bouwt de Inhoud-boom niet langer synchroon opnieuw op vanuit Qt's actieve `dropEvent`; de verplaatsing wordt pas na het drop-event uitgevoerd. Dit voorkomt een native Qt-crash waarbij boomitems tijdens de drag-loop werden vernietigd.
- Als de AI-assistent is uitgeschakeld, wordt die toestand na herstel van de venster-/paneelstatus opnieuw afgedwongen. De AI-knop kan daardoor niet via oude UI-state terugkeren en een eventueel actief AI-paneel wordt gesloten en uit de actieve rechterpaneelpagina gehaald.
- De bestaande `nl.json`/`en.json`-infrastructuur is nu daadwerkelijk gekoppeld aan een opgeslagen programmataal. Instellingen biedt Nederlands en Engels; de keuze wordt bij de volgende start toegepast.
- Nieuwe regressietests voor deferred chapter drops, AI-zichtbaarheid na state restore en runtime locale-selectie.

## 0.18.6 — Hoofdstukselectie en optionele AI

- Het hoofdstuk dat automatisch opent bij het openen van een boek wordt nu ook direct geselecteerd in de Inhoud-boom.
- Hoofdstukselectie is rij-gebaseerd: titel en sleepgreep vormen visueel één geselecteerde regel, met nog maar één accentlijn in plaats van een accent per kolom.
- Nieuwe instelling **AI-assistent gebruiken**. Uitschakelen bewaart de bestaande provider/modelinstellingen, maakt de AI-configuratie inactief en verbergt de AI-knop uit de editorrail.
- De AI-instellingen leggen expliciet uit dat QuietWriter zelf geen AI-model bevat, dat Ollama lokaal kan draaien en dat OpenRouter een externe provider is.
- Nieuwe AI-teksten zijn toegevoegd aan zowel de Nederlandse als Engelse locale.

## 0.18.5 — Boekenplank hero hersteld
- Donkere boekenplank-header loopt weer volledig over de beschikbare contentbreedte; alleen de inhoud binnen de hero volgt de gecentreerde max-width contentas.
- De gecentreerde host uit 0.18.4 krimpt inhoud niet langer onbedoeld tot een derde van de pagina; content groeit tot de beschikbare breedte of de ingestelde maximum breedte.
- Transparante hero-inner voorkomt dat de algemene QWidget-achtergrond een lichte uitsparing over de donkere hero schildert.
- Kaartmaten, spacing, sortering en zoekgedrag uit 0.18.4 blijven ongewijzigd.

## 0.18.4 — Boekenplank polish
- Boekenplank gebruikt nu één gecentreerde contentas met een maximale breedte; op brede schermen wordt lege ruimte links en rechts bewust gebalanceerd in plaats van alleen rechts te blijven staan.
- Hero, sorteer/zoekbalk en kaartgrid volgen dezelfde horizontale uitlijning.
- Boekkaarten zijn subtiel vergroot en spacing/schaduwen zijn verfijnd, zonder de rustige dichtheid van de plank te verliezen.
- Responsive kaartgrid blijft automatisch het aantal kolommen aanpassen aan de beschikbare breedte.
- Zoekveld heeft een bruikbare minimum breedte; sortering gebruikt stabiele interne keys in plaats van zichtbare/vertaalde tekst.
- Alle boekenplankteksten zijn toegevoegd aan zowel `nl.json` als `en.json`.

## 0.18.3 — Zichtbare value-controls en Toevoegen als zijpaneel

- QSpinBox-velden hebben nu expliciete, contrastrijke chevron-assets voor omhoog/omlaag; de klikgebieden uit 0.18.2 blijven behouden.
- De rechterrail-functie Toevoegen gebruikt geen los QMenu meer maar hetzelfde uitklapbare rechterpaneelpatroon als Zoeken, AI, Spelling en Geschiedenis.
- Het nieuwe InsertPanel heeft intern een CurrentPageStack, zodat toekomstige invoegflows (bijvoorbeeld afbeeldingen met instellingen) in hetzelfde paneel kunnen doorstappen zonder nieuwe popup-taal.
- Scènebreuk invoegen sluit het Toevoegen-paneel daarna automatisch.
- Nieuwe invoegteksten zijn toegevoegd aan zowel nl.json als en.json.

## 0.18.2 — Spinbox-bediening en editor micro-interacties

- QSpinBox-subcontrols krijgen expliciete klikgebieden; de bovenste stapknop wordt niet meer door het tekstveld overlapt.
- Scènebreuken hebben nu een hover-only verwijderknop met tooltip; verwijderen blijft één gewone editorhandeling en normaliseert alleen de omliggende witregels.
- Toevoegen-flyout heeft een expliciete pressed-state en publicatie-/scènebreukteksten lopen via de locale-bestanden.
- Nederlandse en Engelse locale-keys uitgebreid voor de nieuwe interacties.

## 0.18.1 — Instellingenlayout en uitleg

- Instellingenrijen gebruiken nu vaste onzichtbare kolommen, zodat labels/uitleg en bediening op alle pagina's exact op dezelfde x-posities uitlijnen.
- De rijen hebben meer verticale ademruimte en bredere control-kolommen; grote schermen blijven rustig terwijl lage laptops via de bestaande scrollviewport blijven werken.
- Werkmapveld verbreed met een bruikbare minimale breedte, zodat paden niet onnodig vroeg worden afgekapt.
- Fontkeuze heeft nu een volwaardige preview-card naast de dropdown met voorbeeldzin en familie/grootte-meta-informatie.
- Combo boxes zijn subtiel afgerond en de dropdownzone is visueel rustiger gemaakt, zonder een nieuwe componentstijl te introduceren.
- Alle knoppen in de zwevende opmaaktoolbar tonen nu ook in het non-activating toolbarvenster betrouwbare hover-uitleg; minder evidente acties hebben beschrijvende tooltips.
- Instellingen- en Over-teksten die in deze iteratie zijn aangeraakt zijn naar locale-keys verplaatst. Naast `nl.json` is een Engelse `en.json` toegevoegd als basis voor latere UI-localisatie.
- Nieuwe regressietests bewaken de kolomuitlijning, font-preview, werkmapbreedte, tooltips, combo styling en NL/EN locale-keys.

## 0.18.0 — UI-consistentie en editorinteractie

- Instellingen opnieuw opgebouwd als rustige tweekoloms settingspagina: naam en noodzakelijke uitleg links, bediening rechts.
- Verwante instellingen zijn gegroepeerd onder subtiele sectiekoppen; de vormgeving is vastgelegd in `UI_GUIDE.md` voor toekomstige schermen.
- Uiterlijk toont het lettertypevoorbeeld nu naast de fontkeuze, zodat de open dropdown de preview niet meer bedekt.
- Microcopy toegevoegd voor minder vanzelfsprekende opties, waaronder Automatisch opslaan (3 seconden na typen; Ctrl+S bij uitgeschakelde autosave), manuscriptinspringing, slimme quotes, opslag, AI en spelling.
- De Opslaan-knop van Instellingen is alleen actief wanneer formulierwaarden werkelijk afwijken van de laatst opgeslagen staat; na succesvol opslaan wordt de dirty-state gereset en blijft de bestaande `Opgeslagen`-feedback behouden.
- De zwevende selectie-toolbar is non-activating: hij accepteert geen keyboard focus en zijn knoppen hebben `NoFocus`, zodat geselecteerde tekst met Delete/Backspace/typen bewerkt kan blijven worden.
- Het normale Qt-rechtermuisknopmenu van de editor blijft intact en heeft nu aanvullend **Opmaak** met vet, cursief, onderstrepen, doorhalen, code en alineastijlen.
- Nieuwe regressietests bewaken de settings-row taal, font-previewplaatsing, dirty-state, non-activating toolbar en uitbreiding van het standaard contextmenu.

## 0.17.1 — Layout hardening op lage schermhoogte

- Structurele fix voor de Windows/Qt minimum-size bug: verborgen pagina's in stacks bepalen niet langer de minimumhoogte van het hoofdvenster.
- Nieuwe `CurrentPageStack` rapporteert uitsluitend de size hints van de zichtbare pagina; toegepast op hoofdmodus, Instellingen, Planning, personagecanvas, editorcontent en publicatie-editor.
- Instellingenpagina's gebruiken voortaan een echte scrollviewport; lange inhoud kan groeien zonder de vensterhoogte op te drijven.
- De vaste Opslaan-zone van Instellingen blijft buiten de scrollbare inhoud en dus bereikbaar op lage laptopschermen.
- Qt's native `saveGeometry()/restoreGeometry()` blijft leidend; er is geen custom clamp, handmatige `setGeometry()` of Windows-specifieke workaround meer.
- De standaard eerste venstergrootte is verlaagd naar 1280×720 zodat een verse start ook op compactere laptops binnen de werkruimte valt.
- Nieuwe regressietests bewaken zowel de stackarchitectuur als het gedrag waarbij een verborgen enorme pagina de minimumhoogte niet mag beïnvloeden.

## 0.17.0 — Meegeleverde schrijftypografie en Over

- Nieuwe fontcatalogus met vier aanbevolen schrijffamilies: Merriweather, Literata, Source Serif 4 en EB Garamond.
- QuietWriter registreert meegeleverde fontbestanden bij opstarten alleen binnen de applicatie; Windows-installatie is niet nodig.
- Instellingen → Uiterlijk groepeert de fontkeuze voortaan in **Aanbevolen** en **Systeemfonts** en toont elke familie maar één keer.
- Nieuwe live voorbeeldregel voor de gekozen schrijftypografie.
- Nieuwe **Over**-pagina onderaan Instellingen met versie-informatie, projectinformatie, maker Lucas Bonsel en fontlicenties.
- De vier gekozen fontfamilies zijn geverifieerd als SIL Open Font License 1.1; copyright- en licentieteksten staan per familie onder `resources/fonts/`.
- `font_manifest.json` legt familie, volgorde, bron en verwachte variable-fontbestanden vast.
- Bron/build-helper `tools/fetch_bundled_fonts.py` haalt exact de geverifieerde upstream binaries op voor packaging/source builds.

## 0.16.3

- Planning gebruikt nu één consistente paginataal: titel links en primaire actie rechts voor verzamelschermen.
- Personages heeft een volwaardige knop `Nieuw personage`; het losse plusje is verwijderd.
- De personagelijst behoudt zijn vaste breedte en gebruikt een subtiel micro-label onder de paginaheader.
- Notities gebruikt dezelfde marges en titelhiërarchie als Outline en Personages, terwijl de editor vrijwel de volledige inhoudsruimte houdt.
- Instellingen heeft alleen nog `Opslaan`; weg navigeren zonder opslaan is de natuurlijke annuleeractie en herstelt live previews.
- Design-audit uitgevoerd op de overige hoofdschermen: formulierpagina's houden hun onderaan geplaatste Opslaan-acties, collectiepagina's gebruiken acties in de header en de Boekenplank blijft bewust een afwijkende hero/startpagina.


## 0.16.2
- Inhoudsopgave opnieuw uitgelijnd; preview staat nu linksboven en de radiokeuze heeft duidelijke thema-eigen indicators.
- Voorwerk, Boek en Achterwerk zijn altijd zichtbaar in de manuscriptboom; Voorwerk/Achterwerk kunnen direct via “wijzig” worden geconfigureerd en behouden ook leeg hun uitklappijl.
- Instellingen verduidelijkt: “Terug zonder opslaan” vervangt de oude Annuleren-knop. Modelverversing schrijft geen instellingen meer stilletjes weg; alleen Opslaan commit de formulierwaarden.
- Opslaan in Instellingen synchroniseert QSettings expliciet en toont pas daarna tijdelijk een thema-eigen “Opgeslagen”-melding rechtsboven.

## 0.16.1 — Publicatiestructuur stabiliteit
- Opgelost: zero-argument `changed`-signalen in publicatieformulieren accepteren nu veilig payloads van Qt-signalen zoals `textEdited(str)`, `toggled(bool)` en `currentTextChanged(str)`.
- Opgelost: de Toevoegen-flyout bewaart geen verwijzing meer naar een door Qt verwijderde popup, waardoor herhaald openen niet meer kan eindigen in `Internal C++ object already deleted`.
- De manuscriptboom toont na activeren van Publicatiestructuur drie duidelijke, inklapbare zones: **Voorwerk**, **Boek** en **Achterwerk**.
- Voorwerk en Achterwerk hebben een rustige `wijzig`-actie waarmee de onderdelen opnieuw gekozen kunnen worden.
- Zonder geconfigureerde publicatiestructuur blijft de bestaande hoofdstuk-/sectieboom ongewijzigd.
- Nieuwe regressietests voor Qt-signaaladapters, popup-lifecycle en de drie manuscriptzones.

## 0.16.0 — Publicatiestructuur (MVP)
- Nieuwe publicatielaag die **Voorwerk → Manuscript → Achterwerk** als één boekstructuur behandelt.
- Via **+ Toevoegen → Publicatiestructuur** kies je met eenvoudige schakelaars welke onderdelen zichtbaar worden.
- Voorwerk: Titelpagina, Copyright, Opdracht, Epigraaf, Inhoudsopgave, Voorwoord en Inleiding.
- Achterwerk: Nawoord, Dankwoord en Over de auteur.
- Geselecteerde onderdelen verschijnen direct in de bestaande Inhoud-boom boven of onder de hoofdstukken.
- Drie expliciete contenttypen: vrije Markdowntekst, gestructureerde formulieren en gegenereerde onderdelen.
- Gestructureerde titelpagina met titel, subtitel, auteur/pseudoniem en uitgever/imprint.
- Gestructureerde copyrightpagina met editie, jaar, uitgever, ISBN-velden per formaat en optionele, vrij bewerkbare clausules.
- Inhoudsopgavegenerator met keuze tussen alleen hoofdstukken of hoofdstukken plus tussenkoppen, inclusief live voorbeeld.
- Vrije onderdelen gebruiken dezelfde rustige ManuscriptEditor maar blijven als losse Markdownbestanden opgeslagen.
- Publicatie-inhoud staat los van Planning en wordt opgeslagen onder `publication/`.
- Publicatiebestanden vallen onder dezelfde SHA-256 externe-wijzigingsbeveiliging en versiegeschiedenis als manuscript en planning.
- Versieherstel herstelt nu ook `planning/` en `publication/`, zodat een historische boekversie daadwerkelijk de bijbehorende ondersteunende boekdata terugzet.
- Exporttemplates/PDF/EPUB zijn bewust nog niet gebouwd; inhoud en semantiek zijn nu losgekoppeld van uiteindelijke vormgeving.
- Nieuwe tests voor publicatiemodellen, opslag, revision-conflicten en herstel uit versiegeschiedenis.

## 0.15.2
- Planning: de hoofdsubnavigatie en personagelijst hebben nu exact dezelfde vaste breedte.
- Personages: lege toestand gebruikt nu een echt blanco contentcanvas; het detailformulier verschijnt alleen bij Nieuw of selectie.
- Notities: gebruikt vrijwel de volledige beschikbare breedte en hoogte met kleine rustige marges.
- Windows: de custom geometry-clamp uit 0.13.5 is teruggedraaid; QuietWriter gebruikt voorlopig weer Qt saveGeometry/restoreGeometry totdat multi-monitor/DPI-gedrag apart is beoordeeld.


- Personages opent nu met een leeg contentvlak; het formulier verschijnt pas na Nieuw of selectie van een bestaand personage.
- Een nieuw personage is eerst een lokale draft en wordt pas bij Opslaan naar schijf geschreven.
- Na opslaan of verwijderen sluit de detailweergave weer naar het lege contentvlak.
- De personagelijst gebruikt een subtiele micro-label zodat subnavigatie en lijstinhoud visueel duidelijker gescheiden zijn.

## 0.15.0 — Boekplanning en ideeën (MVP)
- Nieuwe optionele **Planning**-modus in de hoofdrail, alleen zichtbaar wanneer een boek geopend is.
- Planning is modulair opgesplitst onder `quietwriter/ui/planning/`: shell, personages, outline en notities hebben elk een eigen scherm/module.
- Gestructureerde personageprofielen met vaste velden die later gericht als AI-context gebruikt kunnen worden: rol, beschrijving, persoonlijkheid, motivatie, doelen, angsten, waarden, conflicten, achtergrond, manier van spreken, gedrag onder druk en notities.
- Personagerelaties gebruiken stabiele IDs en ondersteunen bekende bidirectionele relatieparen; relaties zijn klikbaar en verwijderbaar.
- Nieuwe outline per bestaand hoofdstuk, plus **Losse ideeën**. Scènes bevatten titel, synopsis, personages, locatie, doel, conflict, uitkomst, status en notities.
- Scènes verwijzen naar stabiele `character_id`- en `chapter_id`-waarden, zodat hernoemen geen koppelingen breekt.
- Boeknotities gebruiken dezelfde `ManuscriptEditor` en blijven gewone Markdown (`planning/notes.md`).
- Planningdata staat bewust los van het manuscript in `planning/characters.json`, `planning/outline.json` en `planning/notes.md`.
- Planningbestanden vallen onder dezelfde SHA-256 revision/conflictbeveiliging als hoofdstukken en `book.json`.
- Versiegeschiedenis neemt de planning automatisch mee; lokale planning kan bij een conflict eveneens als herstelversie worden bewaard.
- Nieuwe storage-/architectuurtests voor personagevelden, relaties, scène-ID-koppelingen, Markdownnotities en externe wijzigingen.

## 0.14.0 — Veilige externe wijzigingen
- Nieuwe optimistic-concurrencylaag in `quietwriter/revisions.py`; geen lockfiles, sessieprotocol of Dropbox-specifieke code.
- Elk geopend boek krijgt in-memory revisions van `book.json` en alle hoofdstukbestanden op basis van bestandsgrootte + SHA-256. `mtime` wordt alleen diagnostisch bewaard en beslist nooit over een conflict.
- Vlak vóór iedere bewaakte schrijfactie controleert de storage-laag de volledige bekende boekstaat. Een externe wijziging wordt nooit stilletjes overschreven.
- Extern toegevoegde/verwijderde hoofdstukbestanden worden eveneens als wijziging gedetecteerd.
- Tijdelijke lees-/sync-locks zijn een aparte verificatiefout; autosave bewaart de tekst in geheugen en probeert later opnieuw in plaats van dit als inhoudsconflict te behandelen.
- Bij een echt conflict pauzeert autosave en kiest de gebruiker tussen **Mijn versie gebruiken** en **Versie op schijf gebruiken**.
- Beide conflictkeuzes maken vooraf automatisch een versie in de bestaande versiegeschiedenis (`conflict_external` of `conflict_local`).
- **Mijn versie gebruiken** laadt eerst de actuele schijfversie en legt alleen het huidige in-memory hoofdstuk daaroverheen, zodat andere externe wijzigingen behouden blijven.
- **Versie op schijf gebruiken** bewaart de lokale in-memory staat eerst als herstelversie en laadt daarna opnieuw van schijf.
- Structurele schrijfacties (manifest, hoofdstukken, secties, verplaatsen, verwijderen en herstel) gebruiken dezelfde revision-guard.
- Nieuwe regressietests voor happy path, externe hoofdstuk-/manifestwijzigingen, identieke inhoud met andere mtime, extern toegevoegde bestanden, pre-mutation guards en lokale recovery snapshots.


## 0.13.5
- Venstergeometrie wordt nu als expliciete normale `QRect` opgeslagen in plaats van via Qt's opaque `saveGeometry()`-blob.
- Opstarten op een andere computer, monitor, resolutie of DPI valideert en begrenst de opgeslagen positie en afmetingen vóór het native Windows-venster wordt aangepast.
- Een venster dat buiten alle huidige schermen valt, verhuist veilig naar het primaire scherm.
- Gemaximaliseerde status wordt los van de normale venstergeometrie bewaard.
- De oude `geometry`-instelling wordt bewust niet meer hersteld; daarmee kan een ongeldige oude geometry geen Windows `setGeometry`-waarschuwing meer veroorzaken.

## 0.13.4 — Opmaakstabiliteit en Windows font-rendering
- Scènebreuken (`***`) zijn nu beschermd tegen alle inline- en blokopmaakacties.
- Andere inline stijlen worden nooit meer in een backtick-codespan geïnjecteerd; code blijft letterlijk en ongewijzigd.
- De gedeelde `is_scene_break_line()`-helper voorkomt dat editorweergave en Markdowntransformaties verschillende definities gebruiken.
- Dode/verwarrende triple-star-parserlogica is vereenvoudigd.
- De verborgen-markertekst gebruikt niet langer een extreem 0,1-punts font of `fontStretch(1)`. Dit vermijdt een waarschijnlijke DirectWrite-trigger achter `QWindowsFontEngineDirectWrite::addGlyphsToPath: GetGlyphRunOutline failed` op Windows.
- Nieuwe gedrags-tests voor scene-break-integriteit, code-span-bescherming, multi-line style state, toolbar-state, undo en Qt runtime-opmaak.

## 0.13.3 — Samengestelde opmaak en toolbar-status
- Inline opmaak wordt nu samengesteld in plaats van elkaar te overschrijven: vet, cursief, onderstrepen, doorhalen en code kunnen betrouwbaar gecombineerd worden.
- De selectie-toolbar toont actief welke stijlen op de volledige selectie van toepassing zijn.
- Een gemengde selectie (bijvoorbeeld enkele cursieve woorden in gewone tekst) kan met één klik volledig cursief worden gemaakt en met een tweede klik volledig naar normaal worden teruggezet.
- Markdown-markeringen worden semantisch genormaliseerd bij toggelen, zodat combinaties zoals vet+cursief geen zichtbare of kapotte markers achterlaten.
- Nieuwe regressietests voor gecombineerde stijlen en gemengde selecties.


## 0.13.2
- Schrijfopmaak opnieuw opgebouwd als echte presentatie-laag boven platte Markdown.
- Markdownmarkeringen voor vet, cursief, onderstrepen, doorhalen, code, koppen, citaten en lijsten worden visueel ingeklapt in plaats van als witte tekens met normale breedte weergegeven.
- Dezelfde highlighter combineert manuscriptopmaak en spellingsonderstreping zodat beide stijlen elkaar niet overschrijven.
- Opsommingen, nummering en citaten krijgen een eigen visuele marker terwijl de Markdownbron intact blijft.
- Opmaaktoolbar heeft circa dubbel zo grote bedieningselementen en duidelijkere typografische iconen.

## 0.13.1 — PySide6 compatibiliteit

- Opgelost: startup-crash op sommige PySide6 6.x-versies bij `QTextBlockFormat.setLineHeight()`.
- De line-height modus wordt nu expliciet genormaliseerd naar de onderliggende integerwaarde en de hoogte naar `float`, conform de bindingsignature op oudere én nieuwere PySide6-versies.
- Geen functionele of visuele wijzigingen aan de manuscriptstijl.

## 0.13.0 — Schrijfopmaak en manuscriptstijl

- Nieuwe selectie-toolbar die na één seconde verschijnt bij geselecteerde tekst.
- Opmaakacties: normale alinea, tussenkop, opsomming, genummerde lijst, citaat, code, vet, cursief, onderstrepen en doorhalen.
- Opmaak blijft opgeslagen als leesbare Markdown/HTML-markup; de editor blijft een plain-text bron bewaren.
- Markdownmarkeringen worden in de schrijfruimte subtiel verborgen terwijl de opmaak visueel wordt weergegeven.
- Sneltoetsen voor vet (Ctrl+B), cursief (Ctrl+I), onderstrepen (Ctrl+U) en doorhalen (Ctrl+Shift+S).
- `***` blijft de bron voor scènebreuken, maar wordt visueel weergegeven als een rustige horizontale divider met drie punten.
- Manuscriptalinea's krijgen automatische eerste-regel-inspringing voor opeenvolgende alinea's; de eerste alinea, tekst na een lege regel, tussenkop, citaat of scènebreuk begint links.
- Nieuwe onafhankelijke manuscriptinstellingen: regelafstand, inspringing, ruimte na alinea en slimme typografische aanhalingstekens.
- Rechte dubbele quotes die tijdens typen worden ingevoerd kunnen automatisch als “slimme” quotes worden geplaatst.
- Opmaak- en manuscriptlogica is modulair opgesplitst in `manuscript_markup.py`, `manuscript_editor.py` en `selection_toolbar.py`.
- Extra regressietests voor Markdown-opmaak, lijsten, tussenkoppen, quotes en UI-architectuur.

## 0.12.1

Zie eerdere release voor de technische UI-refactor en reviewfixes.
