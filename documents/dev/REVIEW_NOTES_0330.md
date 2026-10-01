# Claude-review 0.33.0 — informatiearchitectuur en declaratieve rail

0.32.x is functioneel afgesloten. 0.33.0 verandert bewust de informatiearchitectuur van de linkerrail, maar geen boekformaten, opslagformaten of AI-promptlogica.

## Eerst: testvangnet uit ronde 33

Controleer vóór productgedrag:

1. **Volledige suite met echte PySide6**. De suite mag nergens hangen.
2. Forceer een onverwachte `QMessageBox.warning` vanuit een `QTimer.singleShot(...)`. De directe AssertionError mag door Qt worden afgevangen, maar de test moet in teardown alsnog falen wegens geregistreerde dialoogaanroep.
3. Forceer `QDialog().exec()`, `QInputDialog.getText(...)` en de drie gebruikte `QFileDialog.get*`-routes. Geen enkele route mag de suite laten hangen; ze moeten direct/uiteindelijk als testfout eindigen.
4. Draai `test_code_health_0327.py` vanuit een andere current working directory. De test moet nog steeds de echte `quietwriter/`-bron vinden. Een expres ingevoegde `return` gevolgd door een statement in een functie of geneste statementlijst moet rood worden.

## A. Railmodel: onafhankelijke waarheid

Productmodel: `quietwriter/ui/rail_model.py`.

Belangrijk: beoordeel het gedrag niet uitsluitend door hetzelfde model terug te lezen. Vergelijk ook handmatig:

### Koude start, AI aan, Advanced aan
Zichtbare items, in volgorde:
- Boekenplank
- Schrijverspersona
- Instellingen
- Prullenbak

Uitgeklapte koppen:
- BIBLIOTHEEK
- PROGRAMMA

Geen HUIDIG BOEK en geen AI-CONTEXT.

### Boek open, AI aan, Advanced aan
- Boekenplank
- Inhoud
- Planning
- Media
- Boekdetails
- Exporteren
- Integriteit
- Boekgeheugen
- Boekprofiel
- Schrijverspersona
- Instellingen
- Prullenbak

Koppen: BIBLIOTHEEK, HUIDIG BOEK, AI-CONTEXT, PROGRAMMA.

### Boek open, AI uit, Advanced uit
- Boekenplank
- Inhoud
- Planning
- Media
- Boekdetails
- Exporteren
- Instellingen
- Prullenbak

Geen AI-CONTEXT, geen Schrijverspersona, geen Integriteit.

## B. Volledige 16-toestandenmatrix

Loop runtime door:
- boek open/dicht;
- AI aan/uit;
- Advanced aan/uit;
- rail uitgeklapt/ingeklapt.

Controleer voor elke toestand:
- geen kop zonder zichtbaar item;
- geen boekitem zonder open boek;
- geen AI-CONTEXT, Boekgeheugen, Boekprofiel of Schrijverspersona wanneer AI uit is;
- geen Integriteit wanneer Advanced uit is;
- ingeklapte rail toont geen groepskoppen;
- itemvolgorde blijft stabiel.

## C. Preview is alleen rendering

1. Open een boek, ga naar Boekgeheugen, open Instellingen.
2. Zet AI uit zonder op te slaan.
   - Boekgeheugen/Boekprofiel/Schrijverspersona en AI-CONTEXT verdwijnen direct uit de rail.
   - De huidige pagina blijft Instellingen.
   - `_settings_return_page` blijft Boekgeheugen.
   - Een reeds geopend AI-paneel/invoer mag door preview niet verloren gaan.
3. Verlaat Instellingen zonder save: opgeslagen toestand en rail keren volledig terug.
4. Herhaal en **sla wel op**: pas nu wordt `_settings_return_page` Inhoud en AI-paneel mag sluiten.

Herhaal hetzelfde met Integriteit + Advanced uit: preview redirect niet; commit valt terug op Inhoud.

De renderer `_render_rail()` mag zelf geen `setCurrentWidget`, rechterpaneelactie, save of `QSettings`-read uitvoeren.

## D. Boek openen/sluiten en herstart

- Koude start: schoon model zoals A.
- Boek openen: HUIDIG BOEK verschijnt direct; AI-CONTEXT alleen volgens AI-setting.
- Terug naar Boekenplank: alle boek- en AI-CONTEXT-items verdwijnen direct.
- Boek verwijderen/future-format detach: zelfde eindtoestand, geen halve rail.
- Herstart met AI uit / Advanced uit: de rail moet onmiddellijk de opgeslagen toestand tonen, zonder eerst een menu te hoeven openen.

`active_book` is runtime-state, geen persistente setting. Bevestig dat 0.33.0 nergens een fictieve `active_book`-setting introduceert.

## E. Lage schermhoogte / scrollgedrag

Met boek open, AI aan, Advanced aan:

Meet op **1280×700**, **1280×720** en **1366×768**, rail zowel open als dicht.

Verwachting:
- venster wordt niet door de rail hoger gedwongen dan gevraagd;
- navigatie blijft bereikbaar via verticale scroll wanneer nodig;
- geen horizontale scrollbar;
- labels breken niet af doordat de verticale scrollbar breedte afneemt;
- scrollbar is smal (5 px QSS; praktisch <= 8 px toegestaan);
- Menu blijft bovenaan buiten het scrollende deel bereikbaar.

Maak bij voorkeur screenshots op 700 en 768 px.

## F. Informatiearchitectuur en tekst

Controleer visueel:
- **AI-CONTEXT** is de kop boven Boekgeheugen + Boekprofiel;
- Schrijverspersona staat onder PROGRAMMA;
- Persona-uitleg zegt duidelijk: globale schrijfstijl/voorkeuren, alle boeken, AI-context;
- Boekprofiel zegt: dit specifieke boek/projectkenmerken, AI-context;
- Boekgeheugen zegt: wat AI over dit boek moet blijven weten;
- `Boek bevat 12.345 woorden` blijft intact;
- conflictmelding gebruikt generiek **Actie niet uitgevoerd**, niet meer **Structuuractie niet uitgevoerd**.

## G. Regressie

Herhaal minimaal de basislijn uit ronde 33:
- koude start;
- ronde 31 notities / bronbehoud;
- publicatietekst 18/18;
- editorbron 8/8;
- ronde 28 30/30;
- settings-preview/rollback;
- transactionele adopt/conflictflows uit 0.31.

## Afbakening

0.33.0 mag **niet** bevatten:
- data-/boekformaatmigratie;
- nieuwe AI-context in prompts;
- automatische personageherkenning;
- `In dit hoofdstuk`;
- Planning→AI-automatisering.

Als deze review alleen kleine state/layout/textcorrecties oplevert, gaan die naar 0.33.1 en sluiten we daarna 0.33.
