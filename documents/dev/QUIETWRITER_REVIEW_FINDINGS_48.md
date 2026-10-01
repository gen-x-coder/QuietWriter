# QuietWriter: reviewronde 48 (versie 0.35.1: crashhardening, opstartfout, HiDPI)

**Gelezen:**
- de diff tegen 0.35.0: `crash_notice.py`, `crash_logging.py`, `app.py`, `icon_theme.py`, `about_page.py`, `splash.py`
  en de workflow;
- `FIRST_RUN_DESIGN_035.md` en `REVIEW_NOTES_0351.md`.

**Getest:**
- de vier runs met echte PySide6 en een koude start;
- het runtimescript uit ronde 47, uitgebreid met een reeks herhaalde fouten, bundeling van meldingen, de cooldown, een
  wisselende foutmelding en een verwijderd oudervenster;
- een opstartfout die in `MainWindow` wordt geïnjecteerd;
- HiDPI op 100%, 125%, 150% en 200%;
- de Over-pagina in drie thema's.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testruns

| Run | Resultaat |
|---|---|
| `pytest` | ✅ **234 geslaagd** (bij ChatGPT 198 + 17 overgeslagen; hier draaien de Qt-tests echt) |
| `pytest -m qt` | ✅ 55 geslaagd |
| `pytest tests/legacy` | ✅ 449 geslaagd, alleen de 2 bekende fonttests falen (manifest volgt in 0.35.2) |
| `pytest tests/legacy -m qt` | ✅ 91 geslaagd |
| `python main.py` (koude start) | ✅ |

## Runtimechecks uit de review notes

| # | Check | Resultaat |
|---|---|---|
| 1 | 50× dezelfde fout vanuit een `QTimer` | ✅ **1 venster** ("En nog 49 fouten…"), en het log bevat alle 50 |
| 2 | Andere fout terwijl het venster open is | ✅ Geen tweede venster, en de teller gaat naar 50 |
| 1b | Dezelfde fout direct na het sluiten | ✅ Onderdrukt |
| 3 | Opstartfout in `MainWindow(...)` | ✅ De splash is al gesloten als de dialoog verschijnt. De dialoog is modaal, heeft als titel "QuietWriter kon niet starten", toont het detail `RuntimeError: STARTUP_BOOM` en heeft de knoppen "Logbestand openen" en "Sluiten". Het log bevat een blok "Opstartfout". `run()` geeft 1 terug |
| 4 | `qWarning` | ✅ In het log, op stderr en zonder dialoog |
| 5 | Over in Helder, Nacht en Aurora | ✅ Het woordmerk is altijd licht op de donkere hero (`r48_about_themes.png`). `hero_text` bestaat in alle 14 thema's |
| 6 | HiDPI | ✅ Zie de tabel hieronder |
| 7 | First-run-ontwerp | ✅ `first_run_done` plus herkenning van bestaande instellingen en werkmap. Mijn check uit ronde 47 bevestigt nog steeds dat `workspace` na een normale start ontbreekt, dus deze correctie was nodig |
| 8 | CI-YAML | ✅ Geldig; de Ubuntu-stap installeert de 5 bibliotheken alleen op Linux |

Ook opnieuw gecontroleerd, en nog steeds goed:
- het log staat lokaal en niet in de werkmap;
- het `.ico` levert alle formaten;
- fouten in een slot en in een thread worden gelogd en gemeld;
- de melding belooft niet dat het werk is opgeslagen.

Een extra randgeval: een melding waarvan het oudervenster (een actief `QDialog`) wordt verwijderd. De volgende fout gaf
toch netjes één nieuwe melding, zonder "Internal C++ object"-fout en zonder recursie. ✅

### HiDPI

| Schaal | Woordmerk op de splash (fysiek / ratio / logisch) | Icoon van 24 px (fysiek) |
|---|---|---|
| 100% | 300×75 / 1.0 / 300 | 24 |
| 125% | 375×94 / 1.25 / 300 | 30 |
| 150% | 450×112 / 1.5 / 300 | 36 |
| 200% | 600×150 / 2.0 / 300 | 48 |

Het woordmerk wordt op de echte schaal gerenderd, en de logische maat blijft gelijk. De iconen kiezen bij 125% en 150% de
2×-pixmap en schalen die omlaag. Dat is scherp genoeg. ✅

---

## Bevindingen

### 1. 🟡 Een herhalende fout met wisselende tekst komt na elke sluiting meteen terug

De cooldown herkent een fout aan `(samenvatting, detail)`, en het detail is de tekst van de exception. Een fout die op
dezelfde plek steeds met een andere tekst optreedt (bijvoorbeeld `KeyError: 'hoofdstuk-17'`, `KeyError: 'hoofdstuk-18'`
in een paint- of refreshroute) komt dus niet door die herkenning. In mijn test kwam de melding na elke sluiting direct
terug (5 van 5 keer).

Er staat nooit meer dan één venster open, dus dit is geen storm meer. Maar de gebruiker kan zo'n fout niet wegklikken.

**Voorstel:** baseer de herkenning op het type exception plus het **laatste frame van de traceback** (bestand:regel),
in plaats van op de tekst. Dat betekent dat `log_exception` naast `details` ook die plaats moet doorgeven aan `_notify`.
**Test:** 5× `RuntimeError(f'item {i}')` vanaf dezelfde regel geeft na de eerste sluiting geen nieuw venster.

### 2. Kleine opmerkingen (geen bug)

- `_device_pixel_ratio()` gebruikt het **primaire** scherm. Bij twee monitoren met een verschillende schaal wordt het
  woordmerk dus voor het primaire scherm gerenderd. Nemen we mee in de Windows-matrix (0.36).
- First-run-ontwerp: in het contract staat "de standaardwerkmap bestaat **en bevat een boek**". Iemand met een lege maar
  bestaande werkmap (alles verwijderd, of net begonnen) krijgt dan wel de wizard. Dat is waarschijnlijk onschuldig,
  maar "de werkmap bestaat" is een eenvoudigere en veiligere regel.

---

## Samenvatting

| # | Onderwerp | Ernst | Nieuw? |
|---|---|---|---|
| 1 | Herkenning in de cooldown gebruikt de tekst van de fout, niet de plek | 🟡 | nieuw (restant van de 🔴 uit ronde 47) |
| 2 | Primair scherm bij DPR; regel "werkmap met boek" in het first-run-ontwerp | opmerking | — |

## Conclusie

Alle bevindingen uit ronde 47 zijn opgelost, en de acht gevraagde runtimechecks slagen. **0.35.1 is groen.** Het
enige punt (🟡 1) is klein en kan mee in 0.35.2, samen met het fontmanifest, de licenties en de vertalingen.

**Niet kunnen testen:**
- de echte taakbalk van Windows (AppUserModelID, icoon op 16/24/32 px);
- echte Windows-DPI en twee monitoren (nagebootst met `QT_SCALE_FACTOR`);
- een echte GitHub Actions-run;
- of "Logbestand openen" op Windows het log in Kladblok opent (`QDesktopServices` wordt aangeroepen met het juiste pad).
