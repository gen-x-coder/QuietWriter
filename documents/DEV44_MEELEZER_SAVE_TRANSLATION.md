# QuietWriter 1.5.0-dev.44 — knoppen gesprek bewaren

De titelvraag bij **Meelezer > Bewaren** gebruikte `QInputDialog.getText` en liet op Windows standaard Engelse knoppen zien. De actie gebruikt nu de bestaande gedeelde `prompt_text`-dialoog uit `quietwriter.ui.dialogs`, met vertaalde **Opslaan**- en **Annuleren**-knoppen. Verder geen gedragswijzigingen.

Controle: `python -m compileall -q quietwriter/ai/ui.py`; `python -m pytest -q tests/current/test_meelezer_manual_archive_dev42.py` (3 geslaagd).

Visuele Windows-test: start een gesprek, klik Bewaren, controleer knopvertalingen, annuleer en heropen; bewaar daarna het gesprek en controleer Gesprekken.
