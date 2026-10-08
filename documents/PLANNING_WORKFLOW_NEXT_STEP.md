# Planningworkflow — gerealiseerd in 1.3.0-dev.22

## Vastgelegd

- Planning blijft de bron; manuscript en Planning blijven gescheiden.
- Scènes hebben al een bestaande status: `idee`, `uitgewerkt`, `geschreven`. Er komt dus geen tweede klaar/afvinkveld.
- De schrijver bepaalt zelf wanneer een scène geschreven is; QuietWriter probeert dat niet automatisch uit manuscripttekst af te leiden.
- Een geschreven scène blijft in Planning zichtbaar.
- De bestaande ghostlaag blijft presentation-only.

## Gerealiseerd in dev.22

1. Status is een vaste dropdown in scènebewerking; vanuit de editor-overlay kan een open scène met één klik op `Klaar` naar `geschreven`. Terugzetten blijft bewust in Planning.
2. Geschreven scènes visueel rustig markeren zonder ze te verbergen.
3. Naast de Tekstbreedte-keuze in de editor een subtiele knop `Planning tonen`.
4. De knop toont tijdelijk een overlay met de aan het huidige hoofdstuk gekoppelde scènes, inclusief status.
5. De overlay moet ook werken als het hoofdstuk al manuscripttekst bevat.
6. Open/niet-geschreven scènes krijgen de nadruk; geschreven scènes blijven als voltooid zichtbaar.
7. De overlay verandert niets aan manuscript, woordtelling, zoeken, export, AI-context of Undo.
8. Geen automatische scene-herkenning, voortgangspercentages, streaks of meldingen.

## Na Windows-acceptatie nog te beoordelen

- of de subtiele tekstknop `Planning` visueel precies goed is;
- overlaypositie, breedte en maximale hoogte op 100/125/150% DPI;
- of het natuurlijke Qt-popupgedrag (Escape/klik buiten sluit) voldoende rustig voelt.
