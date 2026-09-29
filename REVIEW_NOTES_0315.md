# Review notes 0.31.5 — reviewronde 24

## Doel van deze build

0.31.5 sluit het laatste bekende punt uit reviewronde 21: een fout tijdens het maken van een `conflict_local`-snapshot mocht niet langer plaatsvinden nadat editor/Planning al naar het nieuwe `Book`-object waren omgebonden.

De architectuur is nu:

1. `_prepare_active_book_adoption()` leest de fallible bronnen;
2. Boekprofiel, Boekgeheugen en Boekdetails berekenen daar hun drie-wegs merge;
3. eventuele `conflict_local`-recoveryversies worden **in deze preflight** geschreven;
4. pas als alles slaagt start de commit/rebind van alle pagina's;
5. conflictmeldingen volgen pas nadat `_active_book` en `track_book()` zijn gecommit.

De merge-semantiek hoort niet veranderd te zijn: local-only blijft lokaal, disk-only volgt schijf, same-field conflict houdt schijf live en bewaart de volledige lokale invoer in History.

## Hoofdtest: failure injection op de drie recovery-snapshots

Test dit in een echte `MainWindow` met PySide6. Maak telkens een same-book externe reload waarbij hetzelfde veld lokaal én extern gewijzigd is, en laat precies de recovery-write falen (bijvoorbeeld `StorageWriteError`/gesimuleerde Windows-lock in `create_version_with_file_overrides`).

### A. Boekgeheugen

- lokaal één geheugenveld dirty;
- extern hetzelfde veld anders wijzigen;
- laad de nieuwe `Book` en roep de centrale adopt-route aan;
- forceer de `conflict_local`-snapshot voor `ai/memory.md` te falen.

**Verwacht:** adoptie breekt af vóór de eerste page-rebind. `_active_book`, editor, Planning, Boekprofiel, Boekgeheugen, Boekdetails, Media, Integriteit en Export blijven allemaal op het oude live `Book`-object. De lokale tekst blijft zichtbaar/dirty. Geen merge-conflictmelding vóór de fout.

### B. Boekprofiel

Zelfde test voor `ai/boekprofiel.md`.

### C. Boekdetails

Zelfde test voor een dubbel gewijzigd metadata-veld in `book.json`.

Controleer vooral dat de failure in alle drie gevallen **geen gemengde identiteit** meer oplevert. Dit was de enige bekende FAIL in de ronde-21 regressiereeks.

## Succespad na preflight

Voor elk van de drie pagina's ook één succesvolle same-field conflict-adoptie:

- recovery snapshot bestaat in History en bevat de lokale invoer;
- schijfwaarde is live voor het conflicterende veld;
- local-only velden blijven lokaal;
- disk-only velden volgen schijf;
- na adoptie refereren alle boekgerichte pagina's en `_active_book` aan exact hetzelfde nieuwe `Book`-object;
- de gebruikersmelding verschijnt pas ná die volledige commit.

## Regressie die expliciet groen moet blijven

1. Volledige testsuite en alle bestaande regressiescripts.
2. Reviewronde 23 / 0.31.4 twee-computersscenario op Export:
   - extern hoofdstuk gewijzigd → exportoptie → zichtbare reload, geen excepthook;
   - export/settings zelf extern gewijzigd → externe keuze blijft live;
   - dirty manuscript/publicatietekst blijft veilig bij alle conflictkeuzes.
3. Afgekapte `export/settings.json` blijft fail-closed en herstelbaar via Integriteit.
4. Beschadigd Voorwoord/Nawoord blijft via Integriteit byte-exact herstelbaar.
5. Spelling katt/matt, eerste klik en snel typen blijven groen.
6. Corrupte JSON/UTF-8 regressies blijven byte-safe.

## Specifieke observatie voor deze ronde

Injecteer ook één fout nadat een eerdere preflight-snapshot al succesvol is gemaakt, bijvoorbeeld Boekprofiel snapshot slaagt en Boekgeheugen snapshot faalt. Een extra herstelversie in History is acceptabel; de **live UI mag nog nergens zijn omgebonden**.

## Bekende niet-functionele UI-opmerking

De tekst `Structuuractie niet uitgevoerd` bij een exportconflict met openstaande publicatietekst is bewust niet in deze architectuurbuild aangepast. Het gedrag is veilig; alleen de woordkeus is generiek/ongelukkig en mag in een latere UI-polishronde worden meegenomen.

## Eigen visuele test voor Lucas

Er is voor deze build weinig nieuws dat visueel getest moet worden. Als je iets wilt nalopen:

- maak Boekgeheugen of Boekprofiel dirty, verander hetzelfde veld extern en trigger een reload/conflict;
- controleer dat de uiteindelijke melding logisch verschijnt en dat je lokale invoer in History terug te vinden is.

De lock/failure-injection en object-identiteitscontrole zijn nadrukkelijk Claude-tests.
