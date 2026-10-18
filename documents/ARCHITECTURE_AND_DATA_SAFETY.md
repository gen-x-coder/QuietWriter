# QuietWriter — architectuur en dataveiligheid

Dit is het technische veiligheidscontract van QuietWriter. Bij refactors is dit document belangrijker dan oude reviewversies.

## Kernprincipe
Als een mutatie niet aantoonbaar veilig kan worden uitgevoerd, blijven de bestaande live bytes ongemoeid en blijft lokale invoer zichtbaar of herstelbaar.

## Bronnen van waarheid
- Manuscript is geschreven tekst.
- Planning is intentie/structuur.
- Boekprofiel is projectspecifiek kader.
- Boekgeheugen is duurzame boekkennis.
- Schrijverspersona is globaal.
- Media heeft een eigen manifest en kan onderdeel van History zijn.

Introduceer geen tweede onafhankelijke bron voor dezelfde informatie.

## Revisions en externe sync
QuietWriter gebruikt revision-/hashcontrole en optimistic concurrency, niet Dropbox-specifieke locks. Voor iedere writeroute moet externe wijziging vóór de write worden gedetecteerd. Bij same-book reload mag dirty invoer in een ander scherm nooit als nevenschade verdwijnen.

**Hoofdstuktekst (sinds 1.6.0)** wordt per bestand beoordeeld (`Library._verify_for_chapter_save`):
- alleen *andere* hoofdstukbestanden extern gewijzigd → stil overnemen (niets in QuietWriter houdt die ongeopgeslagen vast) en rustig melden in de statusbalk;
- *dit* hoofdstuk hier én elders gewijzigd, en alleen hoofdstuktekst → beide bewaren zonder dialoog (`save_chapter_keep_both`): eerst een `conflict_local`-versie, dan de schijfversie als nieuw hoofdstuk direct eronder, dan de lokale tekst in het hoofdstuk zelf. Elke tussenstand na een crash verliest niets; een fout bij het schrijven draait alles behalve de veiligheidsversie terug (`_rollback_keep_both`: oude bytes van `book.json`, extra bestand weg, bewaakte stand terug) en valt terug op de gewone conflictkeuze (sinds 1.6.1);
- open hoofdstuk onveranderd en extern bijgewerkt → bij terugkeer in de app stil herladen (`refresh_open_chapter_from_disk`);
- `book.json`, Planning, profielen, publicatie → de bestaande expliciete conflictkeuze blijft.

**Dagversies** worden (instelbaar, standaard aan) uitgedund: alles < 30 dagen, daarna één per week, na 180 dagen één per maand. Alleen soort `daily` zonder ster; handmatige, ★- en veiligheidsversies nooit.

## Atomische writes
Normale writes gebruiken tijdelijk bestand + atomische replace. Een blijvende Windows/sync-lock geeft een fout; er is bewust geen directe truncate/overwrite-fallback. Een fallback mag nooit gevaarlijker zijn dan de fout die hij probeert op te lossen.

## Afsluiten is fail-closed
Als een laatste save faalt, blijft het venster open. Ook onverwachte save-excepties mogen het standaard close-event niet doorlaten.

## Transactionele book adoption
Bookwissels en conflictadoptie volgen **prepare → commit**:
1. bronvalidering en merges;
2. benodigde `conflict_local` snapshots;
3. pas daarna pagina's ombinden;
4. actieve Book/revisionbaseline committen;
5. gebruikersmeldingen achteraf.

Recovery-writes horen dus vóór UI-rebinding.

## History
History is herstelmechanisme, niet alleen versiebrowser. Niet iedere snapshot is automatisch een geldige herstelbron. Herstelbron moet semantisch passen; waar snapshot-bytefideliteit het contract is, is herstel byte-exact.

Belangrijke rollen zijn onder andere conflict-local, pre-migration en pre-repair. Een snapshot van de kapotte toestand is niet automatisch herstelmateriaal.

## Corruptie
Ongeldige UTF-8, kapot JSON en structureel onjuiste data zijn expliciete foutstaten. Ze worden nooit geïnterpreteerd als lege inhoud. Normale save/autosave weigert een corrupte bestaande bron te vervangen. Integriteit/Herstel is de expliciete route die, na validatie, wel mag herstellen.

Waar mogelijk blijft het boek open en degradeert alleen het getroffen onderdeel naar read-only.

## Future formats
Een nieuwere bestandsversie is **niet corrupt**. Oude QuietWriter mag zo'n bestand niet downgraden of 'herstellen' naar een oud formaat. Future Planning kan read-only degraderen; een incompatible Book wordt write-blocked en lokale dirty invoer wordt vóór detach veiliggesteld.

## Detached/write-blocked
Alleen `untrack`en is niet veilig: dan verdwijnen juist revisionguards. Een incompatibel/detached book-id blijft expliciet write-blocked tot het opnieuw ondersteund wordt geopend.

## Drie-wegs merge
Voor geschikte formulierdata: baseline + lokaal + disk.
- alleen lokaal gewijzigd → lokaal behouden;
- alleen disk gewijzigd → disk;
- beide hetzelfde → veilig;
- same-field conflict → disk live, lokale volledige state eerst in History.

