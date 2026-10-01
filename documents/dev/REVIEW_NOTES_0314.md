# Review notes 0.31.4

## Hoofddoel

Reviewronde 23. Controleer eerst de drie bevindingen uit `QUIETWRITER_REVIEW_FINDINGS_22.md`. Gebruik voor UI/conflictgedrag waar mogelijk de echte `MainWindow` met PySide6 en `QTest`. De transactionele adopt-commit uit ronde 21 is nog **bekend open** en hoort pas bij 0.31.5.

## Claude — technische/runtime tests

1. **Export na externe hoofdstukwijziging — zichtbaar en veilig**
   - Open een boek en zorg dat Editor/Publicatie schoon is.
   - Wijzig daarna buiten QuietWriter één hoofdstukbestand, alsof Dropbox vanaf een andere computer synchroniseerde.
   - Open Exporteren en klik eenmaal op een ander formaat of een optie.
   - Verwacht: geen exception naar `sys.excepthook`; instelling wordt niet stil opgeslagen; de nieuwste boekversie wordt centraal geadopteerd; er verschijnt een korte melding dat de nieuwste versie is geladen en de exportinstelling opnieuw gekozen moet worden.
   - Controleer dat alle pagina's na de reload hetzelfde live `Book`-object gebruiken.

2. **Export na externe wijziging van `export/settings.json`**
   - Zelfde proef, maar wijzig alleen `export/settings.json` buiten QuietWriter.
   - Verwacht dezelfde zichtbare reloadflow en geen overschrijving van de externe bytes vóór de reload.
   - Kies daarna de instelling opnieuw en controleer dat de tweede keuze normaal wordt opgeslagen en de revision-baseline groen is.

3. **Dirty editor/publicatie tijdens exportconflict**
   - Forceer voor de runtime-test een dirty manuscripteditor of pending publicatietekst en laat daarna een externe boekwijziging ontstaan.
   - Trigger `_persist_settings()` via een echte Export-UI-actie.
   - Verwacht: delegatie naar de bestaande editor-conflictflow; lokale pending tekst mag niet door een automatische reload verdwijnen.

4. **Afgekapte `export/settings.json`**
   - Maak syntactisch afgekapt maar geldig UTF-8 JSON.
   - Open Exporteren.
   - Verwacht: pagina direct fail-closed/disabled met de bestaande melding om Integriteit te openen; klikken veroorzaakt geen `CorruptSourceError` naar de excepthook; bytes blijven identiek.
   - Integriteit moet `export/settings.json` als herstelbaar probleem tonen.

5. **Beschadigde vrije publicatietekst via Integriteit**
   - Zet ongeldige UTF-8 in `publication/texts/foreword.md`; herhaal bij voorkeur met een achterwerk-item.
   - Open het item: alleen-lezen herstelmelding blijft correct.
   - Open Integriteit: exact dat pad moet als `aux_text_invalid`, severity error en recoverable verschijnen.
   - Herstel vanuit History en controleer byte-inhoud, centrale reload en daarna normale bewerkbaarheid van Voorwoord/Achterwerk.

6. **Geen regressie in normale Export**
   - Zonder externe wijzigingen: wissel meerdere keren formaat/template/marges/vinkjes.
   - Schrijf daarna verder in het manuscript.
   - Verwacht: geen vals extern conflict; `export/settings.json` verandert alleen door echte gebruikersacties, niet door `set_book()`/adopt/openen.

7. **Volledige regressie**
   - Volledige testsuite en regressiescripts uit de vorige rondes.
   - Controleer speciaal ronde 21/22: spelling katt/matt, eerste klik, JSON fail-closed, publicatietekst alleen-lezen en navigatiegap.

## Bekend open — niet als regressie rapporteren

De transactionele `adopt_active_book()`-commit uit ronde 21 punt 6 blijft open: een schrijffout tijdens het maken van een `conflict_local`-snapshot kan nog een gemengde pagina-state achterlaten. Dit is de geplande architectuurfix voor **0.31.5**. Test hem desgewenst als baseline, maar beoordeel 0.31.4 daar niet op.

## Lucas — visueel/handmatig

1. Gebruik Exporteren normaal: wissel formaat, template en enkele vinkjes. Er mag geen onverwachte melding of hapering zijn.
2. Als je eenvoudig twee gesynchroniseerde computers kunt gebruiken: wijzig op computer B een hoofdstuk terwijl het boek op computer A open staat; klik op A daarna op een exportoptie. Je moet één duidelijke melding krijgen en daarna opnieuw kunnen kiezen. Dit is optioneel, omdat Claude dit scenario technisch kan nabootsen.
3. Open een normaal Voorwoord en Achterwoord na een Integriteit-controle. De editor moet visueel hetzelfde blijven als in 0.31.3.
