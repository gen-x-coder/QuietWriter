# QuietWriter: reviewronde 47 (versie 0.35.0: branding, crashvangnet, CI)

**Gelezen:**
- de diff tegen 0.34.10: `app.py`, `crash_logging.py`, de nieuwe `ui/crash_notice.py`, `icon_theme.py`, `splash.py`,
  `about_page.py`, `settings_page.py` en `main_window.py`;
- `.github/workflows/tests.yml`;
- `FIRST_RUN_DESIGN_035.md` en `REVIEW_NOTES_0350.md`.

**Getest:** de vier runs met echte PySide6, een koude start, een runtimescript in de echte opstartroute (`run()` met een
geïsoleerde HOME, XDG-mappen en instellingen), een splash in drie thema's en op 150% schaal, rotatie en de tempmap als
terugvaloptie, en een fout tijdens het opstarten.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns

| Run | Resultaat |
|---|---|
| `pytest` | ✅ 226 geslaagd |
| `pytest -m qt` | ✅ 47 geslaagd |
| `pytest tests/legacy` | ✅ 449 geslaagd, **2 fonttests falen** (zie bevinding 5) |
| `pytest tests/legacy -m qt` | ✅ 91 geslaagd |
| `python main.py` (koude start) | ✅ |

## Wat werkt (runtime 12 van de 14 checks)

| Onderdeel | Resultaat |
|---|---|
| Log in `AppLocalDataLocation/logs/crash.log`, niet in de werkmap | ✅ |
| Geen nieuw `crash.log` in de werkmap | ✅ |
| Venster- en app-icoon uit het `.ico` (16 t/m 256 px aanwezig) | ✅ |
| Exception in een **Qt-slot** (knop): in het log, en een niet-modale melding | ✅ |
| Exception in een **Python-thread**: in het log met de threadnaam, en een melding via de signaalbrug | ✅ |
| `qWarning`: in het log, zonder dialoog | ✅ |
| De melding belooft niet dat het werk is opgeslagen, maar vraagt de laatste wijziging te controleren | ✅ Goede keuze |
| Rotatie bij 2 MiB (`crash.log.1`) | ✅ |
| Terugvaloptie naar de tempmap als de logmap niet aangemaakt kan worden | ✅ |
| Woordmerk op de splash in Helder, Nacht en Aurora (`r47_splash_themes.png`) | ✅ |
| Woordmerk op Over kleurt mee na een themawissel (Nacht) | ✅ |
| Workflow-YAML is geldig (2 besturingssystemen, 4 suites) | ✅ |

---

## Bevindingen

### 1. 🔴 Een fout die zich herhaalt, opent tientallen foutvensters

Een fout in een timer die zich herhaalt, gaf **58 fouten en 58 open meldingen**: 58 losse vensters. Dezelfde situatie ontstaat
bij een fout in een `paintEvent` of `resizeEvent`, en die herhaalt zich eindeloos. Vóór 0.35.0 was zo'n fout stil. Nu
wordt de app er onbruikbaar door, want de gebruiker moet elk venster afzonderlijk sluiten.

**Voorstel:** toon maximaal één melding tegelijk. Komen er meer fouten terwijl de melding open staat, tel die dan in
dezelfde melding ("en nog 12 fouten, zie het logbestand"). Toon na het sluiten dezelfde fout (zelfde type en plaats) pas
weer na bijvoorbeeld een minuut. Het log blijft alles bevatten.
**Test:** een timer die 50 keer faalt geeft 1 open melding en 50 ingangen in het log.

### 2. 🟡 De first-run-trigger zou bestaande gebruikers treffen (ontwerp voor 0.36)

`FIRST_RUN_DESIGN_035.md` zegt: toon de wizard alleen als de instelling `workspace` nog niet bestaat. Maar `workspace`
wordt alleen geschreven bij Opslaan in Instellingen of via de herstelroute van de werkmap. Na een normale start waren
de instellingen in mijn test **volledig leeg**. Wie altijd de standaardmap `~/QuietWriter` gebruikte en nooit op
Opslaan drukte, krijgt na de update dus de wizard te zien.

**Voorstel:** gebruik een eigen sleutel `first_run_done`. Zet die direct bij de eerste start van 0.35.x/0.36 op `True`
als er al instellingen zijn, of als de standaardwerkmap al bestaat of boeken bevat. Maak dat onderdeel van het contract
vóór de bouw.

### 3. 🟡 Een fout tijdens het opstarten blijft onzichtbaar

Als het opstarten faalt vóór `app.exec()`, bijvoorbeeld in de constructor van `MainWindow`, wordt de fout wel gelogd en
wordt er wel een melding aangemaakt. Maar er draait nog geen event loop en het proces stopt direct. De gebruiker ziet
alleen dat de splash verdwijnt en dat er niets gebeurt. Juist voor 1.0 ("QuietWriter start niet") is dit de belangrijkste
fout om te laten zien.

**Voorstel:** vang in `run()` (of `main.py`) de exceptions van de opstartfase af, log ze, sluit de splash en toon
**modaal** een `QMessageBox.critical` met het pad naar het log en de knop "Logbestand openen".
**Test:** een `MainWindow` die een exception gooit, geeft een melding die zichtbaar is voordat het proces stopt.

### 4. 🟡 Het woordmerk is niet scherp bij 125% en 150% schaal

