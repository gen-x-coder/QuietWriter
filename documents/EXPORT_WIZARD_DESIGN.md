# QuietWriter: ontwerp "Begeleid exporteren" (exportwizard)

Doel van dit document: ChatGPT kan hiermee de exportwizard bouwen. Het bevat het UX-ontwerp (wat de gebruiker ziet en
doet) en het technische ontwerp (modules, datamodel, opslag, tests). De schermontwerpen staan op het canvas
**"QuietWriter Exportwizard"** (8 schermen, thema Helder, 1280×760).

Uitgangspunten: `PRODUCT_AND_UI_PHILOSOPHY.md` en `UI_REFERENCE.md`. Waar dit ontwerp daarvan afwijkt, staat dat
expliciet in §6.

---

## 1. Kernbeslissingen (en waarom)

| # | Beslissing | Waarom |
|---|---|---|
| 1 | De wizard is een **modus van de Exporteren-pagina**, geen modaal dialoogvenster | Export is al een eigen boekpagina. Een modaal venster blokkeert de navigatie, terwijl de stap **Controle** de gebruiker juist naar Boekdetails, Media of de publicatiestructuur stuurt. Na het oplossen komt hij terug op dezelfde stap. |
| 2 | Bovenaan de pagina een schakelaar **Begeleid / Zelf instellen**, onthouden in QSettings | Eén plek, direct zichtbaar, geen extra instelling in Instellingen. "Zelf instellen" is de huidige pagina, ongewijzigd. |
| 3 | De gebruiker kiest een **doel**, geen formaat | Een beginner weet wat hij wil (lezen op een e-reader), niet wat EPUB is. Het formaat staat wel klein op de kaart, zodat hij het leert. |
| 4 | **Eén exportroute** voor beide modi | Principe: "verbergen mag nooit een tweede gedragspad introduceren". De wizard vult dezelfde instellingen en roept dezelfde exportfunctie aan als "Zelf instellen". |
| 5 | **Keuzes in de wizard zijn een concept tot de export** | Principe "preview versus commit": wie halverwege stopt, verandert niets aan `export/settings.json`. Pas bij de exportknop worden de keuzes opgeslagen. |
| 6 | **Controle en Inhoud zijn alleen-lezen** | Principe "kan kijken per ongeluk data muteren?" De wizard repareert nooit zelf. Hij stuurt door naar de plek waar je het oplost. |
| 7 | **Delen** en **Back-up** zijn twee doelen met hetzelfde formaat | Ze verschillen in wat meegaat: bij delen gaan versiegeschiedenis en Meelezer-gesprek standaard **niet** mee (privacy, kleiner bestand), bij een back-up wel. |

---

## 2. UX-ontwerp

### 2.1 Opbouw van de pagina

```
┌ Exporteren                                   [ Begeleid | Zelf instellen ] ┐
│ Maak een bestand van “<titel>”.                                            │
│ 1 Doel   2 Controle   3 Inhoud   4 Vormgeving   5 Exporteren   (stappenrij) │
│ ───────────────────────────────────────────────────────────────────────── │
│ <stapinhoud, in een QScrollArea>                                           │
├────────────────────────────────────────────────────────────────────────────┤
│ [Terug]                                         <hulptekst>  [Volgende]   │  ← vaste footer, buiten de scrollviewport
└────────────────────────────────────────────────────────────────────────────┘
```

- Paginatype: **setup-flow** binnen een boekpagina. Kop en actiebalk volgen het instellingenpatroon: de primaire actie
  blijft buiten de scrollviewport.
- De inhoud staat links uitgelijnd met `max-width` 820 px, net als de huidige exportpagina (marges 42/32).
- **Stappenrij:** de huidige stap is vet met een accentstreep van 2 px (`accent`). Afgeronde stappen tonen "✓ Naam"
  in `muted`, komende stappen "n Naam" in `muted`. De stappenrij is **niet klikbaar**; navigeren gaat via
  Terug/Volgende. Onder een contentbreedte van 700 px wordt het de compacte vorm "Stap 2 van 5 · Controle".
- Het aantal stappen hangt af van het doel (zie 2.2). De rij past zich aan zodra het doel wijzigt.

### 2.2 Doelen → formaat → stappen

