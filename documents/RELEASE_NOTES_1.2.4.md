# QuietWriter 1.2.4

## Nieuw

- **Open punten** voor tekst die je later wilt aanvullen. Selecteer tekst of plaats de cursor, voeg eventueel een notitie toe en vind alle open punten terug in het rechterpaneel.
- QuietWriter legt bij het eerste open punt expliciet uit dat deze functie bedoeld is in plaats van eigen `XXX`, `TODO` of `???`-markeringen.
- Gewone exports bevatten alleen de zichtbare tekst; de technische open-puntmarkeringen worden verwijderd. De exportcontrole waarschuwt zolang er open punten zijn en kan het overzicht direct openen.
- **Duits, Frans en Spaans** toegevoegd als volledige interfacetalen naast Nederlands en Engels.
- Themawissels verversen nu ook de itemkleuren van Voorwerk/Achterwerk en **wijzig**, zodat onder meer Lamplicht overal dezelfde themakleuren gebruikt.

## Veiligheid en compatibiliteit

Open punten gebruiken QuietWriter-commentaar in de bestaande Markdownbron. Vanaf 1.2.5 bevat die marker alleen een id en staan notities apart in `planning/open_points.json`. QWBOOK en Versiegeschiedenis bewaren beide; publicatie-exports en AI-context laten de technische markers weg.
