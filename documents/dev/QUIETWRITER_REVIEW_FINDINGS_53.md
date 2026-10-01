# QuietWriter: reviewronde 53 (versie 0.36.4: warmup, werkmap, smoketest, LEESMIJ)

**Gelezen:** de diff tegen 0.36.3: `ai/ui.py`, `app.py`, `workspace_path.py` (nieuw), `first_run_wizard.py`,
`settings_page.py`, de spec, `prepare_release.py`, `build-windows.yml`, `documents/LEESMIJ.txt` en
`REVIEW_NOTES_0364.md`.

**Getest (Python 3.12.3, PySide6 6.11.2):**
- de vier runs en de undefined-names-check;
- Instellingen opslaan in de echte UI;
- werkmapscenario's in de wizard (via de echte `run()`) en in Instellingen;
- de warmup met nagebootste providers, inclusief een meting van hoe snel de UI blijft reageren;
- `--smoke-test` op de broncode, op een **gebouwde** exe en met een **opzettelijk kapotte** `MainWindow`;
- een nieuwe PyInstaller-build om te zien waar de LEESMIJ terechtkomt.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns

| Run | Geleverde 0.36.4 | Met de fix uit bevinding 1 |
|---|---|---|
| `tools/check_undefined_names.py` | ❌ `settings_page.py:841: undefined name 'normalized_workspace'` | ✅ OK |
| `pytest` | ❌ 1 gefaald, 274 geslaagd | ✅ 275 geslaagd |
| `pytest -m qt` | ❌ 1 gefaald, 62 geslaagd | ✅ 63 geslaagd |
| `pytest tests/legacy` | ❌ 1 gefaald, 450 geslaagd | ✅ 451 geslaagd, 284 subtests |
| `pytest tests/legacy -m qt` | ❌ 1 gefaald, 90 geslaagd | ✅ 91 geslaagd |

---

## Bevindingen

### 1. 🔴 Opslaan in Instellingen werkt niet meer

De twee nieuwe regels die het werkmappad normaliseren, staan in `refresh_models()` (regel 737–738) in plaats van in
`save_settings()`. Daardoor geeft `save_settings()` op regel 841 bij **elke** klik op Opslaan een
`NameError: name 'normalized_workspace' is not defined`.

Bevestigd in de echte UI: het thema wordt op Nacht gezet, er komt een `NameError`, en het thema blijft Helder. Thema,
taal, AI-provider, spelling en werkmap kunnen dus niet meer worden opgeslagen.

Gevolg voor jouw handmatige tests:
- het Instellingen-deel van test 1 loopt hierop stuk;
- **stap 1 van test 2** ("Kies OpenRouter als provider") ook;
- test 3 alleen als je de provider via `--first-run` in de wizard kiest.

**Oplossing:** verplaats die twee regels naar het begin van `save_settings()`. Daarmee is alles groen (de tabel hierboven).
`refresh_models()` hoort het werkmapveld ook niet te veranderen.

**Over het proces:** de checker uit 0.35.4 is precies hiervoor gemaakt en zou dit direct gemeld hebben. In de notes
staat "Python compile-check is groen", maar dat vangt geen undefined names. Laat ChatGPT `pyflakes` installeren
(`pip install pyflakes`) en `tools/check_undefined_names.py` vóór elke oplevering draaien. Of push eerst naar GitHub: de
CI maakt dit binnen een minuut rood.

### 2. 🟡 `--smoke-test` overschrijft de echte instellingen van het dev-profiel

De smoketest gebruikt `QSettings('QuietWriter', 'QuietWriter-Dev')` en schrijft daar **blijvend** in:
`workspace=/tmp/quietwriter-smoke-…`, `ai_enabled=false` en `first_run_done=true`.

Bevestigd: een dev-profiel met `workspace=…/MijnDevBoeken` en AI aan had na één smoketest een tijdelijke werkmap en AI
uit. Op een CI-runner maakt dat niet uit. Maar wie de exe lokaal met `--smoke-test` start, opent daarna in het
dev-profiel een lege tijdelijke werkmap: "mijn dev-boeken zijn weg".

**Voorstel:** gebruik in smoke-modus `QSettings(<tijdelijke map>/smoke.ini, QSettings.IniFormat)`.

### 3. 🟡 Een smoketest met een opstartfout faalt niet, maar blijft hangen

Met een opzettelijke `RuntimeError` in `MainWindow.__init__` geeft `--smoke-test` geen exitcode 1. Hij toont de gewone
**modale** foutdialoog en blijft daarop wachten (timeout na 25 s, rc 124). De fout staat wel in het log. Op GitHub loopt
zo'n job standaard tot 6 uur door, want de stap heeft geen `timeout-minutes`.

Een exception in een slot tijdens de 1,5 s waarin het venster draait, geeft alleen de niet-modale melding, en
`app.quit()` eindigt dan toch met rc 0.

**Voorstel:**
- in smoke-modus geen dialoog: log de fout, schrijf hem naar stderr en geef `return 1`;
- tel nieuwe exceptions in `crash.log` tijdens de run en geef rc 1 als het er meer dan 0 zijn;
- zet `timeout-minutes: 5` op de stap.

### 4. 🟡 De LEESMIJ staat in `_internal/`, niet naast `QuietWriter.exe`

