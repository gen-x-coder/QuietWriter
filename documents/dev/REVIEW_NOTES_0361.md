# QuietWriter 0.36.1 — review notes

## Doel

First-run en twee volledig gescheiden runtimeprofielen bovenop de schone portable-build uit 0.36.0.

## Verplichte runs

```text
pytest
pytest -m qt
pytest tests/legacy
pytest tests/legacy -m qt
python main.py
```

## Runtimecontroles voor Claude

1. Bestaande productieomgeving: start normaal met `QuietWriter.exe`; **geen wizard** en bestaande boeken/instellingen blijven zichtbaar.
2. Nieuwe dev-omgeving: start `QuietWriter.exe --profile dev`; wizard verschijnt exact één keer en standaardwerkmap is `~/QuietWriter-Dev`.
3. Start dev daarna opnieuw; wizard verschijnt niet opnieuw.
4. Start `QuietWriter.exe --profile dev --first-run`; wizard verschijnt opnieuw, bestaande waarden zijn vooraf ingevuld en **Overslaan reset niets**.
5. Controleer de vier wizardstappen, Vorige/Volgende/Overslaan/Voltooien en sluiten met X. Sluiten met X mag bestaande instellingen niet wijzigen.
6. Kies in dev Engels + ander thema + afwijkende werkmap; na Voltooien moet het eerste hoofdvenster die taal/thema gebruiken.
7. AI: nieuwe gebruiker begint op Geen AI. Ollama mag tijdens startup niet worden benaderd als AI uit staat.
8. Spelling: nl_NL moet in de portable build beschikbaar zijn; gevonden systeemwoordenboeken mogen erbij staan.
9. Profielisolatie: verander thema/werkmap in dev en controleer dat productie onaangeroerd blijft.
10. Venstertitel dev bevat `QuietWriter — DEV`; productie alleen `QuietWriter`.
11. Bouw opnieuw met `build_exe.cmd`; controleer dat `QuietWriter DEV.cmd` en `QuietWriter PROD.cmd` in de portable releasemap staan en naar dezelfde exe wijzen met verschillende profielargumenten.
12. Controleer dat PPM/tests/reviewbestanden nog steeds niet in de portable release terechtkomen.

## Verwachte Windows-opslag

- Productie QSettings: `HKEY_CURRENT_USER\Software\QuietWriter\QuietWriter`
- Dev QSettings: `HKEY_CURRENT_USER\Software\QuietWriter\QuietWriter-Dev`
- Productiewerkmap standaard: `%USERPROFILE%\QuietWriter`
- Devwerkmap standaard: `%USERPROFILE%\QuietWriter-Dev`

De gebruiker hoeft voor first-run-tests niets in het register te verwijderen; gebruik bij voorkeur `--profile dev --first-run`.

## Lokale assistant-runs

- current: 228 passed, 17 skipped
- current `-m qt`: 25 passed, 17 skipped, 203 deselected
- legacy: 426 passed, 24 skipped, 284 subtests passed
- legacy `-m qt`: 66 passed, 24 skipped, 360 deselected
- `compileall`: groen

Echte PySide6-runtime en Windows-exe moeten door Claude/Lucas worden getest.