| Doel-id | Kaarttitel | Uitleg (één regel) | Formaat | Stappen |
|---|---|---|---|---|
| `ereader` | Lezen op een e-reader of telefoon | Voor Kobo, Kindle-app, Apple Boeken en telefoon. De tekst past zich aan het scherm aan. | EPUB | Doel · Controle · Inhoud · Vormgeving · Exporteren |
| `print` | Afdrukken of als PDF delen | Vaste pagina's, zoals een echt boek. Voor proeflezers op papier of een drukker. | PDF | Doel · Controle · Inhoud · Vormgeving · Exporteren |
| `word` | Laten redigeren in Word | Voor een redacteur of meelezer die opmerkingen en wijzigingen in Word zet. | DOCX | Doel · Controle · Inhoud · Exporteren |
| `share` | Delen met een andere QuietWriter-gebruiker | Je hele boek in één bestand: tekst, afbeeldingen en Planning. Zonder je oude versies. | QWBOOK | Doel · Controle · Inhoud · Exporteren |
| `backup` | Een back-up voor mezelf | Alles in één bestand, ook je versiegeschiedenis. QuietWriter kan het later volledig terugzetten. | QWBOOK | Doel · Controle · Inhoud · Exporteren |
| `website` | Op een website of blog plaatsen | Platte tekst met een vaste kop, klaar om te plakken in je site. | Markdown | Doel · Controle · Inhoud · Exporteren |

De doelen staan als kaarten in een raster van 2 kolommen, of 1 kolom onder een contentbreedte van 640 px. Een kaart
bestaat uit een icoon, een titel, een formaatlabel (klein, `panel2`) en één regel uitleg. De gekozen kaart gebruikt
dezelfde stijl als `exportFormatCard:checked` (`accent_soft` met een `accent`-rand). Bij de eerste keer is er geen
voorselectie en blijft Volgende uitgeschakeld. Daarna wordt het laatst gebruikte doel van dit boek voorgeselecteerd.

### 2.3 Stap 1: Doel

- Kop "Wat wil je met je boek doen?", met de uitleg "Kies wat het dichtst in de buurt komt. QuietWriter kiest daarna
  het juiste formaat en goede standaardinstellingen."
- Onder de kaarten een gedempte regel: "Weet je al precies welk formaat en welke instellingen je wilt? Kies rechtsboven
  **Zelf instellen**. QuietWriter onthoudt je keuze."
- Terug is uitgeschakeld.

### 2.4 Stap 2: Controle

- Kop "Is je boek klaar voor een <e-book | PDF | Word-bestand | QuietWriter-boek | websitebestand>?", met de uitleg
  "QuietWriter kijkt alleen. Er wordt niets aan je boek veranderd."
- **Alles in orde:** een groen paneel (`success_soft`) met "Alles is in orde · Je kunt verder", daaronder de
  gecontroleerde punten als rijen (✓, label, waarde). Een `info`-item krijgt "i" en een uitleg, bijvoorbeeld bij ISBN:
  "Niet ingevuld. Alleen nodig als je via een winkel verkoopt."
- **Er zijn punten:** een geel paneel (`warning_soft`) met "Nog n punten", gevolgd door één kaart per punt:
  - het label **"Moet opgelost"** (`danger`) of **"Mag je overslaan"** (`warning`). De betekenis zit dus ook in de
    tekst en niet alleen in de kleur;
  - een titel en één zin over het gevolg ("E-readers tonen dan ‘Onbekende auteur’");
  - rechts een knop naar de plek waar je het oplost (zie de tabel in 4.4).
  - De punten die in orde zijn, staan ingeklapt onder "▸ n andere controles in orde".
- **Footer:**
  - bij een `error`: Volgende uitgeschakeld, met links ervan de hulptekst "Los eerst het punt ‘Moet opgelost’ op." en
    de knop **Opnieuw controleren**;
  - bij alleen warnings: Volgende werkt.
- **Terugkomen na het oplossen:** de wizard staat nog op stap 2 en voert de controle automatisch opnieuw uit (zie
  4.5).

### 2.5 Stap 3: Inhoud

**Voor EPUB, PDF, DOCX en Markdown:**
- Kop "Dit komt in je <e-book | PDF | Word-bestand | websitebestand>", met de uitleg "Klopt dit? Zo niet, pas de
  publicatiestructuur aan. Daarna kom je hier terug."
