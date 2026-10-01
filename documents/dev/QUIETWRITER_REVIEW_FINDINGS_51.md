# QuietWriter: reviewronde 51 (versie 0.35.4: afsluiter 0.35)

**Gelezen:** de diff tegen 0.35.3: `combo_value.py` (nieuw), `outline_page.py`, `characters_page.py`, `main.py`,
`tools/check_undefined_names.py` (nieuw), de workflow en de nieuwe tests.

**Getest (Python 3.12.3, PySide6 6.11.2):**
- de vier runs en een koude start;
- de checker, zowel schoon als met twee **zelf ingevoegde fouten**;
- de versiecontrole onder 3.11 en 3.10;
- de vijf Planning-scenario's uit ronde 50 plus vijf randgevallen, in NL en EN;
- een **end-to-end-test tot in `outline.json` en `characters.json`**;
- de Engelse rondgang als regressietest.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns

| Run | Resultaat |
|---|---|
| `pytest` | ✅ 255 geslaagd |
| `pytest -m qt` | ✅ 61 geslaagd |
| `pytest tests/legacy` | ✅ 451 geslaagd, 284 subtests |
| `pytest tests/legacy -m qt` | ✅ 91 geslaagd |
| `python main.py` (3.12) | ✅ |
| `python tools/check_undefined_names.py` | ✅ "Undefined-name check: OK", exitcode 0, ondanks de 19 ongebruikte imports |

## Bevinding 2 uit ronde 50: CI-checker ✅

| Test | Resultaat |
|---|---|
| Schone code | ✅ OK, exitcode 0 |
| De fout uit 0.35.2 opnieuw ingevoegd (`from ..i18n import tr` weggehaald) | ✅ Gevangen: `ai/ui.py:89:31: undefined name 'tr'`, … |
| Een ongedefinieerde functie ingevoegd in `storage.py` | ✅ Gevangen |
| Workflow | ✅ Roept `tools/check_undefined_names.py` aan in plaats van kale `pyflakes` |

## Bevinding 3 uit ronde 50: Python 3.12+ ✅

| Interpreter | `python main.py` |
|---|---|
| 3.12 | ✅ Start |
| 3.11 | ✅ "QuietWriter vereist Python 3.12 of nieuwer. Gevonden: Python 3.11.15.", exitcode 2, zonder `SyntaxError`-traceback |
| 3.10 | ✅ Zelfde nette melding |

De controle staat in `main.py` vóór `import quietwriter.app`. Daardoor wordt `ai/ui.py` onder een oude Python nooit
geparsed. Op Windows toont hij een MessageBox. ✅

## Bevinding 1 uit ronde 50: Planning ✅

### Via de dialogen (`SceneDialog.apply()` en `CharacterDetail._add_relation()`), in NL en EN

| Scenario | NL | EN |
|---|---|---|
| Status kiezen uit de lijst → canoniek | ✅ | ✅ |
| **Bestaande eigen status "in revisie" opnieuw opgeslagen** | ✅ `in revisie` | ✅ `in revisie` |
| Status zelf typen zonder Enter | ✅ | ✅ |
| Vertaald label typen ("written"/"geschreven") → canoniek | ✅ | ✅ |
| Relatie kiezen uit de lijst → canoniek | ✅ | ✅ |
| **Relatie zelf typen ("buurman van") zonder Enter** | ✅ | ✅ |
| Randgeval: eigen status **mét** Enter (Qt voegt dan een item zonder data toe) | ✅ tekst bewaard | ✅ |
| Randgeval: lege status → `idee`; lege relatie → `kent` | ✅ | ✅ |
| Randgeval: bestaande canonieke status (`geschreven`) getoond als label en weer canoniek bewaard | ✅ | ✅ |

### End-to-end tot op schijf (Planning-pagina → `edit_scene` → alleen de synopsis gewijzigd)

```
outline.json:    s1 ('in revisie', 'nieuw')   s2 ('geschreven', 'nieuw')     # NL en EN identiek
characters.json: c1 → [buurman van → c2, ouder van → c2]   c2 → [kind van → c1]
```

De eigen waarden blijven exact bewaard, de bekende waarden blijven canoniek Nederlands, en de automatische omgekeerde
relatie (`kind van`) klopt. ✅

## Regressie

- Engelse schermrondgang: geen Nederlandse tekst en niets afgekapt. De twee treffers van de scanner zijn de Engelse lijst
  met relatietypen die ik zelf toevoeg, en de onzichtbare Ctrl+S-actie. ✅
- De overige code is niet gewijzigd ten opzichte van de geteste 0.35.3.

---

## Kleine opmerkingen (geen bug, ideeën, niet meteen inbouwen)

- **Hoofdletters:** wie het label met andere hoofdletters typt ("WRITTEN"), krijgt het als eigen status opgeslagen,
  omdat `findText` standaard hoofdlettergevoelig vergelijkt. Met `combo.findText(text, Qt.MatchFixedString)` wordt dat
  hoofdletterongevoelig. Dit komt zelden voor.
- **Checker:** pyflakes heeft ook de melding `UndefinedLocal` (een variabele gebruiken vóór de toewijzing in dezelfde
  functie). Dat geeft tijdens het draaien een `UnboundLocalError`, dezelfde klasse als `NameError`. Die kan ook in de
  filter.
- **Nog open uit ronde 50, afgesproken voor 0.36:**
  - Nederlandse foutmeldingen uit `storage.py` in het Engels (Integriteit geblokkeerd, terugzetten uit de prullenbak,
    `CorruptSourceError`, het "Fout:"-voorvoegsel in de AI-chat);
  - de "g" van "wijzig" raakt het tabje nog net.

## Conclusie

**0.35.4 is groen.** Alle drie de punten uit ronde 50 zijn opgelost en aantoonbaar vastgelegd: de gegevens van Planning
blijven behouden in beide talen tot op schijf, de CI-checker vangt precies de goede klasse, en Python 3.12+ ligt vast
met een nette melding.

**0.35 kan dicht.** Het fundament voor 1.0 staat:

| Onderdeel | Status |
|---|---|
| Crashvangnet (lokaal log, bundelen van meldingen, bronherkenning, opstartfout) | ✅ |
| Branding (`.ico`, woordmerk, HiDPI, 14 thema's) | ✅ |
| Tweetaligheid (1091 sleutels, weergave en opslag gescheiden) | ✅ (restje in foutpaden → 0.36) |
| Licenties en fonts (manifest, OFL, Over-pagina, echte fetch) | ✅ |
| CI (Ubuntu en Windows, 4 suites, undefined-name-check) | ✅ (een echte run nog niet gezien) |
| First-run-contract | ✅ ontwerp klaar voor 0.36 |

**Advies voor de start van 0.36:** push 0.35.4 naar GitHub en kijk of de eerste echte Actions-run op **beide**
besturingssystemen groen is, voordat de first-run en de portable build erop gebouwd worden. Dat is het enige onderdeel
van 0.35 dat nog niemand echt heeft zien draaien.

**Niet kunnen testen:** een echte GitHub Actions-run, en Windows (taakbalk, DPI, MessageBox van de versiecontrole).
