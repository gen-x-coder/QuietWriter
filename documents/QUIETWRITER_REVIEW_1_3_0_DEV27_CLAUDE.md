# QuietWriter 1.3.0-dev.27: gerichte verificatie van de dev.26-review

**Reviewer:** Claude · **Datum:** 8 oktober 2026
**Snapshot:** `QuietWriter-1.3.0-dev.27.zip`, SHA-256 `8214897fb09eea05aee43b8f7051a9c4ccdd32c8ec4754cea7bb0a0ddd6670fa`. Dat komt overeen met
de opgegeven hash. Er is geen productcode gewijzigd.

**Scope:** de opgeloste punten B1, B2 en M1–M4 uit `QUIETWRITER_REVIEW_1_3_0_DEV26_CLAUDE.md`, plus regressie. De
visuele en Windows-punten uit het testplan doet Lucas zelf.

---

## 0. Conclusie

**Alle zes punten zijn correct opgelost en er zijn geen regressies.**
- De suite is weer groen: 796 geslaagd.
- De opt-in staat alleen nog in Instellingen en blijft in beide richtingen staan.
- Een wiel zonder focus verandert niets meer.
- Editor, boom, covers, notities en publicatie-editor gebruiken het actieve profiel.
- De lege flyout heeft geen grijs vlak meer.
- `WA_NoMouseReplay` staat aan.

**Er zijn geen blockers.** Vanuit mijn kant kan de volgende feature beginnen zodra jouw Windows-testplan groen is.

---

## 1. Testresultaten

| Controle | Resultaat |
|---|---|
| `pytest` met PySide6 | ✅ **796 geslaagd**, 0 gefaald, 304 subtests, 104 s |
| Exitcode | rc 139: de bekende teardown, ongewijzigd |
| `--smoke-test` | ✅ rc 0 |
| locales | ✅ `OK: 1614 keys in 5 locales` |
| undefined-names | ✅ OK |
| pyflakes | 36 meldingen: de 32 van dev.26 plus **4 nieuwe ongebruikte imports** (§3, P-a) |
| `README.md` | ✅ byte-identiek; `README_EN.md` niet aanwezig |
| ZIP | ✅ geen `.pytest_cache` en geen `__pycache__` |

### Harnassen

