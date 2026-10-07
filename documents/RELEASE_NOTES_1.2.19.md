# QuietWriter 1.2.19 — Letterlijke invoer en escaping-basis

Deze ontwikkelversie introduceert de eerste echte syntaxverbetering bovenop de nieuwe `DocumentView`.

## Wat verandert voor de schrijver

Gewone tekst blijft voortaan gewone tekst, ook wanneer die toevallig op Markdown lijkt. Voorbeelden:

- `de man tikte *31623455 in`;
- `Prijs: 5*3 = 15`;
- `- Kom je mee?`;
- `1944. Het was een koude winter.`

QuietWriter kan intern een backslash opslaan om de bedoeling ondubbelzinnig te maken. Die technische backslash is niet bedoeld om zichtbaar te zijn in de editor of export.

## Expliciete opmaak blijft werken

Ctrl+B, Ctrl+I, Ctrl+U en de opmaak-/blockacties maken nog steeds echte semantische opmaak. De nieuwe escaping is voor gewone getypte of geplakte proza, niet voor expliciete formatteringsacties.

## Compatibiliteit

Bestaande hoofdstukken worden niet herschreven. Er is geen bulk- of stille migratie. De nieuwe syntax ontstaat alleen door nieuwe letterlijke invoer/plakacties of is al expliciet aanwezig in de bron.

## Testfocus

Omdat dit voor het eerst het typgedrag en de opgeslagen bron bij nieuwe invoer wijzigt, is een gerichte Windows-GUI-test nodig voordat deze stap als stabiele tussenbaseline geldt.
