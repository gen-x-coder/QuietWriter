# QuietWriter: reviewronde 93 (1.2.11, WrappedLabel, live verversen van Open punten)

**Getest (Linux, Python 3.12.3, PySide6 6.11.2, offscreen):**
- de diff ten opzichte van 1.2.10:
  - `panel_help.py` (nieuw: `WrappedLabel`, plus `showEvent`);
  - `ai/ui.py` (de melding als `QVBoxLayout` met een `WrappedLabel`);
  - `editor_page.py` (debounce-timer van 300 ms);
  - de tests;
- de volledige suite (inclusief Qt), de undefined-names-check (pyflakes), `check_locales.py` en `--smoke-test`;
- **mijn smalle-Meelezer-test via de echte route**: `MainWindow` en `show_ai()` direct bij openen, zonder resize achteraf.
  Dat heb ik gedaan in 5 talen × 3 situaties (100% op 1024×683, 150% op 1024×683, en 125% op 1536×830). Daarbij heb
  ik zowel de uitleg als de toestemmingsmelding nagemeten;
- dezelfde controle op afgekapte uitleg in **alle 8 rechterpanelen**, ook in 5 talen × 3 situaties;
- **Ongedaan maken en Opnieuw met Open punten open**, met echte toetsaanslagen (Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z). Dat
  heb ik gedaan in een klein boek en in een boek van 150 hoofdstukken;
- de scenario's uit ronde 91 en 92 opnieuw, als regressietest.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testresultaten

| Run | Resultaat |
|---|---|
| `tools/check_undefined_names.py` | ✅ OK |
| `tools/check_locales.py` | ✅ OK: 1503 sleutels in 5 talen |
| `pytest` (volledig, inclusief alle Qt-tests) | ✅ **619 geslaagd**, 0 fouten, 304 subtests, 102 s |
| `--smoke-test` | ✅ rc 0 |
| ZIP | ✅ schoon |

## De smalle Meelezer, via MainWindow: groen

Tekst hoog / nodig, bij het direct openen van de Meelezer:

| Taal | Uitleg (300 px) | Melding (300 px) | Uitleg (360 px) | Melding (360 px) |
|---|---|---|---|---|
| nl | 84 / 84 ✅ | 70 / 70 ✅ | 84 / 84 ✅ | 56 / 56 ✅ |
| en | 84 / 84 ✅ | 56 / 56 ✅ | 84 / 84 ✅ | 56 / 56 ✅ |
| de | 98 / 98 ✅ | 70 / 70 ✅ | 98 / 98 ✅ | 70 / 70 ✅ |
| fr | 98 / 98 ✅ | 84 / 84 ✅ | 98 / 98 ✅ | 70 / 70 ✅ |
| es | 70 / 70 ✅ | 84 / 84 ✅ | 70 / 70 ✅ | 84 / 84 ✅ |

- **De 300 px-kolommen** gelden bij zowel 100% als 150%. Ze zijn identiek.
- **`notice_nl_crop.png`:** de melding staat volledig in beeld, inclusief "…verlaten deze gegevens je computer.", met
  **Begrepen** eronder. Hij ziet er nu uit als het uitlegblok, maar in de waarschuwingskleur.
- **Alle 8 panelen** × 5 talen × 3 situaties: **nergens** afgekapte uitleg.
- **De minimale venstergrootte** is ongewijzigd (322 bij 150%).

## Ongedaan maken en Opnieuw met Open punten open: groen

| Stap | 3 hoofdstukken | 150 hoofdstukken |
|---|---|---|
| Open punt toevoegen | ✅ direct +1 | ✅ direct +1 |
| **Ctrl+Z** | ✅ na 300 ms −1 (bron en lijst gelijk) | ✅ |
| **Ctrl+Y** / Opnieuw | ✅ na 300 ms +1 | ✅ |
| Typen in een punt ("de haven" wordt "de haven zee") | ✅ de lijst toont na 300 ms de nieuwe tekst | ✅ |
| Plakken van tekst met een ruwe markering | ✅ de markering wordt opgeschoond, de lijst verandert niet | ✅ |
| Wisselen van hoofdstuk met een nog niet opgeslagen punt | ✅ het punt blijft in de lijst | ✅ |
| Typen terwijl het paneel dicht is | ✅ 0 keer ververst | ✅ |
| 6 tekens snel achter elkaar typen met het paneel open | ✅ 1 keer ververst (de debounce werkt) | ✅ |
| Duur van één keer verversen | 1 ms | 11 ms |

**Regressie uit ronde 91 en 92:** alles is nog groen.
- Bij het eerste gebruik: Begrepen, het ?, het toetsenbord en geen modale vensters.
- De Meelezer klapt in bij Context en Snelacties, zonder vlag.
- Alle uitleg weer tonen en Standaardinstellingen herstellen.
- De kleur van het ? na een themawissel.
- In dit hoofdstuk is leeg zonder grijs vlak.

---

## Bevindingen

### 1. 🟡 Bij het live verversen raakt de Open punten-lijst de selectie en de scrollpositie kwijt

Bij het verversen wordt de lijst leeggemaakt en opnieuw gevuld. Omdat dat nu na elke typpauze gebeurt:
- **Selectie:** wie een punt in de lijst heeft geselecteerd en daarna in de editor typt, verliest die selectie
  (`currentRow` van 149 naar **−1**).
- **Scrollpositie:** in een lange lijst springt die terug (van 139 naar 64).

Met de muis valt het weinig op. Met het toetsenbord (pijltjes door de lijst, Enter, iets aanpassen, weer terug naar de
lijst) begin je elke keer weer bovenaan.

**Oplossing:** onthoud vóór `self.list.clear()` het `point_id` van het huidige item en de waarde van de scrollbalk.
Zet ze na het vullen terug: zoek het item met dat id, `setCurrentRow`, en zet de scrollwaarde terug. Gebruik
`blockSignals` rond het terugzetten, zodat er geen sprong naar het punt in de editor plaatsvindt.

---

## Niet getest (expliciet)

- **Windows zelf** (Segoe UI/DirectWrite) en een echte schaal van 125%/150%. De hoogte wordt nu uitgerekend op basis
  van de **echte** breedte en het **echte** font, op het moment van tonen, van resizen en van een nieuwe tekst. Ik
  verwacht daarom dat het op Windows ook klopt. Gezien heb ik het niet.
- **De duur van het verversen op Windows** met virusscanner of een netwerk- of OneDrive-map: hier 11 ms voor 150
  hoofdstukken, met warme schijfcache. Op een trage of gesynchroniseerde map kan dat meer zijn, al gebeurt het hooguit
  één keer per typpauze en alleen met het paneel open.
- **Een schermlezer:** dat de lijst na verversen opnieuw wordt voorgelezen, zou vervelend kunnen zijn. Dat heb ik niet
  gecontroleerd.

## Conclusie

**Groen.** Beide 🔴 uit ronde 92 zijn echt dicht, gecontroleerd via de echte route:
- de Meelezer-uitleg past bij het direct openen op 300 px, in alle 5 talen;
- de privacymelding staat volledig in beeld, met Begrepen eronder.

Ongedaan maken, Opnieuw, typen en plakken houden de Open punten-lijst actueel, met een nette debounce en zonder werk
als het paneel dicht is. Er blijft één 🟡 over: de lijst vergeet bij het verversen de selectie en de scrollpositie. Dat
is een kleine verbetering, geen blokkade. Wat mij betreft is deze ronde rond de paneeluitleg en Open punten afgesloten.
