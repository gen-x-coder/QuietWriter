# QuietWriter 1.2.28 — DOCX-importhardening

Deze ontwikkelversie bouwt verder op de nieuwe DocumentView/ImportDocument-architectuur. De nadruk ligt op één regel: **zichtbare Word-tekst mag niet stil verdwijnen**.

## Wat is verbeterd

- Word soft breaks blijven als regeleinde binnen dezelfde QuietWriter-alinea behouden.
- Tabelinhoud wordt als leesbare tekst meegenomen wanneer echte tabelsemantiek nog niet wordt ondersteund.
- Veldresultaten, tracked insertions, content controls en tekstvaktekst worden waar mogelijk als gewone tekst behouden.
- Een corrupte ingebedde afbeelding stopt de hele import niet meer; de afbeelding wordt overgeslagen en QuietWriter meldt dit.
- Oude achtergelaten DOCX-stagingmappen worden veilig opgeruimd.

## Nog niet in deze versie

- Hyperlinkadressen worden nog niet als semantische links opgeslagen.
- Tabellen krijgen nog geen eigen QuietWriter-tabelsyntax.
- Word-layout, track-changesmetadata en veldlogica worden niet gereconstrueerd.

Bestaande QuietWriter-boeken worden niet gemigreerd of herschreven.
