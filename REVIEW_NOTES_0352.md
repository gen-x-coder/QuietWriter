# Review notes 0.35.2

## Doel van deze build

0.35.2 rondt de resterende releasefundamenten van 0.35 af: crash-cooldown op bronlocatie, vertaalgate, fontmanifest/CI en licentie-inventaris. Er zijn geen nieuwe schrijf- of AI-features toegevoegd.

## Verplicht door Claude met echte PySide6

Draai steeds:

```text
pytest
pytest -m qt
pytest tests/legacy
pytest tests/legacy -m qt
python main.py
```

De twee oude fonttests horen vanaf deze build **ook groen** te zijn; er is geen geplande fontuitzondering meer.

## Specifieke runtimechecks

1. **Crash-cooldown met wisselende tekst:** laat vanaf exact dezelfde code-regel vijf keer `RuntimeError(f"item {i}")` ontstaan. Na het sluiten van de eerste melding mag binnen de cooldown geen nieuw venster verschijnen. Het log moet alle vijf fouten bevatten. Een fout vanaf een andere code-regel moet wel als afzonderlijke bron kunnen worden gemeld.
2. Herhaal de 50× timerfout uit ronde 48: nog steeds maximaal één open crashvenster, teller correct.
3. Startfout vóór `app.exec()` blijft modaal zichtbaar nadat de splash is gesloten.
4. **Fontresources:** controleer dat `bundled_fonts()` vier families oplevert en dat de legacy-fonttests nu zonder uitzondering slagen. Indien internet beschikbaar is: draai `python tools/fetch_bundled_fonts.py` en controleer dat de acht TTF-bestanden worden opgehaald.
5. **Over → Licenties:** open QuietWriter-licentie, Licenties van derden en minstens één fontlicentie. Controleer zowel Nederlands als Engels.
6. **Engelse schermrondgang:** zet taal op Engels en klik alle primaire pagina's en rechterpanelen door. Extra aandacht: right rail, Book details, Book profile, Book memory, Writer persona, Planning, AI-context, Search en fout-/bevestigingsdialogen. Noteer elke Nederlandse resttekst.
7. Wissel terug naar Nederlands en controleer dat de functies nog hetzelfde gedrag hebben, vooral AI-contextbereik `chapter/section/book`.
8. CI-YAML: controleer dat Ubuntu/Windows vóór de suites `tools/fetch_bundled_fonts.py` uitvoeren en dat de Linux Qt-libraries behouden zijn.
9. First-run-document: bevestig dat een bestaande standaardwerkmap — ook leeg — voldoende is om de wizard bij migratie niet te tonen.

## Lokaal bij ChatGPT

- `pytest`: 204 geslaagd, 17 Qt-skips.
- `pytest -m qt`: 25 geslaagd, 17 skips.
- `pytest tests/legacy`: 426 geslaagd, 24 skips, 284 subtests. **Geen fontfailures meer.**
- `pytest tests/legacy -m qt`: 66 geslaagd, 24 skips.
- `compileall`: groen.

De echte Qt-runtime en een echte GitHub Actions-run kunnen hier niet worden bevestigd; dat is expliciet onderdeel van jouw review.
