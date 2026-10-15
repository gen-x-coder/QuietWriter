# QuietWriter dev.32 — reviewoverdracht

**GEEN PRODUCTIE-GO.** De bron komt uit de volledige dev.31 ZIP, niet uit GitHub.
Het interne versienummer blijft voorlopig dev.28: wijzig dat pas bij een
gezamenlijke release-synchronisatie met alle versiepins en workflows.

## Gebouwd
- Wizard toont vertaalde waarschuwing en opent de woordenboekcatalogus zonder
  al een werkmap aan te maken.
- Pilotvertalingen in vijf talen; geen `.bak` in de distributie.
- Portable werkmapbescherming herkent bovenliggende root van `app-*`.
- Prototypestarter: snelle controle van inventarisbestanden op aanwezigheid en
  grootte; SHA-256 van EXE. Extra bestanden in de actieve map blokkeren starten
  niet. Dit is **geen authenticatie**.
- Twee pointer-slots `current.a.json` / `current.b.json` met seq en checksum;
  één beschadigd slot is overleefbaar. BOM wordt bij lezen toegestaan.
- Cross-process lab-lock voor pointerwissels; downgrade in lab en dubbele
  rollback worden geweigerd. De activeringsfunctie blijft lab-only.
- Starter handelt `Popen`-fouten af zonder ruwe traceback.
- Externe certificaatdienst uit de actieve release-instructies geschrapt.

## Nog expliciet open (productieblokkades)
1. Geen native Windows-starter-EXE; Python-prototype is NIET bedoeld voor users.
2. Geen offline productiesleutel, ondertekende versie-records, veilige staging
   of end-to-end transactie met pending/confirmed/blocked.
3. Geen OS- of proces-herstartprotocol / automatische back-up vóór formaatwijziging.
4. Geen Windows/Defender/USB-exFAT stroomuitvaltesten; geen handmatige pilotinstall.
5. `activate_staged` is een compatibiliteitslabfunctie, NIET te koppelen aan UI.
6. Productversie/build- en broncode-guards nog met publieke lijn reconciliëren.

## Reviewer: expliciet beoordelen
- Zijn beide pointer-slots voldoende bij corruptie en tegen gelijktijdige writers?
- Kloppen de starter-checks, incl. junction/hardlink/toctou en crashes?
- Treden geen bijwerkingen op vóór de wizard-/werkmapbeveiliging?
- Is er enige codeweg van proefmarker of updateknop naar installatiefunctie?
- Draai volledige pytest; draai de Claude harnassen `ud531.py` en `ui531.py`
  op kopieën en geef per bevinding GO/NO-GO.

## Testwaarneming van ChatGPT
Gerichte dev.31 + dev.32 startertests: 29 geslaagd. Volledige pytest begon
zonder F en bereikte circa 87%, maar liep vast binnen de lokale limiet.
**Geen volledige groene suite geclaimd.**
`check_source_assets.py` en `check_locales.py` groen; `check_undefined_names.py`
kon lokaal niet lopen omdat de optionele `pyflakes`-dependency hier ontbreekt.
