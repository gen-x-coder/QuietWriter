# QuietWriter 0.28.4 — reviewnotes

Deze release sluit uitsluitend de twee rode punten uit reviewronde 12. Er is nog geen Integriteit & Herstel-UI toegevoegd.

## 1. Future-format loskoppelen is write-blocked en save-vrij

`force_return_to_bookshelf()` doet niet langer `untrack_book()`. Het zet het boek via `Library.block_book()` expliciet op slot voor alle latere guarded writes. `verify_book_unchanged()` weigert een geblokkeerd boek altijd. Alleen een expliciete `track_book()` bij opnieuw openen heft de blokkade op.

Planning krijgt daarnaast `set_book(None, force=True)`. Die route roept **geen** `save_pending()` aan en wist notities, personageconcept en outline-state uit de UI nadat die state al in `conflict_local` is veiliggesteld.

Test vooral byte-voor-byte dat na future-format + Planning geen enkel live boekbestand verandert, bij zowel "Mijn planning" als "Versie op schijf". Test ook een pending nieuw personage, daarna ander boek openen en op Opslaan klikken: er mag niets meer in het oude boek terechtkomen.

## 2. Boekdetails heeft nu normale external-change conflictflow

`BookDetailsPage.save()` behandelt `ExternalModificationError` apart. Het laadt het nieuwste boek. Als dat een future format blijkt, gaat het via de centrale recovery/close-route. Anders roept het `MainWindow.adopt_active_book()` aan, zodat de bestaande drie-wegs merge voor Boekdetails de lokale formulierstate bewaart. De eerste savepoging retourneert daarna `False`; na controle kan de gebruiker opnieuw opslaan.

De pagina bewaart nu een expliciete `self.main`-referentie. Er wordt niet meer via `parent()` gezocht naar `MainWindow`.

Test normale Dropbox-wijziging terwijl synopsis dirty is, zowel ander veld als hetzelfde veld. Bij hetzelfde veld moet de lokale formulierstate in `conflict_local` staan. Test daarna opnieuw opslaan en afsluiten.

## Gevraagde runtimechecks

1. Planning-notities dirty + extern format 3 + "Versie op schijf": live map byte-identiek.
2. Hetzelfde + "Mijn planning": live map byte-identiek.
3. Pending nieuw personage + future format: concept in conflict_local, daarna volledig uit Planning-UI.
4. Na loskoppelen ander boek openen: geen enkele actie kan nog naar het oude boek schrijven.
5. Directe late write op het geblokkeerde oude Book-object wordt geweigerd.
6. Expliciet opnieuw openen/retracken van een normaal ondersteund boek heft de blokkade op.
7. Boekdetails dirty + extern gewijzigd hoofdstuk: lokale formulierinvoer blijft zichtbaar, pagina zit niet vast.
8. Boekdetails lokaal en extern hetzelfde metadata-veld gewijzigd: disk live, lokale volledige form in conflict_local.
9. Boekdetails dirty + extern format 3: lokale state in History, live map byte-identiek, terug naar boekenplank.
10. Recovery-snapshot failure in geval 9: boek blijft open en formulierstate blijft zichtbaar.
11. Regressie rondes 9–12 volledig opnieuw draaien.

Controleer bij 1–4 hashes van **alle bestanden** in de live boekmap, niet alleen `book.json`.
