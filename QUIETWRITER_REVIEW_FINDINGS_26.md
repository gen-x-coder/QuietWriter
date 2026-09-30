# QuietWriter: reviewronde 26 (versie 0.32.0)

Bron: Claude-review aangeleverd door Lucas na 0.32.0.

## Resultaat

Testsuite: 584 geslaagd, 280 subtests, 0 overgeslagen. Alleen de 2 bekende fonttests falen. Alle regressiescripts van rondes 9–25 groen.

## Rode punten

1. **Startupcrash wanneer spelling uit staat.** `EditorPage.__init__` riep `load_dictionary_from_settings()` aan voordat `self.spell = SpellPanel(self)` bestond. De disabled-tak gebruikte daardoor `self.spell` tijdens startup.
2. **`settings_saved()` werd via de echte UI-route nooit aangeroepen.** `SettingsPage.parent()` is na opname in de paginastapel `CurrentPageStack`, niet `MainWindow`. Daardoor werden spelling, AI/provider/model, schrijftypografie, manuscriptstijl en spellingstaal niet direct na Opslaan toegepast. Ook terugkeer vanaf een inmiddels verborgen pagina bleef verkeerd.

## Wat al goed werkte

- AI-zichtbaarheid zelf: AI-knop, Schrijverspersona, Boekgeheugen, Boekprofiel en SCHRIJVEN-groep volgen AI aan/uit zonder data te verwijderen.
- Geavanceerde opties kan Integriteit en de bijbehorende witruimte verbergen/tonen.
- Integriteit toont de herkomst van de herstelkopie.

## Visuele observatie

`Geavanceerde opties gebruiken` stond dubbel: als rijlabel én als checkboxtekst.

## Advies

Maak 0.32.1 met een expliciete MainWindow-referentie in SettingsPage, verplaats/guard de spellinginitialisatie, en voeg echte Qt-tests toe voor startup met spelling uit en Settings Opslaan met directe spellingsfeedback.
