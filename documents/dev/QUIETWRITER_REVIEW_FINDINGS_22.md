# QuietWriter: reviewronde 22 (versie 0.31.3)

**Gelezen:** de volledige diff van:
- `storage.py` (`_guard_existing_json`);
- `exporting/settings.py`, `planning_storage.py` en `publication_storage.py`;
- `export_page.py`, `publication_editor.py`, `spell_panel.py`, `editor_page.py` en `main_window.py`;
- `REVIEW_NOTES_0313.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Muisklikken en toetsen heb ik met `QTest` op de echte
editor-viewport gedaan. Bij elke corruptieroute heb ik de bytes vergeleken.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

---

## Testsuite en regressie

- **Testsuite:** 566 geslaagd, 280 subtests, 0 overgeslagen. Alleen de 2 bekende fonttests falen.
- **Regressie, allemaal groen:**
  - rondes 9–11 (47/47, 15/15, 8/8);
  - ronde 11 UI (36/36), ronde 12 (32/32), ronde 13 (10/10);
  - Integriteit (19/19);
  - corruptie 16–18 (2/2, 5/5, 3/3);
  - 0.31.0 (18/18);
  - de ronde-21-reeks: 8/9, waarbij de enige FAIL het bekende adopt-commitpunt is (zie onderaan);
  - openen met ongeldige UTF-8 in alle vier de JSON-bestanden: geen crash en geen gemengde toestand.

## Wat nu goed werkt

| Check (REVIEW_NOTES_0313) | Resultaat |
|---|---|
| 1. Export: eigen wijzigingen (formaat, template, marges, vinkjes, zes acties) → daarna schrijven | ✅ geen vals conflict; `verify_book_unchanged` blijft na elke actie groen |
| 3. `set_book`, adopt en de Exportpagina openen | ✅ `export/settings.json` byte- en mtime-identiek |
| 4. Spelling: de exacte katt/matt-reproductie | ✅ tweede katt gekozen (@37), Wijzigen vervangt precies die, geen selectie in de editor |
| 5. Spelling: eerste klik na openen, opslaan en een opmaakronde | ✅ eerste klik telt; doortypen laat het paneel staan; pijltjes volgen |
| 6. Afgekapte JSON (geldige UTF-8): characters, outline, publication | ✅ bytes identiek, nette melding, Integriteit ziet het |
| 7. Beschadigd Voorwoord openen | ✅ geen crash, alleen-lezen, Opslaan uit; typen, autosave en navigeren laten de bytes identiek |
| 8. Witruimte vóór Integriteit | ✅ zichtbaar bij openen, weg na Boekenplank en na loskoppelen |

De twee rode punten uit ronde 21 zijn dicht. Het wijzigen van eigen exportinstellingen geeft geen conflict meer, en
spelling kiest na typen de juiste fout.

---

## 1. 🔴 Exportpagina: na een externe wijziging (gewone Dropbox-sync) geeft elke klik een exceptie, en de instelling gaat stil verloren

**Nieuw in 0.31.3.** Het is een bijwerking van de terechte `verify` in `ExportSettingsStore.save()`.

**Bestand:** `ui/export_page.py`, `_format_changed()` en `_options_changed()`. Beide roepen `self.store.save(...)` aan
zonder foutafhandeling.

**Reproductie (runtime):**
- **(2b)** Boek open → een hoofdstuk wordt extern gewijzigd, bijvoorbeeld door de andere computer → Exporteren → PDF
  aanklikken. Resultaat: `ExternalModificationError` naar `sys.excepthook`, geen dialoog. Hetzelfde gebeurt bij elke
  volgende klik.
- **(2)** Idem met een externe wijziging van `export/settings.json` zelf. Het bestand blijft terecht onaangeroerd, maar
  ook hier komt een onafgevangen exceptie.

**Gevolg:** de gebruiker ziet de knop omgaan (PDF lijkt gekozen), maar er wordt niets opgeslagen en er komt geen melding.
De eerstvolgende editor-save start wel de gewone conflictflow. Tot die tijd is de Exportpagina stil kapot.

Dit is het gewone twee-computers-scenario: iets is gesynchroniseerd, en je opent daarna Exporteren.

**Fix:** zet één kleine helper om beide `store.save`-aanroepen:
```python
def _persist_settings(self):
    try:
        self.store.save(self.book, self.export_settings)
    except ExternalModificationError:
        latest = self.main.library.load_book(self.book.path)    # schone pagina, niets lokaals te verliezen
        self.main.adopt_active_book(latest)                      # of: via editor-conflictflow als editor dirty is
        QMessageBox.information(self, 'Boek extern gewijzigd', 'De nieuwste versie is geladen. Kies je exportinstelling opnieuw.')
    except (CorruptSourceError, BookBlockedError, StorageWriteError) as exc:
        QMessageBox.warning(self, 'Exportinstellingen niet opgeslagen', str(exc))
