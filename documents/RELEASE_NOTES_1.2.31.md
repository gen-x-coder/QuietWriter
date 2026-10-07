# QuietWriter 1.2.31 — finale hardening van de manuscriptarchitectuur

Deze ontwikkelversie verwerkt het laatste gerichte hardeningblok uit de onafhankelijke review van 1.2.30. De architectuur zelf blijft ongewijzigd: platte QuietWriter-tekst, DocumentView als centrale interpretatie en één serializeergrens.

De belangrijkste correctie zit in de eenmalige syntaxmigratie. Boeken die al met de escape-aware editor uit 1.2.19–1.2.29 zijn bewerkt worden niet opnieuw herschreven. Echte oudere boeken krijgen alleen de minimale backslashaanpassingen die nodig zijn om dezelfde zichtbare tekst te behouden; een zeldzaam dubbelzinnig geval vraagt expliciet om een keuze en maakt altijd eerst een herstelcheckpoint.

Verder zijn structurele escapes bij gewone editorbewerkingen gehard, Shift+Enter is weer een echte soft break, vervanging over een opmaakgrens kan geen losse Markdownmarker meer achterlaten en twee resterende DOCX-verliesgevallen zijn afgedekt.

Na een volledige PySide6/Qt-eindcontrole is deze lijn bedoeld om de grote manuscriptrefactor af te sluiten.
