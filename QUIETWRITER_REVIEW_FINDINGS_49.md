# QuietWriter: reviewronde 49 (versie 0.35.2: vertaling, licenties, fonts, crash-cooldown)

**Gelezen:**
- de diff tegen 0.35.1: `ai/ui.py`, `ai/context.py`, de pagina's voor persona, boekprofiel en boekgeheugen,
  `search_panel.py`, `crash_logging.py`, `crash_notice.py` en `about_page.py`;
- de locales, het fontmanifest, `LICENSE`, `THIRD_PARTY_LICENSES.md`, de workflow en
  `FIRST_RUN_DESIGN_035.md`.

**Getest:**
- de vier runs en een koude start, eerst op de geleverde build en daarna op een kopie met één importregel erbij (zie
  bevinding 1);
- `pyflakes` op het hele pakket;
- de crash-cooldown;
- de echte fontfetch (8 TTF-bestanden) met registratie;
- een automatische Engelse schermrondgang die elke zichtbare tekst, tooltip, keuzelijst en dialoog scant. De scanner
  is gecontroleerd door dezelfde rondgang in het Nederlands te draaien: 281 treffers;
- een statische scan van tekstletterlijken;
- een vergelijking van de AI-context tussen Nederlands en Engels, met onderschepping van de prompt.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns

| Run | Geleverde 0.35.2 | Met één regel `from ..i18n import tr` erbij |
|---|---|---|
| `pytest` | ❌ **31 gefaald**, 209 geslaagd | ✅ 240 geslaagd |
| `pytest -m qt` | ❌ **31 gefaald**, 30 geslaagd | ✅ 61 geslaagd |
| `pytest tests/legacy` | ❌ **4 gefaald**, 447 geslaagd | ✅ **451 geslaagd**, 284 subtests, geen fontfouten meer |
| `pytest tests/legacy -m qt` | ❌ **4 gefaald**, 87 geslaagd | ✅ 91 geslaagd |
| `python main.py` | ❌ **"QuietWriter kon niet starten"** | ✅ |

---

## Bevindingen

### 1. 🔴 De app start niet: `tr` wordt niet geïmporteerd in `ai/ui.py`

`ai/ui.py` roept `tr()` op 70 plaatsen aan, maar de import `from ..i18n import tr` ontbreekt. `AIPanel.__init__` stopt
daardoor met een `NameError`, en daarmee `EditorPage` en `MainWindow`. Een gebruiker ziet bij elke start alleen de (goed
werkende) opstartmelding: *"QuietWriter kon niet starten. NameError: name 'tr' is not defined"*.

**Waarom is dit niet gevangen?**
- `compileall` controleert geen namen.
- Bij ChatGPT worden alle Qt-tests overgeslagen, en juist die bouwen `MainWindow`.
- De nieuwe vertaaltests lezen alleen tekst.

**Oplossing:** voeg de ene importregel toe. Op mijn kopie is dan alles groen.

**Zodat dit niet meer kan gebeuren** (dit vangt de hele klasse, ook zonder Qt):
- Voeg een test toe die `pyflakes` draait en faalt op `undefined name`. Of doe het zonder afhankelijkheid: elke module
  die `tr(` aanroept, moet `tr` importeren (een AST-test). `pyflakes` vond verder niets in het pakket.
- De CI uit 0.35.0 had dit direct rood gemaakt. **Push elke build eerst naar GitHub voordat hij naar review gaat**, dan
  is dit soort fout binnen een paar minuten zichtbaar.

### 2. 🟡 Engelse modus: er zijn nog zichtbare Nederlandse teksten

De scan vond **op alle primaire pagina's, rechterpanelen en instellingen geen Nederlands en geen afgekapte labels**
(`r49_english.png`). Maar de teksten hieronder komen via een variabele, een f-string of een eigen menu op het scherm, en
daar kijkt de test voor hardgecodeerde tekst niet naar.

