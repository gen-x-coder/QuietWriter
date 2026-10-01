# Review notes 0.36.2

## Doel

Deze onderhoudsronde ruimt de ontwikkelartefacten op en corrigeert de first-run taalwissel.

## Structuur

- `documents/`: eindgebruikersdocumentatie, momenteel changelog en roadmap.
- `documents/dev/`: plannen, technische ontwerpen, reviewbevindingen, audits en tussenrapporten van de ontwikkelcyclus met Claude/ChatGPT.
- `documents/licenses/`: QuietWriter-eigen licentie en het overzicht van third-partylicenties. Resource-specifieke licentiebestanden blijven naast fonts/woordenboeken staan.

De release-staging blijft allowlist-based. Alleen de twee productlicentiebestanden uit `documents/licenses/` gaan als documentatie-resource mee naar PyInstaller; `documents/dev/` komt niet in de portable distributie.

## First-run

`FirstRunWizard` koppelt de taalkeuzelijst nu aan de process-wide locale. Alle statische wizardlabels en knoppen hebben een i18n-key/default als widgetproperty en worden bij een taalwijziging opnieuw vertaald. Dynamische voortgang en Volgende/Voltooien lopen via de bestaande `_update_nav()`.

Na `_commit()` wordt dezelfde taal opgeslagen in QSettings. `run_first_setup()` past na sluiten van de wizard de opgeslagen appearance opnieuw toe, waardoor ook het hoofdvenster in dezelfde run in de gekozen taal start.

## Gericht testen

1. Start met `--first-run`.
2. Kies `English` op stap 1. De wizard moet onmiddellijk omschakelen: `Welcome to QuietWriter`, `Step 1 of 4`, `Back`, `Skip`, `Next`.
3. Ga door alle stappen. Ook Werkmap/Spelling/AI moeten Engels zijn.
4. Rond af. Het hoofdvenster moet direct Engels zijn, zonder QuietWriter opnieuw te starten.
5. Herhaal met `Nederlands` om de terugschakeling te controleren.

## Reviewfocus voor Claude

Controleer vooral regressies in Qt-parenting/signalen bij live retranslation, de PyInstaller datapaden voor `documents/licenses`, en dat `documents/dev` nooit via staging in de portable build terechtkomt.