## Editor source fidelity
Qt-presentatie is niet de persistente bron. Highlighting, spelling, thema, font, regelafstand en tekstbreedte mogen geen false-dirty of save veroorzaken. Bronkarakters zoals NBSP/U+2028/U+2029 mogen door presentationpasses niet verdwijnen.

Undo/Redo mag niet worden vervuild door verborgen automatische formatting.

## Intern manuscript-/boekformaat

De huidige canonieke manuscriptbron is Markdown per hoofdstuk. Dat is de **huidige werkelijkheid**, niet automatisch een permanent architectuurbesluit.

Vanaf 1.2.13 staat expliciet een nieuw architectuuronderzoek op de roadmap omdat QuietWriter meer semantische functies en meer gebruikers krijgt.

Tot dat onderzoek is afgerond:

- Markdown blijft canoniek;
- bestaande boeken worden niet stil geconverteerd;
- nieuwe features mogen niet ongemerkt een tweede concurrerende manuscriptbron introduceren;
- sidecar-data moet een heldere ownership- en recoveryregel hebben;
- iedere mogelijke formaatwijziging vereist backward/forward compatibility, migratie, History, conflict- en recoveryontwerp.

Het onderzoek moet open tekstformaten, gestructureerde modellen en hybride varianten vergelijken op dataveiligheid, openheid, source fidelity, sync/conflicten, semantiek, export, performance en herstelbaarheid.

Een technisch mooier model is onvoldoende reden om bestaande gebruikersdata te migreren. De aanbevolen oplossing moet aantoonbaar beter zijn voor zowel het product als de veiligheid van echte boeken.

Zie `ROADMAP_AND_IDEAS.md`.

## Media
Afbeeldingen kunnen als beschermd visueel blok worden weergegeven, maar de leesbare Markdownbron blijft canoniek. Search/replace mag image-path/UUID-syntax niet als gewone prozatekst muteren. Cleanup is conservatief: onzekerheid, onleesbare bron of History/trash-referenties betekenen behouden/blokkeren.

## Caches
Zoekindex en soortgelijke caches zijn niet autoritatief. Een corrupte cache mag worden weggegooid en herbouwd. Cachefailure mag schrijven/startup niet blokkeren. SQLite/filehandles worden expliciet gesloten, met name op Windows.

## AI async
Een late callback van een oud boek/gesprek/request mag nieuwe state nooit muteren. Workers moeten voldoende context/generationbinding hebben om stale resultaten te negeren. Netwerk-/availabilitychecks blokkeren de Qt-thread niet.

## AI privacy
- Ollama is lokaal; background warmup is toegestaan.
- OpenRouter is extern; alleen Meelezer openen doet geen request.
- Pas bij een echte vraag gaat geselecteerde context naar OpenRouter.
- Geen autonome persistente AI-writes.

## Contextprecedentie
1. Schrijverspersona
2. Boekprofiel
3. Boekgeheugen
4. expliciet geselecteerde Planning
5. optionele hoofdstukplanning
6. actuele manuscriptcontext

Verschillen worden niet stil gladgestreken; de Meelezer mag inconsistentie benoemen.

## Canonieke opslag versus vertaling
Gelokaliseerde labels zijn display. Bekende opslagwaarden blijven canoniek; custom waarden blijven exact bewaard. Locale-switch mag data niet wijzigen.

## Migraties
Migraties zijn expliciet, maken een checkpoint en worden gevalideerd vóór commit. Geen stille migratie in een gewone open/load-flow. Bij nieuwe schemawijzigingen moet vooraf duidelijk zijn hoe oude versies future-format herkennen.

## Reviewchecklist voor iedere writeroute
- welke file verandert?
- revisionbaseline?
- externe wijziging?
- atomisch?
- lock/failure?
- corrupte bron?
- future format?
- waar blijft dirty lokale state?
- History/checkpoint nodig?
- canonical of afgeleid?
- actieve regressietest aanwezig?

## Write-auditmethode

Wanneer persistente schrijfroutes opnieuw worden geaudit, controleer niet alleen de centrale atomic helpers. Zoek minimaal naar:

- `_safe_atomic_write_text` / `_safe_atomic_write_bytes`;
- `atomic_write*`;
- `.write_text(` / `.write_bytes(`;
- `json.dump(` / vergelijkbare directe serializers;
- databasewrites die gebruikersdata of herstelstate bevatten.

Classificeer iedere route als:
- canonieke gebruikersdata;
- herstel/history;
- afgeleide cache/log;
- bewuste last-writer-wins uitzondering.
### Transactionele externe import

DOCX-import publiceert nooit incrementeel naar een zichtbare boekmap. De volledige import wordt eerst opgebouwd in een verborgen stagingmap onder `books/`. Pas nadat `book.json` kan worden geladen en alle gerefereerde hoofdstukbestanden bestaan, wordt de stagingmap binnen hetzelfde bestandssysteem naar de definitieve boekmap hernoemd.

Een fout vóór die rename mag alleen stagingdata achterlaten en geen zichtbaar half boek. Normale afgevangen fouten ruimen staging direct op. Een procescrash kan hoogstens een verborgen `.import-*`-map achterlaten; deze map wordt niet door `list_books()` als boek aangeboden en bevat dus geen half gepubliceerd boek.

