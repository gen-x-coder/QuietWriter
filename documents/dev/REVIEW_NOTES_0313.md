# Review notes 0.31.3

## Hoofddoel

Controleer eerst dat de twee rode regressies uit reviewronde 21 echt gesloten zijn. Test daarna de drie corruptieroutes en de kleine spellings/nav-fixes. Gebruik waar mogelijk de echte `MainWindow` met PySide6 en `QTest`, niet alleen source-inspectie.

## Claude — technische/runtime tests

1. **Export — geen vals conflict meer**
   - Open normaal boek, ga naar Exporteren.
   - Wissel EPUB → PDF, template, marges en vinkjes meerdere keren.
   - Ga terug naar Inhoud, wijzig manuscript en forceer save.
   - Verwacht: géén dialoog “Boek extern gewijzigd” voor `export/settings.json`.
   - Controleer dat `library.verify_book_unchanged(book)` na iedere eigen exportinstelling-save groen blijft.

2. **Export — echte externe wijziging blijft beschermd**
   - Open boek en wijzig daarna `export/settings.json` buiten QuietWriter.
   - Wijzig vervolgens een exportoptie in QuietWriter.
   - Verwacht: normale externe-conflictflow; externe wijziging mag niet stil worden overschreven.

3. **Export — set_book/reload schrijft niet**
   - Instrumenteer `ExportSettingsStore.save()` of mtime/hash.
   - Alleen een boek adopteren / Exportpagina opnieuw binden mag `export/settings.json` niet wijzigen door combobox/toggle-signalen.

4. **Spelling — stale offsets na typen**
   - Tekst exact: `De katt zit op de mat.\nDe katt zit op de matt.`
   - Open spelling, typ `XXXXXXXXXX ` aan het begin.
   - Klik één keer op de tweede `katt`.
   - Verwacht: paneel toont die tweede `katt`; Wijzigen vervangt die occurrence en niet `matt`.
   - Controleer dat refresh geen selectie in de editor maakt.

5. **Spelling — eerste klik**
   - Na hoofdstuk openen/opslaan en na een formatteringsronde: open spelling en klik direct één keer op de tweede fout.
   - Verwacht: eerste klik wordt verwerkt; geen tweede klik nodig.
   - Typen zelf mag het paneel niet per letter laten springen.

6. **Afgekapte JSON — fail closed**
   Test apart voor:
   - `planning/characters.json`
   - `planning/outline.json`
   - `publication/publication.json`
   - `export/settings.json`
   Maak geldige UTF-8 maar syntactisch afgekapt JSON. Open het boek; probeer via normale UI te schrijven.
   - Verwacht: bronbytes blijven byte-identiek; nette fout; Integriteit blijft het probleem zien.
   - Herstel via Integriteit en controleer daarna normale werking.

7. **Vrije publicatietekst corrupt**
   - Zet ongeldige UTF-8 in `publication/texts/foreword.md` (en bij voorkeur één achterwerk-item).
   - Open Voorwerk/Achterwerk → betreffend item.
   - Verwacht: geen crash; alleen-lezen herstelmelding; Opslaan disabled; bytes blijven identiek.
   - Herstel via Integriteit; heropen item; editor moet weer normaal bewerkbaar zijn.

8. **Integriteit-gap**
   - Rail uitgeklapt, boek open: 6 px scheiding vóór Integriteit zichtbaar.
   - Klik gewone knop Boekenplank: scheiding direct weg.
   - Open opnieuw; force-return/detach route: scheiding eveneens weg.

9. **Regressie**
   - Volledige testsuite.
   - Alle regressiescripts uit eerdere rondes die in ronde 21 groen waren.
   - Besteed extra aandacht aan Export, Planning/publicatie-corruptie, conflictflow en spelling.

## Bekend open — expres niet als opgelost beoordelen

De transactionele adopt-commit uit ronde 21 punt 6 is nog niet gesloten in 0.31.3. Reproduceer hem desgewenst opnieuw als baseline, maar rapporteer hem als bekende openstaande architectuurfix voor 0.31.4, niet als regressie van 0.31.3. Gewenste volgende stap: merges + `conflict_local` snapshots in `_prepare_active_book_adoption`, pas na succesvolle commit meldingen tonen.

## Lucas — visueel/handmatig

1. Gebruik Exporteren een minuut zoals normaal: wissel formaat en enkele opties, schrijf daarna verder. Er mag nergens een onverwachte conflictdialoog verschijnen.
2. Open spelling bij een hoofdstuk met meerdere dezelfde fouten. Typ vooraan een paar woorden en klik daarna één keer op de tweede/derde fout. Het paneel moet meteen precies dat woord tonen en mag je tekst niet selecteren.
3. Let tijdens snel typen met spelling open op rust: geen flikkeren, verspringen of focusverlies van de editor.
4. Open een normaal Voorwoord en controleer dat de publicatie-editor visueel ongewijzigd is. (De corrupte variant kan Claude technisch testen.)
5. Met uitgeklapte linkerrail: open een boek, controleer de rustige scheiding vóór Integriteit; klik Boekenplank en controleer dat die ruimte direct verdwijnt.
