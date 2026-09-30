# Tussentijds rapport — QuietWriter 0.32.3

## Aanleiding
Reviewronde 28 verklaarde 0.32.2 functioneel groen, maar vond twee resterende tekstintegriteitspunten voor hoofdstukken met Qt-gevoelige Unicode-tekens:

1. de clean-baseline was ruwe schijftekst terwijl dirty-detectie `toPlainText()` gebruikte;
2. gewone saves gebruikten `toPlainText()` en konden harde spaties en U+2028 normaliseren.

## Oplossing
`EditorPage` heeft nu één centrale bronfunctie:

- `document().toRawText()` bewaart de typografische bronkarakters die `toPlainText()` normaliseert;
- Qt's interne alineascheiding U+2029 wordt teruggezet naar `\n` voor de QuietWriter-bronbestanden.

Diezelfde bronrepresentatie wordt gebruikt voor:

- `_clean_text` direct na laden;
- dirty-detectie;
- gewone hoofdstuk-save;
- lokale tekst in de externe-conflictflow;
- de actuele hoofdstuktekst in zoeken/vervangen waar bron-offsets relevant zijn.

Daardoor vergelijkt QuietWriter voortaan Qt-met-Qt en schrijft het dezelfde editorbron die ook de clean-baseline bepaalt.

## Gedragsdoel
- Alleen openen/presentatieacties mogen een hoofdstuk met U+00A0/U+2028/U+2029/BOM niet dirty maken of herschrijven.
- Bij een echte wijziging blijven U+00A0 en U+2028 behouden.
- Gewone alinea's blijven als `\n` op schijf staan.

## Tests hier
Volledige suite in deze omgeving:

- 564 geslaagd;
- 280 subtests geslaagd;
- 30 Qt-runtime-tests overgeslagen (PySide6 ontbreekt hier);
- alleen de 2 bekende fontresource-tests falen.

De nieuwe echte Qt-runtimeproeven staan in `tests/test_editor_source_text_0323.py` en in `REVIEW_NOTES_0323.md` voor Claude.

## Bewust niet meegenomen
Het bezoeken van Boekgeheugen/Boekprofiel kan nog een leeg sjabloonbestand materialiseren. Dat is genoteerd als latere polish; 0.32.3 blijft gericht op tekstbron-fideliteit.