| Waar | Tekst | Hoe vaak zichtbaar |
|---|---|---|
| **Statusbalk** (`editor_page.py:1324–1328`) | "Boek: 5 woorden · Hoofdstuk 1 van 1: 5 woorden", met een punt als duizendtalscheiding | **Altijd** |
| **Rechtsklikmenu in de editor** (`manuscript_editor.py:710–734`) | Opmaak, Vet, Cursief, Onderstrepen, Doorhalen, Alineastijl, Normale alinea, Tussenkop, Citaat, Opsomming, Genummerde lijst | Bij elke selectie + rechtsklik |
| AI-chat (`ai/ui.py:793`) | Label "**JIJ**" boven eigen berichten | Elk gesprek |
| Spellingpaneel (`spell_panel.py:105–106`) | "3 van 10 · Hoofdstuktekst / Hoofdstuktitel" | Bij spellingcontrole |
| Zoeken → Alles vervangen (`editor_page.py:1990`) | Dialoog "Alles vervangen / Wil je N voorkomens vervangen?" | Bij Alles vervangen |
| Conflictdialoog (`editor_page.py:1038`) | "… en N meer" | Zelden |
| Foutdialogen (`editor_page.py:1387`, `1412`) | "De sectie / Het hoofdstuk is niet toegevoegd." | Bij een fout |
| Statusmeldingen (`editor_page.py:1936`, `2017`) | "N beschadigd(e) hoofdstuk(ken) … overgeslagen. Herstel via Integriteit." | Bij beschadigde hoofdstukken |
| Boekenplank (`bookshelf.py:297`) | "• N boek(en) niet geopend: …" | Bij kapotte boeken |
| Planning → scène (`outline_page.py:25`) | Status: idee / uitgewerkt / geschreven | Elke scène |
| Planning → personages (`characters_page.py:18`) | Relatietypen: ouder van, kind van, partner van, … | Bij relaties |
| Nieuw boek (`storage.py:312`) | Eerste hoofdstuk heet "**Hoofdstuk 1**" (import: "Hoofdstuk") | Elk nieuw boek |
| `preserve_local_and_close_future_book(context='boekgegevens' / 'boekgeheugen' / 'wijzigingen')` | Nederlands woord midden in een dialoog | Zelden |

**Let op bij het oplossen van de laatste drie rijen: dit zijn opgeslagen gegevens, geen labels.**
- Status en relatietype worden als tekst in `planning/*.json` bewaard, en `RELATION_PAIRS` gebruikt ze voor de omgekeerde
  relatie. Vertaal alleen de **weergave** en bewaar de Nederlandse waarde (of een id), net zoals bij de AI-context. Anders
  worden boeken afhankelijk van de taal waarin ze bewerkt zijn.
- "Hoofdstuk 1" is een begintitel die de gebruiker toch overschrijft. Die mag gewoon via `tr()` in de taal van dat moment.

**Voorstel voor de test:** laat de test niet alleen naar letterlijke tekst in UI-aanroepen kijken. Laat hem alle
tekstletterlijken in `quietwriter/ui/` en `ai/ui.py` controleren op woorden die alleen in `nl.json` voorkomen, met een
kleine allowlist voor interne sleutels en opgeslagen waarden. Mijn scan met die aanpak vond precies de lijst hierboven.

### 3. 🟡 Knop "wijzig"/"edit" bij Voorwerk wordt bedekt door de inklapknop (bestaand, door mij gemist)

In de inhoudsboom valt de inklapknop van het paneel over de actie van de eerste rij (Voorwerk/Front matter): je ziet
"wijz"/"ed". Dat gebeurt in het Nederlands en in het Engels even erg (`r49_edit_overlap.png`), dus het komt niet door de
vertaling. Het zit er al langer in en ik heb het in eerdere rondes niet gezien.

**Voorstel:** geef de actiekolom een rechtermarge ter breedte van de inklapknop, of zet de knop onder de kop "Inhoud".

### 4. 🟡 Kleine punten

- In alle vier `resources/fonts/*/OFL.txt` staan na de echte copyrightregel nog de **sjabloonregels** van de OFL:
  "Copyright (c) <dates>, <Copyright Holder> (<URL|email>), with Reserved Font Name <Reserved Font Name>…". Haal die
  weg. De originele OFL.txt van Google Fonts heeft ze niet.
