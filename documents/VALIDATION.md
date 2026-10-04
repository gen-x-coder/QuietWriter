# QuietWriter — validatiestatus 1.0.0

Deze pagina maakt controleerbaar waarop uitspraken als "groen" zijn gebaseerd.

## Reviewronde 56 — 2 oktober 2026

Omgeving van de onafhankelijke lokale review:
- Python 3.12.3
- PySide6 6.11.2

Resultaten vóór de laatste overdraagbaarheidsfixes:
- `tools/check_undefined_names.py`: OK
- actieve suite: 433 geslaagd + 284 subtests
- `pytest -m qt`: 80 geslaagd
- app koude start: OK
- `python main.py --smoke-test`: exitcode 0
- release staging + Windows version-info: OK
- oude 0.36.10 legacy-suite tegen rc2-code: 450/451; de enige fout zocht het bewust verwijderde oude `documents/dev/UI_GUIDE.md` en was geen productgedrag
- corrupte zoekcache: succesvol verwijderd en herbouwd
- brandinggenerator: `.ico` en drie in-app SVG's byte-identiek gereproduceerd

De review bevestigde dat de codewijzigingen voor de zoekcache en het expliciet sluiten van de zoekindex correct werken.

## Fixes naar aanleiding van reviewronde 56

De clean-source set is daarna aangevuld/gecorrigeerd met:
- `.github/workflows/tests.yml` en `build-windows.yml` terug in de bron;
- volledige SIL OFL 1.1-teksten voor alle vier gebundelde fonts;
- versieneutrale `LEESMIJ.txt`;
- tekstbreedte-combobox verbreed naar 160 px zodat ook Extra breed / Extra wide volledig zichtbaar zijn;
- actuele `branding/README.md` en `shapely` in `requirements-dev.txt`;
- `DEVELOPER_REFERENCE.md` met runtime-, opslag- en module-naslag;
- `UI_REFERENCE.md` met de concrete UI-specificaties die bij de eerste consolidatie te sterk waren samengevat;
- neutralere pytest-markertekst;
- release-stagingtest gebruikt een tijdelijke map via `QUIETWRITER_STAGE_DIR`;
- volledige fontlicentie-inhoud wordt nu met een test bewaakt.

## Interpretatie

"Groen" betekent dus niet dat alle toekomstige praktijksituaties bewezen zijn. Voor stabiele 1.0 blijven de handmatige/praktische checks uit `ROADMAP_AND_IDEAS.md` gelden, waaronder clean Windows, SmartScreen, meerdere DPI-schalen, echte providers, oude/grote boeken en langere dagelijkse schrijfsessies.


## Stap 1 vervolgcontrole — 3 oktober 2026

Na reviewronde 57 zijn de twee resterende overdraagbaarheidspunten verwerkt en opnieuw gecontroleerd:

- tekstbreedte-combo staat op 160 px;
- `UI_REFERENCE.md` bevat geen `Herschrijf selectie` en gebruikt **Meelezer** als productterm;
- gerichte regressietest `tests/current/test_review_03610.py`: **3 geslaagd**;
- `.github/workflows/tests.yml` en `build-windows.yml` zijn aanwezig;
- release staging is opnieuw opgebouwd en `prepare_release.py --check` meldt **Release staging: OK**;
- applicatieversie was in deze stap nog `1.0.0-rc2`; na de persona-datafix uit reviewronde 58 is de volgende kandidaat `1.0.0-rc3`;
- bron-ZIP bevat geen `release/`, `tests/legacy/`, `__pycache__`, `.pytest_cache`, `.pyc` of `.pyo`;
- de v2-roadmap markeert de reviewpunten nu als afgerond.

Beperking van deze controleomgeving:
- Python is hier 3.13.5;
- PySide6, spylls en pyflakes zijn hier niet geïnstalleerd;
- daarom zijn de volledige Qt-suite, de echte GUI-smoketest en de undefined-name-check in deze controle niet opnieuw uitgevoerd;
- een echte Windows portable build/SmartScreen/DPI-test kan alleen op Windows worden uitgevoerd.

