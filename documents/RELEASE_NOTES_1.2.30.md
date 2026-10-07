# QuietWriter 1.2.30 — veilige afronding van de manuscriptarchitectuur

Deze ontwikkelversie rondt de grote DocumentView-/serializerverbouwing van de Markdownachtige manuscriptopslag af. Oude boeken worden niet stil anders geïnterpreteerd: bij een legacy boek vraagt QuietWriter expliciet om een eenmalige syntaxupdate en maakt vooraf automatisch een herstelversie. Backslashes worden daarbij zo omgezet dat de zichtbare tekst gelijk blijft.

Daarnaast is de dirty-check tijdens typen goedkoper geworden, is de read-side manuscriptsyntaxis losgetrokken van de editorbewerkingen en zijn woordtelling/zoek-/AI-projecties uit de medialaag gehaald. DOCX-opmaakresolutie doet minder herhaalde Word-stijlopzoekingen.

De volgende stap is geen nieuw architectuurblok maar een onafhankelijke eindreview met volledige Qt-, compatibiliteits- en performancechecks.
