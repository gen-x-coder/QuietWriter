# QuietWriter review 0.34.0

## Eerst: regressie van de door Lucas gevonden railbug
1. Open een boek. Klik achtereenvolgens Schrijverspersona → Inhoud, Instellingen → terug naar Inhoud, Prullenbak → Planning.
2. Er mag steeds exact één linkerrailknop geselecteerd zijn. PROGRAMMA en het scrollende middendeel vormen één selectiekring.
3. Programmatic navigation naar Boekprofiel/Boekgeheugen/Planning moet de actieve knop met `ensureWidgetVisible()` in beeld brengen wanneer die onder de vouw staat.

## In dit hoofdstuk — eerste slice
4. Maak opgeslagen Planning met twee scènes gekoppeld aan het actieve hoofdstuk, plus personages. Open **In dit hoofdstuk**. Alleen deze scènes en de gekoppelde personages moeten verschijnen.
5. Voeg daarnaast een scène voor een ander hoofdstuk en een verwijderde/missing personage-id toe. Die mogen niet verschijnen en mogen geen exceptie geven.
6. Wijzig Planning lokaal maar sla niet op: het paneel moet de opgeslagen stand blijven tonen. Na succesvolle save en terugkeer naar Inhoud moet de nieuwe stand verschijnen.
7. Zet AI uit: **In dit hoofdstuk** blijft beschikbaar.
8. Voorwoord/Nawoord/publicatie-instellingen, geschiedenis-preview en een beschadigd hoofdstuk: de knop is verborgen/niet beschikbaar.
9. Beschadig afzonderlijk `planning/outline.json` en `planning/characters.json`: het paneel toont een korte leesfout, maar manuscript typen/opslaan blijft werken. Geen write naar Planning.
10. Klik **Planning openen** vanuit het paneel: centrale Planning-pagina opent via de normale route; geen dubbele railselectie.

## Geen verborgen scope-uitbreiding
11. Controleer dat AI-prompts/context in 0.34.0 inhoudelijk gelijk zijn aan 0.33.1: het nieuwe paneel voegt nog niets automatisch toe aan AI-context.
12. Geen nieuwe Planning-bestanden of schemawijzigingen door alleen het paneel te openen.

## Layout/smoke
13. Test op 700/720/768 px en Windows DPI 100/125/150%. Rechterpaneel moet bruikbaar blijven; hoofdstukboom en editor mogen niet verdwijnen tot onbruikbare breedte.
14. Herhaal koude start en railmatrix-smoke uit 0.33.1.
15. Volledige suite met echte PySide6. Vermeld de twee bekende fonttests apart.