- Eén zin: "Ongeveer **82.400 woorden** in **14 hoofdstukken**, verdeeld over 3 delen, met **6 afbeeldingen** en een
  omslag." Woorden worden afgerond op honderdtallen; het woord "ongeveer" is bewust.
- Een tabel met de rijen Voorwerk, Boek en Achterwerk. Boek toont per deel de titel, het aantal hoofdstukken en het
  aantal woorden.
- Een grijs paneel "Blijft alleen in QuietWriter: Planning, Boekprofiel, Boekgeheugen, het Meelezer-gesprek, de
  Bewaarplaats en je versiegeschiedenis." Dit beantwoordt de vraag die een beginner niet stelt.
- De knop **Publicatiestructuur aanpassen** gaat naar de bestaande setup (`_open_publication_setup`).
- De primaire knop heet **Klopt, volgende**.
- **Markdown met afbeeldingen:** de controle geeft dan al `markdown_images_pending` als error. Deze stap wordt dus
  nooit bereikt; in stap 2 staat bij dat punt de knop **Ander doel kiezen** (terug naar stap 1).

**Voor QWBOOK (delen of back-up):**
- Kop "Dit krijgt de ander van je" (delen) of "Dit zit in je back-up" (back-up).
- Rijen die altijd meegaan (✓, "altijd"):
  - manuscript (hoofdstukken, woorden);
  - afbeeldingen en omslag;
  - Planning, publicatiestructuur en boekgegevens;
  - Boekprofiel en Boekgeheugen.
- Twee keuzes met een checkbox:
  - **Meelezer-gesprek meesturen** (standaard: uit bij delen, aan bij back-up). **Dit is nieuw: zie 4.6.**
  - **Versiegeschiedenis meesturen**, met de regel "n versies · ongeveer x MB extra" (standaard: uit bij delen, aan
    bij back-up).
- Een infopaneel. Bij delen: "Oude versies kunnen tekst bevatten die je bewust hebt geschrapt. Daarom gaan ze bij delen
  standaard niet mee. Het pakket wordt nu ongeveer **6 MB**." Bij back-up: "Bewaar dit bestand buiten deze computer,
  bijvoorbeeld op een USB-stick of in de cloud."

### 2.6 Stap 4: Vormgeving (alleen EPUB en PDF)

**EPUB:**
- Kop "Hoe moet je e-book eruitzien?", met de uitleg "Kies een stijl. Lettergrootte en lettertype bepaalt de lezer
  later zelf op zijn e-reader."
- Drie stijlkaarten (Klassiek, Modern, Literair) met een **statische voorbeeldtekst** in die stijl. De voorbeelden
  worden gemaakt met de CSS van de template, in een kleine `QTextBrowser`; dat hoeft geen echte EPUB-rendering te
  zijn.
- Omslag, alleen als het boek een omslag heeft: een miniatuur en de vraag "Staat er al tekst op je omslag?" met twee
  radio-opties. Dit zijn de bestaande modi `artwork_only` en `artwork_with_text`, in eenvoudiger woorden. Zonder
  omslag staat hier: "Je boek heeft nog geen omslag. Die kun je toevoegen in Boekdetails." (zonder knop, de controle
  meldde het al).
- Checkbox "Elk deel begint met een eigen titelpagina" (`show_section_titles`). Alleen zichtbaar als het boek meer
  dan één deel heeft.

**PDF:**
- dezelfde stijlkaarten;
- "Boekformaat": A5 ("zoals een paperback") of A4 ("gewoon printpapier");
- de checkboxen Paginanummers en Lopende kop (standaard aan);
- Marges staan **niet** in de wizard; de standaard is goed genoeg.

### 2.7 Stap 5: Exporteren

- Kop "Klaar om te maken", met de uitleg "Kijk nog één keer. Met **Terug** kun je elke keuze nog veranderen."
- Een samenvattingskaart:
  - icoon met de bestandsnaam (de echte naam: `<slug>.<ext>`) en het soort bestand;
  - rijen Inhoud, Stijl (alleen EPUB/PDF) of Meegestuurd (QWBOOK), en **Opslaan in** met de knop **Wijzigen…**. Die
    knop gebruikt de bestaande `_choose_output_dir` en QSettings `export/output_dir`.
