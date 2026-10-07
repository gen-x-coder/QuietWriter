# QuietWriter 1.2.24

## DOCX-afbeeldingen

DOCX-import kan nu PNG- en JPEG-afbeeldingen meenemen naar de boeklokale mediastore. De import blijft transactioneel: tekst en media worden volledig in staging opgebouwd voordat het boek zichtbaar wordt.

- Word-afbeeldingen worden neutraal gelezen en pas bij boekimport als QuietWriter-media opgeslagen.
- Alt-tekst wordt behouden waar Word die beschikbaar stelt.
- Dubbele binaire afbeeldingen worden gededupliceerd.
- Inline Word-afbeeldingen worden als losse manuscriptblokken geïmporteerd met een duidelijke waarschuwing.
- Niet-ondersteunde afbeeldingsformaten worden gemeld in plaats van stil verloren te gaan.
