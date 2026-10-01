# QuietWriter: reviewronde 54 (versies 0.36.5–0.36.9)

**Gelezen:**
- CHANGELOG 0.36.5–0.36.9;
- de diff tegen 0.36.4: `settings_page.py`, `editor_page.py`, `manuscript_editor.py`, `editor_view.py` (nieuw),
  `smoke_test.py` (nieuw), `app.py`, `openrouter_provider.py`, `build_exe.cmd`, `build-windows.yml`, de spec en de LEESMIJ.

**Getest (Python 3.12.3, PySide6 6.11.2):**
- de vier runs, een koude start en de undefined-names-check;
- de vijf punten uit ronde 53 opnieuw, met de bestaande scripts (onder andere een opzettelijk kapotte `MainWindow` en
  een fout in een slot tijdens de smoketest);
- de OpenRouter-modelkeuze met en zonder gratis-filter, via de echte Instellingen;
- de tekstbreedte: vijf standen, het bestand byte-voor-byte gecontroleerd, synchronisatie met Instellingen, en de
  **minimale vensterbreedte** vergeleken met 0.36.4.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns

| Run | Resultaat |
|---|---|
| `tools/check_undefined_names.py` | ✅ OK |
| `pytest` | ✅ 289 geslaagd |
| `pytest -m qt` | ✅ 63 geslaagd |
| `pytest tests/legacy` | ✅ 451 geslaagd, 284 subtests |
| `pytest tests/legacy -m qt` | ✅ 91 geslaagd |
| `python main.py` | ✅ |

## Punten uit ronde 53: alle vijf opgelost ✅

| # | Punt | Resultaat |
|---|---|---|
| 1 | Opslaan in Instellingen | ✅ Werkt (thema → Nacht wordt opgeslagen) |
| 2 | Smoketest overschrijft dev-profiel | ✅ Dev-instellingen byte-identiek na `--smoke-test`, geen appdata geschreven |
| 3 | Smoketest blijft hangen bij een fout | ✅ Kapotte `MainWindow` → **rc 1 binnen 1 s** met melding op stderr. Fout in een slot tijdens de test → rc 1. Normale run → rc 0. Workflow: `timeout-minutes` aanwezig |
| 4 | LEESMIJ | ✅ `build_exe.cmd` kopieert hem naast de exe en controleert dat. De workflow faalt als hij ontbreekt of in `_internal` staat. Inhoud: eerst uitpakken, SmartScreen-stappen, logpad (`%LOCALAPPDATA%\QuietWriter\QuietWriter\logs\crash.log`), gewone backslashes, NL en EN |
| 5 | Onterechte melding "Werkmap gewijzigd" | ✅ Alleen het thema wijzigen met een opgeslagen pad `…/ws/` geeft geen melding. Een echte werkmapwissel geeft die wel |

## Nieuw en goed

| Onderdeel | Resultaat |
|---|---|
| UTF-8 in OpenRouter-streams (0.36.7) | ✅ `iter_lines(decode_unicode=False)` levert volledige regels als bytes, die daarna als UTF-8 worden gedecodeerd. Een `é` kan dus niet tussen twee chunks in vallen |
| Gratis-herkenning (0.36.6) | ✅ `:free`, `openrouter/free` en prijs 0/0 via `Decimal`. `openrouter/auto` (prijs −1) en ontbrekende prijzen worden terecht **niet** als gratis gezien |
| Tekstbreedte (0.36.8/9) | ✅ Vijf standen geven 674 / 804 / 964 / 1098 px viewport. Alleen weergave: het bestand blijft byte-identiek en er komt geen undo. De editor en Instellingen blijven in beide richtingen gelijk, en een ongeldige waarde wordt `normal` |
| Locales | ✅ 1125 = 1125 sleutels |

---

## Bevindingen

### 1. 🔴 Met "Alleen gratis modellen tonen" aan wordt het OpenRouter-model gewist zodra je iets anders opslaat

De lijst met OpenRouter-modellen wordt niet bewaard tussen sessies. Hij is leeg tot je op **Modellen ophalen** klikt.
Zonder filter blijft het opgeslagen model daarom zichtbaar en bewaard. **Met** filter niet:

| Filter | Opgeslagen model | Modellijst na herstart | Na **alleen het thema** opslaan |
|---|---|---|---|
| uit | `anthropic/claude-x` | `[anthropic/claude-x]` | ✅ `anthropic/claude-x` |
| **aan** | `meta/llama:free` (zelf gratis!) | `[]` | ❌ **`''`** |
| **aan** | `anthropic/claude-x` | `[]` | ❌ **`''`** |

Iemand die gratis modellen gebruikt, opent dus na een herstart Instellingen, wijzigt bijvoorbeeld het thema, en heeft
daarna geen model meer. De Meelezer meldt dan "Kies eerst een AI-model". Dit raakt precies de groep die de nieuwe optie
gebruikt.

