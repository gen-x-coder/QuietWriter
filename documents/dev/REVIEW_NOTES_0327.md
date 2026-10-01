# QuietWriter 0.32.7 — reviewronde 33

0.32.7 verandert bewust geen productgedrag. Deze build hardent uitsluitend de tests na de bevindingen uit reviewronde 32.

## Verplicht

1. Draai de volledige suite met echte PySide6. Verwacht geen hangende QMessageBox.
2. Controleer dat `tests/test_code_health_0327.py` groen is op 0.32.7 en rood wordt wanneer in een tijdelijke kopie van een functie code direct achter een onvoorwaardelijke `return` wordt gezet.
3. Controleer specifiek dat de 0.32.4-vorm van `ManuscriptEditor.source_text()` door de nieuwe generieke test wordt gevangen.
4. Forceer in minstens één Qt-test een onverwachte `QMessageBox.information(...)` en een onverwachte `QMessageBox(...).exec()`; beide moeten direct als AssertionError eindigen, niet hangen.
5. Draai koude start en een korte smoke van hoofdstuk/notities/publicatietekst om te bevestigen dat productgedrag identiek aan 0.32.6 blijft.

## Regressie

- Alle bekende regressiereeksen blijven op de basislijn van 0.32.6.
- Alleen de twee bekende fonttests mogen falen wanneer de fontresources ontbreken.

## Let op

De centrale dialogenfixture staat in `tests/conftest.py`. Een test die bewust een dialoog simuleert mag de relevante QMessageBox-methode lokaal opnieuw monkeypatchen.
