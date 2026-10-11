# QuietWriter 1.3.0-dev.22

Deze ontwikkelbuild maakt de Planningworkflow tijdens het schrijven interactief zonder Planning en manuscript te vermengen. Naast Tekstbreedte staat nu een subtiele knop **Planning**. Die opent tijdelijk een overlay met de scènes die aan het huidige hoofdstuk zijn gekoppeld, ook wanneer er al manuscripttekst staat.

Elke scène toont haar bestaande status (`idee`, `uitgewerkt`, `geschreven`). Open scènes kunnen vanuit de overlay bewust met **Klaar** als geschreven worden gemarkeerd. QuietWriter probeert nooit zelf uit de manuscripttekst af te leiden of een scène klaar is. De overlay schrijft geen tekst naar het manuscript en verandert niets aan woordtelling, zoeken, spelling, export, AI-context of Undo.

De ghost/planninghulp in een leeg hoofdstuk toont nu ook de status van iedere scène. In scènebewerking is Status voortaan een vaste dropdown en geen vrij tekstveld. Planning > Personages selecteert bij openen automatisch het eerste opgeslagen personage, zodat de detailweergave niet leeg begint. De scrollbar-track van de hoofdstukkenlijst gebruikt dezelfde achtergrond als de pagina.

`library.json`, manuscriptbestanden en het Planning-opslagformaat zijn ongewijzigd. De bestaande `status`-waarde in `planning/outline.json` wordt hergebruikt; er is geen nieuw klaar-veld toegevoegd.

README.md en README_EN.md zijn bewust niet gewijzigd.
