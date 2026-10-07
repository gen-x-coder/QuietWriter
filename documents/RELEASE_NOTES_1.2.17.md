# QuietWriter 1.2.17 — DocumentView als gedeelde manuscriptlezer

Deze ontwikkelversie trekt de centrale manuscriptinterpretatie verder door zonder het opslagformaat te wijzigen.

## Veranderd

- XHTML/EPUB gebruikt `DocumentView` voor blocksemantiek.
- Publicatie-inhoudsopgave gebruikt dezelfde heading-interpretatie.
- Afbeeldingsblock-ranges en blockopmaak gebruiken de centrale laag.
- Zichtbare inline-tekst wordt via één gedeelde helper afgeleid.

Er is geen nieuwe syntax toegevoegd en bestaande manuscripten worden niet gemigreerd of genormaliseerd.

Geautomatiseerde suite vóór versie-update: 529 passed, 45 skipped, 304 subtests passed.