| Harnas | Resultaat |
|---|---|
| `rt1327.py` (nieuw, B2 en M1–M4) | **33/33** |
| `rt1326.py` (de 33 scenario's uit dev.26) | 49/52; dezelfde 3 bekende punten als in dev.26: offscreen-beperking bij buitenklik, undo per teken, scènebreuk-plakken |
| `demo137.py` (stable en dev) | 36/37, alleen de bekende verborgen exportlabels |
| `demo138.py` | 26/26 |
| `cache139.py` | 25/25 |

---

## 2. Verificatie per punt

| Punt | Controle | Resultaat |
|---|---|---|
| **B1** | De twee testverwachtingen zijn bijgewerkt ("Idee", maximaal 180 px) | ✅ de suite is groen |
| **B2** | Boekdetails bevat geen `progress_tracking`, geen "Vandaag geschreven" en geen "Bijhouden" meer | ✅ |
| B2 | Instellingen op **Bijhouden** → Boekdetails woorddoel wijzigen en opslaan, ook op een vers gebouwde Boekdetails-pagina | ✅ blijft **Bijhouden** |
| B2 | Instellingen op **Niet bijhouden** → idem | ✅ blijft **Niet bijhouden** |
| B2 | Stable-opslag tijdens dit alles | ✅ nooit aangeraakt |
| **M1** | Wiel zonder focus: Geavanceerde opties, AI Meelezer, Tekstgrootte, Slimme aanhalingstekens, Thema, Lettertype, Tekstbreedte, Regelafstand, Taal, Spellingtaal, Vandaag bijhouden | ✅ geen wijziging |
| M1 | Wiel **met** focus | ✅ de waarde verandert wel. Bij Spellingtaal is maar één woordenboek beschikbaar, dus daar kon niets veranderen. |
| M1 | Wat er met het event gebeurt | ✅ zonder focus wordt het event genegeerd (`isAccepted() == False`), zodat Qt het doorgeeft aan de scrollpagina |
| M1 | Boekdetails: Woorddoel, Einddatum-modus, datumveld, Boektaal, Gepubliceerd | ✅ geen wijziging zonder focus |
| M1 | Implementatie | Centraal in `ui/form_controls.py`: `_WheelNeedsFocus` met `StrongFocus`, in `QuietComboBox`, `QuietSpinBox` en `QuietDateEdit`. `SettingsBooleanChoice` erft van `QuietComboBox`. Eenvoudig en goed. |
| **M2** | Dev-profiel met thema Nacht, stable-opslag op Helder | ✅ `ManuscriptEditor.settings` is het profielobject, en `_theme()` is Nacht |
| M2 | Profielinstellingen in de rest | ✅ `ManuscriptTree`, de Boekenkast-covers, de Planning-notities en de publicatie-editor gebruiken dezelfde instellingen. Er staat nergens meer een directe `QSettings('QuietWriter','QuietWriter')` in de UI; alleen nog als terugvaloptie in vier constructors. |
| **M3** | Lege flyout | ✅ melding eindigt op y=107 van 636 |
| M3 | Kleur onder de melding | ✅ fillerpixels gelijk aan de flyoutachtergrond: `#ffffff` in Helder, `#202328` in Nacht; geen afwijkend vlak |
| **M4** | `planning_overlay.testAttribute(Qt.WA_NoMouseReplay)` | ✅ |
| M4 | Tweede klik (press · eventloop · release) | ✅ sluit |
| M4 | Escape, daarna klik | ✅ opent één keer |
| M4 | Klikken buiten de flyout en opnieuw afspelen van de klik | blijft een Windows-controle (offscreen niet na te bootsen); dit staat in jouw testplan als stap 10 |

---

## 3. Nieuwe kleine punten (backlog, geen blocker)

| # | Punt |
|---|---|
| P-a | **Vier ongebruikte imports** na de omzetting: `QComboBox`, `QDateEdit` en `QSpinBox` in `book_details.py`, en `QSettings` in `editor_page.py`. Cosmetisch, één regel elk. |
| P-b | **Nog niet beschermde velden.** De wielbescherming geldt alleen voor Instellingen en Boekdetails. Dezelfde Qt-eigenschap zit nog in andere scrollbare formulieren met gewone `QComboBox`/`QSpinBox`: de Exportpagina (4), Scène bewerken in de Outline (2), Personages (2) en de Colofonpagina (1). Daar is het risico kleiner, want de waarden worden niet direct als voorbeeld toegepast. Omzetten naar `Quiet*` is mechanisch werk. |
| P-c | **De lege flyout is nu schoon, maar nog steeds 636 px hoog** voor drie regels tekst. Hij bedekt daarmee onnodig een flink stuk manuscript. Optioneel: in de lege toestand de hoogte op de inhoud zetten (`adjustSize` zonder vaste hoogte). Dit is een productkeuze, geen fout. |

Openstaande backlog uit de dev.26-review, ongewijzigd:
- P1: scènebreuk en opmaak gaan verloren bij intern plakken;
- P2: undo per teken;
- P3–P12.

---

## 4. Niet getest

- **Popuprouting op Windows**: klikken buiten de flyout, en het opnieuw afspelen van de klik bij een tweede klik op de
  knop. Offscreen niet na te bootsen. Staat in jouw testplan (stap 10).
- **Echt scrollgedrag met muis of touchpad.** Geverifieerd is dat het event wordt genegeerd; het doorgeven aan de
  scrollpagina is standaard Qt-gedrag en niet als echte OS-scroll gemeten.
- **Een spellingtaalkeuze met meerdere woordenboeken.** Er was er maar één aanwezig.

### Bijlage

`rt1327.py` (aanroep: `python3 rt1327.py <zip-pad> <uitvoermap>`, met
`QT_QPA_PLATFORM="offscreen:configfile=screen1080.json"`) en de screenshots `shots27/`:
- `m2_ghost_nacht_devprofiel`;
- `m2_boekenkast_nacht_devprofiel`;
- `m3_flyout_leeg_helder`;
- `m3_flyout_leeg_nacht`.