- `_root_text('LICENSE')` leest de licentie vanaf de projectroot (`parents[2]`). In de PyInstaller-build van 0.36
  staan `LICENSE` en `THIRD_PARTY_LICENSES.md` dus alleen goed als ze op dezelfde relatieve plek worden meegebundeld.
  Zet dit op de packaging-checklist.
- `main_window.build_ai_context` (regels 1136–1156) wordt nergens aangeroepen. Het is dode code met Nederlandse labels,
  en kan weg.
- Het variabele font Merriweather registreert naast "Merriweather" ook een aparte familie "Merriweather Light".
  Controleer of die als vijfde lettertype in de fontkeuze verschijnt.

---

## Wat werkt

| Check | Resultaat |
|---|---|
| Cooldown: 5× `RuntimeError(f"item {i}")` vanaf dezelfde regel | ✅ 1 venster, en na het sluiten geen nieuw venster. Het log bevat alle 5 |
| Zelfde type, **andere regel** | ✅ Wel een nieuwe melding |
| 50× dezelfde timerfout | ✅ 1 venster, en de teller klopt |
| Opstartfout | ✅ Modaal na het sluiten van de splash. Bevinding 1 bewijst het ongewild in de praktijk |
| AI-context in NL en EN (hoofdstuk/sectie/boek, met planning-opt-in) | ✅ Precies dezelfde tekst in de prompt, en alleen het label verschilt |
| Zoeken "Hele boek" / "Whole book" | ✅ Zelfde resultaat |
| Persona, Boekprofiel en Boekgeheugen | ✅ Alleen de **weergave** is vertaald, de opgeslagen Markdown-koppen blijven gelijk |
| Locales | ✅ 1045 = 1045 sleutels, zonder verschil |
| Fontfetch (echt uitgevoerd) | ✅ 8 TTF-bestanden (0,75–4,6 MB). `bundled_fonts()` geeft 4 families en de registratie werkt |
| Legacy-fonttests | ✅ Groen |
| Over → licenties | ✅ Kaarten voor de QuietWriter-licentie, licenties van derden en 4 fontlicenties, met de tekst uitklapbaar in NL en EN |
| CI-YAML | ✅ Fontfetch vóór de suites, Ubuntu-bibliotheken behouden |
| First-run-document | ✅ Een bestaande standaardwerkmap, ook leeg, telt als bestaand gebruik |

## Samenvatting

| # | Onderwerp | Ernst | Nieuw? |
|---|---|---|---|
| 1 | `tr` niet geïmporteerd in `ai/ui.py` → app start niet | 🔴 | nieuw in 0.35.2 |
| 2 | Nederlandse restteksten in het Engels (statusbalk, rechtsklikmenu, "JIJ", …) | 🟡 | nieuw zichtbaar door Engels |
| 3 | Inklapknop bedekt "wijzig"/"edit" | 🟡 | **eerdere bevinding, door mij gemist** |
| 4 | OFL-sjabloonregels, licentiepad in de build, dode code, Merriweather Light | 🟡 | nieuw |

## Conclusie

**0.35.2 is niet groen**, maar het verschil is één regel. Bevinding 1 is een typische fout voor een omgeving zonder Qt.
Een `pyflakes`-test en het pushen naar CI vóór de review maken hem voortaan onmogelijk. Met die regel erbij is alles
wat 0.35.2 belooft in orde: cooldown, fonts, licenties en vertaalde functies zonder gedragsverschil.

**Om 0.35 af te sluiten** zou ik in 0.35.3 alleen nog doen:
- bevinding 1 met de `pyflakes`-test;
- de lijst uit bevinding 2, met weergave en opslag gescheiden voor status en relaties, en de bredere scan als test;
- de OFL-sjabloonregels.

Bevinding 3 mag mee als dat klein blijft.

**Niet kunnen testen:**
- een echte GitHub Actions-run;
- de echte taakbalk van Windows;
- afgekapte teksten op 125% en 150% in het Engels. Ik heb op 100% gescand; Windows met DPI-schaling staat voor 0.36
  op de matrix.
