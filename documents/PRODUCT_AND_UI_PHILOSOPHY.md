# QuietWriter — product- en UI-filosofie

## Productkarakter
QuietWriter moet tijdens schrijven zo weinig mogelijk als een interface voelen: rustig, voorspelbaar, tekstgericht en terughoudend met automatisering.

## Eén visuele grammatica
Gebruik een klein aantal paginatypen: overzicht, detail/formulier, document, instellingen en setup-flow. Nieuwe functies krijgen niet ieder een eigen interactiemodel.

## Rust boven feature density
Toon details wanneer ze relevant zijn. Geen permanent dashboard of extra statuslaag alleen omdat informatie beschikbaar is. Niet-interactieve kaarten krijgen geen hover alsof ze klikbaar zijn.

## Navigatie
De linkerrail is declaratieve state, geen reeks losse `setVisible()`-regels. Bij een verborgen huidige bestemming geldt één fallback: Inhoud als een boek open is, anders Boekenplank. Programmatische navigatie gebruikt dezelfde route als gebruikersnavigatie.

## Responsive en DPI
Test lage laptophoogte, 100%, 125% en 150% schaal. Hidden pages mogen minimumsize niet bepalen. Lange titels worden ge-elided in plaats van het venster breder te maken. Automatische paneelcollapse is een UX-keuze, geen standaard technische fix.

## Thema's en contrast
Gebruik semantische tokens; geen schermspecifieke hardcoded themakleuren. Richtlijnen: normale/muted tekst minimaal 4,5:1 waar van toepassing, focusindicator minimaal 3:1.

## Keyboard en focus
Keyboard is first-class. Tabvolgorde volgt de visuele/logische volgorde, lijsten/trees ondersteunen pijlen + Enter, Escape sluit tijdelijke panelen/flyouts en focus keert terug naar de opener. Destructieve acties worden nooit impliciet door list-activatie uitgevoerd.

## Settings preview versus commit
Preview is tijdelijk en niet-destructief. Zonder Opslaan valt de UI terug naar persisted state en mag geen tekst/invoer verdwijnen. Na Save wordt runtime eenmaal consistent toegepast. Een presentatie-instelling mag manuscript niet dirty maken.

## Manuscriptweergave
Font, grootte, regelafstand, thema en tekstbreedte zijn view state. Ze veranderen geen Markdown en geen export. Autosave is vangnet, niet excuus voor onzichtbare status; een expliciete Save/dirty-indicatie kan bij documentachtige flows passend blijven.

## Rechterpanelen
Contexttools, geen permanente dashboards. Sluiten met Escape, focus terug, venster minimumwidth niet onnodig vergroten.

## Integriteit/Herstel
Herstel is transparant: bestand, fouttype, herstelbaarheid en herkomst van herstelkopie zijn zichtbaar. Future-format wordt niet als herstelbare corruptie gepresenteerd.

## Media en export
Media blijft klein en robuust: toevoegen, bewerken, verwijderen, relatieve grootte/uitlijning/wrap. Geen ingebouwde grafische DTP-engine of coverdesigner. Export is een aparte boekpagina; Boekdetails beheert metadata/omslag.

## AI heet Meelezer
De naam is productstrategie. De Meelezer mag analyseren, controleren en feedback geven, maar niet manuscriptproza schrijven of een selectie herschrijven. De historische actie **Herschrijf selectie** is daarom bewust verwijderd.

## AI-context moet begrijpelijk zijn
Gebruiker moet de lagen kunnen onderscheiden: Persona, Boekprofiel, Boekgeheugen, Planning, hoofdstukplanning en manuscript. Nieuwe automatische contextbronnen zijn niet 'gratis slimheid': privacy en inspecteerbaarheid horen bij het ontwerp.

## Providerprivacy
OpenRouter: paneel openen is lokaal en doet geen warmuprequest. Pas bij echte send gaat context extern. Ollama mag lokaal in background warmen.

## AI-geheugen
Voorstellen vragen expliciete keuze (Onthouden/Bewerken/Negeren). Geen autonome writes. Succes kan subtiel lokaal in de chat worden bevestigd, maar zo'n lokale notice wordt niet als modelcontext teruggestuurd.

## First run
Maximaal vier korte stappen: taal/thema, werkmap, spelling, AI. Overslaan en teruggaan kan, AI staat standaard uit, bestaande gebruikers krijgen de wizard niet opnieuw.

## Beoordelingsvragen voor nieuwe UI
- welk bestaand paginatype is dit?
- is er al een plek voor hetzelfde concept?
- wat gebeurt er op 1280×700 en 150%?
- keyboard/focus/Escape?
- preview of commit?
- kan kijken per ongeluk data muteren?
- is tekst gelokaliseerd?
- past dit nog bij 'zo weinig mogelijk interface'?