- Een gedempte regel per formaat. Bij EPUB: "QuietWriter controleert het e-book na het maken nog een keer. Pas als
  alles klopt, wordt het bestand opgeslagen. Je keuzes worden voor dit boek onthouden."
- **De primaire knop heeft een werkwoord per doel:** E-book maken · PDF maken · Word-bestand maken · Bestand om te delen
  maken · Back-up maken · Websitebestand maken.
- **Overschrijven:** de bestaande `confirm()`-dialoog, zelfde tekst.

### 2.8 Klaar (na een geslaagde export)

- Alle stappen ✓. Een groen paneel met `role=status`: "Je <e-book> is klaar", met daaronder bestandsnaam, grootte en
  map.
- Knoppen **Bestand openen** (primair) en **Map openen**. Bij QWBOOK alleen **Map openen** (zoals in 1.0.20).
- Eén korte hulptekst per doel, bijvoorbeeld "Hoe zet ik het op mijn e-reader?" of "Stuur dit bestand naar de andere
  QuietWriter-gebruiker. Die kiest **Boek importeren** op de Boekenkast."
- Rechts in de actiebalk: **Nog een export maken**. Dat gaat terug naar stap 1, met het doel voorgeselecteerd.
- Geen QMessageBox bij succes (bestaande regel). Wel de statusbalkmelding zoals nu.

### 2.9 Toetsenbord en focus

- **Tabvolgorde:** schakelaar Begeleid/Zelf instellen → stapinhoud → Terug → Volgende.
- **Doel- en stijlkaarten:** één tabstop voor de hele groep. Pijltjestoetsen verplaatsen de keuze; Enter of Spatie
  kiest. Dit is hetzelfde gedrag als een radiogroep.
- **Volgende is de standaardactie:** Enter in de stapinhoud (niet in een tekstveld) activeert Volgende als die aan
  staat.
- **Bij een stapwissel** krijgt het eerste bedienbare element van de nieuwe stap focus. Bij stap 2 met punten is dat
  de eerste actieknop.
- Escape doet niets: dit is een pagina, geen flyout.
- **Focusstijl:** de bestaande `focus`-token, zonder dat de layout verspringt.

### 2.10 Responsive (1280×700 bij 150%)

- De stapinhoud scrollt; kop, stappenrij en actiebalk blijven staan. De actiebalk staat bewust bóven de scrollbare stapinhoud, zodat de vervolgstap na een keuze direct zichtbaar is.
- Kaarten gaan van 2 naar 1 kolom onder een contentbreedte van 640 px; de stappenrij gaat dan naar de compacte vorm.
- De wizard mag de minimumgrootte van het hoofdvenster **niet** verhogen. Verborgen stappen zitten in een
  `QStackedWidget` met `QSizePolicy.Ignored` voor niet-actieve pagina's (bestaande regel: "hidden pages mogen
  minimumsize niet bepalen").

---

## 3. Gedrag van de modusschakelaar

| Situatie | Gedrag |
|---|---|
| QSettings `export/mode` ontbreekt | `guided` (ook voor bestaande gebruikers: één klik terug, en die keuze wordt onthouden) |
| Gebruiker kiest **Zelf instellen** | De huidige pagina verschijnt, met de **opgeslagen** instellingen. Een openstaand concept uit de wizard wordt weggegooid, niet opgeslagen. |
| Gebruiker kiest **Begeleid** vanuit Zelf instellen | De wizard start bij stap 1, met het laatst gebruikte doel van dit boek voorgeselecteerd (of zonder voorselectie). |
| Ander boek geopend | De wizard gaat terug naar stap 1 van dat boek. |
| Terug naar Exporteren na een fix (Boekdetails, Media, Publicatiestructuur) | De wizard blijft op dezelfde stap en voert snapshot en controle opnieuw uit. |

---

## 4. Technisch ontwerp

### 4.1 Nieuwe en gewijzigde modules

