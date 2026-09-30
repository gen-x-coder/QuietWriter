# Vertaal-audit 0.35.0 — nulmeting

Deze nulmeting is bewust nog geen productwijziging. De vertaalpass volgt in 0.35.x.

## Resultaat tegen de 0.34.10/0.35.0-code

- `nl.json` en `en.json` bevatten dezelfde historische basisset.
- Er worden momenteel **74 `tr()`-sleutels** in Python gebruikt die nog niet expliciet in de locale-bestanden staan. De UI werkt doordat iedere aanroep een Nederlandse fallbacktekst bevat, maar in de Engelse interface blijven die plekken daardoor Nederlands.
- Daarnaast bestaan nog hardgecodeerde gebruikersstrings buiten `tr()`. De releasepass moet die systematisch verwijderen; het AI-paneel en enkele rechterpanelen verdienen extra aandacht.

## Gate die in de vertaalpass wordt toegevoegd

1. Een test die alle letterlijke `tr('key', ...)`-sleutels uit de Pythonbron verzamelt en eist dat ze in **beide** locale-bestanden staan.
2. Een AST-test voor zichtbare tekst in onder meer `QLabel`, `QPushButton`, `setText`, `setToolTip` en `setPlaceholderText`, met een kleine expliciete allowlist voor technische/niet-gebruikersgerichte strings.
3. Een handmatige Engelse schermrondgang, in het bijzonder: rechter werkbalk, Boekdetails, Boekprofiel en AI.

De nulmeting voorkomt dat 1.0 met een gedeeltelijk Nederlandse Engelse UI wordt uitgebracht zonder dat we de bestaande tweetalige architectuur hoeven te vervangen.
