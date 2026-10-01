# QuietWriter reviewronde 26 — versie 0.32.0

## Doel van deze ronde

0.31.6 is door Claude groen bevonden: 579 tests, alle regressies 9–25 groen, geen bekende open defecten. 0.32.0 verlaat daarom bewust de stabiliteitsreeks en start de eerste UI/editor-polishstap.

Deze release heeft vier veranderingen die runtime in de echte `MainWindow` moeten worden getest:

1. AI aan/uit stuurt nu alle AI-oppervlakken.
2. Nieuwe instelling Geavanceerde opties stuurt voorlopig alleen Integriteit.
3. Spellingscontrole uit verwijdert rode markeringen zonder herstart.
4. Integriteit toont de herkomst van de herstelkopie.

## 1. AI-functies tijdelijk uitschakelen

Test met een geopend boek waarin Schrijverspersona, Boekprofiel en Boekgeheugen herkenbare tekst bevatten.

- Instellingen → AI → **AI-assistent gebruiken** uit → Opslaan.
- Verwacht direct:
  - AI-knop rechts verdwenen;
  - Schrijverspersona links verdwenen;
  - Boekprofiel links verdwenen;
  - Boekgeheugen links verdwenen;
  - groep SCHRIJVEN verdwijnt als daardoor geen item meer over is;
  - Inhoud, Planning, Media, Boekdetails en Exporteren blijven normaal zichtbaar.
- Controleer byte-exact dat `persona/schrijver.md`, `ai/boekprofiel.md` en `ai/memory.md` niet zijn gewijzigd door alleen deze instelling.
- Zet AI daarna weer aan en sla op.
- Verwacht dat alle vier de UI-oppervlakken direct terugkomen en dezelfde inhoud tonen.

Extra routes:
- Open eerst Boekgeheugen, ga daarna naar Instellingen en zet AI uit. Na Opslaan/teruggaan mag QuietWriter niet naar een verborgen Boekgeheugenpagina terugkeren maar naar Inhoud.
- Doe hetzelfde vanuit Schrijverspersona en Boekprofiel.
- Laat vóór het uitschakelen het AI-paneel rechts open staan. Na Opslaan moet dat paneel gesloten zijn en mag het niet door restored window state terugkomen.

## 2. Geavanceerde opties

- Nieuwe/default settings: **Geavanceerde opties gebruiken** moet aan staan.
- Met geopend boek: uit → Opslaan:
  - Integriteit verdwijnt;
  - de 6 px scheiding vóór Integriteit verdwijnt ook;
  - andere boekfuncties veranderen niet.
- Aan → Opslaan: Integriteit en de bestaande scheiding komen direct terug.
- Open eerst Integriteit, ga dan naar Instellingen, zet Geavanceerde opties uit en sla op. Terugkeren moet naar Inhoud gaan, niet naar een verborgen pagina.
- Controleer dat deze instelling geen boekbestanden wijzigt.

Let UX-matig op de tekst en positie onder Instellingen → Algemeen. Voor 0.32.0 valt bewust alleen Integriteit onder deze schakelaar.

## 3. Spellingscontrole zonder herstart

Dit is een expliciete gebruikersreproductie.

1. Open een hoofdstuk met meerdere zichtbare rode spellingsonderstrepingen.
2. Instellingen → Spelling → spellingscontrole uit → Opslaan.
3. Klik terug naar Inhoud zonder QuietWriter opnieuw te starten.
4. Verwacht **direct geen rode onderstrepingen**.
5. De spellingsknop rechts is verborgen.
6. Typ enkele woorden: de onderstrepingen mogen niet terugkomen.
7. Zet spelling weer aan → Opslaan: onderstrepingen komen terug wanneer een woordenboek beschikbaar is.

Extra: herhaal terwijl het Spellingspaneel zelf open staat. Uitschakelen moet het paneel sluiten zonder focus-/splitterproblemen.

Controleer dat deze presentatie-refresh geen manuscript-dirty state, Ctrl+Z-stap of tekstwijziging veroorzaakt.

## 4. Herkomst herstelkopie in Integriteit

Maak een herstelbaar corrupt bestand met als nieuwste geldige History-bron een `conflict_local`-snapshot.

- Integriteit → selecteer issue.
- Verwacht naast “geldige herstelkopie” ook iets als **Herstelkopie: lokale conflictversie van 21:34**.
- Bij handmatige/dagversie moet het type passend wijzigen.
- Herstel zelf moet exact hetzelfde kandidaatbestand kiezen als 0.31.6; dit is alleen transparantie, geen gewijzigd herstelbeleid.
- Controleer dat herstel byte-exact blijft en revision tracking groen is.

## 5. Regressie

Draai de volledige suite en alle bestaande regressiereeksen 9–25. Bijzonder belangrijk:

- ronde 24 transactionele adopt: alles-of-niets blijft intact;
- ronde 25 corrupte dirty bron: lokale invoer veilig naar History, geen dead-end;
- ronde 21–23 export/spelling/conflictflows;
- AI worker/state regressies uit 0.21.x–0.23.x;
- navigatie 0.31.0/0.31.1.

## 6. Visuele beoordeling

Graag naast QTest/headless ook melden of deze drie dingen visueel logisch voelen:

- de linker rail wanneer AI uit staat;
- Algemeen met de nieuwe Geavanceerde opties-regel;
- het verdwijnen/terugkomen van rode spellingsstrepen in een echt zichtbaar editorvenster.

Niet als bug beschouwen zonder reproductie: de twee bekende fonttests kunnen in een omgeving zonder gebundelde fontresources blijven falen.
