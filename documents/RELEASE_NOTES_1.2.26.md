# QuietWriter 1.2.26 — Zichtbare tekst centraal en sneller typen

Deze ontwikkelversie bouwt voort op de escaping-hardening van 1.2.25. De schrijver-zichtbare tekstprojectie is verder gecentraliseerd en de belangrijkste snelle performancewinst uit de onafhankelijke 1.2.24-review is toegepast.

## Belangrijkste wijzigingen

- Full-text search-indexering gebruikt nu de compacte writer-visible projectie in plaats van een offsetmasker.
- De Bewaarplaats toont en filtert fragmenttekst via dezelfde zichtbare projectie, zodat interne markup niet in previews lekt.
- Woordtelling gebruikt centraal `DocumentView`-gedrag.
- AI-context behoudt echte nummers van genummerde lijsten.
- Woordtelling tijdens typen is 400 ms gedebounced, zodat lange hoofdstukken niet meer op iedere toets volledig worden geparset.
- De roadmap bevat bovenaan de nieuwe productrichting **Boekenkast met meerdere planken**, inclusief verborgen/privéplanken voor rustige demo- en privacyweergave.

Er is geen nieuwe manuscriptsyntaxis en er worden geen bestaande hoofdstukken gemigreerd.
