# QuietWriter 1.3.0-dev.24

Deze ontwikkelbuild rondt vóór de volgende externe review drie concrete polishpunten af.

De Planning-overlay is smaller en hoger gemaakt, zodat hij zo min mogelijk over het manuscript valt. De knop **Planning** wordt bovendien volledig verborgen wanneer **Planninghulp in editor** is uitgeschakeld. De bestaande toggle-implementatie is verder bewust niet opnieuw verbouwd; het resterende klikgedrag wordt na Lucas' acceptatietest gericht aan Claude voorgelegd.

Zoeken en vervangen houdt nu altijd een vaste resultatenzone. Bij nul treffers blijft de onderkant van het paneel daardoor op zijn plek en verschijnt alleen **Geen resultaten gevonden**, niet daarnaast ook nog **0 resultaten**.

Bij intern kopiëren en plakken blijft opmaak behouden, maar de geplakte tekst blijft niet langer geselecteerd. De cursor staat na het plakken gewoon achter de ingevoegde tekst.

`library.json`, Planning-opslag en manuscriptopslagformaten zijn ongewijzigd.

README.md en README_EN.md zijn bewust niet gewijzigd.
