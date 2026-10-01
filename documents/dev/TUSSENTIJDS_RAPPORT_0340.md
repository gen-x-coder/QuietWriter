# Tussentijds rapport 0.34.0

## Gebouwd
- Door Lucas gemelde dubbele railselectie gerepareerd met één expliciete QButtonGroup over alle linkerrailknoppen.
- Programmatic navigation scrolt het actieve railitem automatisch in beeld.
- Eerste slice van **In dit hoofdstuk** als zelfstandig rechterpaneel.
- Pure `build_chapter_context`-builder; opgeslagen Planning is de enige bron.
- Scènes/personages alleen-lezen, verweesde personages stil overgeslagen.
- Paneel onafhankelijk van AI; verborgen bij publicatie, history-preview en corrupte hoofdstukken.
- Corrupte Planning geeft alleen een lokale foutmelding in het paneel.

## Lokale tests
- Nieuwe pure contextbuildertest groen.
- Nieuwe Qt-runtimeproeven zijn toegevoegd maar worden in deze omgeving overgeslagen.
- Volledige lokale suite: 579 geslaagd + 280 subtests; 34 Qt-runtimetests overgeslagen; alleen de 2 bekende ontbrekende fontresource-tests falen.

## Reviewfocus
Echte PySide6 is essentieel voor railselectie, rechterpaneelgedrag en layout/DPI. Zie `REVIEW_NOTES_0340.md`.
