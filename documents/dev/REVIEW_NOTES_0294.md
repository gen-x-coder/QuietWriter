# Review notes 0.29.4

Focus van deze review: de twee bevindingen uit reviewronde 17.

## Runtimechecks voor Claude

1. Open een beschadigd hoofdstuk, ga naar Achterwerk > Nawoord, typ tekst en sluit direct af vóór de publicatie-autosave. De tekst moet bewaard zijn.
2. Herhaal via navigatie naar Planning en Boekenplank. Geen stil tekstverlies.
3. Herhaal met Voorwerk.
4. Hele boek zoeken terwijl een ander hoofdstuk ongeldige UTF-8 bevat: geen exceptie; gezonde hoofdstukken leveren resultaten; status meldt het overgeslagen hoofdstuk.
5. Alles vervangen over het hele boek met één corrupt ander hoofdstuk: gezonde hoofdstukken worden vervangen, corrupt bestand blijft byte-identiek en er volgt een melding.
6. Dupliceer een corrupt hoofdstuk: nette weigering, volledige boekmap byte-identiek.
7. De dubbele corruptiebarrière uit 0.29.3 blijft intact voor scènebreuk, cursorinsert, spelling, afbeelding, Boekgeheugen/Boekprofiel en AI-Onthouden.
8. Integriteit-herstel blijft werken en maakt herstelde tekst weer normaal bewerkbaar.
9. Guard-proef: wijziging na openen Integriteit maar vóór Herstel blijft geweigerd.
10. Draai regressiescripts rondes 9–17.

Bij checks 1, 2, 5 en 6 graag de volledige boekmap vergelijken waar dat zinvol is.
