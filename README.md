# QuietWriter

QuietWriter is een lokale desktop-schrijfomgeving voor boeken en langere teksten. De applicatie combineert een rustige editor met Planning, revisiegeschiedenis/herstel, spelling, publicatie/export, media en een optionele **AI Meelezer** voor feedback, feiten, consistentie en persona-/stijlcontrole.

**Status:** `1.0.1` — eerste onderhouds-/ontwikkeliteratie na de stabiele 1.0-release. De eerste v2-bouwsteen is de opslaglaag voor Darlings; de publieke 1.0.0-release blijft de stabiele baseline.

## Start hier
Voor ontwikkeling of AI-overdracht lees je eerst:
1. `documents/PROJECT_GUIDE.md`
2. `documents/ARCHITECTURE_AND_DATA_SAFETY.md`
3. `documents/PRODUCT_AND_UI_PHILOSOPHY.md`
4. `documents/HISTORY_AND_LESSONS.md`
5. `documents/TEST_STRATEGY.md`
6. `documents/ROADMAP_AND_IDEAS.md`
7. `documents/RELEASE_BRANDING_AND_OPERATIONS.md`
8. `documents/DEVELOPER_REFERENCE.md`
9. `documents/UI_REFERENCE.md` (bij UI-wijzigingen)
10. `documents/VALIDATION.md` (laatste overdraagbaarheidscontrole)
11. `documents/CHANGELOG.md`

De tientallen oude review findings, review notes en tussentijdse rapporten zijn bewust verwijderd nadat hun blijvende lessen, ideeën en risico's in deze kernset zijn samengebracht.

## Bron uitvoeren
Python 3.12+:
```bash
python -m pip install -r requirements.txt
python main.py
```
Voor ontwikkeling, tests en branding:
```bash
python -m pip install -r requirements-dev.txt
```

## Tests
```bash
python tools/check_undefined_names.py
pytest
pytest -m qt
```
Zie `documents/TEST_STRATEGY.md`.

## Windows-build
```bat
build_exe.cmd
```
De build gebruikt een schone allowlist-stage en maakt een portable onedir ZIP onder `release/`.

## Branding
De canonieke bronnen staan in `branding/bron/`. Pas afgeleide iconen niet los aan zonder de bron/generator mee te wijzigen.

## Data, AI en privacy
Boeken en instellingen blijven lokaal tenzij de gebruiker bewust een externe AI-provider gebruikt. Bij OpenRouter wordt pas context verstuurd bij een echte vraag. De Meelezer schrijft geen manuscriptproza en wijzigt Boekgeheugen niet autonoom. De OpenRouter API-key wordt momenteel als gewone lokale QSettings-waarde opgeslagen (op Windows doorgaans in het gebruikersregister), niet in een versleutelde credential store. Deel daarom geen instellingen-/registry-export met de sleutel erin.

## Licentie
QuietWriter is geen open-sourceproject. Zie `LICENSE` en `documents/licenses/`.
