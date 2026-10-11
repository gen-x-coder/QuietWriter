# QuietWriter 1.3.0-dev.23

Deze ontwikkelbuild polijst de in dev.22 geïntroduceerde Planning-overlay zonder de Planningworkflow of opslag te veranderen.

De knop **Planning** naast Tekstbreedte is nu een echte toggle: een tweede klik sluit de overlay betrouwbaar, terwijl Escape en klikken buiten de overlay de knopstatus weer netjes terugzetten. De overlay schaalt mee met het editorvenster en gebruikt maximaal ongeveer de helft van de editorbreedte, zodat scènes en synopses beter leesbaar zijn zonder het manuscript te overnemen.

Zichtbare scènestatussen zijn consequent titelcased: **Idee**, **Uitgewerkt** en **Geschreven**, zowel in de dropdown als in Planninghulp en overlay. De opgeslagen waarden blijven bewust de bestaande lowercase waarden (`idee`, `uitgewerkt`, `geschreven`), dus het Planning-opslagformaat verandert niet.

De scrollbar van de hoofdstukkenlijst gebruikt nu niet alleen de scrollbarbasis, maar ook groove en lege trackdelen in dezelfde pagina-achtergrond. Daardoor blijft er bij lange boeken geen witte strook meer zichtbaar.

`library.json`, manuscriptbestanden en `planning/outline.json` zijn inhoudelijk en qua schema ongewijzigd.

README.md en README_EN.md zijn bewust niet gewijzigd.
