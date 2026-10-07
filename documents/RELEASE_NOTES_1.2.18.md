# QuietWriter 1.2.18 — Centrale semantische inline-laag

Deze ontwikkelversie rondt een volgende fase van de `DocumentView`-refactor af.

## Veranderd

- Inline-opmaak wordt centraal vertaald naar zichtbare tekst-runs met semantische stijlen.
- DOCX, XHTML/EPUB en PDF hoeven de manuscriptmarkering daardoor niet meer zelf te ontcijferen.
- Afbeeldings- en scèneherkenning loopt verder via dezelfde centrale documentgrens.
- Een letterlijk ongepaard sterretje, bijvoorbeeld `*31623455`, blijft gewone zichtbare tekst.

Er is nog geen nieuwe escaping-syntax actief. Bestaande hoofdstukken worden niet gemigreerd of genormaliseerd.

Geautomatiseerde suite vóór verpakking: 532 passed, 45 skipped, 304 subtests passed.
