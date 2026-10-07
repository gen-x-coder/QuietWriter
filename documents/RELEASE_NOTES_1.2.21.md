# QuietWriter 1.2.21

Deze ontwikkelversie bouwt verder op de nieuwe `DocumentView`-architectuur. Niet alleen het lezen, maar ook het **genereren** van QuietWriter-manuscriptsyntax loopt nu via centrale helpers.

## Belangrijkste wijzigingen

- Letterlijke tekst wordt eerst veilig gecodeerd voordat semantische vet/cursief/lijst/citaat-opmaak wordt toegevoegd.
- DOCX-import kan daardoor Markdownachtige tekens uit gewone Word-proza niet meer per ongeluk als QuietWriter-opmaak interpreteren.
- Word Strong/Emphasis en overgeërfde stijlopmaak worden beter herkend.
- Opgemaakte tekst met een harde regeleinde blijft per QuietWriter-alinea correct opgemaakt.
- QuietWriter-scènebreuken krijgen in DOCX een herkenbare eigen stijl voor betrouwbare roundtrip.
- Eigen Word-stijlen die op Heading 1/2 zijn gebaseerd worden als structuur herkend.
- Import meldt nu expliciet bekende Word-constructies die niet volledig worden overgenomen, waaronder track changes, content controls, veldlogica, hyperlinkdoelen en voetnoten.

Er vindt geen stille migratie van bestaande QuietWriter-boeken plaats.
