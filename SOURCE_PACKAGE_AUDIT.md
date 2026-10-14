# Source package audit – QuietWriter 1.5.0-dev.24

Dit is het aangeleverde ontwikkelpakket, aangevuld met een controlehulpmiddel. Het bevat **nog niet** alle publieke brandingafbeeldingen: die ontbraken in de invoer-ZIP. Ze worden niet vervangen door placeholders.

Maak de bronset op je Windows-machine compleet:

```powershell
python tools/check_source_assets.py --restore-missing
python tools/check_source_assets.py
```

Deze opdracht haalt uitsluitend ontbrekende publieke screenshots en de Engelse README van de bekende publieke commit op, verifieert de Git-blobhash en overschrijft geen bestaande bestanden. Internetverbinding vereist. De ontwikkel-README blijft ongemoeid. Bestanden zoals CONTRIBUTING.md staan niet in dit bronpakket en worden niet automatisch aangemaakt.

De juiste workflow is: source-ZIP voor ontwikkeling met alle afbeeldingen en README's; portable Windows-ZIP is voor eindgebruikers en hoort alleen runtimebestanden te bevatten. Voer de bronpakketcontrole altijd uit vóór het maken van een overdrachts-ZIP.
