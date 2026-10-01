# QuietWriter: reviewronde 50 (versie 0.35.3: afsluiter 0.35)

De tweede ZIP (`0.35.3_3`) is byte-voor-byte gelijk aan de eerste. Deze review geldt voor beide.

**Gelezen:**
- de diff tegen 0.35.2: Planning (`outline_page.py`, `characters_page.py`), `ai/ui.py`, `storage.py`, `spell_panel.py`
  en `manuscript_editor.py`;
- de workflow, de locales, de OFL-bestanden en `REVIEW_NOTES_0353.md`.

**Getest:**
- de vier runs, een koude start en `pyflakes`, **onder Python 3.12** (zie bevinding 3);
- de Engelse schermrondgang met scanner;
- een brede statische scan van tekstletterlijken;
- de opslag van Planning via de echte `SceneDialog.apply()` en `CharacterDetail._add_relation()`, in NL en EN, met
  0.35.2 als vergelijking;
- de zichtbare punten uit de notes, met schermafbeeldingen.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns (Python 3.12.3, PySide6 6.11.2)

| Run | Resultaat |
|---|---|
| `pytest` | ✅ 246 geslaagd |
| `pytest -m qt` | ✅ 61 geslaagd |
| `pytest tests/legacy` | ✅ 451 geslaagd, 284 subtests, geen fontfouten |
| `pytest tests/legacy -m qt` | ✅ 91 geslaagd |
| `python main.py` | ✅ onder 3.12, ❌ onder 3.11 (bevinding 3) |
| `pyflakes`: undefined names | ✅ 0 |

---

## Bevindingen

### 1. 🔴 Planning: eigen scènestatussen en relaties gaan verloren bij het opslaan (regressie in 0.35.3)

De status- en relatielijsten zijn bewerkbare keuzelijsten. Sinds 0.35.3 slaat de code `currentData()` op zodra die
bestaat. Maar bij een bewerkbare `QComboBox` blijft `currentIndex` op het laatst gekozen item staan, ook als het veld
iets anders toont of de gebruiker zelf iets typt.

| Scenario (via de echte `SceneDialog.apply()` en `_add_relation()`) | 0.35.2 | 0.35.3 (NL én EN) |
|---|---|---|
| Status kiezen uit de lijst | (tekst) | ✅ canoniek, bijvoorbeeld `geschreven` |
| **Scène met eigen status "in revisie" openen en opslaan, zonder de status aan te raken** | ✅ `in revisie` | ❌ **`idee`**. Het veld toont "in revisie", maar opgeslagen wordt `idee` |
| Status zelf typen ("eerste versie") zonder Enter, na eerst "uitgewerkt" te hebben gekozen | ✅ `eerste versie` | ❌ **`uitgewerkt`** |
| Het vertaalde label typen ("written") | — | ❌ `idee` |
| Relatie kiezen uit de lijst | (tekst) | ✅ `ouder van` |
| **Relatie zelf typen ("buurman van")** zonder Enter, na eerst "ouder van" te hebben gekozen | ✅ `buurman van` | ❌ **`ouder van`**: de verkeerde relatie, en de omgekeerde relatie wordt er ook bij aangemaakt |

Het eerste ❌-scenario is het ernstigste. Wie een scène met een eigen status alleen opent om de synopsis aan te passen,
verliest zonder waarschuwing die status. Dit komt precies voort uit het scheiden van weergave en opslag waar ik in ronde
49 om vroeg. Ik had het risico van bewerkbare keuzelijsten toen moeten noemen.

**Oplossing:** gebruik één hulpfunctie voor beide lijsten, bijvoorbeeld:

```python
def combo_value(combo):
    text = combo.currentText().strip()
    i = combo.currentIndex()
    if i >= 0 and combo.itemText(i) == text:
        return combo.itemData(i)          # onveranderd gekozen item
    j = combo.findText(text)               # getypt label van een bekend item
    return combo.itemData(j) if j >= 0 else text   # anders: eigen waarde, ongewijzigd
```

Zet bij het laden van een eigen waarde eerst `setCurrentIndex(-1)` en daarna `setEditText(...)`.

**Tests:** de vijf ❌-regels hierboven, elk als regressietest, in NL en EN.

### 2. 🔴 De CI-stap met `pyflakes` faalt altijd, waardoor er in CI geen enkele test draait

`python -m pyflakes quietwriter` geeft **exitcode 1 bij elke melding**, ook bij onschuldige, zoals ongebruikte imports.
Het pakket heeft er 19 (bijvoorbeeld `integrity.py:9`, `app.py:17`, `ai/__init__.py`). Daardoor faalt de stap "Static
undefined-name check" bij elke push, en worden alle vier de testsuites daarna **overgeslagen**. CI is dan altijd rood
zonder dat er iets getest is.

**Oplossing:** laat de stap alleen op `undefined name` falen. Omdat Windows-runners standaard PowerShell gebruiken (geen
`grep`), kan dat het beste als pytest-test of klein script:

```python
from pyflakes import api, messages, reporter
class R(reporter.Reporter):
    def __init__(self): self.bad = []
    def flake(self, m):
        if isinstance(m, messages.UndefinedName): self.bad.append(str(m))
    def syntaxError(self, *a): self.bad.append(str(a))
    def unexpectedError(self, *a): self.bad.append(str(a))
r = R(); api.checkRecursive(['quietwriter'], r); assert not r.bad, r.bad
```

De 19 ongebruikte imports kun je apart opruimen. Dat is geen bug.

### 3. 🟡 `ai/ui.py:794` werkt alleen op Python 3.12 en hoger

```python
f'...{html.escape(tr('ai.you', 'JIJ'))}...'
```