De spec zet `documents/LEESMIJ.txt` op bestemming `'.'`. In een onedir-build van PyInstaller 6 is dat de
`_internal`-map. Bevestigd met een echte build: `dist/QuietWriter/_internal/LEESMIJ.txt`. In de uitgepakte release ziet
de gebruiker alleen `QuietWriter.exe`, `_internal/` en de twee `.cmd`-bestanden. De LEESMIJ vindt niemand.

**Voorstel:** haal de spec-regel weg en kopieer hem in `build_exe.cmd` na de `xcopy` naar `!OUT!\LEESMIJ.txt`. Laat de
workflow controleren dat hij daar staat.

**Inhoud (klein, maar dit is wat testgebruikers als eerste lezen):**
- `Documenten\\QuietWriter` staat met **dubbele backslashes** in een gewoon tekstbestand; dat moet `Documenten\QuietWriter`
  zijn.
- **SmartScreen:** er staat dat Windows kan waarschuwen, maar niet hoe je verdergaat. Voeg toe: *"Klik op 'Meer info' en
  daarna op 'Toch uitvoeren'."*
- **Crashlog:** er staat niet waar het staat. Voeg toe: de knop "Logbestand openen" in de foutmelding, of het pad
  `%LOCALAPPDATA%\QuietWriter\QuietWriter\logs\crash.log`.
- Voeg vooraan toe: *"Pak de ZIP eerst volledig uit; start QuietWriter niet vanuit de ZIP."* Dit is de meest gemaakte
  beginnersfout met portable ZIPs.

### 5. 🟡 Een onterechte melding "Werkmap gewijzigd" na het opslaan van alleen een thema

`save_settings()` vergelijkt de oude, **ongenormaliseerde** opgeslagen waarde met de nieuwe, genormaliseerde. Is het
opgeslagen pad tekstueel anders, dan krijgt de gebruiker bij het opslaan van alleen een thema toch "Werkmap gewijzigd,
herstart nodig". Denk aan een slash aan het eind, andere hoofdletters op Windows, `..` erin, of een relatief pad uit een
oudere versie.

Bevestigd (met de fix uit bevinding 1): een opgeslagen pad `…/ws/` plus een thema-wijziging gaf die melding.

**Voorstel:** vergelijk `normalize(old)` met `normalize(new)`.

**Randgeval:** iemand die in een oudere versie al een relatief pad had opgeslagen, krijgt bij het volgende opslaan
ongemerkt een andere map. Dat komt waarschijnlijk niet voor bij testgebruikers, want die beginnen met 0.36.

---

## Wat werkt

| Check | Resultaat |
|---|---|
| **OpenRouter:** paneel openen | ✅ Lokale introductie direct (0,11 s, ook als `is_available` 2 s zou duren), **0** netwerkaanroepen, invoer direct aan |
| OpenRouter: Nieuw gesprek | ✅ Weer direct de introductie, en geen aanroep |
| OpenRouter: echte vraag | ✅ `send()` duurt 0,003 s (geen blokkerende controle), de context gaat mee, verzonden vanuit een workerthread |
| **Ollama:** hangende warmup | ✅ UI blijft reageren: **grootste pauze 21 ms** (49 timer-ticks in 1 s). Laadtekst zichtbaar, invoer uit, warmup in een achtergrondthread |
| Ollama: na het antwoord | ✅ Introductie van het model zichtbaar, invoer aan |
| Ollama: mislukte warmup | ✅ Lokale welkomsttekst zonder "Fout:", invoer aan |
| **Werkmap in de wizard:** `mijnboeken` | ✅ `<HOME>/mijnboeken`, **niets** aangemaakt in de huidige map |
| Werkmap in Instellingen: `testboeken` | ✅ `<HOME>/testboeken` (met de fix uit bevinding 1) |
| `normalize_workspace_path` | ✅ `~/x` → home/x, leeg → standaard, absoluut blijft ongewijzigd |
| `--smoke-test` op de bron en op een **gebouwde exe** | ✅ rc 0 binnen 30 s |
| Staging | ✅ LEESMIJ in de stage, `documents/dev/` erbuiten |

## Samenvatting

| # | Onderwerp | Ernst |
|---|---|---|
| 1 | Opslaan in Instellingen geeft altijd een `NameError` | 🔴 |
| 2 | Smoketest overschrijft de instellingen van het dev-profiel | 🟡 |
| 3 | Smoketest blijft hangen bij een opstartfout in plaats van te falen | 🟡 |
| 4 | LEESMIJ staat in `_internal/`, en de inhoud mist SmartScreen-stappen, logpad en "eerst uitpakken" | 🟡 |
| 5 | Onterechte melding "Werkmap gewijzigd" | 🟡 |

## Conclusie

**Nog niet groen**, door één verkeerd geplaatste regel. De inhoudelijke wijzigingen zelf zijn goed. De warmup werkt
precies zoals beschreven, en de werkmap is nu veilig.

Voor **0.36.5 → 1.0.0-rc1** zou ik doen:
- bevinding 1, en de checker draaien vóór de oplevering;
- bevinding 4: LEESMIJ naast de exe, plus de vier tekstpunten;
- bevindingen 2 en 3: smoketest met tijdelijke instellingen, `return 1` zonder dialoog, en een timeout.

Bevinding 5 is klein, en mag mee. Daarna is wat mij betreft de release candidate klaar voor de kleine groep.

**Niet kunnen testen:**
- een echte Windows-build en -start;
- een echte Ollama met een koude start (jouw test 3);
- een echte OpenRouter-vraag;
- een echte GitHub Actions-run.
