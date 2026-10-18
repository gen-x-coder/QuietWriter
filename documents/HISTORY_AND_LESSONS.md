# QuietWriter — geschiedenis en blijvende lessen

Dit document vervangt de tientallen chronologische reviewrapporten. Het changelog bevat versies; hier staan de probleemklassen die de huidige architectuur hebben gevormd. De originele rapporten staan in `archive/` (index: `archive/README.md`); zoek daar op versienummer als je de details nodig hebt.

## Externe sync en stale state
Meerdere pagina's hielden ooit verschillende Book/revisionstates vast. Een externe wijziging kon daardoor pas laat worden ontdekt of stale data laten schrijven. Les: sync is een concurrency/stateprobleem, geen Dropboxprobleem. Centrale revisions en één live Book-state zijn verplicht.

## Transactionele adoptie
Book adoption bond vroeger pagina's één voor één om; een latere recovery-write kon falen en een half oude/half nieuwe UI achterlaten. Oplossing: prepare/preflight, daarna commit. Recoverywrites vóór rebind, notices achteraf.

## Corrupt is niet leeg
Ongeldige UTF-8/JSON werd in vroege paden soms als leeg behandeld en later overschreven. Oplossing: expliciete read-only foutstaat, storageguard en Integriteit als enige herstelroute.

## Future format is niet corrupt
Een nieuwere Planning-versie werd ooit als herstelbare corruptie gezien, waardoor een oude History-versie kon downgraden. Nu: future-format aparte foutklasse, geen restore/downgrade, update QuietWriter.

## Onveilige fallback
Een directe overwrite na mislukte atomic replace leek gebruikersvriendelijk maar kon bij Windows/sync-lock juist truncaten. Fallback verwijderd. Liever een zichtbare fout dan beschadigde bytes.

## Savefout bij afsluiten
Een onverwachte exception in de laatste save kon het close-event toch laten passeren. Nu is sluiten fail-closed.

## Detach zonder write-block
Alleen revisiontracking uitschakelen bleek gevaarlijk: een vergeten writeroute kreeg dan juist minder bescherming. Nu is incompatible/detached expliciet write-blocked.

## Herstel is pas klaar als UI opnieuw gesynchroniseerd is
Een correct hersteld hoofdstuk kon door stale editorinhoud opnieuw worden overschreven. Na herstel moet de actieve workspace dezelfde waarheid adopteren.

## Qt-presentatie was geen betrouwbare bron
Highlighting, `toPlainText()` en presentation revisions veroorzaakten false-dirty en normaliseerden o.a. harde spaties/Unicode-separators. Er kwam een expliciet source-text contract. Dezelfde bugklasse bleek later ook in Planning-notities en publicatietekst te bestaan. Les: zoek het architectuurpatroon, niet alleen de eerste plek.

## Undo en automatische formatting
Automatische blockformatting kon een extra verborgen Undo-stap veroorzaken. Tekstbewerking en presentatie zijn nu bewust gescheiden en formatting scheduling wordt rond Undo/Redo afgeschermd.

## Settings preview was te destructief
AI uitvinken in preview kon een open paneel en half getypte vraag verliezen zonder Save. Preview is sindsdien alleen rendering; commit doet side effects.

## Qt parent() als service locator
Een refactor reparentte Settings onder een page stack, waarna code via `parent()` de verkeerde eigenaar vond. Les: expliciete references/contracts, geen domeinlogica op toevallige Qt-parenthiërarchie.

## Losse navigation visibility groeide oncontroleerbaar
Combinaties van boek open/dicht, AI, Advanced en rail open/dicht leverden inconsistenties. De rail werd declaratief gemodelleerd.

## Hidden pages beïnvloedden toch layout
QStackedWidget kon hidden pages in minimumsize meenemen. Er kwam een eigen page-stack/layoutcontract. 'Niet zichtbaar' is in Qt niet hetzelfde als 'geen layoutinvloed'.

## Lange boektitel en rechterpanelen
Lange titel + toolbar/panelen kon minimumwindow veel te breed maken. Titel mag nu krimpen/eliden. Dynamische content mag minimumsize niet dicteren.

## HiDPI branding
SVG-bronnen waren scherp maar pixmaps niet altijd bij 125/150%. Device pixel ratio is onderdeel van het brandingcontract.

## Crashstorm
Een timer-/paintfout kon tientallen foutvensters openen. Nu: één notice, teller/cooldown, volledig log. Fouttekst belooft bewust niet dat 'alles opgeslagen is' wanneer dat niet bewezen kan worden.

