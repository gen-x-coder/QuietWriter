# QuietWriter 1.2.20

Crashfix voor de eerste escaping-invoerlaag.

- De editor importeert nu alle vier benodigde escapinghelpers.
- Gewoon typen, plakken en kopiëren kunnen daardoor de nieuwe letterlijke-invoerlogica gebruiken zonder `NameError`.
- Geen wijziging aan bestaande manuscriptbytes of het boekformaat.
- De DocumentView-architectuur uit 1.2.18/1.2.19 blijft ongewijzigd.
