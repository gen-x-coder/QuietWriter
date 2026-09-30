# Tussentijds rapport — QuietWriter 0.32.2

## Aanleiding
Reviewronde 27 bevestigde dat 0.32.1 de twee rode punten uit ronde 26 oploste, maar bracht één belangrijk nieuw bereikbaar probleem aan het licht: presentatiepasses (`rehighlight`) werden als manuscriptwijziging gezien. Daarnaast was de live rail-preview visueel niet volledig consistent en kon een mislukte Settings-save de runtime half in de nieuwe toestand achterlaten.

## Wijzigingen

### 1. Dirty-status volgt nu brontekst
`EditorPage` bewaart `_clean_text`, de laatst geladen/opgeslagen manuscripttekst. `on_text_changed()` vergelijkt de actuele `toPlainText()` met deze baseline. Alleen echte tekstverschillen zetten dirty en starten autosave. Presentatiepasses zoals syntax/spelling-rehighlight doen dat niet meer. Undo terug naar de schone tekst maakt de editor opnieuw clean.

### 2. Preview gebruikt effectieve waarden
`MainWindow` bewaart tijdelijk de previewwaarden voor AI en Geavanceerde opties. `_apply_nav_width()` kan die waarden gebruiken, zodat ook de kop `SCHRIJVEN` en de Integriteit-witruimte direct met de checkbox-preview meeschakelen, inclusief rail inklappen/uitklappen.

### 3. AI-paneel blijft tijdens preview intact
Het verbergen/sluiten van een uitgeschakelde rechtertool gebeurt alleen bij een gecommitteerde instelling (`adjust_return=True`). Alleen previewen van AI-uit verandert de rechterpaneeltoestand dus niet permanent.

### 4. Settings-save is transactioneler
Voor de write wordt de vorige QSettings-toestand vastgelegd. Als `sync()` faalt, worden die waarden in-memory teruggezet en worden live previews teruggedraaid. `settings_saved()` wordt uitsluitend na succesvolle sync uitgevoerd. Het formulier blijft ongewijzigd/dirty zodat opnieuw Opslaan mogelijk blijft.

## Tests in deze omgeving
- 564 passed
- 280 subtests passed
- 29 skipped (voornamelijk Qt-runtime in deze omgeving)
- 2 bekende fontresource-tests falen doordat `resources/fonts/font_manifest.json` hier ontbreekt

## Volgende stap
Claude reviewronde 28 volgens `REVIEW_NOTES_0322.md`. Bij groen resultaat kan 0.32.x verder met resterende UI/editor-polish in plaats van conflict-/integriteitswerk.
