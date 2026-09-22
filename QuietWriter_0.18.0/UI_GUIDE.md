# QuietWriter UI-richtlijnen

QuietWriter moet tijdens het schrijven zo weinig mogelijk als een interface voelen. Nieuwe schermen gebruiken daarom dezelfde visuele grammatica in plaats van per functie een nieuw patroon te introduceren.

## Paginasoorten

### Overzicht
- Titel links, één primaire actie rechts.
- Lijsten en lege toestanden blijven rustig; geen formulier tonen zolang niets is gekozen.
- Voorbeelden: Personages, Outline.

### Instellingen
- Vaste subnavigatie links.
- Scrollbare inhoud rechts; de Opslaan-actie blijft buiten de scrollviewport.
- Instellingen staan in rijen: naam en noodzakelijke uitleg links, bediening rechts.
- Verwante instellingen krijgen een kleine gedempte sectiekop.
- Uitleg alleen waar gedrag of gevolgen niet vanzelf spreken.
- Opslaan is alleen actief wanneer waarden gewijzigd zijn.

### Detail/formulier
- Vaste header, scrollbare inhoud, primaire actie onderaan wanneer commit nodig is.
- Voorbeelden: Boekdetails, gestructureerde publicatiepagina's.

### Document
- Inhoud domineert; zo weinig mogelijk chrome.
- Voorbeelden: manuscript, boeknotities, vrije publicatietekst.

### Setup-flow
- Een tijdelijke keuze- of configuratiestap mag Gereed/Annuleren gebruiken als beide acties betekenis hebben.

## Interactie

- Selecteren van tekst mag toetsenbordbewerkingen nooit blokkeren.
- Zwevende hulpmiddelen mogen geen keyboard focus van de editor stelen.
- Het standaard contextmenu blijft beschikbaar en kan QuietWriter-acties aanvullen.
- Primaire, secundaire en destructieve acties gebruiken overal dezelfde button-stijlen.
- Flyouts en tijdelijke balken sluiten zodra hun context verdwijnt.

## Responsive gedrag

- Beschikbare vensterruimte is leidend; content mag nooit het hoofdvenster groter afdwingen.
- Lange content zit in een scrollviewport.
- Verborgen pagina's mogen via stacks geen minimumafmetingen van het hoofdvenster bepalen.
- Controleer releases op lage laptophoogte en 100%, 125% en 150% schaal wanneer mogelijk.
