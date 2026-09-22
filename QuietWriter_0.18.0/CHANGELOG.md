# Changelog

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
