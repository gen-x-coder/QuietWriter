# Tussentijds rapport — QuietWriter 0.28.4

## Doel

0.28.4 is de laatste correctieronde vóór 0.29.0. De backend van 0.28.2 was groen; reviewronde 12 vond twee rode UI-grensproblemen in de nieuwe loskoppel- en Boekdetails-routes.

## Wijzigingen

### Loskoppelen is nu een echte terminale toestand

Een future-format boek wordt niet meer `untrack`ed voordat de UI wordt leeggemaakt. Dat bleek onveilig: een vergeten save-pad kreeg dan juist géén revisioncontrole meer. De Library kent nu een in-memory write-block per book-id. `verify_book_unchanged()` weigert zo'n boek categorisch. Een expliciete `track_book()` bij opnieuw openen heft de blokkade op.

Planning heeft een force-detach die niets opslaat. De lokale Planning-state is vóór deze stap al in `conflict_local` gezet; daarna worden notes/draft/outline alleen uit het scherm verwijderd. Hierdoor kan `set_book(None)` niet alsnog het nieuwere live boek muteren.

### Boekdetails kan een gewone externe wijziging verwerken

Bij `ExternalModificationError` laadt Boekdetails de nieuwste ondersteunde versie en laat `adopt_active_book()` de bestaande drie-wegs merge uitvoeren. Lokale-only wijzigingen blijven in het formulier; disk-only wijzigingen worden overgenomen; same-field conflicten bewaren de volledige lokale form eerst in History. Daarna blijft de saveguard bewust staan tot de gebruiker de gemergede waarden heeft gecontroleerd en opnieuw opslaat.

Blijkt de nieuwste manifestversie te nieuw, dan wordt de lokale formulierstate eerst in History veiliggesteld en gebruikt de pagina dezelfde centrale future-format exit als Editor, Publicatie, Planning, Boekprofiel en Boekgeheugen.

### Geen parent()-afhankelijkheid

Boekdetails bewaart de expliciete MainWindow-referentie die bij constructie wordt meegegeven. Qt mag widgets reparenten zonder dat de conflictflow daardoor een verkeerde eigenaar aanspreekt.

## Veiligheidsregel voor vervolg

Een 'detach' mag nooit impliciet opslaan. Een detached incompatibel boek blijft write-blocked totdat het expliciet opnieuw wordt geopend. Bij nieuwe saveguards testen we steeds de uitweg bij een structurele fout: lokale state moet zichtbaar blijven of aantoonbaar in History staan.

## Volgende stap

Pas na runtimegroen van deze ronde: 0.29.0 Integriteit & Herstel-UI. Geen nieuwe features zijn in 0.28.4 toegevoegd.
