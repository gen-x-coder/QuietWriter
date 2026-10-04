# QuietWriter — geschiedenis en blijvende lessen

Dit document vervangt de tientallen chronologische reviewrapporten. Het changelog bevat versies; hier staan de probleemklassen die de huidige architectuur hebben gevormd.

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

## Overkoepelende regels
- data boven gemak;
- één waarheid per concept;
- prepare vóór commit;
- privacy zichtbaar maken;
- test de laag waar de bug leeft;
- rust is een productfeature;
- een bestaande feature mag worden verwijderd als ze de productidentiteit verzwakt.
