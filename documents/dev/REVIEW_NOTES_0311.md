# Review notes 0.31.1

## Navigatie runtime
Controleer in uitgeklapte en ingeklapte rail:
1. HUIDIG BOEK: Inhoud, Planning, Boekgeheugen, Boekprofiel, Media, Boekdetails, Exporteren, Integriteit.
2. Geen extra subkoppen binnen HUIDIG BOEK.
3. Alleen vóór Integriteit een kleine extra witruimte in uitgeklapte toestand.
4. Boekgeheugen, Boekprofiel, Integriteit en Schrijverspersona zijn ook in de ingeklapte rail visueel van elkaar te onderscheiden.
5. Tab door de linker navigatie volgt exact de zichtbare knopvolgorde.
6. HUIDIG BOEK + integriteitsruimte verdwijnen correct als geen boek open is.

## Volgende technische stap
Lees `TECHNISCH_ONTWERP_0312.md` en de genoemde bronbestanden. Nog geen implementatie van spelling of transactionele adoptie in deze release. Graag eerst technische analyse van:
- hoe `adopt_active_book` echt prepare/commit kan worden zonder dirty/conflictgedrag te breken;
- welke adopt-calls nog kunnen falen/schrijven;
- minimale robuuste selectie/cursor -> SpellPanel occurrence-sync;
- of hover/contextmenu werkelijk nuttig en betrouwbaar is.