De volledige Python 3.12/PySide6 6.11.2-runtimecontrole uit reviewronde 57 blijft daarom de laatste volledige Qt-baseline. Vanaf hier bestaat stap 1 vooral uit handmatige praktijkvalidatie op Windows en met echte boeken/providers.


## Reviewronde 58 — persona-conflictgat en RC3

Reviewronde 58 vond één echte 1.0-dataveiligheidsleemte buiten de oorspronkelijke conflict-audit: de globale Schrijverspersona kon een externe wijziging van `persona/schrijver.md` stil overschrijven. De audit is daarop herhaald via alle writeroutes (`_safe_atomic_write_text`, atomic writes en vergelijkbare persistente schrijfpaden).

RC3 corrigeert dit als laatste bekende 1.0-datafix:

- PersonaPage onthoudt de file-revision die bij `reload()` is geladen.
- `Library.save_persona()` vergelijkt die revision direct vóór de atomische write.
- Bij afwijking wordt niets overschreven en verschijnt een expliciete conflictkeuze.
- Kiest de gebruiker lokaal, dan wordt de externe versie eerst bewaard onder `archive/persona/*__conflict_external.md`.
- Kiest de gebruiker schijf, dan wordt de lokale invoer eerst bewaard onder `archive/persona/*__conflict_local.md`.
- Verandert het bestand opnieuw tijdens conflictoplossing, dan faalt de write opnieuw gesloten.
- Het Meelezer-gesprekslog `.quietwriter/ai_chat.json` is voor 1.0 bewust gedocumenteerd als last-writer-wins uitzondering; het is geen auteursbron.

Controle in de lokale beperkte omgeving:

- gerichte persona/release-tests: **14 geslaagd**;
- volledige actieve suite: **388 geslaagd, 29 overgeslagen, 284 subtests geslaagd**;
- de 29 skips zijn Qt-runtimechecks doordat PySide6 hier ontbreekt;
- `pyflakes` ontbreekt hier eveneens, dus de undefined-name-check kon niet opnieuw worden uitgevoerd;
- reviewronde 58 zelf reproduceerde de oorspronkelijke fout met Python 3.12.3/PySide6 6.11.2; een volledige echte Qt-run voor RC3 blijft daarom onderdeel van de volgende externe/praktische validatie.

Omdat de code na de gepubliceerde RC2 wijzigt, draagt deze bron terecht versienummer **1.0.0-rc3**. Darlings blijft ontwerpwerk tot de stabiele 1.0.0 is uitgebracht.

## Reviewronde 59 — RC3 validatie en RC4-fixes

Externe review van RC3 (Python 3.12.3 / PySide6 6.11.2) rapporteerde:

- volledige suite: **438 geslaagd + 284 subtests**;
- Qt-subset: **80 geslaagd**;
- undefined-names-check: OK;
- koude start: OK;
- `--smoke-test`: exitcode 0;
- tien persona-conflictscenario's uitgevoerd.

De kern van de RC3-personafix is daarmee bevestigd. Reviewronde 59 vond nog drie 1.0-randgevallen die in RC4 zijn verwerkt:

1. een extern verwijderd persona-bestand kon de conflictflow en afsluiten blokkeren;
2. twaalf localeberichten bevatten letterlijke `\n` in plaats van regeleinden;
3. het persoonlijke woordenboek schreef een oude in-memory set terug en kon externe toevoegingen verliezen.

RC4 voegt regressiedekking toe voor ontbrekende persona-revisions, locale-newlines en merge-before-write van beide persoonlijke woordenlijsten. Een corrupte persona blijft fail-closed: het live bestand wordt niet overschreven en lokale invoer wordt eerst onder `archive/persona/` veiliggesteld.

RC4 moet opnieuw met echte PySide6/Windows worden gevalideerd voordat een stabiele 1.0-tag wordt gezet.



## Reviewronde 60 — corrupte persona en optionele AI-context

Reviewronde 60 bevestigde dat alle RC4-fixes werken en vond nog één startupblokkade: een niet-UTF-8 `persona/schrijver.md` liet `MainWindow` tijdens opbouw crashen. Daarnaast kon de Meelezer crashen wanneer een optionele vaste contextbron (persona, Boekprofiel of Boekgeheugen) beschadigd was.

