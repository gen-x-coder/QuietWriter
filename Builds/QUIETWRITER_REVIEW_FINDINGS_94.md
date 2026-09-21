# QuietWriter: reviewronde 94 (1.2.12, Open punten behoudt selectie en scrollpositie)

**Getest (Linux, Python 3.13, PySide6, offscreen):**
- de diff ten opzichte van 1.2.11: de enige codewijziging is `quietwriter/ui/open_points_panel.py` (`refresh`). Verder
  zijn er de nieuwe test `test_open_points_1212_qt.py`, de versie- en metadatabestanden, de CHANGELOG en de release notes;
- de volledige suite (inclusief Qt), de undefined-names-check (pyflakes), `check_locales.py` en `--smoke-test`;
- **de echte route via `MainWindow`**, met een boek van 150 hoofdstukken (1 open punt per hoofdstuk) en het paneel
  Open punten open. Ik heb geselecteerd met het toetsenbord (End en 9× pijl omhoog), daarna getypt in de editor met een
  wachttijd van 400 ms, Ctrl+Z en Ctrl+Y gebruikt, een punt toegevoegd boven de selectie, Enter op een rij gegeven, de
  technische markering geprobeerd te verwijderen, **Open punt afronden** op het geselecteerde punt gebruikt, het paneel
  dicht- en weer opengeklapt en van boek gewisseld;
- het paneel los (zonder MainWindow) in 5 scenario's: met en zonder selectie, en met de selectie buiten beeld
  gescrold.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Testresultaten

| Run | Resultaat |
|---|---|
| `tools/check_undefined_names.py` | ✅ OK |
| `tools/check_locales.py` | ✅ OK: 1503 sleutels in 5 talen |
| `pytest` (volledig, inclusief alle Qt-tests) | ✅ **620 geslaagd**, 0 fouten, 304 subtests (de nieuwe 1212-Qt-test draait hier wél mee en slaagt) |
| `--smoke-test` | ✅ rc 0 |
| ZIP | ✅ schoon (geen `__pycache__`, `.pyc` of instellingen) |

## De echte route: grotendeels groen

| Stap (150 hoofdstukken, selectie op rij 140, gescrold tot onderaan) | Selectie | Scroll | Sprong naar editor |
|---|---|---|---|
| Typen in de editor + debounce | ✅ 140 | ✅ 139 → 139 | ✅ geen |
| Ctrl+Z / Ctrl+Y | ✅ 140 | ✅ | ✅ geen |
| Nieuw open punt **boven** de selectie (rij erbij) | ✅ volgt het punt (140 → 141) | ✅ | ✅ geen |
| Ctrl+Z van dat nieuwe punt | ✅ terug naar 140 | ✅ | ✅ geen |
| Enter op een rij (naar een ander hoofdstuk) | ✅ blijft 140 | ✅ | ✅ precies 1, zoals bedoeld |
| Markering wissen (wordt geweigerd met een melding) | ✅ | ✅ | ✅ geen |
| Paneel dicht en weer open | ✅ | ✅ | ✅ geen |
| **Open punt afronden** op het geselecteerde punt | ✅ −1 (het punt is weg) | 🔴 **139 → 64** | ✅ geen |
| **Wisselen van boek** (van 150 naar 60 punten) | ✅ −1 | 🟡 **opent op 49/49 (onderaan)** | ✅ geen |

Het `blockSignals`-gedeelte werkt: tijdens het verversen is er nergens een `openPointRequested` gevuurd. De selectie
wordt teruggezet op basis van `(chapter_id, point_id)` en niet op rijnummer. Daardoor gaat het ook goed als er boven de
selectie een rij bijkomt. Netjes.

---

## Bevindingen

### 1. 🔴 Na een synchrone refresh springt de lijst toch terug (139 → 64), bijvoorbeeld bij Open punt afronden

Dit is dezelfde sprong als in ronde 93 (ook toen 139 → 64). Hij komt nog voor zodra er na het verversen **geen** rij
geselecteerd wordt.

**Oorzaak:** `QListView` legt nieuwe items lui (uitgesteld) neer. `refresh()` doet `clear()` en `addItem()`, en zet
daarna direct `verticalScrollBar().setValue(min(scroll_value, maximum()))`. Op dat moment is `maximum()` nog de
**verouderde** waarde van 64. Daardoor wordt 139 afgekapt tot 64. Mijn trace:

