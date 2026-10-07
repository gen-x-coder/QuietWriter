# QuietWriter — releaseproces

Dit document is de canonieke werkinstructie voor het publiceren van een QuietWriter-release.

Doel: een toekomstige maintainer — mens of AI — moet een release kunnen uitvoeren zonder de oude chatgeschiedenis nodig te hebben.

## 1. Repositorymodel

QuietWriter gebruikt twee repositories:

- `gen-x-coder/QuietWriter-dev` — private ontwikkelrepository.
- `gen-x-coder/QuietWriter` — publieke open-source- en releaserepository.

De private repository is de werkplaats. De publieke repository is de autoritatieve bron voor officiële releases, publieke CI, release-tags en code signing.

Een officiële release mag daarom **niet rechtstreeks vanuit QuietWriter-dev worden gepubliceerd**.

## 2. Huidige uitgangssituatie

Sinds 6 oktober 2026 is de publieke repository ingericht als GPLv3-open-sourceproject.

De publieke `main` bevat:

- de volledige QuietWriter-bron;
- GPLv3;
- publieke tests;
- Windows- en Ubuntu-CI;
- Windows-buildworkflow;
- privacybeleid;
- downloadinformatie;
- security- en contribution-documentatie;
- code-signing policy.

De testworkflow draait automatisch op `main` en pull requests en gebruikt GitHub-hosted Windows- en Ubuntu-runners.

### Historische uitzondering: 1.1.0

Release `v1.1.0` bestond al voordat de broncode in de publieke repository werd gepubliceerd.

De bestaande `v1.1.0`-tag wordt **niet verplaatst of herschreven**.

Vanaf de eerstvolgende release moet de tag exact wijzen naar de publieke broncommit die daadwerkelijk is gebouwd en ondertekend.

## 3. Releaseprincipes

Voor iedere officiële release gelden deze regels:

1. De te releasen bron is eerst getest in de ontwikkelomgeving.
2. De volledige releasebron staat vóór tagging op `gen-x-coder/QuietWriter/main`.
3. De versie in `quietwriter/__init__.py` is de bron van waarheid.
4. Publieke Windows- en Ubuntu-tests moeten groen zijn.
5. De officiële Windows-build ontstaat uit de publieke repository.
6. De release-tag wordt pas gezet nadat de publieke bron en CI correct zijn.
7. Na activering van SignPath wordt alleen het door SignPath ondertekende artifact gepubliceerd als officiële Windows-release.
8. Release-assets krijgen een SHA-256-bestand.
9. Tags en gepubliceerde releases worden niet achteraf stil herschreven.
10. Bij twijfel of inconsistente build/signing: stop de release en maak een nieuwe versie of release candidate.

## 4. Voorbereiding in QuietWriter-dev

Ontwikkeling en functionele validatie gebeuren eerst in `QuietWriter-dev`.

Voor release:

- alle geplande wijzigingen zijn afgerond;
- Claude/testsuite of andere afgesproken review is groen;
- noodzakelijke visuele Windows-tests zijn uitgevoerd;
- er zijn geen bekende dataverlies- of releaseblokkerende bugs;
- `documents/CHANGELOG.md` is bijgewerkt;
- release notes zijn aanwezig indien gewenst;
- versie is correct in `quietwriter/__init__.py`;
- build- en packagingbestanden horen bij dezelfde versie.

Gebruik bij voorkeur een expliciete releasecommit in de dev-repository.

Maak **geen officiële release-tag in QuietWriter-dev**.

## 5. Bron naar de publieke repository brengen

De publieke repository moet vóór de release exact de bron bevatten die gebruikers kunnen controleren.

Aanbevolen proces:

1. Werk de private dev-branch af.
2. Controleer dat er geen secrets, lokale instellingen, API-sleutels, caches of gebruikersdata in de bron zitten.
3. Breng de volledige geteste bron naar `gen-x-coder/QuietWriter/main`.
4. Behoud de publieke repositorydocumentatie en publieke CI-configuratie.
5. Push de publieke bron.
6. Wacht op de automatische publieke CI.

Bij grote versieovergangen is een tijdelijke lokale clone/branch veilig omdat daarmee de private en publieke histories niet onbedoeld worden vermengd.

## 6. Publieke CI-gate

De workflow `.github/workflows/tests.yml` draait:

- op pushes naar `main`;
- op pull requests naar `main`;
- handmatig via `workflow_dispatch`.

De matrix bevat:

- `ubuntu-latest`;
- `windows-latest`.

Belangrijke stappen:

- Python 3.12;
- testdependencies installeren;
- fonts ophalen;
- undefined-name check;
- volledige pytest-suite;
- Qt-testsubset.

Een release mag pas verder wanneer beide platforms groen zijn.

### CI-fouten

Maak onderscheid tussen:

- echte productregressie;
- platformafhankelijke test;
- verouderde release-test;
- CI-/runnerprobleem;
- cleanup/resource-lock.

Verzwak een test niet alleen om CI groen te maken. Herstel de test zodat hij de oorspronkelijke functionele bedoeling platformonafhankelijk controleert.

## 7. Windows build

De workflow `.github/workflows/build-windows.yml` bouwt op `windows-latest`.

De build gebruikt:

- Python 3.12;
- MSVC build environment;
- `build_exe.cmd`;
- schone allowlist-stage via `tools/prepare_release.py`;
- PyInstaller onedir;
- executable smoke test;
- SHA-256 van de portable ZIP.

De distributie bevat geen tests, Git-metadata, ontwikkelrapporten, caches of interne DEV/PROD-launchers.

## 8. Tagging

Versievoorbeeld: `1.2.13`.

De officiële tag is:

`v1.2.13`

Voor tagging controleren:

- publieke `main` bevat exact versie `1.2.13`;
- Windows CI groen;
- Ubuntu CI groen;
- changelog/release notes correct;
- geen onbeoordeelde commits na de releasecandidate;
- SignPath-configuratie actief als signing verplicht is.

Daarna wordt de tag op de juiste publieke commit geplaatst.

De buildworkflow controleert dat:

`tag == "v" + quietwriter.__version__`

Bij mismatch moet de build stoppen.

## 9. SignPath — status vóór goedkeuring

QuietWriter heeft een aanvraag ingediend voor SignPath Foundation Open Source Code Signing.

Tot de aanvraag is goedgekeurd:

- geen self-signed certificaat gebruiken voor officiële releases;
- geen commercieel certificaat aanvragen alleen om deze flow te omzeilen;
- de publieke buildworkflow mag unsigned artifacts maken;
- nieuwe officiële signed releases wachten op de Foundation-configuratie wanneer signing als release-eis is afgesproken.

De publieke repository bevat:

- `CODE_SIGNING_POLICY.md`;
- `DOWNLOAD.md`;
- `PRIVACY.md`;
- de verplichte SignPath Foundation-vermelding.

## 10. SignPath — definitieve flow na goedkeuring

Na goedkeuring moeten deze gegevens in SignPath worden vastgelegd en daarna in dit document worden ingevuld:

- SignPath organization ID;
- project slug;
- artifact-configuration slug;
- signing-policy slug;
- naam van het toegewezen SignPath Foundation-certificaat;
- GitHub trusted build system;
- eventueel benodigde GitHub secretnaam voor de SignPath API-token.

**Deze waarden niet raden.** Ze worden pas ingevuld nadat SignPath ze daadwerkelijk heeft toegewezen.

### Verwachte technische flow

1. GitHub Actions checkt de publieke releasecommit uit.
2. Windows-build produceert het unsigned portable artifact.
3. `actions/upload-artifact` bewaart het unsigned buildartifact in dezelfde workflow.
4. De officiële SignPath GitHub Action dient een signing request in.
5. SignPath controleert de oorsprong via GitHub/Origin Verification.
6. SignPath ondertekent `QuietWriter.exe` in het artifact volgens de artifact configuration.
7. De workflow downloadt/ontvangt het signed artifact.
8. De signed ZIP wordt de officiële GitHub Release-asset.
9. SHA-256 wordt berekend over het artifact dat daadwerkelijk wordt gepubliceerd.
10. Alleen als signing en alle verificaties groen zijn, wordt de release gepubliceerd.

De eerder voorbereide artifactconfiguratie moet overeenkomen met de werkelijke ZIP-layout. Controleer dat opnieuw wanneer SignPath wordt geactiveerd.

## 11. GitHub secrets na SignPath-goedkeuring

De SignPath API-token mag nooit in broncode, workflowtekst, documentatie of release notes staan.

Gebruik uitsluitend GitHub Actions Secrets.

De precieze secretnaam wordt na goedkeuring vastgelegd. Verwacht bijvoorbeeld een naam als:

`SIGNPATH_API_TOKEN`

Maar gebruik alleen de naam die de definitieve workflow daadwerkelijk verwacht.

## 12. Publiceren van de GitHub Release

Een stable release bevat minimaal:

- `QuietWriter-windows-portable.zip`;
- `QuietWriter-windows-portable.zip.sha256`.

Na SignPath-activering is de ZIP de **signed** build.

