# QuietWriter: reviewronde 27 (versie 0.32.1: settings-apply, live preview, start met spelling uit)

**Gelezen:**
- de diffs van `settings_page.py` (`self.main`, `_preview_feature_switches`, `restore_preview`);
- de diffs van `main_window.py` (`_set_feature_visibility`, `preview_feature_visibility`, `_leave_settings_preview`);
- de diffs van `editor_page.py` (volgorde in `__init__`) en `planning_page.py`;
- `REVIEW_NOTES_0321.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Ik heb de echte route gevolgd: Instellingen openen, vinkje
wijzigen, `save_settings()` en daarna via de rail weg. Ook de boekmap heb ik byte voor byte vergeleken, vóór en na elke stap.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

**Testsuite:** 591 geslaagd, 280 subtests. Alleen de 2 bekende fonttests falen.

---

## De twee rode punten uit ronde 26: gesloten

| Check (REVIEW_NOTES_0321) | Resultaat |
|---|---|
| **1.** `MainWindow` bouwen met `spell_enabled=False` | ✅ geen exceptie, de spellingknop is verborgen en de highlighter is inactief |
| **2.** De reproductie van Lucas: rode strepen → Spelling uit → Opslaan | ✅ 2 → **0** onderstrepingen, direct en zonder wissel van hoofdstuk; knop weg, `spell_active=False` |
| 2. Spelling weer aan → Opslaan | ✅ strepen en knop terug |
| **3.** AI uit **met** Opslaan, vanuit Boekgeheugen, Boekprofiel en Persona | ✅ terugkeerdoel is Inhoud (3/3) |
| 3. AI 6× uit/aan | ✅ `persona`, `memory.md` en `boekprofiel.md` byte-identiek |
| 3. AI-preview zonder Opslaan, weg via Inhoud, Boekenplank, Planning of Boekdetails | ✅ 12/12: de knoppen verdwijnen direct en komen daarna terug. Bij heropenen staat het vinkje weer goed en is Opslaan niet actief |
| **4.** Geavanceerd uit met Opslaan vanuit Integriteit | ✅ Inhoud, en Integriteit blijft verborgen |
| **5.** Lettergrootte en inspringing | ✅ direct toegepast (15 → 18 pt, 0 → 48 px); de undo-stack blijft schoon |
| 5. AI-provider → openrouter | ✅ `ai.apply_settings()` wordt na Opslaan aangeroepen, met de nieuwe provider |
| 5. Spellingstaal wisselen | niet getest: er is in deze container maar één woordenboek |
| **6.** Planning-intro, ook bij 1366×700 | ✅ rustig, geen dubbele titel en geen grote witruimte |
| **7.** Algemeen | ✅ "Geavanceerde opties gebruiken" staat één keer, rechts alleen het vinkje |
| Herkomst van de herstelkopie (0.32.0) | ✅ ongewijzigd |

Een opmerking: `return_from_settings()` heeft geen knop in de UI. Je verlaat Instellingen altijd via de rail. Omdat de
verborgen pagina's dan ook geen knop meer hebben, is het doel na Opslaan in de praktijk altijd goed.

---

## 1. 🔴 Opslaan in Instellingen markeert het open hoofdstuk als gewijzigd: autosave herschrijft het, met een vals conflict bij twee computers

**Nieuw bereikbaar in 0.32.1.** De oorzaak bestond al, maar `settings_saved()` werd tot nu toe nooit aangeroepen.

**Wat er gebeurt:** `settings_saved()` roept `apply_writing_font`, `apply_manuscript_style` en
`load_dictionary_from_settings` aan. Alle drie doen een `rehighlight()`. `QSyntaxHighlighter.rehighlight()` laat het
document `contentsChanged` uitzenden, dus `textChanged`. Daardoor zet `EditorPage.on_text_changed` `dirty = True` en toont
het "Niet opgeslagen". `apply_typography` blokkeert wel signalen voor zijn eigen tekenformaat, maar de `rehighlight()`
daarna valt buiten dat blok.

**Runtime (elke Opslaan, ook zonder één gewijzigde instelling):**

| Stap | Resultaat |
|---|---|
| Direct na Opslaan | `ed.dirty=True`, status "Niet opgeslagen" |
| 3 s later (autosave), zonder navigeren | het hoofdstuk wordt opnieuw geschreven |
| Of: navigeren naar Planning | `save_chapter` wordt aangeroepen; CRLF → LF; `book.json` krijgt een nieuwe `last_used` |

Hetzelfde geldt voor lettertype, thema, AI aan/uit en spelling aan/uit: het maakt niet uit welke instelling je wijzigt.

**Het scenario met twee computers:** op computer A open je alleen Instellingen en klik je Opslaan. Ondertussen komt via
Dropbox de nieuwe tekst van computer B binnen, voor precies dit hoofdstuk. Dan verschijnt op A:

> "Dit boek is buiten QuietWriter gewijzigd." [Mijn versie gebruiken] [Versie op schijf gebruiken]

Dat gebeurt voor een hoofdstuk waar de schrijver op A niets in heeft getypt.

| Keuze | Gevolg |
|---|---|
| "Mijn versie gebruiken" (voor de hand liggend, want de app zei "Niet opgeslagen") | de **oude** tekst van A komt live over het werk van B. B's tekst staat nog wel in `archive/…`, dus hij is herstelbaar |
| "Versie op schijf gebruiken" | goed |
| Geen keuze | goed, blijft staan |

Zonder dat tweede scenario blijft het een ongevraagde schrijfactie: extra Dropbox-verkeer, en de regeleinden van het bestand
worden genormaliseerd.

**Dezelfde oorzaak, maar al langer bestaand:** in het spellingspaneel maken **"Negeer overal"** en **"Toevoegen aan
woordenboek"** het hoofdstuk ook "Niet opgeslagen" (runtime: `dirty=True` bij beide). `ignore_always` gebruikt dezelfde
aanroep.

**Fix (robuust, één plek):**
- Laat `on_text_changed` alleen dirty zetten als de brontekst echt veranderd is. Houd bijvoorbeeld `self._clean_text` bij, dat
  wordt gezet bij laden, opslaan en reload. Dan doe je in `on_text_changed`: `if self.editor.toPlainText() == self._clean_text:
  return`. Dat vangt alle presentatie-routes tegelijk.
- Het alternatief is een vlag `_presentation_pass` rond elke `rehighlight()`. Die moet je dan wel op zes plekken zetten, en
  een nieuwe aanroep vergeet je snel.

**Test:** `save_settings()` → `ed.dirty is False`. Daarna 4 s pompen: het hoofdstuk is byte-identiek. Extern wijzigen en
dan navigeren geeft geen dialoog. De notitie-editor van Planning werd in mijn test **niet** herschreven.

---

## 2. 🟡 Live preview: de kop SCHRIJVEN en de witruimte boven Integriteit volgen de opgeslagen stand, niet het vinkje

**Nieuw in 0.32.1.** `_set_feature_visibility` zet de kop en de witruimte op basis van de preview-waarden, maar roept
daarna `self._apply_nav_width(False)` aan. Die leest `ai_enabled` en `advanced_options` opnieuw **uit de opgeslagen
instellingen** en zet de kop en de witruimte weer terug.

**Runtime (rail uitgeklapt):**

| Toestand | SCHRIJVEN | Persona | Integriteit | Witruimte |
|---|---|---|---|---|
| Preview AI uit | **zichtbaar, lege kop** | weg | — | — |
| Preview Geavanceerd uit | — | — | weg | **blijft** |
| Na Opslaan | weg | weg | weg | weg ✅ |
| Preview beide weer aan | **ontbreekt** | zichtbaar | zichtbaar | **ontbreekt** |

In `r27_preview_both_off.png` zie je de losse kop SCHRIJVEN direct boven PROGRAMMA staan. Na Opslaan of na weggaan klopt
alles weer. Het gaat dus alleen om het preview-moment, en dat is precies het moment dat Lucas beoordeelt.

**Fix:** roep `_apply_nav_width(False)` in `_set_feature_visibility` **eerst** aan en zet daarna de kop en de witruimte. Of
geef `_apply_nav_width` de effectieve waarden mee. Let op: `toggle_nav()` tijdens de preview gebruikt dezelfde functie.

---

## 3. 🟡 AI uitvinken in de preview sluit het AI-paneel definitief, ook zonder Opslaan

**Nieuw in 0.32.1.** In preview-modus voert `_set_feature_visibility` ook de `hidden_right`-tak uit: het AI-paneel gaat
naar Zoeken en wordt verborgen.

**Runtime:** AI-paneel open → Instellingen → AI uit → AI weer aan → terug naar Inhoud: het paneel is dicht (`was=True`,
`nu=False`). Hetzelfde gebeurt met AI uit en weggaan zonder Opslaan. Er gaat geen data verloren. Het paneel-type en de
invoer blijven bewaard, maar de toestand is niet "de opgeslagen toestand terug", zoals de notes beloven.

**Fix:** voer `hidden_right` alleen uit als `adjust_return=True`, dus bij de commit. Tijdens de preview is de editor toch
niet zichtbaar.

---

## 4. 🟡 (klein, bestond al) Mislukte Opslaan laat de nieuwe waarden toch in het geheugen staan

`save_settings()` doet eerst alle `setValue(...)` en daarna pas `sync()`. Faalt `sync()`, dan verschijnt de melding "De
instellingen konden niet betrouwbaar worden geschreven", maar de waarden staan al in het `QSettings`-object.

**Runtime (nagebootste `AccessError`):** AI uit → Opslaan faalt → naar Inhoud: `ai_enabled` is `False` in het geheugen en
Persona is verborgen. Tegelijk is `settings_saved()` niet gedraaid, dus typografie en woordenboek volgen niet. De app staat
dan half in de nieuwe en half in de oude stand. Na een herstart hangt het ervan af wat er wel op schijf kwam.

**Fix:** bewaar vóór de `setValue`-reeks een dict met de oude waarden en zet die bij een mislukte `sync()` terug, of roep
na de melding `restore_preview()` aan. Lage prioriteit.

---

## Regressie

| Reeks | Resultaat |
|---|---|
| Rondes 12–13 (future-format, notities) | 32/32, 10/10 |
| Ronde 14 (integriteit) | 19/19 |
| Ronde 15 | 7/12; de 5 FAIL-regels zijn gelijk aan 0.32.0 (testartefact: bestand stond niet in de snapshot, dus geen herstelkopie) |
| Rondes 16–18 (corruptie) | 2/2, 5/5, 3/3 |
| 0.31.0 | 18/18 |
| Adopt / openen met corrupte JSON | geen gemengde toestand; open → ok → Integriteit toont het probleem |
| Ronde 21 · spelling | 9/9 · 6/6 |
| Rondes 22–24 | 12/12, 12/12, 10/10 |
| Randgeval ronde 24 | beide keuzes: navigatie, Integriteit en sluiten werken; bytes intact; lokaal in History |
| Ronde 25 (met AI aan) | 25/29, alleen de 4 bekende artefact-regels (herstel toont het lokale concept, zoals ontworpen) |
| Ronde 26 (start, spelling, AI/advanced, herkomst) | alles groen |
| Backend 9–11 | 47/47, 15/15, 8/8 |

De transactionele adopt en de conflictflows uit 0.31 zijn niet geraakt.

## Visueel (headless, zonder app-thema)

- **Planning:** de titel en de uitleg staan bovenaan, daaronder Personages, Outline en Notities. Ook op 1366×700 blijft de
  pagina rustig, zonder dubbele titel. In de headless render oogt de uitleg niet gedempt; dat komt waarschijnlijk doordat
  het thema ontbreekt. Controleer dat even op je eigen scherm.
- **Algemeen:** in orde.
- **Preview:** zie punt 2 (`r27_preview_both_off.png`).

## Tips voor ChatGPT

- Voeg een test toe die **`save_settings()` met een open hoofdstuk** draait en daarna `editor_page.dirty is False` en
  byte-identieke hoofdstukbestanden controleert. Dat vangt punt 1 en elke toekomstige `rehighlight()`-route.
- Gebruik in zichtbaarheidstests `isHidden()` en niet `isVisible()`. `isVisible()` is offscreen of op een niet-actieve pagina
  altijd `False`, en dan slaagt een test ten onrechte.
- Test de preview met de rail **uitgeklapt**. De kop en de witruimte bestaan alleen in die stand.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| 1 | Opslaan in Instellingen (en "Negeer overal"/"Toevoegen" in Spelling) zet het hoofdstuk op dirty: onnodige herschrijving, en bij twee computers een vals conflict waarin "Mijn versie" oude tekst live terugzet | 🔴 | Hoog voor een Dropbox-opzet met twee computers; externe tekst wel in het archief |
| 2 | De preview laat de kop SCHRIJVEN en de witruimte op de opgeslagen stand staan | 🟡 | Visueel, alleen tijdens de preview |
| 3 | De preview sluit het AI-paneel, ook zonder Opslaan | 🟡 | Klein, geen data |
| 4 | Mislukte Opslaan laat de waarden in het geheugen staan | 🟡 | Klein, randgeval, bestond al |

**Conclusie:** beide rode punten uit ronde 26 zijn echt dicht. Starten met spelling uit werkt, de reproductie van Lucas werkt
direct, en de AI- en advanced-commit en de terugkeer kloppen. Juist doordat `settings_saved()` nu wél draait, komt een oude
fout tevoorschijn: presentatiewerk wordt als tekstwijziging gezien. Dat is punt 1. De fix is klein en centraal. Daarna zijn
punten 2 en 3 twee kleine aanpassingen in `_set_feature_visibility`.

**Niet kunnen testen:**
- een tweede spellingstaal (er is maar één woordenboek in de container);
- de echte ophaalroute van AI-modellen (geen netwerk);
- het app-thema in de schermafbeeldingen;
- echte Dropbox-timing (nagebootst door het bestand direct te wijzigen).
