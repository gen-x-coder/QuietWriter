# QuietWriter reviewnotities 0.32.2 — ronde 28

Doel van deze release: de polishlaag stabiliseren na reviewronde 27. Er zijn geen nieuwe subsystemen toegevoegd.

## Te testen door Claude

1. **Geen valse dirty na Instellingen**
   - Open een boek en hoofdstuk; noteer bytes/mtime van het hoofdstuk.
   - Instellingen openen en zonder tekstwijziging Opslaan (liefst meerdere categorieën/settings wijzigen: thema, font, AI, spelling).
   - Verwacht direct: editor `dirty == False`, status niet "Niet opgeslagen", autosave-timer niet actief.
   - Wacht minstens 4 seconden en navigeer daarna naar Planning: hoofdstuk bytes moeten identiek blijven en `save_chapter` mag niet door presentatie-events worden aangeroepen.
   - Simuleer daarna een externe wijziging van dat hoofdstuk na een Settings-save: navigeren mag geen vals conflict geven zolang lokaal niet is getypt.

2. **Spelling-presentatie maakt niet dirty**
   - Open een hoofdstuk met spelfouten.
   - Gebruik `Negeer overal` en `Toevoegen aan woordenboek` zonder manuscripttekst te wijzigen.
   - Verwacht: geen dirty-status, geen autosave/herschrijving.
   - Typ daarna echt één teken: dirty/autosave moet wél normaal werken.
   - Undo terug naar exact de geladen/opgeslagen tekst: dirty moet weer verdwijnen en autosave stoppen.

3. **Live preview rail volledig consistent**
   - Rail uitgeklapt.
   - AI uitvinken zonder Opslaan: AI-items én kop `SCHRIJVEN` direct weg.
   - Geavanceerde opties uitvinken: Integriteit én de witruimte direct weg.
   - Beide weer aan: alles direct terug.
   - Klap tijdens deze preview de rail in en weer uit: previewtoestand moet behouden blijven.
   - Verlaat Instellingen zonder Opslaan via Inhoud, Planning, Boekdetails en Boekenplank: opgeslagen toestand moet terugkomen.

4. **AI-paneel tijdens preview**
   - Open het AI-paneel rechts.
   - Instellingen → AI uitvinken → weer aanvinken → Instellingen verlaten zonder Opslaan.
   - Verwacht: het AI-paneel is niet door de preview gesloten/vervangen; panel state/input blijft intact.
   - Daarna AI uitzetten en wél Opslaan: het paneel mag bij de commit sluiten omdat de functie daadwerkelijk uit staat.

5. **Mislukte Settings-save rollback**
   - Forceer `QSettings.sync()`/status-failure na nieuwe waarden (zoals ronde 27).
   - Wijzig minstens AI, Geavanceerd, thema en spelling.
   - Na foutmelding: effectieve runtime en in-memory QSettings moeten weer de oude opgeslagen waarden gebruiken; geen half nieuwe feature visibility/theme/provider.
   - Het formulier mag de nieuw gekozen waarden blijven tonen en Opslaan moet actief blijven zodat opnieuw proberen mogelijk is.
   - Controleer dat `settings_saved()` niet is uitgevoerd bij failure.

6. **Regressie**
   - Volledige suite en regressiescripts rondes 9–27.
   - Extra aandacht voor 0.31 transactionele adopt/conflictflows en ronde 26 spelling-startup/direct apply.

## Visueel voor Lucas

- Rail uitgeklapt: AI en Geavanceerd aan/uit moeten inclusief groepskop/witruimte onmiddellijk logisch ogen.
- Planning-intro uit 0.32.1 blijft onveranderd.
- Na Opslaan in Instellingen mag boven de editor niet kort "Niet opgeslagen" verschijnen.

## Bekende omgevingbeperking hier

In de ChatGPT-container ontbreken de gebundelde fontresources; alleen de twee bekende fonttests falen. Qt-runtimecases worden hier deels overgeslagen en moeten door Claude worden uitgevoerd.
