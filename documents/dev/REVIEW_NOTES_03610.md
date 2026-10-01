# Review notes 0.36.10

Fix-only ronde onder feature freeze richting 1.0.0-rc1.

Te controleren door Claude:
- OpenRouter free-only: opgeslagen gratis én betaald model blijven behouden na herstart als de catalogus nog niet is opgehaald en alleen een andere instelling wordt opgeslagen.
- Na catalogusrefresh filtert free-only wel degelijk betaalde modellen uit de zichtbare lijst; expliciete `:free`-modellen blijven behouden.
- Lange boektitels rekken de minimumvensterbreedte niet meer op; met Meelezer open en 66 tekens titel blijft minimumSizeHint <= 1100 px.
- Tekstbreedtecombo is compact maar de vijf presets blijven intact en globaal.
- LEESMIJ staat naast de exe en heeft UTF-8 BOM.
- Undefined-name checker, current, current Qt, legacy en legacy Qt allemaal draaien.
