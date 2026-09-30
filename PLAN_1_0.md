# QuietWriter: plan naar 1.0

Dit plan is de gezamenlijke versie van het voorstel van ChatGPT, de correcties van Lucas en de reviewbevindingen van
Claude. Het is gecontroleerd tegen de code van 0.34.10.

## De harde regel

> Vanaf nu komt een functie alleen in de 1.0-lijn als die aantoonbaar nodig is om QuietWriter **stabiel, begrijpelijk of
> distribueerbaar** te maken. Alles wat alleen "leuk" of "slimmer" is, gaat naar v2.

Buiten bugfixes is AI bevroren.

## Wat er al is (vertrekpunt 0.34.10)

Een paar onderdelen bestaan al. Het werk daaraan is daardoor kleiner dan de roadmap doet vermoeden.

- **Crashlogging bestaat al.** `crash_logging.py` schrijft naar `<werkmap>/logs/crash.log`, roteert bij 2 MiB, gebruikt
  `faulthandler` en `sys.excepthook` en `threading.excepthook`, en valt terug op de tempmap van het besturingssysteem.
  Wat nog ontbreekt:
  - de gebruiker merkt er niets van (geen melding, geen "Logbestand openen");
  - Qt's eigen waarschuwingen (`qWarning` en dergelijke) worden niet gelogd;
  - **het log staat in de werkmap.** Staat die werkmap in Dropbox, dan schrijven twee computers naar hetzelfde
    `crash.log`. Dat geeft conflictkopieën en een log waarvan je niet weet van welke computer het komt.
- **Er is al een splash:** tekst, status en voortgang. Er ontbreekt alleen een logo.
- **Tweetaligheid is aanwezig.** `nl.json` en `en.json` hebben elk 738 sleutels. Twee concrete gaten:
  - **74 sleutels** worden in de code gebruikt maar staan niet in `en.json`, en tonen in het Engels dus Nederlands;
  - volgens een grove zoekactie staan er **minstens 39 hardgecodeerde Nederlandse teksten** buiten `tr()`, vooral in
    `ai/ui.py`.