Dezelfde soort aanhalingstekens binnen een f-string is pas sinds Python 3.12 toegestaan. Onder 3.11 geeft dit een
`SyntaxError` en start de app niet. Daarom heb ik deze ronde onder 3.12 getest.

QuietWriter richt zich volgens de CHANGELOG op 3.12, dus op Lucas' machine is dit waarschijnlijk geen probleem. Maar het
project heeft sinds 0.21.5 wel een 3.11-regel (`test_characters_page_parses_as_python_311`). Die test controleert alleen
`characters_page.py`, en `ast.parse(feature_version=(3, 11))` vangt deze f-string-regel **niet** af. Ik heb dat onder 3.12
geprobeerd: de regel wordt gewoon geaccepteerd.

**Kies één van twee:**
- **Officieel 3.12+** (mijn advies, de build bundelt toch zijn eigen Python): zet een versiecontrole met een nette
  melding in `main.py` en haal de 3.11-test weg.
- **3.11 blijft ondersteund:** herschrijf regel 794 (`tr("ai.you", "JIJ")`) en voeg in CI een stap
  `python3.11 -m compileall -q quietwriter` toe.

### 4. 🟡 Nederlands in het Engels, alleen nog in foutpaden

De rondgang en de scan vonden in de normale schermen **geen Nederlands meer**. Wel nog in foutmeldingen uit
`storage.py` die via `str(exc)` in een dialoog komen:
- **Integriteit:** "Dit boek is losgekoppeld en geblokkeerd…" (`storage.py:201` → `integrity_page.py:245`).
- **Prullenbak:** "Het verwijderde hoofdstuk bestaat niet meer." en andere meldingen bij het terugzetten
  (`storage.py:981–987`, `1136`).
- **Beschadigd bronbestand:** "… is beschadigd en kan niet veilig worden overschreven" (`CorruptSourceError`,
  `storage.py:29`).
- **AI-foutmelding:** het voorvoegsel "Fout:" in de chat (`ai/ui.py:740`, wordt opgeslagen in het gesprek).
- **Standaardnamen bij een lege titel:** `Nieuw hoofdstuk`, `Nieuwe sectie`, `(kopie)` en `Hersteld hoofdstuk`. De UI
  geeft normaal zelf een vertaalde titel mee, dus die zie je zelden.

Dit kan naar 0.36. Het blokkeert niet.

### 5. 🟡 "wijzig" raakt nog net het inklaptabje

In het Engels staat "edit" nu vrij. In het Nederlands valt de "g" van het langere "wijzig" nog net tegen het tabje
(`r51_edit.png`). Het is veel beter dan in 0.35.2. Een paar pixels extra ruimte lost het op.

---

## Wat werkt

| Check uit de review notes | Resultaat |
|---|---|
| `AIPanel` en `MainWindow` bouwen (startblokkade uit 0.35.2) | ✅ |
| Statusbalk | ✅ "Book: 2,100 words · Chapter 1 of 1: 2,100 words" (Engelse duizendtalscheiding) |
| Rechtsklikmenu | ✅ Formatting / Bold / Italic / Paragraph style / Normal paragraph … via `tr()` |
| AI-chatlabel | ✅ YOU |
| Spellingteller | ✅ "{index} of {total} · {where}" |
| Replace all, "and N more", beschadigde hoofdstukken, meldingen op de boekenplank | ✅ via `tr()` |
| Planning-weergave | ✅ Status en relatietypen in het Engels, bekende opgeslagen waarden blijven Nederlands (zie wel bevinding 1) |
| Nieuw boek in het Engels | ✅ "Chapter 1" |
| Future-book-context | ✅ stabiele id's (`book_memory`, `book_profile`, `changes`) |
| `build_ai_context` weg | ✅ |
| OFL-bestanden | ✅ geen `<dates>`, `<Copyright Holder>` of `<Reserved Font Name>` meer |
| Locales | ✅ 1091 = 1091 sleutels |
| Engelse rondgang: alle pagina's, panelen, instellingen, scènedialoog | ✅ geen Nederlands, niets afgekapt |
| Crash-cooldown | ✅ code gelijk aan de geteste 0.35.2 |

## Samenvatting

| # | Onderwerp | Ernst | Nieuw? |
|---|---|---|---|
| 1 | Bewerkbare keuzelijsten in Planning overschrijven eigen status en relatie | 🔴 | regressie in 0.35.3 |
| 2 | CI-stap `pyflakes` faalt altijd, zodat er geen suites draaien | 🔴 | nieuw |
| 3 | f-string alleen geldig in 3.12+; de 3.11-test vangt dat niet | 🟡 | nieuw, **keuze nodig** |
| 4 | Nederlandse foutmeldingen uit `storage.py` in het Engels | 🟡 | restant |
| 5 | "wijzig" raakt het tabje | 🟡 | restant |

## Conclusie

**Nog niet groen.** De vertaling zelf is nu goed, en alles wat de notes vroegen is in orde. Maar bevinding 1 kost
stilletjes gebruikersdata, en bevinding 2 maakt de hele CI waardeloos. Beide zijn klein om op te lossen.

Voor een **0.35.4** zou ik alleen doen:
- bevinding 1, met de hulpfunctie en vijf tests;
- bevinding 2, met de pyflakes-test die alleen op undefined names filtert;
- de keuze voor bevinding 3, zodat de Python-versie officieel vastligt.

Bevindingen 4 en 5 mogen naar 0.36. Daarna kan 0.35 wat mij betreft dicht.

**Niet kunnen testen:** een echte GitHub Actions-run en Windows (taakbalk, DPI).
