# Review notes 0.31.2

Focus voor runtime-review:

1. Open een boek met ongeldige UTF-8 in `planning/characters.json`, `planning/outline.json`, `publication/publication.json` en `export/settings.json`, elk apart. Geen crash en geen half geadopteerd boek.
2. Probeer de betreffende gegevens via de normale UI te wijzigen. Het corrupte bronbestand moet byte-identiek blijven en Integriteit moet het melden.
3. Herstel via Integriteit en controleer dat de pagina daarna weer normaal werkt.
4. Forceer een fout tijdens de voorbereidende adoptiefase. Controleer dat `_active_book` en de zichtbare pagina's niet naar het kandidaatboek zijn omgezet.
5. Controleer dezelfde-book reload met dirty Boekdetails/Planning; bestaande conflict/recovery-semantiek moet intact blijven.
6. Spellingspaneel open: klik of navigeer met pijltjes naar een rood onderstreept woord. Paneel moet die occurrence tonen zonder de editorselectie te veranderen.
7. Typ door terwijl het spellingspaneel open is. Het paneel mag niet bij iedere letter naar een andere fout springen.
8. Controleer meerdere gelijke spelfouten: cursor op de tweede occurrence moet precies die occurrence in het paneel kiezen.
9. Rail uitgeklapt: witruimte vóór Integriteit verschijnt direct bij openen en verdwijnt direct bij Boekenplank, zonder eerst rail in/uit te klappen.
10. Draai regressies rondes 9–17 en de 0.31.0/0.31.1 navigatietests opnieuw.

Nog niet in deze release: spelling via contextmenu. Hover blijft bewust buiten scope.
