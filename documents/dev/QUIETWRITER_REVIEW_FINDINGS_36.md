# QuietWriter: reviewronde 36 (versie 0.34.0: eerste slice "In dit hoofdstuk" en fix voor de railselectie)

**Gelezen:**
- `chapter_context.py` en `ui/chapter_context_panel.py`;
- de diffs van `editor_page.py` en `main_window.py` (`QButtonGroup`, `ensureWidgetVisible`, de nieuwe toolknop);
- `REVIEW_NOTES_0340.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless) met het echte stylesheet, plus layoutmetingen op de
logische venstergroottes die bij Windows DPI 125% en 150% horen.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

**Eerst een correctie op de toelichting:** de railselectiefout heb **ik niet** gevonden, dat was Lucas. Mijn railmatrix in
rondes 34 en 35 controleerde alleen zichtbaarheid, niet welke knop geselecteerd is. Die controle zit er nu wel in (punt 1–3
hieronder).

**Testsuite:** 627 geslaagd, 280 subtests. Alleen de 2 bekende fonttests falen.

---

## REVIEW_NOTES_0340: resultaat

| # | Check | Resultaat |
|---|---|---|
| 1–2 | Klikreeks Persona → Inhoud → Instellingen → terug → Prullenbak → Planning → Boekprofiel → Instellingen → Boekenplank | ✅ na elke stap precies één geselecteerde knop, ook over de grens tussen het scrollende deel en PROGRAMMA |
| 2 | Twee keer op de actieve knop klikken | ✅ blijft geselecteerd |
| 3 | Op 1280×700 via code naar Boekprofiel, Boekgeheugen en Planning (scroll eerst weg) | ✅ alle drie geselecteerd **en** in beeld gescrold |
| 4 | Twee scènes bij hoofdstuk 1 (Anna, Bram), één scène bij hoofdstuk 2 (Cees), een verweesd id `cX` | ✅ alleen Aankomst en Ruzie; personages "Anna, Bram"; geen Elders, Cees of `cX`, geen exceptie |
| 5 | Paneel openen | ✅ `planning/` byte-identiek |
| 6 | Wijziging alleen in het geheugen van Planning | ✅ het paneel toont de opgeslagen stand |
| 6 | Opgeslagen wijziging, daarna naar Planning en terug naar Inhoud | ✅ de nieuwe titel verschijnt |
| 6 | Naar hoofdstuk 2 wisselen | ✅ Elders en Cees |
| 7 | AI uit | ✅ de knop blijft zichtbaar en actief; de AI-knop is weg |
| 8 | Voorwoord open | ✅ knop verborgen, paneel dicht |
| 8 | Terug naar een hoofdstuk | ✅ weer beschikbaar |
| 8 | Voorbeeld uit de geschiedenis | ✅ knop verborgen; na afsluiten weer beschikbaar |
| 9 | Ongeldige JSON in `outline.json` en in `characters.json` | ✅ korte melding in het paneel; typen en opslaan in het manuscript werken; Planning byte-identiek |
| 9 | Structureel verkeerde maar geldige JSON | ❌ **boek opent niet** (zie punt 1; bestond al) |
| 10 | "Planning openen" | ✅ Planning opent; alleen de Planning-knop in de rail is geselecteerd |
| 11 | AI-prompts | ✅ `quietwriter/ai/` is ongewijzigd ten opzichte van 0.33.1 |
| 12 | Nieuwe bestanden of schemawijzigingen | ✅ `planning_storage.py` ongewijzigd; openen schrijft niets |
| 13 | Layout 700, 720, 768 en DPI | ✅ met een kanttekening, zie punt 3 |
| 14 | Railmatrix uit 0.33.1 | ✅ 26/26 (de ene FAIL is de bekende scriptcontrole op het oude scrollgebied) |
| 15 | Smoke-regressie | ✅ editorbron 8/8, publicatie 18/18, notities, scène/afbeelding, rondes 12–24, randgeval ronde 24, herkomst, backend 47/15/8 |

---

## 1. 🟡 (bestond al, nu relevanter) Geldige JSON met een verkeerde structuur in Planning maakt het boek onopenbaar

Het paneel vangt `JSONDecodeError` goed af. Maar JSON die wel geldig is en een verkeerde vorm heeft, komt nooit bij het
paneel aan: het boek opent al niet.

| `planning/…` | 0.33.1 | 0.34.0 |
|---|---|---|
| `outline.json` = `{"version":1,"scenes":5}` | `TypeError` in `load_scenes` → boek opent niet | idem |
| een scène met `"character_ids": null` | `TypeError` in `Scene.from_dict` → boek opent niet | idem |
| `characters.json` met een personage met `"relations": 5` | `TypeError` in `Character.from_dict` → boek opent niet | idem |

De route is `open_book → adopt_active_book → _prepare_active_book_adoption → load_scenes/load_characters`. Er verschijnt
geen melding: de exceptie gaat de Qt-eventloop in, en voor de gebruiker gebeurt er gewoon niets als hij op het boek klikt.

**Waarom nu relevanter?** 0.34 gaat in de volgende slices verder met Planning-data. De realistische aanleiding is dus een
nieuwere QuietWriter op de andere computer die het Planning-schema uitbreidt of verandert. De oudere versie kan het boek dan
niet eens meer openen. Ook handmatig bewerkte JSON of een half gesynchroniseerd bestand kan dit veroorzaken.

**Fix, voordat 0.34 het schema aanraakt:**
- `load_scenes` en `load_characters`: accepteer `rows` alleen als het een `list` is. Anders `CorruptSourceError`, zodat de
  bestaande alleen-lezen-foutstaat uit 0.29.3 en de route via Integriteit worden gebruikt.
- `from_dict`: `character_ids` alleen als het een lijst is (`data.get('character_ids') or []` met een `isinstance`-check);
  hetzelfde voor `relations`.
- Laat `ChapterContextPanel.refresh` dezelfde `CorruptSourceError` afvangen. Dan is de `_validate_json`-dubbellezing niet
  meer nodig.
- **Test:** de drie vormen hierboven plus een `"version": 2` met een onbekende structuur. Het boek opent, Planning is
  alleen-lezen met een melding, en het paneel toont de leesfout.

## 2. 🟡 De koppen in het paneel hebben geen opmaak

`chapter_context_panel.py` gebruikt `setObjectName('subsectionTitle')` voor "Personages", "Scènes" en de scènetitels. Die
naam bestaat nergens in `themes.py`: er is alleen `QLabel#sectionTitle`. Koppen, scènetitels en synopsis zien er daardoor
identiek uit (zie `r36_1093x614.png`, dezelfde opname na het verwerken van de uitgestelde verwijderingen). Met vijf scènes is het lastig te zien waar de ene scène eindigt en de volgende begint.

