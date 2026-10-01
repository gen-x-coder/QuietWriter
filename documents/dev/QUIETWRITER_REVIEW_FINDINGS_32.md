# QuietWriter: reviewronde 32 (versie 0.32.6: baseline voor publicatietekst en afgeharde tests)

**Gelezen:**
- de diff van `publication_editor.py`: `_clean_text` in `set_text`, `_changed` en het "mine"-pad;
- de nieuwe en gewijzigde tests;
- `REVIEW_NOTES_0326.md`.

**Getest:**
- de volledige suite met echte PySide6;
- `python main.py` koud gestart;
- runtime in de echte `MainWindow` (headless), met byte-vergelijkingen van `publication/texts/*.md`;
- de AST-vangnetten, los gedraaid tegen het `manuscript_editor.py` uit 0.32.4.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Resultaat: groen, geen fouten in de app

### Eerst verplicht

| Check | Resultaat |
|---|---|
| Volledige suite met PySide6 | ✅ **608 geslaagd**, 280 subtests, geen hang (12 s). Alleen de 2 bekende fonttests falen |
| `test_review_0324.py`, `test_publication_dirty_0326.py`, `test_manuscript_editor_init_0325.py` | ✅ 7/7 |
| Onverwachte modal in `test_review_0324.py` | ✅ een geforceerde "Werkmap gewijzigd" geeft `AssertionError: Unexpected QMessageBox.information`, dus een failure en geen hang |
| `python main.py` koud gestart | ✅ draait, geen traceback |
| Rail bij een koude start | ✅ 7/7 zoals in ronde 31 |

### Vrije publicatietekst (Voorwoord `foreword` en Nawoord `afterword`, allebei)

| Check | foreword | afterword |
|---|---|---|
| Na laden niet dirty; de bron houdt harde spatie en U+2028 | ✅ | ✅ |
| `rehighlight()`: niet dirty, timer uit, na 2,6 s en navigeren bytes identiek | ✅ | ✅ |
| Teken typen: dirty; undo exact terug: clean en timer uit | ✅ | ✅ |
| Typen + opslaan: clean, `_clean_text == source_text()`, 2× harde spatie + U+2028 behouden | ✅ | ✅ |
| `rehighlight()` na save | ✅ clean | ✅ clean |
| Conflict "Mijn versie": baseline gelijk aan het live bestand, `rehighlight()` clean, harde spatie, U+2028 en lokale tekst live | ✅ | ✅ |
| Conflict "Versie op schijf": baseline gelijk aan het live bestand (de externe tekst), `rehighlight()` clean | ✅ | ✅ |
| Open tekst + Instellingen opslaan (thema en lettergrootte) | ✅ niet herschreven | ✅ niet herschreven |

**18/18.**

### Regressie

| Reeks | Resultaat |
|---|---|
| Ronde 31: koude start, notities, bronteksten, scène/afbeelding (7/7, 5/5, 4× behouden) | ✅ |
| Notities en Instellingen (4 varianten) | ✅ 0× `persist_notes` |
| Ronde 29 editorbron | ✅ 8/8 |
| Ronde 28 | ✅ 30/30 |
| Ronde 27 (live preview) | 36/37; de ene FAIL komt uit het testscript zelf (het geparkeerde sjabloonbestand, ongewijzigd) |
| Ronde 26 (start met spelling uit, AI en advanced, herkomst) | ✅ |
| Rondes 12–24 | ✅ allemaal op de bekende basislijn (32/32, 10/10, 19/19, 2/2, 5/5, 3/3, 18/18, 9/9, 6/6, 12/12, 12/12, 10/10) |
| Ronde 15 · 25 | 7/12 · 25/29, dezelfde bekende artefact-regels |
| Randgeval ronde 24 | alle drie de keuzes ok |
| Backend 9–11 | 47/47, 15/15, 8/8 |

De transactionele adopt en de conflictflows uit 0.31 zijn niet geraakt.

---

## Eén opmerking over de tests (🟡, geen fout in de app)

**De nieuwe AST-test zou de fout van 0.32.4 zelf níét vangen. De positietest ernaast wel.**

Ik heb beide tests uit `test_manuscript_editor_init_0325.py` gedraaid tegen het `manuscript_editor.py` van 0.32.4:

| Test | Resultaat op 0.32.4 |
|---|---|
| `test_source_text_is_declared_after_manuscript_editor_init_setup` (tekstposities) | ✅ **faalt**, dus vangt de fout |
| `test_manuscript_editor_init_has_no_nested_method_or_early_return` (AST) | ❌ **slaagt** |

Waarom slaagt de AST-test? In 0.32.4 stond `def source_text` op klasse-inspringing (4 spaties). Python ziet hem dus als een
gewone methode, **na** een `__init__` die op dat punt gewoon eindigt. De `return` en alle code daarna horen bij
`source_text`, niet bij `__init__`. Het echte symptoom is: *code na een `return` in een functie*.

Het vangnet werkt nu dus, maar alleen dankzij de positietest. Die is gebonden aan exacte regels tekst en breekt bij de
eerstvolgende herindeling.

**Robuuster, en generiek voor het hele pakket:**

```python
def test_no_unreachable_code_after_return():
    for path in Path('quietwriter').rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for stmt in node.body[:-1]:
                    assert not isinstance(stmt, (ast.Return, ast.Raise)), f'{path}:{node.lineno} {node.name}'
```

Dit vangt 0.32.4 (`source_text`, 33 onbereikbare regels) en geeft op 0.32.6 **nul** meldingen in het hele pakket. Ik heb
het gecontroleerd.

**Kleiner punt:** de stub tegen onverwachte dialogen staat alleen in `test_review_0324.py`. Het is een autouse-fixture
met een naam die met `_` begint, dus hij geldt niet voor andere bestanden, ook niet voor `test_publication_dirty_0326.py`.
Hij vangt ook geen dialogen die via `QMessageBox(...).exec()` lopen, zoals de conflictdialogen.

Verplaats hem naar `tests/conftest.py` en stub daar ook `QMessageBox.exec`. Dan kan geen enkele Qt-test meer hangen op een
dialoog.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | Baseline voor publicatietekst, geen hang meer, startvangnet | ✅ | — |
| 1 | De AST-test vangt de 0.32.4-vorm niet (de positietest wel). De dialoogstub geldt maar voor één bestand en niet voor `exec()` | 🟡 | Alleen de tests |

**Conclusie:** 0.32.6 is groen. Alle drie de editors die op schijf schrijven (hoofdstuk, notities en vrije publicatietekst)
gebruiken nu dezelfde regel: dirty alleen bij een echte bronwijziging, een Unicode-veilige bron en een baseline die in alle
conflictroutes gelijk is aan het live bestand. De suite draait volledig zonder te hangen. Ik zie geen blokkade voor gebruik.
Het testpunt hierboven is een verbetering voor een volgende release.

**Niet kunnen testen:**
- een tweede spellingstaal;
- de echte ophaalroute van AI-modellen;
- het app-thema;
- echte Dropbox-timing (nagebootst).