- **Logo-assets zijn klaar:** `quietwriter_icons.zip` (app-`.ico`, licht, donker, klein, woordmerk, in-app-SVG's).

## Scope

| Onderdeel | Categorie | Versie | Klaar als… |
|---|---|---|---|
| Crashvangnet afmaken | **Must** | 0.35 | Een onverwachte fout geeft een rustige melding ("Er ging iets mis. Je werk is opgeslagen." en "Logbestand openen"). Het log staat lokaal per computer (`QStandardPaths.AppLocalDataLocation`), niet in de werkmap. Qt-berichten gaan via `qInstallMessageHandler` ook naar het log. Er is een test die in een slot een exception opwekt en controleert dat log en melding verschijnen. |
| Logo en branding inbouwen | **Must** | 0.35 | `quietwriter.ico` is het venster- en taakbalkicoon, met een AppUserModelID zodat Windows niet het Python-icoon toont. Het woordmerk staat op de splash en de Over-pagina, in themakleur. |
| Splash behouden | **Must** | 0.35 | Met logo. Blijft alleen in beeld tot het hoofdvenster verschijnt (zoals nu) en verbergt nooit een foutdialoog. Test: een foutmelding tijdens de start is zichtbaar en bedienbaar. |
| Vertaalcontrole | **Must** | 0.35 | De 74 ontbrekende `en`-sleutels zijn aangevuld en de hardgecodeerde teksten lopen via `tr()`. **Twee tests maken dit blijvend:** één faalt als een `tr()`-sleutel in `en.json` ontbreekt, één AST-test faalt op letterlijke tekst in `QLabel`/`setText`/`setToolTip`/`QPushButton`/`setPlaceholderText`. Extra aandacht voor het rechtermenu, Boekdetails, Boekprofiel en het AI-paneel. |
| Licentie-inventaris | **Must** | 0.35 | Er is een eigen `LICENSE` en een `THIRD_PARTY_LICENSES.md` met PySide6/Qt (LGPL), elk meegeleverd lettertype, elk Hunspell-woordenboek en Python. Beide zijn zichtbaar vanaf de Over-pagina. |
| First-run | **Must** (klein) | 0.35 ontwerp, 0.36 bouw | Maximaal 4 stappen: taal en thema → werkmap → spelling → AI (standaard **uit**). Elke stap is over te slaan en alles is later te wijzigen in Instellingen. **Bestaande gebruikers zien hem nooit**: de test is dat er al een `workspace`-instelling bestaat. |
| CI | **Must** | 0.35 (uiterlijk RC1) | GitHub Actions draait `pytest`, `-m qt`, `tests/legacy` en `tests/legacy -m qt` offscreen, op **Ubuntu én Windows**. De Windows-runner test dan echte Windows-bestandssemantiek bij elke push. |
| Portable Windows-build | **Must** | 0.36 | PyInstaller in **onedir**-modus (sneller opstarten en minder vals alarm bij antivirus dan onefile). Meegebundeld: lettertypen (dan worden ook de 2 fonttests groen), woordenboeken, de Qt-plugins `platforms`, `imageformats`, `iconengines` en `styles`, versie-informatie in het `.exe`, en het `.ico`. Start op een schone Windows 10 **en** 11 zonder Python. |
| Uitleg over SmartScreen | **Must** | 0.36 | Eén alinea in "Aan de slag": waarom Windows waarschuwt en hoe je verdergaat. |
| Windows-praktijktest | **Must** | 0.36–0.37 | De matrix hieronder is volledig afgevinkt. |
| Migratie van echte oude boeken | **Must** | 0.37 | Minstens 3 echte boeken uit oudere versies openen, bewerken en opslaan zonder verlies. Voor en na staat een bytevergelijking van de manuscripttekst. |
| Grote-boektest | **Must** | 0.37 | Een testboek van ongeveer 150.000 woorden in 40 hoofdstukken: openen, van hoofdstuk wisselen, typen, zoeken en exporteren blijven vlot. Zo wordt het criterium "editor voelt soepel" meetbaar. |
| Back-upinstructie | **Must** | 0.37 | Een documentatiepagina: welke map je kopieert, wat History wel en niet doet, en hoe je terugzet. |
| Documentatie (4 pagina's) | **Must** | 0.37 | Aan de slag · Bestanden en back-up · Privacy en AI · Problemen en logbestand. |
| Bekende problemen | **Must** | RC1 | Een lijst in de release notes, inclusief wat niet getest is. |
| Zelf ermee schrijven | **Must** | RC1 | 2–3 weken dagelijks schrijven zonder data-incident. |
| Werkmap exporteren met één klik | Nice if cheap | 0.37 | Een zip van de hele werkmap, zonder cache en logs. |
| Code signing | Nice if cheap | — | Alleen als het betaalbaar en eenvoudig is. Anders v2. |
| Transparant `.ico` zonder tegel | Nice if cheap | — | De SVG's staan al in het pakket. |
| Installer en updater | V2 | — | |
| Contextbudget | V2 | — | Tenzij de release candidate een echt probleem laat zien. |
| Nieuwe AI-functies, grote Planning-uitbreidingen | V2 | — | |
| Cloud- en sync-functies, plugins | V2 | — | |
| Luxe export- en mediafuncties | V2 | — | |
| macOS- en Linux-builds | V2 | — | |

## Windows-testmatrix (0.36–0.37)

| Situatie | Wat controleren |
|---|---|
| DPI 100%, 125%, 150% | Rail, editor, dialogen, iconen scherp, geen afgekapte tekst |
| Twee monitoren met verschillende DPI | Venster verslepen, dialogen openen op de juiste monitor |
| Lange paden (> 260 tekens) | Boek aanmaken, opslaan, History, export |
| Bestand vergrendeld door een ander proces | Opslaan geeft een nette melding, geen verlies, opnieuw proberen lukt |
| Antivirus of Defender scant tijdens het opslaan | Atomisch vervangen (`replace`) slaagt of meldt netjes |
| Werkmap in **OneDrive** | Windows 11 zet `Documenten` vaak standaard in OneDrive, met "Bestanden op aanvraag" (placeholders). Openen, opslaan en History |
| **Dropbox, twee computers** | Beide open, om beurten bewerken, tegelijk bewerken: de conflictmelding werkt en er gaat niets verloren |
| Slaapstand of netwerk weg tijdens AI-verzoek | Nette foutmelding, gesprek blijft intact |
| Schone Windows zonder Python | De portable build start, spelling werkt, lettertypen zijn aanwezig |

## Versies

### 0.35: fundament voor de release
Crashvangnet · logo en splash · vertaalcontrole met twee tests · licentie-inventaris · ontwerp van de first-run · CI.
**Klaar als:** alle vier de testruns zijn groen in CI op Ubuntu en Windows, er is een Engelse schermrondgang zonder
Nederlandse resten, en de crashmelding is gedemonstreerd.

### 0.36: Windows en verpakking
Portable build · first-run gebouwd · SmartScreen-alinea · eerste helft van de Windows-matrix (DPI, paden, vergrendeling,
schone machine).
**Klaar als:** de build start op een schone Windows 10 en 11 en de matrixregels voor 0.36 zijn afgevinkt.

### 0.37: praktijkgebruik
Migratie van echte boeken · grote-boektest · Dropbox en OneDrive · back-upinstructie · documentatie · bugs uit dagelijks
gebruik.
**Klaar als:** de hele Windows-matrix is groen en er zijn geen open 🔴-bevindingen.

### 1.0.0-rc1
Functies bevroren; alleen nog bugs. De lijst met bekende problemen is gepubliceerd, en Lucas schrijft er 2–3 weken mee.

### 1.0.0
Pas als alle vijf de voorwaarden gelden:
1. Er is geen bekende bug met dataverlies.
2. De grote-boektest is vlot.
3. De Windows-build is stabiel op de hele matrix.
4. `current`, `legacy` en `qt` zijn groen in CI, en de koude start slaagt.
5. De periode van dagelijks schrijven is voorbij zonder incident.

## Reviewafspraken per build

- Zoals nu: `pytest`, `pytest -m qt`, `pytest tests/legacy`, `pytest tests/legacy -m qt` en een koude start.
- Vanaf 0.35 draait CI dezelfde vier runs. Een build gaat pas naar review als CI groen is.
- Vanaf 0.36 komt er per build een smoketest van de portable build op Windows bij (door Lucas: starten, boek openen,
  typen, opslaan, afsluiten).
- Claude blijft testen wat CI niet kan: runtime-scenario's, foutinjectie, bytevergelijkingen en onderschepping van de
  prompt.
