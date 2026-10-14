# QuietWriter 1.5.0-dev.38 — crashherstel voor 'Alles vervangen'

## Wat is veranderd

- Vóór de eerste manuscriptwijziging wordt in `archive/<book-id>/replace-recovery-*/transaction.json` een duurzaam journaal opgeslagen met de SHA-256-hashes van originele en nieuwe tekst. De originelen liggen in dezelfde lokale herstelmap buiten de Dropbox/OneDrive-boekenmap.
- Het journaal heeft de statussen `pending`, `committed` en `recovered`.
- Bij het openen van een `Library` wordt een achtergebleven `pending`-transactie gecontroleerd. Alleen bestanden die exact overeenkomen met de door QuietWriter eerder geschreven nieuwe inhoud, worden teruggezet. Een intussen anders geworden hoofdstuk (bijv. door Dropbox) wordt niet overschreven. Er blijft een melding in `Library._replace_recovery_alerts` en het journaal blijft staan voor handmatige controle.
- Tijdens het vervangen is er een niet-blokkerende OS-bestandslock per boek in de lokale `archive`-map. De lock komt vrij als het proces stopt.
- De bestaande rollback bij een gewone schrijffout blijft werken.

## Grenzen en open punten

Dit is een bronreviewkandidaat, geen productieclaim van strikt atomaire vervanging. De herstelcode is vooral getest op gecontroleerde onderbrekingen en handmatig aangemaakte journaaltoestanden. Een harde Windows-kill of stroomuitval, filesystem-durability onder NTFS/exFAT, OneDrive/Dropbox in het wild en gelijktijdige bewerkingen in dezelfde boekmap op meerdere computers zijn **niet bewezen**. De OS-lock beschermt processen op *dezelfde computer*; Dropbox synchroniseert die lock niet als een distributed lock.

Herstelwaarschuwingen worden nu vastgelegd in `Library._replace_recovery_alerts`; een expliciete gebruikersinterface die deze op een rustige manier toont, ontbreekt nog. Dat is een prioriteit voor de volgende integratie. Wijzigde hoofdstukken, beschadigde back-ups of ontbrekende boekmappen vereisen handmatige beoordeling. Herstelbestanden worden bewust niet verwijderd.

**Let op:** het project bevat nog interne versiemetadata uit een eerdere iteratie; de ZIP-naam is een reviewlabel en geen gepubliceerde release. De automatische programma-updater blijft uitgeschakeld. De handmatige GitHub-route wordt niet gewijzigd.

## Testuitslagen in deze omgeving

- `test_replace_crash_journal_dev38.py`, `test_replace_batch_dev37.py`, `test_sync_conflicts_dev36.py`, `test_dev37_review_safety.py`, `test_review_dev34_regressions.py`: 17 tests geslaagd.
- Bredere gerichte reeks inclusief boekenkast/sync: 24 geslaagd, 1 overgeslagen.
- Volledige suite, Windows-runtime en echte tweecomputerproef: niet uitgevoerd.

## Nog te doen

1. Herstelwaarschuwingen zichtbaar maken en tegen verder schrijven beveiligen wanneer een transactie niet volledig hersteld kan worden.
2. Crashinjection in een echt subprocess en Windows-test met kill tussen twee hoofdstukwrites.
3. Een gebruikergerichte knop om herstelkopieën te bekijken, zonder ze automatisch te verwijderen.
4. Versieadministratie en volledige suite toetsen voordat dev.38 lokaal wordt geïntegreerd.