**Oplossing:**
- Filter alleen als er prijsinformatie is opgehaald. Zonder die informatie laat je de lijst zien zoals zonder filter, en
  blijft het opgeslagen model behouden.
- Houd een opgeslagen `:free`-model altijd zichtbaar.
- Overschrijf `openrouter_model` nooit met een lege waarde als de lijst leeg is.

**Test:** de drie rijen hierboven, met als verwachting dat het model in alle gevallen behouden blijft.

### 2. 🔴 De minimale vensterbreedte is met ongeveer 245 px gegroeid; met de Meelezer open past QuietWriter niet meer op een gangbaar laptopscherm

De werkbalk van de editor heeft er een label "Tekstbreedte" en een keuzelijst bij gekregen. De boektitel ernaast wordt
nooit ingekort (dat was al zo). Samen bepalen ze hoe smal het venster minimaal kan worden. Gemeten met
`minimumSizeHint`:

| Boektitel | Meelezer | 0.36.4 | **0.36.9** |
|---|---|---|---|
| 4 tekens | uit | 633 | 878 |
| 4 tekens | aan | 937 | 1182 |
| 31 tekens ("De verloren haven van Antwerpen") | uit | 829 | 1074 |
| 31 tekens | **aan** | 1133 | **1378** |
| 66 tekens | aan | 1347 | **1592** |

Een laptop van 1920×1080 op **150% schaal** (de Windows-standaard op veel laptops) heeft 1280 logische pixels, en een
1366×768-scherm heeft er 1366. Met een gewone titel en de Meelezer open past het venster daar niet meer op. Het
rechterpaneel, met het invoerveld en de verzendknop, valt dan buiten beeld. In 0.36.4 paste dat nog.

**Oplossing (beide klein):**
- **Kort de boektitel in** met `fontMetrics().elidedText(…, Qt.ElideRight, width)` in `resizeEvent`, en
  `setMinimumWidth(0)`. Dan kan de titel nooit meer het venster oprekken.
- **Maak de tekstbreedte compact:** laat het losse label weg (de tooltip en de toegankelijke naam staan er al), of gebruik
  één klein knopje met een menu (bijvoorbeeld "↔").

**Test:** `minimumSizeHint().width()` met de Meelezer open en een titel van 66 tekens blijft ≤ 1100 px.

### 3. 🟡 Kleine punten

- `LEESMIJ.txt` is UTF-8 **zonder BOM** ("officiële", "continuïteit"). Kladblok in Windows 10/11 opent dat goed, maar
  oudere viewers tonen "officiÃ«le". Een BOM (`utf-8-sig`) maakt het overal leesbaar.
- Op een venster van 1600 px zijn **Breed** en **Extra breed** gelijk (beide 1098 px), omdat de kolom niet breder kan dan
  de beschikbare ruimte. Dat is logisch, maar je ziet dan geen verschil. Dit is geen bug.
- De ZIP bevat `release/stage/` en `.pytest_cache/`. Beide staan in `.gitignore`, en de release wordt toch opnieuw
  gestaged, dus dit is alleen een kwestie van een opgeruimde ZIP.

---

## Samenvatting

| # | Onderwerp | Ernst | Sinds |
|---|---|---|---|
| 1 | Gratis-filter wist het OpenRouter-model bij het opslaan na een herstart | 🔴 | 0.36.6 |
| 2 | Minimale vensterbreedte +245 px; met de Meelezer open past het niet op een 1280/1366-scherm | 🔴 | 0.36.8 |
| 3 | LEESMIJ zonder BOM, Breed/Extra breed gelijk op middelgrote vensters, ZIP-inhoud | 🟡 | — |

## Conclusie

De fixes uit ronde 53 zijn allemaal goed, en ook de UTF-8-fix en de tekstbreedte als functie werken. **0.36.9 is toch
niet groen**, door twee regressies uit de nieuwe functies:
- het verdwijnende OpenRouter-model, dat de gratis-gebruiker treft;
- het te brede venster, dat iedere testgebruiker met een laptop op 150% en de Meelezer open treft.

Beide zijn klein om op te lossen.

**Advies voor het proces richting de RC:** 0.36.5 tot en met 0.36.9 bevatten vier nieuwe functies na de vorige review.
Voor een release candidate zou ik nu een **feature freeze** afspreken: alleen nog fixes, tot de testgroep hem heeft. Elke
nieuwe functie bracht in de laatste rondes een regressie mee. Ideeën als de gratis-modellen en de tekstbreedte zijn
mooi, maar horen eigenlijk in de "Nice"- of "V2"-kolom van het 1.0-plan.

**Niet kunnen testen:**
- echte Windows met 150% schaal (de breedte is gemeten met `minimumSizeHint`);
- een echte OpenRouter-catalogus met prijzen en een echte stream;
- een echte GitHub Actions-run.