```
Dit is hetzelfde patroon als de Media-pagina (0.27.1) en Integriteit (0.29.1). De Exportpagina wordt pas geopend
nadat de editor en de andere pagina's zijn opgeslagen, dus automatisch herladen is hier veilig.

---

## 2. 🟡 Afgekapte (geldige UTF-8) `export/settings.json`: de pagina blijft actief, elke klik geeft een `CorruptSourceError`-exceptie

**Bestand:** `ui/export_page.py`, `set_book()`. `_corrupt_source` wordt alleen gezet bij een `UnicodeDecodeError`, niet
bij kapotte JSON.

**Runtime:** afgekapte `export/settings.json` → Exporteren → PDF → EPUB. De bytes blijven identiek (de storage-guard
werkt ✅), maar er komen twee `CorruptSourceError`-excepties naar de excepthook, zonder melding. Integriteit ziet het
probleem wel.

**Fix:** detecteer in `set_book()` dezelfde toestand als de guard (`_guard_existing_json` in een `try`), en zet dan
`_corrupt_source` plus de bestaande uitleg. De `try/except` uit punt 1 vangt het daarnaast ook af.

---

## 3. 🟡 Beschadigde publicatietekst: de melding verwijst naar Integriteit, maar Integriteit ziet het bestand niet

**Bestand:** `integrity.py`. `UTF8_FILES` bevat `publication/texts/*.md` niet.

**Runtime:** `publication/texts/foreword.md` met ongeldige UTF-8 → Voorwoord toont "…Open Integriteit om het te
controleren en zo mogelijk te herstellen" → Integriteit: **"Geen integriteitsproblemen gevonden"**, geen herstelknop.
Er staat wel een goede kopie in History.

Het Voorwoord blijft daardoor permanent alleen-lezen. De enige uitweg is een volledige versie-restore of het bestand met
de hand repareren. Er gaat niets verloren, maar de aangewezen route loopt dood.

**Fix:** laat de audit ook `publication/texts/*.md` (alle bestaande bestanden in die map) op UTF-8 controleren, als
`aux_text_invalid` met `recoverable=True`. `latest_recovery_file` en `restore_file_from_history` werken daar al
generiek voor.

---

## Bekend open (baseline voor 0.31.4, geen regressie)

**Adopt-commit (ronde 21 #6):** een lock tijdens de conflict-snapshot van Boekgeheugen laat nog steeds een gemengde
toestand achter. Editor en Planning staan dan op het nieuwe object; Boekgeheugen, Boekdetails, Media en Export op het
oude; `_active_book` is oud. Zoals afgesproken is dat voor 0.31.4.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| 1 | Exportpagina na een externe wijziging: onafgevangen exceptie per klik, instelling stil niet opgeslagen (nieuw) | 🔴 | Middel/hoog: gewoon Dropbox-scenario |
| 2 | Afgekapte `export/settings.json`: pagina actief, exceptie per klik | 🟡 | Laag, geen dataverlies |
| 3 | Beschadigde publicatietekst: Integriteit ziet hem niet, dus de verwijzing loopt dood | 🟡 | Laag/middel, geen dataverlies |

**Conclusie:** de corruptiebescherming staat nu voor alle bronbestanden in de opslaglaag, en de spelling doet precies wat
jullie beschreven. Punt 1 zou ik in 0.31.4 meenemen; het is dezelfde soort fix als eerder bij Media en Integriteit. Punten
2 en 3 zijn kleine aanvullingen die er direct bij passen. Daarna kan de transactionele adopt-commit met een schone
basislijn beginnen.

**Niet kunnen testen:** echte Dropbox-timing en Windows-locks (nagebootst), en hoe het spellingspaneel in de praktijk
aanvoelt bij snel typen (headless met `QTest`).