## Runtime i18n-fout
Een ontbrekende `tr` import veroorzaakte startcrash. Static undefined-name en translation gates werden releasefundament.

## Vertaling versus opgeslagen data
Editable Planning-combo's konden custom waarden of canonieke status door vertaling verliezen. Display en storage zijn sindsdien strikt gescheiden.

## Overgeslagen Qt-tests gaven vals vertrouwen
Source/unit tests waren groen terwijl echte PySide6 een crash of hang kon tonen. Qt-runtime draait daarom expliciet in CI. `-m qt` vervangt bestandsnaamfiltering.

## Modale dialogen lieten tests hangen
Timer/slot-dialogen werden niet altijd gemonkeypatcht. Testinfra behandelt onverwachte modaliteit als fout.

## Legacytests konden rotten
Een historische suite die niet standaard draait bleek zelf stuk te kunnen gaan. Langetermijnregel: belangrijke regressie hoort actief; irrelevante test wordt verwijderd, niet eeuwig gearchiveerd.

## SQLite-handles op Windows
`with sqlite3.connect()` sluit de connection niet automatisch; tempdirectorycleanup kon falen. Expliciet sluiten is nodig. Zoekcache is niet-autoritatief en mag bij corruptie worden weggegooid/herbouwd.

## AI async stale callbacks
Late providercallbacks moesten aan request/boekgeneration gebonden worden zodat een oud verzoek geen nieuw boek/gesprek kan muteren.

## AI-context werd te impliciet
Meer context leek 'slimmer', maar maakte privacy en semantiek onduidelijk. Context bekijken, expliciete labels en hoofdstukplanning-opt-in zijn daarom onderdeel van het product.

## Herschrijf selectie is bewust verwijderd
Technisch bruikbaar, productmatig onjuist: het maakte de AI een ghostwriter. QuietWriter kiest expliciet voor een Meelezer.

## OpenRouter warmup
Extern warmen bij paneelopen zou latency én privacy-effect hebben zonder echte vraag. OpenRouter doet dat niet; Ollama mag lokaal background warmen.

## OpenRouter UTF-8
SSE zonder charset kon als Latin-1 geïnterpreteerd worden. Stream wordt expliciet als UTF-8 behandeld.

## Free-model filter
Een nog niet geladen catalogus mocht de persisted OpenRouter-modelkeuze niet leegschrijven. UI-selectie is niet altijd de volledige persisted state.

## First-run en echte gebruikersstate
Alleen ontbreken van een setting was geen betrouwbare 'nieuwe gebruiker'-trigger. Bestaande settings of standaardwerkmap tellen als bestaand gebruik. Testprofielen zijn van productie gescheiden.

## Release uit een rommelige ontwikkelmap
Handmatig zippen was te foutgevoelig. Build gebruikt allowlist staging, hygiene en smoke. Publieke RC1 bevatte nog DEV/PROD launchers; daarna zijn die expliciet verboden.

# Lessen uit 1.4 en de 1.5.0-ontwikkellijn

## Een eigen updater bouwen was de verkeerde investering (1.5.0-dev.5 – dev.63)
We bouwden een eigen, ondertekende updater: Ed25519-manifesten, veilige extractie, mapwissel met journaal, health-check van de nieuwe exe, rollback, versiemappen met pointerbestanden en een aparte starter. Na ongeveer dertig ontwikkelversies was het nog steeds een lab ("production NO-GO") en had het bijna de hele 1.5-lijn gekost. In 1.5.1 is het vervangen door Velopack. Les: infrastructuur die niet over schrijven gaat (installeren, bijwerken, signeren) nemen we van een onderhouden standaardtool. Zelf bouwen doen we alleen als niets bestaands past bij "eenvoudig, niet technisch, portable". De eisen uit dat werk blijven wel gelden:
- gebruikersdata staat nooit in de programmamap (`workspace_path.py`, sinds dev.30);
- bijwerken gebeurt pas na een keuze van de gebruiker en loopt via het normale afsluitpad, zodat alles eerst wordt opgeslagen;
- alleen officiële HTTPS-releases, geen stille downgrade;
- een lokaal inventarisbestand bewijst nooit de herkomst van software.
Details: `archive/dev-overdrachten/` (UPDATE_*, UPDATER_*, DEV30 – DEV32, CLAUDE_REVIEW_UPDATER_DEV29) en de 1.5.0-dev-regels in de oude changelog.

## Een ontbrekend hoofdstuk is niet leeg (dev.33 – dev.34)
Dropbox/OneDrive kunnen `book.json` eerder leveren dan de hoofdstukbestanden. Een ontbrekend bestand werd als lege tekst getoond en kon zo worden opgeslagen. Nu geeft het `ChapterNotAvailableError`: de editor gaat op alleen-lezen, autosave stopt en woordtelling, AI-context, dupliceren en conflictversies weigeren of tonen een neutrale plaatshouder.