| Bestand | Soort | Inhoud |
|---|---|---|
| `quietwriter/exporting/purposes.py` | **nieuw**, puur Python | `ExportPurpose` en `PURPOSES`: de tabel uit 2.2 als data, plus `steps_for(purpose_id)` en `apply_purpose(settings, purpose_id) -> dict` |
| `quietwriter/exporting/summary.py` | **nieuw**, puur Python | `ContentSummary` en `build_content_summary(document)`; `PackageSummary` en `build_package_summary(library, book)` |
| `quietwriter/exporting/runner.py` | **nieuw**, puur Python | `run_export(library, book, document, format_name, settings, destination) -> ExportResult`. Dit is het formaatafhankelijke deel uit `ExportPage._export`, dat dan één route wordt |
| `quietwriter/exporting/settings.py` | wijzigen | sleutel `purpose` laden en opslaan; `qwbook.include_ai_chat` |
| `quietwriter/qwbook_io.py` | wijzigen | `export_qwbook(..., include_ai_chat: bool = True)` (zie 4.6) |
| `quietwriter/exporting/preflight.py` | wijzigen | QWBOOK-controles (zie 4.4) |
| `quietwriter/ui/export_page.py` | wijzigen | wordt een container: kop met de modusschakelaar, en een `QStackedWidget` met `[ExportWizard, ManualExportPanel]`. De huidige inhoud verhuist ongewijzigd naar `ManualExportPanel` (of blijft inline als tweede pagina). `_export` roept `run_export` aan |
| `quietwriter/ui/export_wizard.py` | **nieuw** | `ExportWizard(QWidget)` met de stapwidgets `PurposeStep`, `CheckStep`, `ContentStep`, `AppearanceStep`, `ReviewStep` en `DoneState`, de stappenrij en de vaste actiebalk |
| `quietwriter/themes.py` | wijzigen | objectnamen `exportPurposeCard`, `wizardStepCurrent`, `wizardStepDone`, `wizardFooter`, `checkBadgeError` en `checkBadgeWarning`; alleen semantische tokens |
| `quietwriter/locales/nl.json`, `en.json` | wijzigen | alle teksten via `tr()` met het voorvoegsel `export.wizard.*` |

### 4.2 Datamodel

```python
# exporting/purposes.py
@dataclass(frozen=True)
class ExportPurpose:
    id: str                 # 'ereader' | 'print' | 'word' | 'share' | 'backup' | 'website'  (stabiel, nooit vertaald)
    format: str             # 'epub' | 'pdf' | 'docx' | 'qwbook' | 'markdown'
    has_appearance: bool    # True voor epub/pdf
    defaults: dict          # bv. share: {'qwbook': {'include_history': False, 'include_ai_chat': False}}

def apply_purpose(saved: dict, purpose_id: str) -> dict:
    """Concept-instellingen voor de wizard: opgeslagen instellingen + formaat + doel-standaarden.
    Overschrijft alleen sleutels uit `defaults`; een eerder gekozen template blijft staan."""
```

```python
# exporting/summary.py
@dataclass(frozen=True)
class SectionSummary:  title: str; chapters: int; words: int
@dataclass(frozen=True)
class ContentSummary:
    words: int; chapters: int; sections: tuple[SectionSummary, ...]
    images: int; has_cover: bool
    front_matter: tuple[str, ...]; back_matter: tuple[str, ...]   # keys, UI vertaalt

@dataclass(frozen=True)
class PackageSummary:
    has_planning: bool; has_profile: bool; has_memory: bool; has_ai_chat: bool
    history_versions: int; history_bytes: int; book_bytes: int; ai_chat_bytes: int
```

- Woorden worden geteld met de bestaande `media.markup.count_words`, per `ExportChapter.markdown`. Dat is dezelfde
  telling als in de statusbalk.
- **`build_package_summary` moet strikt alleen-lezen zijn.** Roep **niet** `list_versions()` of `_history_root()` aan:
  die maken `archive/<id>/` aan (`mkdir`). Gebruik `library.archive_dir / book.id`, en als die bestaat `history.json`
  en `os.scandir`/`stat` voor de grootte. Een test moet bewijzen dat er na de samenvatting geen map is bijgekomen.

### 4.3 Opslag

