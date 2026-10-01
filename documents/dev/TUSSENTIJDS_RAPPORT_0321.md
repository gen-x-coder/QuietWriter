# Tussentijds rapport QuietWriter 0.32.1

## Aanleiding

0.32.0 introduceerde de juiste feature-zichtbaarheid, maar reviewronde 26 vond twee rode regressies: startup crashte met spelling uit en Settings committeerde wel naar QSettings maar riep de runtime-apply niet aan doordat `parent()` inmiddels een `CurrentPageStack` was. Lucas meldde daarnaast dat Planning als enige belangrijke boekpagina geen korte uitleg bovenaan had.

## Wijzigingen

- SettingsPage bewaart een expliciete `MainWindow`-referentie en gebruikt die voor `settings_saved`, theme-preview en modelrefresh.
- Spellingsinitialisatie wordt pas uitgevoerd nadat `SpellPanel` bestaat.
- AI en Geavanceerde opties geven direct railpreview; zonder Opslaan herstelt de opgeslagen toestand bij verlaten van Instellingen.
- De committed settingspass corrigeert het terugkeerdoel wanneer de bronpagina verborgen is.
- Planning heeft een paginatitel en rustige introductietekst gekregen.
- Dubbele checkboxtekst bij Geavanceerde opties is verwijderd.

## Tests lokaal

- Nieuwe bron-/architectuurtests voor expliciete MainWindow-route, initialisatievolgorde, live preview, Planning-intro en checkboxcopy.
- Nieuwe PySide6-runtime tests voor startup met spelling uit en de echte Settings save/return-route; deze worden in de lokale container overgeslagen omdat PySide6 ontbreekt en moeten door Claude worden uitgevoerd.
- Volledige lokale suite: 561 geslaagd, 280 subtests geslaagd, 28 overgeslagen; alleen de 2 bekende fontresource-tests falen.
