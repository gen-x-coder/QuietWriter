# Review notes 0.31.6 — reviewronde 25

0.31.6 richt zich uitsluitend op het zeldzame randgeval uit reviewronde 24: een gebruiker heeft lokale, niet-opgeslagen invoer open terwijl precies het bijbehorende Markdown-bronbestand extern beschadigd raakt (ongeldige UTF-8).

## Verwachte hoofdregel

Een onleesbare eigen bron mag nooit meer de normale conflictflow blokkeren. QuietWriter moet dan:

1. de lokale dirty invoer als `conflict_local` in Versiegeschiedenis veiligstellen;
2. de live corrupte bytes onaangeroerd laten;
3. de nieuwste boekversie transactioneel adopteren;
4. de betreffende pagina in de bestaande alleen-lezen-foutstaat openen;
5. navigeren, Integriteit en afsluiten weer mogelijk maken;
6. pas na een geslaagde commit melden dat de lokale invoer in History staat.

Als het herstelpunt zelf niet geschreven kan worden, moet de 0.31.5-garantie blijven gelden: de volledige oude workspace blijft intact en dirty.

## A. Boekgeheugen — exacte reproductie uit ronde 24

- Open een boek en wijzig Boekgeheugen zonder op te slaan.
- Beschadig extern `ai/memory.md` met ongeldige UTF-8.
- Trigger een save/navigatie die normaal `ExternalModificationError` geeft.

Controleer:
- er verschijnt **geen** mine/disk-keuzedialoog voor deze onleesbare bron;
- de lokale tekst komt byte-/tekstgetrouw in een `conflict_local`-versie;
- het live `ai/memory.md` blijft byte-identiek corrupt;
- na adoptie zijn alle negen boekreferenties op exact hetzelfde nieuwe `Book`-object;
- Boekgeheugen toont de bestaande beschadigd/alleen-lezen-staat;
- navigeren naar Integriteit werkt;
- afsluiten werkt;
- na herstel via Integriteit kan Boekgeheugen weer normaal bewerkt en opgeslagen worden.

Herhaal ook via een **onverwante externe wijziging** (bijv. hoofdstuk/exportinstelling) terwijl Boekgeheugen dirty is en `ai/memory.md` corrupt is. De centrale preflight moet dezelfde veilige uitkomst geven.

## B. Boekprofiel

Herhaal A voor `ai/boekprofiel.md` en dirty Boekprofiel. Controleer dezelfde zes eigenschappen plus herstel via Integriteit.

## C. Planning-notities

- Maak Planning > Notities dirty.
- Beschadig extern `planning/notes.md` met ongeldige UTF-8.
- Trigger zowel een directe Notes-save als een adoptie via een andere externe boekwijziging.

Controleer:
- lokale notities staan in `conflict_local` History;
- live corrupte bytes blijven onaangeroerd;
- Notities opent read-only met de bestaande corruptiemelding;
- de pending lokale tekst wordt **niet** na `load()` opnieuw over de foutstaat heen gezet;
- de autosave-timer veroorzaakt geen nieuwe conflictlus;
- Integriteit is bereikbaar en herstel maakt Notities weer bewerkbaar.

## D. Failure-injection

Laat `create_version_with_file_overrides` falen tijdens de corrupt-preflight voor:

1. Boekgeheugen;
2. Boekprofiel;
3. Planning-notities.

Verwacht telkens:
- exception/foutmelding volgens de bestaande flow;
- geen enkele pagina omgebonden;
- `_active_book` blijft oud;
- lokale invoer blijft zichtbaar en dirty;
- corrupte live bytes blijven onaangeroerd.

## E. Regressie

Draai de volledige suite en alle eerdere regressies. Let extra op:

- ronde 24 transactionele adopt: 5/5 failure-injection + succespad;
- ronde 23 Export/twee-computersscenario;
- spelling katt/matt + eerste klik;
- corruptieguards en Integriteit;
- normale, geldige Boekgeheugen-/Boekprofiel-/Notities-conflicten: mine/disk-keuzes blijven onveranderd als de bron gewoon leesbaar is.

## Visueel/handmatig

Beoordeel op echt Qt-scherm alleen:

- de bestaande read-only corruptiestaat blijft rustig en volgens `UI_GUIDE.md`;
- de nieuwe melding “lokale invoer/notities veilig bewaard” verschijnt pas nadat de pagina werkelijk read-only op de nieuwe live book state staat;
- geen dubbele meldingen of flits van oude lokale tekst na adoptie.

## Bekend buiten scope

- Echte Dropbox timing en echte Windows locks blijven alleen aanvullend; failure-injection is voldoende voor de releasebeoordeling.
- De eerder genoteerde tekst “Structuuractie niet uitgevoerd” bij een exportconflict met publicatietekst is nog een UI-woordkeuze en geen onderdeel van 0.31.6.
