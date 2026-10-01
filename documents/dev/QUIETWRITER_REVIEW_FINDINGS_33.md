# QuietWriter: reviewronde 33 (versie 0.32.7: alleen de tests afgehard)

**Gelezen:** `tests/conftest.py`, `tests/test_code_health_0327.py`, de gewijzigde tests en `REVIEW_NOTES_0327.md`.

**Gecontroleerd:** `diff` van `quietwriter/` tegen 0.32.6. Alleen `__init__.py` (het versienummer) is anders. Het
productgedrag is dus per definitie gelijk.

**Getest:** de suite met echte PySide6, de nieuwe tests tegen expres kapotgemaakte kopieën, dialoogproeven in een echte
Qt-test, een koude start en een smoke-regressie.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Resultaat: groen. De gevraagde bewijzen kloppen.

| # | Check (REVIEW_NOTES_0327) | Resultaat |
|---|---|---|
| 1 | Volledige suite met PySide6 | ✅ 608 geslaagd, 280 subtests, 13 s, geen hang. Alleen de 2 fonttests falen |
| 2 | `test_code_health_0327.py` op 0.32.7 | ✅ groen |
| 2 | Kopie met `return None` + code erachter in `storage.verify_book_unchanged` | ✅ **rood**: `storage.py:198 verify_book_unchanged: Return on line 199 is followed by unreachable code on line 200` |
| 3 | Kopie met het `manuscript_editor.py` van 0.32.4 | ✅ **rood**: `manuscript_editor.py:57 source_text: Return on line 66 is followed by unreachable code on line 68` |
| 4 | Onverwachte `QMessageBox.information` (echte `settings_saved` met andere werkmap) | ✅ direct `AssertionError: Unexpected QMessageBox.information: Werkmap gewijzigd` |
| 4 | Onverwachte `QMessageBox(...).exec()` | ✅ direct `AssertionError: Unexpected QMessageBox.exec: Probe exec` |
| 4 | Via de eigen helper `dialogs.confirm()` (die intern `.exec()` gebruikt) | ✅ ook gevangen |
| 5 | `python main.py` koud gestart | ✅ draait, geen traceback |
| 5 | Smoke: koude start 7/7, notities 5/5, publicatietekst 18/18, editorbron 8/8, ronde 28 30/30 | ✅ |
| 5 | Kern-regressie (rondes 12, 14, 19, 23, 24) en backend 47/15/8 | ✅ basislijn |

---

## Drie kleine gaten in het vangnet (🟡, alleen tests, geen blokkade)

### 1. Een dialoog die vanuit een Qt-slot of timer komt, laat de test níét falen

Neem een dialoog die ontstaat in een `QTimer`-callback: autosave, de notities-timer of een uitgestelde adopt. De
`AssertionError` wordt dan binnen de Qt-eventloop gegooid. PySide6 print hem naar stderr en gaat verder, dus pytest ziet
niets.

Runtime-proef: `QTimer.singleShot(0, lambda: QMessageBox.warning(None, 'Probe timer', 'x'))`, dan `qWait(100)`. De test
**slaagt**.

Dat is precies de klasse fouten van rondes 27 en 29: dialogen die 3 seconden later via de autosave-timer verschijnen.

**Fix in `conftest.py`:** houd de aanroepen bij in een lijst en laat de test in de teardown falen:

```python
calls = []
def unexpected(kind):
    def fail(*args, **kwargs):
        calls.append(kind)
        raise AssertionError(f'Unexpected QMessageBox.{kind}')
    return fail
# ... monkeypatch zoals nu ...
yield
assert not calls, f'Unexpected dialogs: {calls}'
```

### 2. Andere modale dialogen hangen nog steeds

`QMessageBox.exec` is afgevangen, maar `QDialog.exec` niet. De app gebruikt ook:
- eigen `QDialog`s: `ai/ui.py` (3×), `persona_page.py`, `outline_page.py` (2×);
- `QInputDialog.getText` (nieuw boek);
- `QFileDialog.get*` (5 plekken).

Runtime-proef: `QDialog().exec()` in een test hangt (timeout na 15 s).

**Fix:** patch in `conftest.py` ook `QDialog.exec`. Dat dekt `QMessageBox` meteen mee, want die erft ervan. Patch
daarnaast `QInputDialog.getText` en `QFileDialog.getOpenFileName`, `getExistingDirectory` en `getSaveFileName`.

### 3. De code-health-test slaagt ongemerkt als hij vanuit een andere map draait

`Path('quietwriter').rglob('*.py')` is relatief aan de huidige map. Runtime: vanuit `/home/claude` gedraaid tegen de
**kapotte** kopie geeft hij `1 passed`, omdat hij nul bestanden ziet.

**Fix:**

```python
ROOT = Path(__file__).resolve().parents[1] / 'quietwriter'
files = list(ROOT.rglob('*.py'))
assert files
```

**Optioneel:** de test kijkt alleen naar het directe `body` van een functie. Een `return` gevolgd door code binnen een
`if`-, `for`- of `try`-blok valt erbuiten. Loop daarvoor over alle statementlijsten: `body`, `orelse`, `finalbody` en
`handlers[*].body`. Dat is niet nodig voor de 0.32.4-vorm, die al gevangen wordt.

---

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | De code-health-test vangt de 0.32.4-vorm; statische en `.exec()`-dialogen falen direct; productcode ongewijzigd | ✅ | — |
| 1 | Dialogen vanuit een slot of timer laten de test niet falen | 🟡 | Alleen tests; precies de autosave-klasse |
| 2 | `QDialog.exec`, `QInputDialog` en `QFileDialog` niet afgevangen: kunnen nog hangen | 🟡 | Alleen tests |
| 3 | De code-health-test slaagt ongemerkt bij een andere werkmap | 🟡 | Alleen tests |

**Conclusie:** 0.32.7 is groen en doet wat de notes beloven. Productcode, gedrag en regressie zijn identiek aan 0.32.6.
Wat mij betreft kun je **0.32.x afsluiten**. De drie punten hierboven zijn kleine verbeteringen van het testvangnet (samen
ongeveer tien regels in `conftest.py` en de code-health-test). Die kunnen mee in de eerste 0.33-build; daar is geen aparte
release voor nodig.

**Niet kunnen testen:**
- een tweede spellingstaal;
- de echte ophaalroute van AI-modellen;
- het app-thema;
- echte Dropbox-timing (nagebootst).
