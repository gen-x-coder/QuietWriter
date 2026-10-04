# QuietWriter — release, branding en operations

## Repositorymodel
Historisch zijn er een private ontwikkelrepository en een publieke downloadrepository. Voor lokaal werken is de project-ZIP de praktische ontwikkelbasis; een eventuele latere Git-sync verandert de productstructuur niet.

## Windows-build
`build_exe.cmd` maakt een schone PyInstaller **onedir** build. De ontwikkelmap zelf wordt niet als distributiemap gebruikt.

`tools/prepare_release.py` bouwt een allowlist-stage, valideert die en voorkomt dat tests, devdocs, caches of andere rommel in de public release komen.

## Waarom onedir
Sneller starten, minder antivirusfrictie dan onefile en een duidelijke resource-layout.

## Release hygiene
Niet in de publieke package:
- tests;
- ontwikkel-/reviewdocumenten;
- Git metadata;
- caches/temp;
- interne DEV/PROD launchers.

Wel: executable, runtime resources, LEESMIJ en noodzakelijke licenties.

## Resources
Fonts en dictionaries hebben een expliciete fetch-/manifestflow. De bron-ZIP hoeft gegenereerde/binaire resources niet als ontwikkelrommel te bewaren zolang de fetch/buildroute ze reproduceerbaar maakt.

## Branding source-of-truth
Onder `branding/bron/`:
- `emblem_src.svg`
- `wordmark_src.svg`
- `logo_geometrie.py`
- `maak_iconen.py`

Deze behandelen we als broncode. Afgeleide iconen moeten reproduceerbaar zijn.

## Appicoon en woordmerk
Appicoon: taakbalk/venster/EXE, meerdere maten en een vereenvoudigde small-icon variant.  
Woordmerk: splash/About, horizontale rol, niet als vierkant icoon renderen.

## HiDPI
Branding moet bij 100/125/150% scherp zijn; SVG alleen is niet genoeg als de pixmap met verkeerde DPR wordt gerenderd.

## Runtimeprofielen
DEV en PROD kunnen gescheiden QSettings/workspaces/logs/AppUserModelID gebruiken. Interne launcherbestanden horen niet in de publieke release.

## Smoke
`--smoke-test` gebruikt geïsoleerde tijdelijke settings/appdata, raakt echte gebruikerstate niet, mag niet door modale startupfout hangen en geeft non-zero bij startup/eventloop failure.

## Versies
Appversie staat in `quietwriter/__init__.py`. Windows numeric file version gebruikt alleen SemVer core; string metadata bevat de volledige RC-versie.

## RC versus stable
RC's zijn prereleases. Een permanente `releases/latest/download/QuietWriter-windows-portable.zip` werkt pas betrouwbaar vanaf een gewone stable release.

## SHA-256
Iedere publieke ZIP hoort een checksumasset te hebben.

## SmartScreen en signing
Zonder code signing kan SmartScreen waarschuwen. Dat is een bekende distributiefrictie. Code signing is een mogelijke post-1.0 keuze als kosten, beheer en CI-secretmodel acceptabel zijn.

## Installer/updater
Niet nodig voor eerste stable. Pas toevoegen met expliciet ontwerp voor install/upgrade/uninstall, signing, rollback en user consent.

## Stable 1.0 checklist
- tests/Qt groen op Windows + Ubuntu;
- clean Windows build + smoke;
- hygiene;
- clean-machine praktijk;
- SmartScreen gecontroleerd;
- DPI gecontroleerd;
- echte AI-providerchecks;
- grote/oudere boeken;
- geen bekende dataverliesbug;
- documentatie/testset opgeschoond;
- branding reproduceerbaar.