De vaste stable-downloadnaam blijft:

`QuietWriter-windows-portable.zip`

Daarmee blijft deze URL bruikbaar:

`https://github.com/gen-x-coder/QuietWriter/releases/latest/download/QuietWriter-windows-portable.zip`

Een release candidate wordt als prerelease gemarkeerd en mag niet onbedoeld de stable `latest` vervangen.

## 13. Release controleren

Na publicatie:

- download de ZIP vanaf GitHub alsof je een gewone gebruiker bent;
- controleer SHA-256;
- pak de ZIP uit naar een schone map;
- start QuietWriter zonder Python-ontwikkelomgeving;
- controleer first-run indien relevant;
- open een bestaand boek;
- typ en sla op;
- test minimaal één export;
- test afsluiten/herstart;
- controleer bij signed releases de digitale handtekening van `QuietWriter.exe`;
- controleer dat de releasepagina de juiste versie en assets toont;
- controleer de vaste `latest/download`-link bij stable releases.

## 14. Praktijktest vóór een belangrijke stable release

Voor een grotere stable release blijven de bestaande QuietWriter-praktijktests relevant:

- schone Windows-machine;
- DPI/schaal;
- groot boek;
- oudere echte boeken;
- Ollama;
- OpenRouter;
- sync-/conflictscenario's;
- first-run;
- updatecontrole;
- export;
- geen dataverlies bij afsluiten of fouten.

Geautomatiseerde CI vervangt deze praktijkvalidatie niet.

## 15. Linux

De publieke CI draait de Python/PySide6-bron ook op Ubuntu.

Dat betekent **niet automatisch** dat QuietWriter een officiële Linux-distributie heeft.

Een Linux-release mag pas worden toegevoegd nadat:

- een afzonderlijke Linux-buildworkflow bestaat;
- een Linux PyInstaller/package-artifact reproduceerbaar wordt gebouwd;
- een smoke test op het Linux-artifact slaagt;
- GUI/praktijktests op een echte Linux-desktop zijn uitgevoerd;
- download- en supportdocumentatie is bijgewerkt.

Tot dat moment is Windows het officiële distributieplatform.

## 16. Fout- en rollbackbeleid

Als een releaseflow faalt vóór publicatie:

- publiceer niets;
- herstel oorzaak;
- herhaal CI/build/signing.

Als een fout wordt ontdekt nadat een tag is gepubliceerd maar vóór brede distributie:

- verplaats de bestaande tag niet stil;
- maak zo nodig een nieuwe patchversie of release candidate.

Als een signing credential of releasekanaal mogelijk gecompromitteerd is:

- stop releases onmiddellijk;
- trek/roteer credentials volgens GitHub/SignPath-procedure;
- onderzoek welke artifacts geraakt kunnen zijn;
- hervat pas na expliciete verificatie.

## 17. Checklist per release

### Bron

- [ ] Versie in `quietwriter/__init__.py` klopt.
- [ ] Changelog bijgewerkt.
- [ ] Release notes gereed indien nodig.
- [ ] Geen secrets of gebruikersdata.
- [ ] Dev-tests/review groen.
- [ ] Volledige releasebron staat op publieke `main`.

### Publieke CI

- [ ] Windows groen.
- [ ] Ubuntu groen.
- [ ] Geen releaseblokkerende warnings/failures.

### Release

- [ ] Juiste publieke commit geselecteerd.
- [ ] Tag `v<versie>` klopt exact.
- [ ] Windows-build groen.
- [ ] Smoke test groen.
- [ ] Release hygiene groen.
- [ ] SignPath signing groen (na activering).
- [ ] SHA-256 hoort bij het gepubliceerde artifact.
- [ ] Stable/prerelease-status klopt.

### Na publicatie

- [ ] Download vanaf GitHub getest.
- [ ] ZIP uitpakken/starten getest.
- [ ] Digitale handtekening gecontroleerd (na activering).
- [ ] `latest/download` gecontroleerd bij stable.
- [ ] Releasepagina en notes gecontroleerd.

## 18. Onderhoud van dit document

Werk dit document bij zodra de daadwerkelijke SignPath Foundation-configuratie beschikbaar is.

Vervang dan de openstaande generieke SignPath-beschrijving door de echte:

- organization/project identifiers;
- signing policy;
- artifact configuration;
- secretnamen;
- workflowstappen;
- goedkeuringsmodel;
- eventuele handmatige SignPath-stappen.

De GitHub-workflows zijn uiteindelijk uitvoerbare waarheid; dit document legt uit **waarom** en **hoe** de flow hoort te werken.
