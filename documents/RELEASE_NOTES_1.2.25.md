# QuietWriter 1.2.25 — Escaping gehard na onafhankelijke review

- Verborgen escapeparen worden in de editor als één zichtbare eenheid behandeld voor cursor, Backspace en Delete.
- Gewone bewerkingen zoals Delete, Backspace en Enter mogen niet stil een lijst, tussenkop, citaat, scènebreuk of afbeeldingsblok creëren.
- Intern kopiëren/plakken bewaart QuietWriter-opmaak via een eigen MIME-type; het gewone klembord bevat alleen zichtbare schrijverstekst.
- Extern geplakte Markdownachtige tekst, inclusief een volledige afbeeldingsregel, blijft gewone tekst.
- Zoeken gebruikt een compacte zichtbare projectie met bron-offsetmapping en vindt nu tekst over escapes en opmaakgrenzen heen, zoals `5*3` en `was heel moe`.
- Zoek-en-vervang schrijft vervangtekst als letterlijke schrijverstekst en laat geen wees-escapes achter.
- `DocumentView` splitst uitsluitend op fysieke `\n`-alineagrenzen; Shift+Enter/U+2028 blijft binnen dezelfde manuscriptalinea.
- Expliciete opmaak gebruikt `source_text()` zodat onder andere non-breaking spaces niet stil genormaliseerd worden.
- Getypte Open-puntsyntax met een escape wordt niet als beheerde marker geïnterpreteerd.
- De leesgrammatica voor structurele escapes is versmald naar echte regelprefixposities; midden-in-proza `\.`, `\-`, `\#` en `\>` blijven letterlijk.
- Regressietests toegevoegd voor zichtbare zoekprojectie, letterlijke structuur, U+2028 en Qt-editorbewerkingen.
- Geen bestaande boeken gemigreerd of herschreven.