## Synchronisatiestatus kun je niet betrouwbaar weten (dev.35 – dev.36)
Er is geen algemene "Dropbox is klaar"-API. QuietWriter claimt daarom nooit dat synchronisatie klaar is. De boekenkast ververst alleen zolang hij zichtbaar is (F5, elke 8 s een metadatacheck). Conflictkopieën worden alleen gesignaleerd, nooit opgeruimd. De praktijktest met twee echte computers staat nog open.

## "Alles vervangen" over meerdere bestanden is geen transactie (dev.37 – dev.40)
Eerst wordt de hele set gecontroleerd. Daarna worden de originelen met een journaal (`pending`/`committed`/`recovered`) en SHA-256 bewaard, en volgt per bestand een atomische vervanging. Herstel zet alleen terug wat nog exact onze eigen geschreven bytes bevat; een intussen extern gewijzigd bestand wordt niet overschreven. Herstelmappen worden nooit automatisch verwijderd en zijn alleen-lezen te bekijken en vergelijken op Integriteit & herstel. Claim nooit volledige ACID-atomiciteit.

## Back-ups: eerst controleren, dan publiceren (1.4.0-dev.3 – dev.37)
Op Windows heeft fsync een schrijfbare handle nodig; met een alleen-lezen handle blokkeerde het (dev.4 → dev.5). Een back-up krijgt pas zijn definitieve naam na verificatie. Retentie draait pas na een geslaagde back-up. Handmatige back-ups en veiligheidskopieën worden nooit automatisch opgeruimd. Verborgen `.partial`-mappen horen nooit in een back-up, en één onvolledige versie mag de andere versies niet verbergen.

## Wat een AI-model zegt, is niet wat QuietWriter deed (dev.51 – dev.53, dev.58)
Modellen beweren soms dat ze iets "hebben opgeslagen". Alleen QuietWriter bevestigt opslag, na herlezen van de schijf. De knop **Onthouden** is de betrouwbare route. AI-tekst wordt als platte tekst of veilige Markdown getoond, zonder ruwe HTML. Links openen alleen na bevestiging en alleen via HTTPS.

## Bronmateriaal is data, geen instructie (dev.59 – dev.60)
Manuscript, profielen, Boekgeheugen en Planning gaan als apart, afgebakend gebruikersmateriaal naar het model, niet in de systeemprompt. Interne geheugenmarkeringen in geciteerde tekst worden geneutraliseerd.

## Geen stille terugval bij inloggegevens (dev.46 – dev.48, dev.61)
OpenRouter heeft twee verbindingsmethoden: browserlogin of API-sleutel. De gekozen methode wordt gebruikt, zonder stille terugval op de andere. Het API-endpoint ligt vast op `https://openrouter.ai/api/v1`, zodat een gemanipuleerde instelling het token niet naar een ander adres kan sturen. Bij verplichte reasoning schakelt QuietWriter niet zelf om en probeert het niet automatisch opnieuw (dev.55).

## Eerst gedrag afspreken, dan bouwen (dev.41 – dev.42)
De focusmodus werd gebouwd en één versie later op verzoek weer verwijderd. Bespreek bij UI-functies eerst het gewenste gedrag met de gebruiker.

## Versie-administratie liep uit de pas
Zipnamen (bijvoorbeeld "dev.41") en `__version__` (nog "dev.28") liepen weken uiteen, en de zip "1.6" bevatte 1.5.0-dev.63. Regel: `quietwriter/__init__.py` is de enige bron, elke bouwronde zet hem goed, en de zipnaam volgt hem.

## "Volledige suite niet gedraaid" mag geen gewoonte worden
Veel overdrachten meldden dat de volledige Qt-suite niet kon draaien, omdat PySide6 in de bouwomgeving ontbrak. Vanaf 1.5.1 draait de bouwer de volledige suite offscreen vóór de overdracht. Windows-specifieke gevallen (symlinks met WinError 1314, codepage, SQLite-handles, credentials op de host) blijven Lucas' Windows-test.

## Overkoepelende regels
- data boven gemak;
- één waarheid per concept;
- prepare vóór commit;
- privacy zichtbaar maken;
- test de laag waar de bug leeft;
- rust is een productfeature;
- een bestaande feature mag worden verwijderd als ze de productidentiteit verzwakt;
- bouw geen infrastructuur die een onderhouden standaardtool al levert.