```
refresh enter: cur 140 scroll 139 / 139
valueChanged -> 64        (in self.list.clear())
refresh exit : cur -1 scroll 64 / 64      ← maximum nog niet bijgewerkt
volgende refresh: scroll 64 / 138         ← maximum klopt pas nu, maar de waarde is al kwijt
```

Als er wel een selectie is, maskeert `setCurrentRow()` het probleem. Die roept `scrollTo()` aan, en dat dwingt de
lay-out af. Daarom slaagt de test in 1.2.12 wel: die heeft altijd een selectie.

**Waar je het merkt:** precies na **Open punt afronden**. Dat is de meest logische actie in een lijst met open punten:
je werkt de lijst van onder naar boven af, rondt een punt af en staat daarna weer halverwege. Hetzelfde geldt voor
elke synchrone `refresh_open_points()` waarbij het geselecteerde punt verdwijnt.

**Oplossing (getest):** dwing de lay-out af vóór het terugzetten:

```python
self.list.doItemsLayout()
self.list.blockSignals(True)
...
```

Met deze regel wordt het resultaat 139 → **138**. Dat is het nieuwe maximum, omdat er een rij minder is.

### 2. 🟡 Bij het wisselen van boek wordt de scrollpositie van het vorige boek meegenomen

`refresh()` onthoudt de scrollwaarde zonder te kijken of het om hetzelfde boek gaat. Zat je in boek A onderaan, dan
opent de Open punten-lijst van boek B ook onderaan (49/49). Bij een ander boek hoort de lijst bovenaan te beginnen.

**Oplossing (getest):**

```python
same_book = (self.book is not None and book is not None
             and getattr(self.book, 'id', None) == getattr(book, 'id', None))
self.book = book
...
scroll_value = self.list.verticalScrollBar().value() if same_book else 0
```

(De selectie heeft dit probleem niet: de sleutel bevat het `chapter_id`, en dat bestaat in een ander boek niet.)

### Patch en test (bijgeleverd)

- `open_points_panel_1213.diff`: beide fixes samen (6 regels). Met deze patch is de volledige suite nog steeds groen:
  **620 geslaagd**.
- `test_open_points_1213_qt.py`: twee Qt-regressietests via `MainWindow`:
  - het geselecteerde punt afronden in een boek van 150 hoofdstukken, waarna de scrollpositie behouden moet blijven;
  - wisselen van boek, waarna de lijst bovenaan moet staan.

  **Beide falen op 1.2.12 en slagen met de patch.**

---

## Niet getest (expliciet)

- **Windows zelf** en een echte schaal van 125%/150%. Het lui neerleggen van `QListView` is platformonafhankelijk,
  dus ik verwacht bevinding 1 daar ook. Gezien heb ik het niet.
- **Muiswiel en scrollbalk slepen tijdens de debounce van 300 ms.** Dat heb ik niet met echte invoer gedaan, alleen via
  `setValue`.
- **Een schermlezer:** of het terugzetten van de selectie met `blockSignals` een dubbele aankondiging geeft of juist
  geen, heb ik niet gecontroleerd.
- **Notitie wijzigen** (`edit_current_open_point_note`) gebruikt hetzelfde synchrone pad als afronden. Ik verwacht
  daar hetzelfde gedrag, maar dat heb ik niet apart doorlopen.

## Conclusie

**Bijna groen: 1 🔴 en 1 🟡, allebei klein en met een geteste patch.** De aanpak uit 1.2.12 klopt: herstel op basis
van een sleutel, `blockSignals` en het begrenzen van de scrollwaarde. Typen, Ongedaan maken, Opnieuw, invoegen boven de
selectie en Enter houden de lijst nu stil.

Alleen in het geval zonder selectie na het verversen zet de scrollpositie terug tegen een verouderd maximum. Dat
gebeurt precies bij Open punt afronden. Met `doItemsLayout()` plus de controle op hetzelfde boek (1.2.13) en de twee
bijgeleverde tests is de serie rond Open punten, paneeluitleg en HiDPI-polish wat mij betreft af.