RC5:
- opent een corrupte persona alleen-lezen in plaats van de applicatiestart te blokkeren;
- overschrijft die bron niet;
- slaat corrupte vaste AI-context per bron over;
- meldt de weggelaten bron in contextinformatie;
- voegt zowel pure regressietests als een echte Qt-runtimecase voor de persona-startup toe.

De volledige Qt-/Windowscontrole moet in een omgeving met Python 3.12 en PySide6 opnieuw worden uitgevoerd voordat RC5 als basis voor de 1.0-praktijkvalidatie wordt beschouwd.


### Lokale RC5-controle in deze bouwomgeving

Na de RC5-wijzigingen:
- volledige beschikbare suite: **402 geslaagd, 30 overgeslagen, 284 subtests geslaagd**;
- gerichte RC5-/packagingtests: **11 geslaagd**;
- `prepare_release.py --check`: **Release staging: OK**;
- de overgeslagen tests zijn Qt-runtimecases omdat PySide6 in deze omgeving niet geïnstalleerd is;
- `tools/check_undefined_names.py` kon hier niet draaien omdat `pyflakes` ontbreekt.

Reviewronde 60 blijft daardoor de laatste volledige Python 3.12/PySide6-baseline voor RC4: 446 tests, 80 Qt-tests, undefined-names en smoke groen. RC5 moet met diezelfde volledige omgeving opnieuw worden gecontroleerd voordat de kandidaat naar praktijkvalidatie gaat.


## RC5 testcorrectie — 3 oktober 2026

Reviewronde 61 bevestigde dat de twee RC5-fixes zelf werken met echte PySide6. Eén nieuw toegevoegde Qt-regressietest gebruikte echter de verkeerde MainWindow-attribuutnaam (`persona_page` in plaats van `persona`). Dit was uitsluitend een testfout; applicatiecode is niet gewijzigd.

Na correctie:
- `test_rc5_corrupt_persona_qt.py` gebruikt `window.persona`;
- de volledige niet-Qt-controle in de huidige ChatGPT-omgeving geeft **402 geslaagd, 30 overgeslagen, 284 subtests**;
- de overgeslagen tests zijn Qt-runtimechecks omdat PySide6 hier niet beschikbaar is;
- de externe PySide6-review meldt dat beide nieuwe Qt-tests met de gecorrigeerde attribuutnaam slagen.

Nieuwe Qt-tests moeten voortaan bij oplevering expliciet worden genoemd wanneer ze in de bouwomgeving niet daadwerkelijk konden draaien.

## 1.0.0 releasebesluit — 4 oktober 2026

De RC5-baseline is na de laatste testfix als stabiele 1.0.0 aangewezen.

Bevestigde praktische validatie richting 1.0:

- Windows 150% DPI: bruikbaar; lange titel, tekstbreedte en Meelezer passen zonder problematische minimummaat;
- groot testboek: 4 delen, 40 hoofdstukken, circa 149.850 woorden; openen, hoofdstukwissel, typen/autosave, zoeken, hernoemen/verplaatsen, Planning, afsluiten en heropenen zonder foutmeldingen of dataverlies;
- Ollama cold start: UI blijft responsief en een echte Meelezer-vraag werkt;
- OpenRouter: echte vraag werkt correct;
- twee-computer/sync-conflict: bestaande conflictflow voorkomt stille overschrijving en bewaart herstelmogelijkheden;
- persona-conflicten, verwijderde/corrupte persona, extern aangevuld woordenboek en corrupte optionele AI-contextbronnen zijn in de RC-rondes specifiek gehard en getest.

Niet als aparte blokkade uitgevoerd:

- oude gebruikersboeken migreren: vóór 1.0 bestaan alleen testboeken, dus er is geen echte historische gebruikerspopulatie om te migreren;
- extra DPI-rondes naast de geslaagde 150%-controle;
- langdurige wekenlange pilot als harde tagvoorwaarde.

De stabiele release verandert geen productfunctionaliteit ten opzichte van de gevalideerde RC5-code; alleen release-/versiemetadata gaat van `1.0.0-rc5` naar `1.0.0`.
