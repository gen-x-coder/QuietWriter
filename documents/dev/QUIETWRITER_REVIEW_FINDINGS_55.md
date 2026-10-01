# QuietWriter: reviewronde 55 (versie 0.36.10: fixes voor de release candidate, feature freeze)

**Gelezen:** CHANGELOG 0.36.10 en de diff tegen 0.36.9 (`editor_page.py`, `settings_page.py`, LEESMIJ, de tests en de
packaging-test). Er zijn geen nieuwe functies; de feature freeze voor `1.0.0-rc1` is vastgelegd. ✅

**Getest (Python 3.12.3, PySide6 6.11.2):**
- de vier runs, een koude start, `--smoke-test` en de undefined-names-check;
- beide 🔴-punten uit ronde 54 opnieuw, met dezelfde scripts en drie extra scenario's met een opgehaalde catalogus;
- titel en keuzelijst gemeten bij 1100, 1280 en 1440 px, in NL en EN, met en zonder Meelezer.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns

| Run | Resultaat |
|---|---|
| `tools/check_undefined_names.py` | ✅ OK |
| `pytest` | ✅ 294 geslaagd |
| `pytest -m qt` | ✅ 66 geslaagd |
| `pytest tests/legacy` | ✅ 451 geslaagd, 284 subtests |
| `pytest tests/legacy -m qt` | ✅ 91 geslaagd |
| `python main.py` | ✅ |
| `python main.py --smoke-test` | ✅ rc 0 |

## Bevinding 1 uit ronde 54: OpenRouter-model bij het gratis-filter ✅

| Filter | Catalogus opgehaald | Opgeslagen model | Na alleen het thema opslaan |
|---|---|---|---|
| aan | nee | `meta/llama:free` | ✅ `meta/llama:free` (was `''`) |
| aan | nee | `anthropic/claude-x` | ✅ `anthropic/claude-x` (was `''`) |
| uit | nee | `anthropic/claude-x` | ✅ behouden |
| aan | ja | `meta/llama:free` | ✅ behouden, lijst toont alleen gratis modellen |
| aan | ja | `anthropic/claude-x` | ✅ behouden (zie 🟡 hieronder) |
| uit | ja | `anthropic/claude-x` | ✅ behouden, gratis modellen bovenaan |

## Bevinding 2 uit ronde 54: minimale vensterbreedte ✅

| Boektitel | Meelezer | 0.36.4 | 0.36.9 | **0.36.10** |
|---|---|---|---|---|
| 4 tekens | aan | 937 | 1182 | **1036** |
| 31 tekens | aan | 1133 | 1378 | **1036** |
| 66 tekens | aan | 1347 | 1592 | **1036** |
| elke titel | uit | 633–1043 | 878–1288 | **732** |

De titel kan het venster niet meer oprekken. Hij wordt ingekort met een ellipsis, en de tooltip toont de volledige
titel. Bij 1280 px met de Meelezer open blijft er ongeveer 180 px titel zichtbaar. Pas rond 1100 px met de Meelezer valt
hij weg, en dat is acceptabel. Dit is zelfs beter dan in 0.36.4. ✅

## Overige punten

- LEESMIJ heeft nu een UTF-8 BOM (`EF BB BF`). ✅
- De ZIP bevat geen `release/`, `.pytest_cache`, `__pycache__` of `.tmp` meer. ✅

---

## Kleine bevindingen (geen 🔴)

### 1. 🟡 De keuzelijst voor tekstbreedte kapt de gekozen stand altijd af

`setFixedWidth(112)` laat door de padding en het pijltje uit het stylesheet maar ongeveer 36 px over voor de tekst.
"Normaal" heeft ongeveer 50 px nodig, "Extra breed" 70 px en "Extra narrow" 77 px. Je ziet dus op **elke**
vensterbreedte "Norma", "Extra b…" en dergelijke (`r56_toolbar.png`).

**Oplossing:** maak de keuzelijst ongeveer 150 px breed, of gebruik
`setSizeAdjustPolicy(QComboBox.AdjustToContents)`. Met een minimum van 1036 px is daar ruimte genoeg voor. Dit is een
regressiefix van één regel, dus het valt gewoon binnen de feature freeze.

### 2. 🟡 Met het gratis-filter aan toont de lijst een ander model dan er wordt opgeslagen

Dit gebeurt bij filter aan, catalogus opgehaald en een opgeslagen **betaald** model. De keuzelijst toont dan
"🆓 meta/llama:free" als gekozen, maar bij het opslaan blijft `anthropic/claude-x` staan. Dat is veilig, want er gaat
niets verloren, maar wat je ziet is niet wat wordt gebruikt.

**Voorstel:** toon het opgeslagen betaalde model als eerste item, met een markering "(niet gratis)", zodat de lijst laat
zien wat er werkelijk actief is. Dit mag ook naar na de RC.

### 3. 🟡 De CHANGELOG-sectie voor 0.36.10 staat boven de kop `# Changelog`

Dit is puur cosmetisch.

---

## Conclusie

**0.36.10 is groen.** Beide regressies uit ronde 54 zijn opgelost en met metingen bevestigd, en er zijn geen nieuwe
🔴-bevindingen. Wat mij betreft kan dit, met de fix van één regel uit bevinding 1, **`1.0.0-rc1`** worden.

**Wat nog bij jou ligt vóór het versturen naar de testgroep** (dat kan ik niet testen):
1. **Eén echte Windows-build** via `build_exe.cmd` of de workflow (met een tag `v1.0.0-rc1`, zodat de release automatisch
   als pre-release wordt gemarkeerd).
2. **Pak de ZIP uit op een schone Windows-pc zonder Python** en doorloop:
   - SmartScreen;
   - de wizard;
   - een boek maken, typen, afsluiten en opnieuw starten;
   - de Meelezer met Ollama (jouw test 3 over de koude start);
   - de schaal op 150%.
3. Vraag de testgroep hun werkmap af en toe te kopiëren, en een fout te melden met het logbestand (zoals de LEESMIJ
   uitlegt).

**Niet kunnen testen:**
- echte Windows (SmartScreen, taakbalk, DPI, de `.cmd`-launchers);
- een echte Ollama of OpenRouter;
- een echte GitHub Actions-run.
