# QuietWriter — regels voor ontwikkelaars en AI-assistenten

QuietWriter is een lokale, portable Windows-schrijfapp voor boeken (Python 3.12, PySide6). Dit bestand is kort met opzet: lees het helemaal voordat je iets verandert. Achtergrond staat in `documents/`, de geschiedenis in `documents/archive/`.

## Werkwijze (vanaf 1.5.1)

- **Claude bouwt, ChatGPT reviewt, Lucas test op Windows en beslist.** Een bouwronde levert één bron-zip met de juiste versie in `quietwriter/__init__.py`, een groene testsuite en één reviewbestand `documents/review/REVIEW_REQUEST_<versie>.md`. Daarin staat wat er veranderde (met bestandsnamen), wat getest is en **wat níét getest kon worden**.
- Een reviewer verandert geen productcode. Hij levert bevindingen met bestand, regel, reproductie en voorstel.
- Na acceptatie gaat het reviewbestand naar `documents/archive/dev-overdrachten/`.
- Versies: `x.y.z` voor wat Lucas uitbrengt. Geen lange `-dev.N`-reeksen meer; liever kleine patchversies.
- **Zipnamen:** elke oplevering krijgt een eigen naam, `QuietWriter-<versie>-devN.zip` (dev1, dev2, …), zodat Lucas ze allemaal kan bewaren. De versie in de app blijft `x.y.z` tot Lucas een nieuwe versie start.

## Productregels die boven gemak gaan

1. **Blijf schrijven.** Niets onderbreekt de schrijver midden in een zin: geen pop-ups, geen modale keuzes tijdens typen, geen meldingen die om aandacht vragen.
2. **Minder interface.** Een nieuwe functie moet schrijven, plannen, reviseren of afronden merkbaar beter maken. Bij twijfel: niet bouwen.
3. **Lokaal en van de schrijver.** Geen account, geen verplichte cloud, geen manuscriptinhoud naar buiten zonder een bewuste actie van de gebruiker.
4. **De AI is een Meelezer.** Ze analyseert en geeft feedback, maar schrijft geen proza voor het manuscript en schrijft nooit zelf naar Boekgeheugen.
5. **Eenvoudig, niet technisch, portable.** Uitpakken en starten. Geen installer die beheerdersrechten vraagt, geen technische keuzes voor de gebruiker.
6. **Eén computer is de norm.** Veel schrijvers gebruiken geen Dropbox of tweede computer. Elke functie moet zonder synchronisatie volledig werken; synchronisatie is een extra waar we veilig mee omgaan, nooit een voorwaarde.

## Datawetten

- **Markdown blijft de manuscriptbron** (zie `documents/MANUSCRIPT_SYNTAX.md`). Geen nieuw opslagformaat zonder expliciete migratie, herstelpunt en toestemming.
- **Niets gebeurt stil.** Geen stille reparatie, migratie, overschrijving of verwijdering van gebruikersdata.
- Externe wijzigingen (Dropbox, tweede computer) worden nooit overschreven. Corrupt is niet leeg; een nieuwer formaat is niet corrupt.
- Schrijf een bestand alleen als de inhoud echt veranderde. Schrijf altijd atomair: tijdelijk bestand, fsync, `os.replace`. Gebruik `storage.py` en voeg geen eigen schrijfroutes toe.
- Tekst die weggaat moet terug te vinden zijn (Bewaarplaats, prullenbak, geschiedenis), en de UI zegt waar hij heen ging.
- Weergave is geen inhoud: zoekmarkering, spelling, Planninghulp en thema's komen nooit in het manuscriptbestand.
- Geen verborgen markers of ID's in het manuscript. Koppelingen tussen Planning en tekst lopen via de volgorde (scène *n* = stuk tekst na scènebreuk *n*, zie `documents/design/SCENES_IN_TEXT_DESIGN.md`).
- Planning-JSON: onbekende velden van een nieuwere versie altijd ongewijzigd terugschrijven (`planning_models.extra`).
- Boeken, instellingen en logs staan **buiten** de programmamap (`workspace_path.py` bewaakt dat). Velopack vervangt bij een update de hele programmamap.

## Waar zit wat

| Gebied | Bestanden |
|---|---|
| Opstarten | `main.py` (Velopack-hook eerst), `quietwriter/app.py` |
| Opslag en veiligheid | `storage.py`, `revisions.py`, `integrity.py`, `workspace_path.py`, `automatic_backups.py`, `qwbook_io.py` |
| Manuscript | `document_view.py`, `manuscript_markup.py`, `manuscript_syntax.py`, `ui/manuscript_editor.py`, `ui/editor_page.py` |
| Planning | `planning_*.py`, `ui/planning/` |
| Export en import | `exporting/`, `docx_io.py`, `import_document.py` |
| Meelezer (AI) | `ai/` |
| Updates | `update_checker.py` (alleen melden, voor bron- en oude builds), `self_update.py` (Velopack) |
| Navigatie en hoofdvenster | `ui/main_window.py`, `ui/rail_model.py` |
| Vertalingen | `locales/*.json` (nl, en, de, fr, es), `i18n.py` |

## Bij elke wijziging

- **Teksten:** altijd `tr('sleutel', 'Nederlandse standaardtekst')`, en de sleutel in alle vijf de `locales/*.json`. Daarna `python tools/check_locales.py`.
- **Dialoogknoppen:** eigen vertaalde knoppen, geen Qt-standaard OK/Cancel.
- **Tests:** draai als bouwer alleen de tests van wat je net maakte of raakte (offscreen: `QT_QPA_PLATFORM=offscreen`). Lucas draait de volledige suite zelf (`python -m pytest tests/current -v`) en geeft de uitvoer door als er iets faalt. Noem in het reviewverzoek welke tests je draaide. Draai ook `python tools/check_undefined_names.py`. Een test die een oude toestand vastpint, pas je aan met een reden in de commit. Verwijder geen test om groen te krijgen.
- **Updates:** alleen `self_update.py` mag Velopack aanroepen. Bijwerken pas na een expliciete keuze van de gebruiker, en via het normale afsluitpad (`MainWindow.close()`), zodat alles eerst wordt opgeslagen.
- **Afhankelijkheden:** nieuw pakket betekent `requirements.txt`, `packaging/requirements-runtime.lock` en `documents/licenses/THIRD_PARTY_LICENSES.md`.
- **Documentatie:** werk `documents/CHANGELOG.md` bij. Geen nieuwe losse statusdocumenten in `documents/`; geschiedenis hoort in `documents/archive/`.

## Wat we bewust niet bouwen

Een AI-ghostwriter of "herschrijf selectie", een eigen updater of installer, Enter-Enter-Enter voor structuur, een coverdesigner of DTP-editor, een mobiele app, autonome Boekgeheugen-writes, of een tweede, losse hoofdstukvolgorde naast het manuscript.