| Wat | Waar | Wanneer geschreven |
|---|---|---|
| Modus `guided`/`manual` | QSettings `export/mode` (per computer, net als `export/output_dir`) | direct bij het omzetten van de schakelaar |
| Laatste doel | `export/settings.json`, sleutel `purpose` (per boek) | **alleen bij een geslaagde export via de wizard** |
| Formaat- en renderkeuzes | `export/settings.json` (bestaand) | wizard: bij de export; Zelf instellen: zoals nu, direct |
| Concept van de wizard | in het geheugen (`ExportWizard._draft`) | nooit |

> **Les uit review 80:** `ExportSettingsStore.load()` en `save()` nemen alleen bekende sleutels over. Voeg `purpose`
> en `qwbook.include_ai_chat` aan **beide** toe, met een roundtrip-test (opslaan → nieuw object → laden → gelijk).

### 4.4 Controle: hergebruik van de preflight, plus koppeling naar acties

`run_preflight` blijft de enige bron. Uitbreiding voor QWBOOK:

- `qwbook_history` (info): het aantal versies en de grootte, alleen als de versiegeschiedenis meegaat;
- `qwbook_large` (warning): het geschatte pakket is groter dan 500 MB;
- `qwbook_over_limit` (error): het geschatte pakket is groter dan `MAX_TOTAL_SIZE` of heeft meer bestanden dan
  `MAX_FILE_COUNT`. Dit vangt een export op die anders pas tijdens het maken zou mislukken.

De UI koppelt elke `PreflightItem.key` aan teksten en een actie. Die koppeling is een tabel in `export_wizard.py`,
**niet** in `preflight.py`, omdat het UI-routes zijn:

| key | Titel (nl) | Gevolg-zin | Actieknop → route |
|---|---|---|---|
| `title` (error) | Je boek heeft geen titel | Zonder titel kan QuietWriter geen bestand maken. | Boekdetails openen → `main.open_current_book_details()` |
| `author` (warning) | Geen auteur ingevuld | E-readers tonen dan ‘Onbekende auteur’. | Boekdetails openen |
| `language` (error) | Geen taal ingesteld | E-readers gebruiken de taal voor afbreking en voorlezen. | Boekdetails openen |
| `chapters` (error) | Je boek heeft nog geen hoofdstukken | Er is niets om te exporteren. | Naar Inhoud → `main.show_editor()` |
| `missing_assets` (error) | Een afbeelding ontbreekt | <naam> verwijst naar een bestand dat niet meer bestaat. | Media openen → `main.show_media()` |
| `markdown_images_pending` (error) | Afbeeldingen passen niet in een websitebestand | Markdown-export ondersteunt nog geen afbeeldingen. | Ander doel kiezen → stap 1 |
| `cover_missing` (warning) | Geen omslag | Je e-book krijgt een eenvoudige tekstomslag. | Boekdetails openen |
| `pdf_wrap_fallback` (warning) | n afbeeldingen zonder tekstomloop | Een lang onderschrift past niet naast de afbeelding; de tekst loopt er dan onderdoor. | (geen knop) |
| `isbn` (info) | ISBN | Niet ingevuld. Alleen nodig als je via een winkel verkoopt. | (geen knop) |
| `qwbook_large` (warning) | Groot bestand | Ongeveer x MB. Zet de versiegeschiedenis uit voor een kleiner bestand. | Naar Inhoud-stap → stap 3 |
| `qwbook_over_limit` (error) | Te groot voor één pakket | … | Naar Inhoud-stap → stap 3 |
| externe wijziging (`ExternalModificationError` bij de snapshot) | Je boek is buiten QuietWriter gewijzigd | QuietWriter heeft de nieuwste versie nodig. | Opnieuw controleren |

### 4.5 Snapshot en hercontrole

- Bij het binnenkomen van stap 2, en bij elke `showEvent` van de pagina terwijl de wizard op stap 2 of later staat:
  1. `editor_page.save()` en `planning_page.save_pending()` (zoals `_export` nu doet). Faalt dat: de stap toont een
     blokkerend item "Niet-opgeslagen wijzigingen konden niet worden bewaard".
  2. `build_export_document(...)` → `run_preflight(document, format, draft)`.
  3. `build_content_summary(document)` (en voor QWBOOK `build_package_summary`).
- Als de wizard al **voorbij** stap 2 staat en de hercontrole geeft nu een `error`, dan springt hij terug naar stap 2
  met een korte regel: "Er is iets veranderd. Controleer opnieuw."
