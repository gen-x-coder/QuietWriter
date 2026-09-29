# Tussentijds rapport 0.31.0

## Scope

Deze release combineert de afgesproken rustige navigatiestructuur met twee kleine editorverbeteringen: autosave is altijd actief en de totale woordtelling is explicieter. Er is bewust niets gewijzigd aan de spellingscontrole.

## Handmatige controle

1. Start zonder open boek: in uitgeklapte navigatie zijn BIBLIOTHEEK, SCHRIJVEN en PROGRAMMA zichtbaar; HUIDIG BOEK niet.
2. Open een boek: HUIDIG BOEK verschijnt boven Inhoud/Planning/Boekdetails/Boekprofiel/Boekgeheugen/Media/Integriteit/Exporteren.
3. Klap de rail in: alle groepskopjes verdwijnen; iconen blijven bruikbaar. Klap weer uit: kopjes komen terug.
4. Schrijverspersona blijft buiten HUIDIG BOEK en buiten Instellingen.
5. Instellingen > Algemeen bevat geen autosave-schakelaar meer, maar vermeldt dat automatisch wordt opgeslagen en Ctrl+S direct opslaat.
6. Zet in een oude settings-file autosave=false, start QuietWriter, typ tekst en wacht circa drie seconden: tekst wordt toch opgeslagen.
7. Simuleer een tijdelijke schrijflock: retry-autosave moet blijven werken, onafhankelijk van de oude setting.
8. Controleer drag/reorder: gepauzeerde autosave wordt na de drag hervat.
9. Boven de editor staat `Boek bevat N woorden`; onderin blijft `Hoofdstuk x van y · N woorden`.
10. Herhaal de corruptie-/Integriteit-regressies van 0.29.4; always-on autosave mag de fail-closed bescherming niet omzeilen.