**Fix:** één QSS-regel (bijvoorbeeld `QLabel#subsectionTitle { font-weight: 600; margin-top: 4px; }`), plus eventueel een
subtiele scheiding tussen scènes.

## 3. 🟡 (bestond al) Met een rechterpaneel open is het venster minimaal 1087 px breed

| Scherm (logisch) | Rail | Venster | Inhoud | Editor | Rechterpaneel |
|---|---|---|---|---|---|
| 1280×720 (= 1920×1080 @150%) | open | 1280 | 280 | **350** | 360 |
| 1366×768 @100% | open | 1366 | 280 | 436 | 360 |
| 1093×614 (= 1366×768 @125%) | open | 1093 | 250 | **247** | 306 |
| 911×512 (= 1366×768 @150%) | open | **1087** (breder dan het scherm) | 250 | 247 | 300 |
| 911×512 | dicht | **933** (breder dan het scherm) | 250 | 247 | 300 |

- Het panel zelf blijft overal bruikbaar: het scrollt en "Planning openen" blijft in beeld.
- Het echte knelpunt is de **editor**. Met de linkerrail open, Inhoud open en een rechterpaneel open blijft er op
  1366×768 bij 125% nog **247 px** schrijfruimte over, en de hoofdstuktitel wordt afgekapt ("oofdstuk 1").
- Dit bestond al voor Zoeken, AI en Spelling. Maar "In dit hoofdstuk" is juist bedoeld om náást het schrijven open te
  staan, dus het wordt nu vaker geraakt.

**Idee, niet meteen inbouwen:** als de editor smaller wordt dan ongeveer 420 px en er een rechterpaneel opengaat, klap dan
de linkerrail automatisch in, of Inhoud. Of zet de minimumbreedte van het rechterpaneel lager (260 in plaats van 300).

Mijn DPI-meting is gesimuleerd met logische venstergroottes, niet met een echte Windows-schaling. Controleer lettergroottes
en iconen bij 125% en 150% dus even op je eigen laptop.

---

## Kleine observaties (geen actie nodig)

- Het paneel ververst bij elke hoofdstukwissel en bij elke terugkeer naar Inhoud, ook als het dicht staat. Dat zijn twee
  kleine JSON-leesacties per keer; geen probleem, alleen goed om te weten als Planning ooit groot wordt.
- Een UTF-8-BOM in `outline.json` geeft in het paneel "kan niet betrouwbaar worden gelezen". Dat is consistent met
  `PlanningStore`, die zo'n bestand ook niet leest.
- In mijn headless schermafbeelding zag ik overlappende tekst. Dat blijkt een testartefact: `deleteLater` wordt zonder echte
  eventloop niet uitgevoerd. Na het verwerken klopt het beeld (`r36_1093x614.png`). Wil je het robuust maken, doe
  dan `widget.hide()` vóór `deleteLater()` in `_clear_rows`. Dat kost één regel.

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | Railselectie, scrollen in beeld, paneelinhoud, opgeslagen versus onopgeslagen, AI uit, verbergen, ongeldige JSON, geen writes, AI-prompts ongewijzigd | ✅ | — |
| 1 | JSON met een verkeerde structuur in Planning → boek opent niet (stil) | 🟡 | Bestond al; fixen vóórdat 0.34 het Planning-schema aanraakt |
| 2 | `subsectionTitle` heeft geen stijl: koppen niet te onderscheiden | 🟡 | Visueel |
| 3 | Met een rechterpaneel open blijft er bij 1366×768 en 125% maar 247 px editor over | 🟡 | Bestond al; wordt vaker geraakt |

**Conclusie:** de eerste 0.34-slice doet precies wat het ontwerp belooft. Hij is alleen-lezen, toont de opgeslagen
Planning, gaat netjes om met verweesde koppelingen, blijft zichtbaar met AI uit, schrijft niets en laat de AI-context
ongemoeid. De railselectiefout is structureel opgelost. Ik zou punt 1 in 0.34.1 meenemen, vóór er verder aan Planning wordt
gebouwd. Punt 2 is één QSS-regel. Punt 3 is een ontwerpkeuze voor een latere slice.

**Niet kunnen testen:**
- echte Windows DPI-schaling (gesimuleerd met logische venstergroottes);
- de ophaalroute van AI-modellen;
- echte Dropbox-timing.