- Bij **Exporteren** wordt de snapshot nog één keer gemaakt (zoals nu). Er wordt dus nooit een verouderde snapshot
  geëxporteerd.

### 4.6 Nieuw in `qwbook_io`: het Meelezer-gesprek optioneel

```python
def export_qwbook(library, book, destination, *, include_history=True, include_ai_chat=True) -> Path:
    ...
    files, payloads = _collect_payloads(book.path)
    if not include_ai_chat:
        files.pop('.quietwriter/ai_chat.json', None)
        payloads = [(r, d) for r, d in payloads if r != '.quietwriter/ai_chat.json']
    package['ai_chat_included'] = bool(include_ai_chat)
```

- De import hoeft niets te veranderen: hij volgt het manifest.
- Het pakketformaat blijft **versie 2**: `ai_chat_included` is een extra informatieve sleutel die oudere 1.0.2x-versies
  negeren.
- `Zelf instellen` krijgt dezelfde checkbox in het bestaande QWBOOK-paneel, zodat beide modi dezelfde opties hebben.

### 4.7 Eén exportroute

```python
# exporting/runner.py
@dataclass(frozen=True)
class ExportResult:  path: Path; format: str; bytes: int; validated: bool

def run_export(library, book, document, format_name, settings, destination) -> ExportResult:
    if format_name == 'epub':     export_epub(document, destination, settings); validated = True
    elif format_name == 'pdf':    export_pdf(document, destination, settings)
    elif format_name == 'docx':   export_docx(document, destination, settings)
    elif format_name == 'qwbook':
        q = settings.get('qwbook', {})
        export_qwbook(library, book, destination,
                      include_history=bool(q.get('include_history', True)),
                      include_ai_chat=bool(q.get('include_ai_chat', True)))
    elif format_name == 'markdown': export_markdown(document, destination, settings)
    else: raise ValueError(format_name)
    ...
```

- In `ExportPage` komt één methode `_prepare_and_run(format_name, settings) -> ExportResult | None` voor beide modi.
  Die doet:
  1. editor en Planning opslaan;
  2. de snapshot maken;
  3. de preflight uitvoeren;
  4. de bestemming bepalen en zo nodig om bevestiging voor overschrijven vragen;
  5. `run_export` aanroepen;
  6. de instellingen opslaan (de wizard: `draft` met `purpose`).
- De wizard en het handmatige paneel tonen het resultaat elk op hun eigen manier.

### 4.8 Wat niet verandert

- De exporters (EPUB, PDF, DOCX, Markdown) en hun uitvoer.
- `qwbook_io`, op de optie uit 4.6 na.
- De publicatiestructuur en Boekdetails.
- "Zelf instellen" ziet er hetzelfde uit; alleen de modusschakelaar en de checkbox voor het Meelezer-gesprek komen erbij.

---

## 5. Tests

**Puur Python (zonder Qt):**
1. `purposes`: elk doel heeft een geldig formaat; `steps_for` geeft 5 stappen voor epub/pdf en 4 voor de rest; de id's
   zijn uniek en ASCII.
2. `apply_purpose`:
   - `share` → `include_history=False` en `include_ai_chat=False`;
   - `backup` → beide `True`;
   - een eerder opgeslagen `epub.template='literary'` blijft staan.
3. `ExportSettingsStore`: roundtrip van `purpose` en `qwbook.include_ai_chat` (opslaan → laden → gelijk); een onbekend
   doel valt terug op `None`.
4. `build_content_summary`: woordtelling gelijk aan `count_words` over alle hoofdstukken; afbeeldingen, omslag en
   voor- en achterwerk kloppen.
5. **`build_package_summary` muteert niets:** `archive/<id>` bestaat niet → na de aanroep nog steeds niet.
   Versie-aantallen en -bytes kloppen.
6. `export_qwbook(include_ai_chat=False)`: geen `ai_chat.json` in de ZIP; `ai_chat_included: false` in het manifest;
   de import werkt.
7. `run_export` per formaat geeft een bestand met dezelfde bytes als de oude `_export`-route, met dezelfde instellingen
   (EPUB en DOCX met een vaste tijd en id).
8. Preflight: QWBOOK boven de limiet → `qwbook_over_limit` en `can_export` is False.

**Qt (offscreen):**

