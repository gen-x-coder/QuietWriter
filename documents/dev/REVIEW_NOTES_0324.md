# QuietWriter reviewnotities 0.32.4 — ronde 30

0.32.4 sluit reviewronde 29 af en bevat daarnaast de door Lucas gevonden koude-startnavigatiefout. Test in de echte `MainWindow` met PySide6; gebruik `isHidden()` voor rail-items.

## Verplichte proeven

1. **Koude start zonder actief boek**
   - Start QuietWriter met uitgeklapte rail, zonder eerst een boek te openen.
   - Alleen Bibliotheek/Boekenplank en globale programmafuncties mogen beschikbaar zijn.
   - Inhoud, Planning, Boekgeheugen, Boekprofiel, Media, Boekdetails, Exporteren en Integriteit moeten verborgen zijn.
   - De kop **HUIDIG BOEK** moet verborgen zijn.
   - Open daarna een boek: de juiste boekknoppen en kop verschijnen direct. Terug naar Boekenplank: alles verdwijnt weer.

2. **Planning-notities + Instellingen**
   - Boek zonder `planning/notes.md`: alleen Instellingen openen en Opslaan, daarna minstens 4 s events pompen.
   - `NotesPage.dirty == False`, timer uit, `persist_notes` 0× en er mag geen `notes.md` ontstaan.
   - Herhaal met bestaand notes-bestand en controleer byte-identiek.
   - Simuleer daarna externe hoofdstukwijziging: Settings-save mag geen planning-conflictdialoog veroorzaken.

3. **Planning-notities bronfideliteit**
   - Gebruik notities met U+00A0 en U+2028. Typ één teken en sla op.
   - Beide tekens blijven behouden.
   - Test ook mine/disk-conflict en `conflict_local`: lokale snapshot moet dezelfde typografische bron bewaren.

4. **Vier documentbrede hoofdstukbewerkingen**
   - Hoofdstuk met meerdere harde spaties + U+2028.
   - Test scènescheiding invoegen, scènescheiding verwijderen, afbeelding invoegen en afbeelding verwijderen.
   - Alleen de bedoelde structuur wijzigt; harde spaties/U+2028 elders blijven behouden.

5. **Publicatie smoke-test**
   - Voorwoord/Nawoord met U+00A0 en U+2028, één echte wijziging en save.
   - Typografische bron moet behouden blijven. Dit is preventief meegenomen na de patroonscan uit ronde 29.

6. **Regressie**
   - Herhaal ronde 28/29 editorbronproeven en de Settings/live-previewproeven uit rondes 26–28.
   - Transactionele adopt/conflictflows uit 0.31 moeten op hun bekende groene basislijn blijven.

## Bekende observatie, niet onderdeel van 0.32.4

Alleen Boekgeheugen/Boekprofiel bezoeken kan nog een leeg sjabloonbestand materialiseren. Dat blijft apart geparkeerd; rapporteer alleen als het gedrag breder is geworden.