`themed_svg_pixmap` maakt een pixmap met `devicePixelRatio` 1. Op 150% (`QT_SCALE_FACTOR=1.5`) wordt het woordmerk
op de splash van 300 px dus opgeschaald naar 450 fysieke pixels, en dat oogt wazig.

**Eerdere bevinding die ik gemist heb:** `icon()` doet hetzelfde. Alle iconen in de rail en de werkbalk zijn pixmaps van 24
px met ratio 1, en zijn daardoor bij 125% en 150% ook onscherp. Dat zit er al lang in, en ik heb het nooit gemeld omdat
ik niet met schaling testte.

**Voorstel:** render met breedte × `devicePixelRatio` van het scherm en zet `pix.setDevicePixelRatio(dpr)`. Voeg in
`icon()` ook een pixmap van 2× toe aan de `QIcon`, dan kiest Qt zelf de beste. Dit hoort bij de DPI-regel van de
Windows-testmatrix.

### 5. 🟡 CI wordt vanaf de eerste push rood

- **De legacy-fonttests falen**, omdat `resources/fonts/font_manifest.json` ontbreekt. Dat bestand zit niet in de ZIP,
  en daardoor kan ook `tools/fetch_bundled_fonts.py` niets ophalen. Als `resources/fonts/` ook niet in de GitHub-repo
  staat, faalt de stap "Legacy suite" op beide systemen. **Voorstel:** zet het manifest (een klein JSON-bestand) in de
  repo en voeg vóór de legacy-stap `python tools/fetch_bundled_fonts.py` toe. Of cache de lettertypen.
- **Ubuntu-runner:** PySide6 heeft `libEGL.so.1`, `libGL.so.1`, `libxkbcommon.so.0`, `libfontconfig.so.1` en
  `libdbus-1.so.3` nodig, ook offscreen. Die ontbreken regelmatig op de standaardimages van GitHub. Ik kan de runner niet
  zelf draaien, maar een voorzorgsstap kost niets:
  `sudo apt-get update && sudo apt-get install -y libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3` (met
  `if: runner.os == 'Linux'`).
- De afhankelijkheden zijn verder compleet. Buiten de standaardbibliotheek importeren de code en de tests alleen
  `requests`, `spylls` en `yaml`.

### 6. 🟡 Kleine punten

- **Qt-berichten verschijnen niet meer in de console.** Er was geen vorige handler (`None`), dus `qWarning` gaat nu
  alleen naar het log. Wie `python main.py` draait, ziet ze niet meer. Stuur ze bij ontbreken van een vorige handler
  ook naar `sys.__stderr__`.
- **Het oude `<werkmap>/logs/crash.log` blijft in Dropbox staan.** Opruimen hoeft niet, maar het mag gerust weg.
- In `crash_logging.py` staat direct na `_install_qt_message_handler` een losse regel `_QT_HANDLER_INSTALLED = False` op
  moduleniveau. Die is onschadelijk, maar overbodig.
- Cosmetisch: de tagline op de splash staat vrij dicht onder het woordmerk. Een paar pixels meer ruimte ertussen oogt
  rustiger.

---

## Samenvatting

| # | Onderwerp | Ernst | Nieuw? |
|---|---|---|---|
| 1 | Herhaalde fout geeft tientallen vensters | 🔴 | nieuw in 0.35.0 |
| 2 | First-run-trigger `workspace` bestaat niet bij bestaande gebruikers | 🟡 | ontwerp 0.36 |
| 3 | Fout tijdens het opstarten blijft onzichtbaar | 🟡 | nieuw |
| 4 | Woordmerk en iconen niet scherp bij schaling | 🟡 | woordmerk nieuw; iconen **eerdere bevinding, door mij gemist** |
| 5 | CI: fontmanifest ontbreekt, Ubuntu-libs | 🟡 | nieuw |
| 6 | Kleine punten (console, oud log, losse regel, spatiëring) | 🟡 | nieuw |

## Conclusie

Het fundament staat goed. Het log is lokaal, alle drie de soorten fouten komen erin, de melding is eerlijk en de
branding werkt in alle thema's. **Bevinding 1 moet vóór de volgende build opgelost zijn**, anders maakt het crashvangnet
een kleine fout erger. Bevinding 3 hoort er direct bij. Bevinding 2 is een ontwerpcorrectie en moet in het contract
vóór 0.36.

**Ideeën, niet meteen inbouwen:**
- Zet het bestandslog al **vóór** `QApplication` aan, met het pad via `%LOCALAPPDATA%` en de omgevingsvariabelen. Dan
  wordt ook de fout "no Qt platform plugin could be initialized" gelogd. Dat is precies de typische fout als een
  PyInstaller-build in 0.36 een plugin mist. Bij mijn eerste koude start zonder offscreen werd dat bericht nergens
  gelogd.
- Zet in het log per start de versie van QuietWriter en Qt en de schaal van het scherm. Dat scheelt navragen bij een
  bugmelding.

**Niet kunnen testen:**
- de echte taakbalk van Windows (AppUserModelID, 16/24/32 px);
- een echte DPI-schaling op Windows (wel nagebootst met `QT_SCALE_FACTOR`);
- een echte run van GitHub Actions;
- of een startfout echt boven de splash verschijnt op Windows. De dialoog van de werkmapherstelroute heeft de splash als
  ouder en komt er dus bovenop, maar een losse crashmelding kan tijdens het opstarten achter de splash (die altijd
  bovenop blijft) vallen.
