# Review notes 0.29.3

Doel: aantonen dat corrupte tekst fail-closed is, ook via gewone UI-acties en directe storage-calls.

1. `ai/memory.md` ongeldige UTF-8 → Boekgeheugen bezoeken → andere sectie → Schrijven. Bestand moet byte-identiek blijven; Integriteit moet het probleem nog zien.
2. Idem Boekprofiel: bezoeken, sectie wisselen, Opslaan/navigeren. Geen byte mag veranderen.
3. Beschadigd Boekgeheugen → AI-Onthouden. Actie moet weigeren en bron byte-identiek laten.
4. Beschadigd huidig hoofdstuk → Scènebreuk. Geen dirty/autosave/write; hoofdstuk byte-identiek.
5. Beschadigd huidig hoofdstuk → afbeelding invoegen, AI-paneel, spelling en Zoeken/Vervangen. Muterende acties mogen het hoofdstuk niet vervangen en mogen geen ongewenste media-side-effecten maken.
6. Direct `Library.save_chapter`, `save_book_memory`, `save_book_profile` en `PlanningStore.save_notes` tegen een reeds getrackte corrupte bron: verwacht `CorruptSourceError`, bytes identiek.
7. Integriteit → Herstel op dezelfde vier bestandstypen: herstel moet nog steeds slagen; daarna normale save moet weer werken.
8. Geldig leeg UTF-8-bestand blijft bewerkbaar/schrijfbaar.
9. Guard-proef 0.29.1: wijziging na openen Integriteit maar vóór Herstel blijft geweigerd.
10. Regressie rondes 14–16 opnieuw uitvoeren.

Vergelijk bij 1–5 bij voorkeur de hele boekmap vóór/na, niet alleen het doelbestand.