9. Zonder `export/mode` start de pagina in de wizard. Omschakelen naar Zelf instellen → na een herstart nog steeds
   handmatig.
10. Wizard-route `ereader` tot aan **E-book maken** → er staat een EPUB en `settings.json` bevat `purpose: 'ereader'`.
11. **Halverwege stoppen verandert niets:** doel kiezen, naar stap 4, template wijzigen, naar Zelf instellen →
    `settings.json` is byte-gelijk aan ervoor.
12. **Controle met een error:** een ontbrekende afbeelding → Volgende staat uit → `show_media()` wordt aangeroepen bij
    de knop. Afbeelding herstellen → `showEvent` → de controle is groen en Volgende staat aan, op dezelfde stap.
13. **Doel `share`:** de stappenrij heeft 4 stappen; in stap 3 staan beide checkboxen uit; in de export zit geen
    `history/` en geen `ai_chat.json`.
14. **QWBOOK klaar:** alleen Map openen is zichtbaar.
15. **Toetsenbord:** focus op de doelgroep; pijl rechts/omlaag verplaatst de keuze; Enter → stap 2.
16. **Minimumgrootte:** met de wizard zichtbaar is `minimumSizeHint().height()` ≤ 700 en `width()` ≤ 1100; het
    venster wordt niet breder gemaakt.
17. **Ander boek openen** → de wizard staat op stap 1.

---

## 6. Besluiten (Lucas, 5 oktober 2026)

1. **Iedereen begint in de begeleide modus**, ook bestaande gebruikers. Uitzetten kan op de pagina zelf en in
   **Instellingen → Algemeen → Begeleid exporteren** (beide gebruiken QSettings `export/guided`).
2. **Het doel "Op een website of blog plaatsen" is altijd zichtbaar**, ook zonder Geavanceerde opties.
3. **Het Meelezer-gesprek kan uit een `.qwbook` worden weggelaten**, en staat bij "Delen" standaard uit.
4. De stijlvoorbeelden in stap 4 zijn statische tekst, geen rendering van het boek (geen previewmotor).
5. De stappenrij is niet klikbaar; Terug blijft altijd mogelijk.

## 6a. Implementatie (referentiecode van Claude)

| Bestand | Inhoud |
|---|---|
| `quietwriter/exporting/runner.py` | `run_export`, `destination_for`, `ExportResult` (één exportroute) |
| `quietwriter/exporting/purposes.py` | de zes doelen, `steps_for`, `apply_purpose` |
| `quietwriter/exporting/summary.py` | `build_content_summary`, `build_package_summary` (alleen-lezen) |
| `quietwriter/exporting/preflight.py` | `package`-parameter, `qwbook_over_limit`/`qwbook_large`/`qwbook_history` |
| `quietwriter/exporting/settings.py` | `purpose` en `qwbook.include_ai_chat` in load/save |
| `quietwriter/qwbook_io.py` | `export_qwbook(..., include_ai_chat=True)`, manifest `ai_chat_included` |
| `quietwriter/ui/export_page.py` | kop met modusschakelaar, `mode_stack`, `run_export_flow`, `persist_settings_dict` |
| `quietwriter/ui/export_wizard.py` | `ExportWizard` met alle stappen |
| `quietwriter/ui/settings_page.py` | checkbox **Begeleid exporteren** |
| `quietwriter/themes.py` | objectnamen voor wizard, kaarten, badges en modusschakelaar |
| `tests/current/test_export_wizard.py`, `..._qt.py` | 8 + 10 tests |

## 7. Bouwvolgorde (voorstel)

1. `runner.py` uit `_export` halen en `_export` laten aanroepen. Gedrag gelijk, tests 7 groen.
2. `purposes.py`, `summary.py`, settings-sleutels, `include_ai_chat`. Tests 1–6 en 8.
3. Modusschakelaar en `ExportPage` als container, met de handmatige modus ongewijzigd. Test 9.
4. De wizardstappen 1 → 5 en Klaar. Tests 10–17.
5. Teksten in `en.json`, de themacheck (contrast van de nieuwe objectnamen in alle thema's) en `UI_REFERENCE.md`
   bijwerken (sectie "Exporteren-pagina": de wizard toevoegen en de achterhaalde regel "drie kaarten" corrigeren).
