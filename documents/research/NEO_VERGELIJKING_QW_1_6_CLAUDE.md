# QuietWriter 1.6 vs. NEO 1.5.5 — vergelijking en advies

*Claude, 15 oktober 2026*

---

## 0. Wat ik heb gedaan, en wat niet

**Wel gedaan**
- QuietWriter-bron uit `QuietWriter-1.6.zip` doorgelopen: 452 Python-bestanden, ca. 58.600 regels, 251 testbestanden en de map `documents/` (filosofie, roadmap, ontwerpdocumenten).
- NEO `main` (1.5.5, 14–15 oktober 2026) doorgelopen: `README`, `AGENTS.md`, `CONTRIBUTING`, `TUTORIAL`, `TRANSLATING`, `package.json`, de bestandsindeling en de opslag-/sync-/snapshotregels. De volledige git-geschiedenis (508 commits) heb ik apart opgehaald.
- NEO-issues: alle ±170 issue- en PR-nummers die in commitberichten voorkomen, plus **ongeveer 55 losse issues, PR's en discussies** die ik één voor één heb geopend. Daarbij heb ik vooral gezocht naar verzoeken die níét in een commit terugkomen: open, afgewezen of nog in discussie.

**Niet gedaan / niet te testen**
- **Geen van beide apps gedraaid.** Alle UX-uitspraken komen uit code, documentatie en issues, niet uit eigen gebruik. Wat ik over QW-gedrag zeg is "zoals ik de code lees". Controleer het dus op Windows.
- **De issuelijst van NEO kon ik niet in één keer ophalen.** De GitHub-pagina rendert via JavaScript en de API was vanuit deze sessie geblokkeerd. Ruim 400 nummers één voor één openen was niet haalbaar. De analyse rust dus op een **steekproef plus de commitgeschiedenis**. Er kunnen goede ideeën tussen de ongeveer 175 nummers zitten die ik niet heb geopend.
- Geen performance-, DPI- of Dropbox-metingen.
- **Versie-opmerking:** de zip heet *1.6*, maar `quietwriter/__init__.py` en `SNAPSHOT_INFO.txt` zeggen **1.5.0-dev.63**. Dat is niet erg, maar laat de bestandsnaam en de interne versie gelijklopen voordat je publiceert.

---

## 1. Samenvatting in één tabel

Prioriteit: **H** = hoog (veel waarde, redelijk werk), **M** = midden, **L** = later of laag. "Niet" = bewust niet doen (onderbouwing in §5).

| # | Advies | Terrein | Prio | Waarom in één zin |
|---|---|---|---|---|
| 1 | **Stop met de eigen updater**; gebruik Velopack, een Inno Setup-installer of winget | Distributie/code | **H** | ~2.250 regels en tientallen dev-versies voor iets wat nog uit staat; NEO lost dit op met een standaardtool |
| 2 | **Geschiedenis als delta + uitdunnen** (alleen gewijzigde hoofdstukken, dagversies na 30 dagen weg, handmatige en gesterde versies blijven) | Data | **H** | De dagelijkse volledige `copytree` (incl. media) in de Dropbox-werkmap groeit nu onbeperkt |
| 3 | **Conflicten per hoofdstuk en zonder modale dialoog**; bij "beide gewijzigd" beide versies bewaren | Data/UX | **H** | Een wijziging elders in het boek mag niet midden in een zin een keuzedialoog geven ("Blijf schrijven") |
| 4 | **Exportdoel "Inzenden" (standaard manuscriptopmaak)** | Export | **H** | Past naadloos in je doelgerichte exportwizard en is precies wat schrijvers voor uitgeverijen en wedstrijden nodig hebben |
| 5 | **Typografie tijdens typen per taal**: gedachtestreepje, beletselteken, enkele aanhalingstekens/apostrof | Editor | **H** | QW doet nu alleen dubbele aanhalingstekens; goedkoop en dagelijks voelbaar |
| 6 | **`AGENTS.md`-achtig kort invariantenbestand** voor ChatGPT en Claude | Proces | **H** | Jullie werken met z'n drieën; NEO bewijst hoeveel één compact regelbestand oplevert |
| 7 | **Scène-ID's als koppeling tussen Planning en tekst** + "meelopende" planningsnotitie in een lege scène | Planning | M | Dit is jouw eigen wens (planning dichter bij het verhaal) en NEO laat zien hoe het werkt |
| 8 | **Ongedaan maken voor structuuracties** (hoofdstuk verplaatst/verwijderd), met een melding waar de woorden heen zijn | UX | M | NEO's #241 en #377; QW heeft een prullenbak maar geen Ctrl+Z op structuur |
| 9 | Sneltoetsenoverzicht (Ctrl+/), boektitel in de venstertitel, UI-zoom | UX/toegankelijkheid | M | Klein werk; NEO-issues #357, #350, #364 en #97 laten zien dat gebruikers erom vragen |
| 10 | **Voorlezen** (QtTextToSpeech) als revisiehulp | Editor | M | Hardop horen is een van de beste revisietechnieken; ingebouwd in PySide6 |
| 11 | Spelling in een **apart proces** (spylls is pure Python) | Code | M | NEO draait Hunspell in een worker-proces; jouw `SPELLING_HANG_ANALYSE` wijst al dezelfde kant op |
| 12 | Vertaalproces: `TRANSLATING.md`, sjabloon met context, controlescript, meervoudsvormen | i18n | M | NEO ging van 1 naar 14 talen dankzij vertalers zonder programmeerkennis |
| 13 | Rustige 30-dagengrafiek in de voortgang, **zonder sprints** | Doelen | L/M | Sluit aan bij je v2-wens; sprints bewust niet |
| 14 | Paperback-PDF (KDP/Brave New Books) met Nederlandse woordafbreking | Export | L | Waardevol, maar groot werk (afbreking, spiegelmarges, bijsnijdformaten) |
| — | Enter-Enter-Enter, AI-omslagen, scenario's/strips, mobiele app, vim-toetsen, tekstkleur, auto-hoofdletters, e-mail-naar-jezelf | — | **Niet** | Zie §5 |

---

## 2. Twee filosofieën naast elkaar

Op papier liggen ze dicht bij elkaar. NEO's regels ("Nothing interrupts a writer mid-sentence", "Words are never lost", "Plain files", "bloat killed every writing app") lezen bijna als QW's `PRODUCT_AND_UI_PHILOSOPHY.md` ("Blijf schrijven", "Anti-bloat", "Lokaal en van jou"). Het verschil zit in de **uitvoering**:

| | NEO | QuietWriter |
|---|---|---|
| Houding | Eigenwijs en automatisch: de app doet dingen vóór je (Enter×3 = hoofdstuk, nummering, typografie, initialen) | Expliciet en voorspelbaar: de schrijver beslist, de app is transparant |
| Interface | Alles verdwijnt tot je eroverheen beweegt; de pagina ziet eruit als een boek | Rustig maar zichtbaar: linkerrail, contextpanelen, 15 thema's |
| Groei | Feature-tempo: van 0.x naar 1.5.5 in ongeveer zes weken, ~400 issues/PR's, veel community-PR's | Hardening-tempo: lange dev-reeksen, reviews, integriteit, herstel |
| AI | Alleen voor schilderijomslagen (OpenAI); geen tekst-AI | Meelezer als kernonderscheid; nadrukkelijk geen ghostwriter |
| Data | HTML per hoofdstuk + JSON | Markdown per hoofdstuk + JSON, `.qwbook`-pakket |
| Platforms | macOS, Windows, Linux, Android en iOS (Pocket) | Windows (portable) |

**Mijn conclusie:** neem van NEO vooral de *schrijfmomenten* over (kleine automatismen die je niet uit je zin halen, planning die uit de tekst voortkomt) en de *pragmatiek* (standaardtools, één regelbestand). Neem het *feature-tempo* niet over: de kracht van QW is juist dat het niet alles doet. Je README zegt dat zelf mooi: "Adding more buttons is easy."

**Waar QW nu al sterker is dan NEO**, en wat je dus moet koesteren:
- **Exportwizard op doel** ("lezen op e-reader", "naar Word", "back-up") tegenover NEO's platte exportmenu. Dat is betere UX.
- **Meelezer met inspecteerbare contextlagen** (Persona, Boekprofiel, Boekgeheugen, Planning). NEO heeft niets vergelijkbaars, en de NEO-issues vragen er ook niet om. Dat maakt het je onderscheid, geen achterstand.
- **Integriteit en herstel zichtbaar** (pagina Integriteit, conflictkopieën, `.qwbook` met controles). NEO lost veel stil op; QW maakt het uitlegbaar.
- **Tests en CI.** NEO heeft tests, maar draait ze niet in CI (alleen een Windows-rooktest). QW heeft 251 testbestanden en een release-gate.
- **Privéplanken**: NEO heeft pseudoniemen, maar geen "verberg tijdens schermdelen".

---

## 3. Wat NEO sinds het vorige onderzoek heeft toegevoegd

Wat relevant is om te vergelijken (uit README, AGENTS en commits van 1.3 tot 1.5.5):

- **Outline als systeemkaartjes** die uit het manuscript voortkomen (elk hoofdstuk en elke `***`-sectie is een kaart); losse kaarten; meerdere selecteren; een lijst plakken wordt kaarten.
- **Kaarten naast de pagina**: tijdens het schrijven toont het rechterpaneel de kaarten van de plek waar je cursor staat; klik op de naam springt naar die plek (#367).
- **Meelopende spooknotitie**: de notitie van een sectie staat grijs in de tekst en loopt één regel onder je woorden mee tot je hem wegklikt.
- **Snapshots** (⌘S plus automatisch één per schrijfdag), als delta's opgeslagen, met een alleen-lezenweergave waarin "verdwenen woorden" gemarkeerd zijn; één hoofdstuk of het hele boek terugzetten.
- **Notities per hoofdstuk** en **voetnoten** (1.5.3).
- **Structureel ongedaan maken** (50 stappen, met opnieuw).
- **Manuscriptopmaak** (Shunn-standaard) als Word of PDF.
- **Paperback voor KDP**: bijsnijdformaten, rugmarges per paginabereik, TeX-woordafbreking, omslagsjabloon.
- **Planken binden tot één boek** (omnibus/trilogie).
- **Scenario's** (Fountain/Final Draft), **Pocket** (Android/iOS), **voorlezen**, **opzoeken** (macOS-woordenboek), **paginabreedte**, **instellingen per apparaat**, **boek dupliceren**, **exporteren vanaf de boekenkast**, **titel in de vensterbalk**.
- Robuustheid: `.bak`/`.tmp`-terugval voor JSON, `book.json` herbouwen uit hoofdstukbestanden, iCloud-placeholders, melding bij Windows *Controlled Folder Access*.

---

## 4. Analyse per terrein

### 4.1 Schrijven en editor

**Doen — typografie per taal tijdens het typen (H).**
QW zet nu alleen een recht `"` om (`manuscript_editor.py`, `smart_double_quote`). NEO doet daarnaast `--` → streep, `...` → `…`, enkele aanhalingstekens en apostrof. Bovendien volgt NEO de aanhalingstekenstijl van de **spellingtaal** (`QUOTE_STYLES`; Duits standaard `»…«`, #109 en #286). Voor QW:
- `'` → `’` binnen een woord (*zo’n*, *auto’s*) en `‘…’` als paar; dat is in het Nederlands veel vaker nodig dan dubbele aanhalingstekens.
- `--` → `–` (Nederlands gebruikt het gedachtestreepje met spaties, Engels het `—` zonder). Dat verschil hoort per taal in de configuratie.
- `...` → `…`.
- Eén instelling "Typografie tijdens typen" (aan/uit), dus geen aparte schakelaar per teken.
- **Let op:** NEO-issue #138 ("a quote after a dash closes speech") en #158 (losse streep in dialoog) laten zien dat de randgevallen zitten in dialoog na een gedachtestreep. Schrijf daar tests voor; NEO heeft er een eigen `dashes.test.js` voor.

**Niet doen — automatische hoofdletter aan het begin van een zin** (NEO #196). In het Nederlands breekt dat direct: *'s Avonds*, *'t Is* en *'s-Hertogenbosch* beginnen met een kleine letter na het weglatingsteken, en afkortingen (*o.a.*, *bijv.*) zien eruit als een zinseinde. Een automatisme dat je moet terugdraaien is erger dan geen automatisme.

**Doen — sneltoetsenoverzicht (M).** NEO heeft ⌘/ / Ctrl+/ met een overzicht. In QW vind ik geen overzicht, terwijl er wel sneltoetsen zijn (Ctrl+Shift+L/R, Ctrl+Shift+Enter enzovoort). Gebruik één rustig paneel van het bestaande "detail"-paginatype. Les uit NEO #349/#385: AMD Radeon-software pakt Ctrl+Shift+X af. Zet in het overzicht dus ook een regel "werkt een sneltoets niet? Andere software kan hem gebruiken."

**Doen — boektitel in de venstertitel (M, klein).** `main_window.py` zet de titel één keer op "QuietWriter". NEO #357: "Mijn boek – NEO". Op Windows helpt dat in de taakbalk en bij Alt+Tab. Let op privéplanken: toon geen titel van een boek op een verborgen plank zolang de privémodus uit staat.

**Doen — UI-zoom en editorzoom (M).** NEO kreeg drie issues over grootte (#97, #350 met 4K-Linux en toegankelijkheid, #364). QW test 100/125/150% DPI, maar heeft geen eigen zoom (ik vind geen `zoom` in de code). Twee niveaus:
- Ctrl+scrollwiel / Ctrl+plus/min in de editor (view state, net als lettergrootte, en nooit opgeslagen in het manuscript).
- Een instelling "Interfacegrootte" (90–200%) via `QT_SCALE_FACTOR` bij het opstarten, dus na een herstart. Dat is eenvoudig en robuust.

**Doen — typemachine-scrollen als optie (L/M).** NEO houdt de cursorregel optisch op vaste hoogte. Het is goedkoop in `QTextEdit` (extra ondermarge plus scrollen naar de cursor) en veel schrijvers zweren erbij. Zet het standaard uit.

**Doen — voorlezen (M).** NEO heeft *Read Aloud*. PySide6 heeft `QtTextToSpeech` en gebruikt op Windows de systeemstemmen. Waarom wel: hardop horen is de klassieke revisietruc en het past bij "reviseren" in je featurecriterium. Waarom voorzichtig: de kwaliteit van Nederlandse stemmen hangt af van wat er in Windows geïnstalleerd is. Begin met alleen "lees selectie/alinea voor" en "stop", zonder stemkeuze-UI.

**Niet doen — Enter-Enter-Enter.** Dat had je al besloten en ik ben het ermee eens. NEO-issue #370 ("No chapter 1 intentional?") en #164 (proloog/delen) laten zien dat impliciete structuur verwarring geeft. QW's expliciete Ctrl+Shift+Enter voor een scènebreuk is beter.

**Niet doen — vim-toetsen, macOS-opzoeken, tekstkleur.** Vim bedient een kleine niche en voegt een modus toe. Opzoeken leunt bij NEO op het macOS-woordenboek, dat Windows niet heeft. Tekstkleur (NEO #116) is daar zelf afgewezen: het is opmaak die niet in export hoort en die alleen afleidt.

**Overwegen — initialen en "het voelt als een boek".** NEO's sterkste emotionele punt is dat de pagina eruitziet als een boek (initiaal, automatische hoofdstuknummers). QW is neutraler. Een *optionele* initiaal in de editor (alleen weergave, nooit in Markdown) is een kleine visuele traktatie die bij een thema als *Papier* of *Lamplicht* past. Lage prioriteit, maar goed voor screenshots en promotie.

### 4.2 Structuur, planning en personages

Hier zit voor jou de meeste inhoudelijke winst. Je wilde personages, outline en verhaal beter laten samenwerken.

**Het kernprincipe van NEO:** *"Cards come from the manuscript, not a separate structure."* Elk hoofdstuk en elke `***`-sectie ís een kaart. Een notitie hangt aan een sectie via een ID op een alinea (`data-sec-id`). Verplaats je de kaart, dan verplaatst de tekst mee. QW heeft juist bewust **geen tweede, onafhankelijke hoofdstukvolgorde** (roadmap §9), en dat is goed. Maar daardoor staan Planning-scènes nu "naast" de tekst.

**Doen — scène-ID op de scènebreuk (M, belangrijk ontwerpbesluit).**
- Geef een scènebreuk in het Markdown-bestand een onzichtbaar, stabiel ID, bijvoorbeeld `* * *` gevolgd door `<!-- qw:scene s-7f3a -->` (of een QW-profielvariant volgens `MANUSCRIPT_SYNTAX.md`).
- Een Planning-scène kan zich dan aan dat segment koppelen. "In dit hoofdstuk" weet welke scène bij de cursor hoort, en klikken op een scène springt ernaartoe (NEO #367).
- **De keerzijde, eerlijk gezegd:** verborgen markers in tekst zijn riskant. NEO-issue #3 ging over vreemde tekens die opdoken door een verborgen Darlings-bladwijzer. Spreek daarom vooraf af: markers staan alleen op een eigen regel bij de scènebreuk en nooit midden in een zin; zoeken, spelling, telling, AI en export negeren ze; de DOCX-roundtrip laat ze weg; testen bewijzen dat knippen, plakken en ongedaan maken ze niet dupliceren. Die markers moeten doorgaan voor "dit is de scènebreuk", niet voor "dit is een tag".

**Doen — de meelopende spooknotitie (M).** QW toont Planninghulp nu alleen in een *leeg hoofdstuk*. Je roadmap noemt al "scènegerichte plaatsing na echte scènebreuken". NEO bevestigt dat het werkt: de notitie staat grijs na de scènebreuk, schuift mee terwijl je typt en verdwijnt als je hem wegklikt. Met scène-ID's is dat een kleine uitbreiding van je bestaande, puur visuele laag.

**Doen — omgekeerd plannen (M, NEO #148, staat daar nog open).** Schrijft iemand eerst en plant hij pas daarna, dan wil hij dat een nieuwe scènebreuk in de tekst ook in Planning verschijnt. Zonder dubbele structuur kan dat zo: toon in Planning **afgeleide, alleen-lezen "ongeplande scènes"** (de eerste regel van elk segment zonder koppeling), met een knop "Maak planningscène". Er wordt dus niets automatisch aangemaakt.

**Twijfel — een kaartenbord als planningsweergave.** NEO's kaartenbord (verslepen, lasso, plakken als kaarten) is indrukwekkend en populair (#335, #316, #366). Maar het is een **nieuw interactiemodel**, en je filosofie zegt: "Nieuwe functies krijgen niet ieder een eigen interactiemodel." Mijn advies: géén versleepbaar bord. Wel een compacte, alleen-lezen overzichtsweergave van hoofdstukken met scènes op één scherm (zoals NEO's ⌘−), met de bestaande lijst als bewerkplek. Lijst plakken als scènes (NEO 1.4.7) is wél goedkoop en handig voor wie al een outline in Word heeft.

**Doen, beperkt — personages herkennen in de tekst (M).** NEO-issue #153 (cast-tab, `@naam` tijdens het schrijven, hernoemen dat doorwerkt in de tekst) staat open en is omstreden; één reactie waarschuwt voor feature creep. Voor QW:
- **Wel:** "In dit hoofdstuk" toont automatisch welke personages (naam + aliassen uit Planning) in dit hoofdstuk voorkomen, plus "eerste verschijning". Dat staat al op je roadmap en is puur lezend.
- **Niet:** `@`-syntax in de tekst (vervuilt het proza en de Markdown) en **automatisch hernoemen in het manuscript**. Een globale vervanging van een naam raakt ook gewone woorden (*Roos*, *Bram*, *Mees*). Bied hooguit "zoek alle voorkomens" via het bestaande zoeken-en-vervangen, met jouw transactionele bescherming.

**Niet doen — kleurmarkeringen en "hoofdstuk klaar en vergrendeld"** (NEO-discussie #387). Hugh twijfelt daar zelf over. QW heeft de scènestatus Idee / Uitgewerkt / Geschreven en Open punten; dat dekt de behoefte. Vergrendelen voegt een staat toe die je kunt vergeten op te heffen.

**Al aanwezig, mooi zo:** Darlings/Bewaarplaats (NEO's sterkste idee; QW heeft het, plus een fragmentstore), Open punten (= NEO's placeholders ⌘⇧X) en notities per hoofdstuk (NEO #380 vroeg erom; QW heeft hoofdstukcontext).

### 4.3 Herstel, geschiedenis en synchronisatie

Dit is het technisch belangrijkste deel, omdat je zelf via Dropbox op twee computers schrijft.

**H — de geschiedenis groeit onbeperkt.**
Zoals ik `storage.py` lees:
- `ensure_daily_archive()` maakt bij de eerste opslag van een nieuwe dag een **volledige `shutil.copytree(book.path, …)`**, inclusief de mediamap.
- Het archief staat in `self.root / 'archive'`, dus **in de werkmap, en dus in Dropbox**.
- Ik vind **geen uitdunning of retentie** voor geschiedenisversies (wel voor de automatische `.qwbook`-back-ups).
- Gevolg: een boek met 30 MB aan afbeeldingen dat je 200 dagen bewerkt, geeft ongeveer 6 GB aan archief, en dat synchroniseert Dropbox allemaal.

NEO doet het zo (`SNAPSHOTS` in AGENTS.md):
- per snapshot alleen de **hoofdstukken die veranderd zijn sinds de vorige** plus een `snapshot.json` met volgorde, titels en een hash per hoofdstuk;
- soorten: handmatig (blijft), dagstart en "vlak voor herstel" (gaan na 30 dagen weg);
- verdwijnt een snapshot, dan kopieert hij zijn bestanden eerst naar de volgende die ze mist, zodat elke snapshot leesbaar blijft;
- de dagelijkse back-up-zip laat de snapshots weg.

Advies voor QW:
1. Sla per versie alleen gewijzigde hoofdstukbestanden op, met een manifest met hashes. Media: alleen bestanden die nieuw of anders zijn (op hash), of verwijs naar de live media zolang de hash gelijk is.
2. Retentie: handmatig en ★ blijven altijd; dagversies na 30 dagen uitdunnen tot één per week; conflictversies na 90 dagen. Maak het zichtbaar in Geschiedenis ("oudere dagversies worden samengevoegd").
3. Overweeg om het archief **buiten de gesynchroniseerde map** te zetten (lokale AppData) met alleen ★-versies in de boekmap. **Afweging:** dan reist je geschiedenis niet mee naar de tweede computer. Voor jou als Dropbox-gebruiker kan dat juist een reden zijn het wél mee te laten reizen. Maak er dus een bewuste keuze van, maar dan wel met delta's.
4. Migratie: laat bestaande volledige kopieën staan. Pas uitdunnen alleen toe op nieuwe versies, of na een expliciete knop. Geen stille migratie; dat is je eigen regel.

**H — conflicten zonder je uit je zin te halen.**
Zoals ik het lees, controleert `verify_book_unchanged()` vóór elke hoofdstukopslag de revisie van het **hele boek**. Een externe wijziging in *een ander hoofdstuk* (bijvoorbeeld net binnengekomen van de laptop) geeft dan een `ExternalModificationError`, en de UI toont een **modale dialoog** ("Mijn versie / Versie op schijf"). Dat is veilig, maar het botst met "Blijf schrijven".

NEO's aanpak (`refreshFromDisk`):
- bij focus, zichtbaar worden en elke 30 s: vergelijk `mtime:size` per hoofdstuk en lees alleen gewijzigde bestanden opnieuw in;
- lokaal ongewijzigd en bestand gewijzigd: neem het bestand over; heeft het bestand alleen *minder* woorden, neem het over en zet de verdwenen tekst in Darlings;
- beide gewijzigd: houd de lokale tekst op de pagina en voeg de schijfversie in als **volgend hoofdstuk** "van het andere apparaat"; er gaat niets verloren en er verschijnt geen dialoog;
- schrijf nooit een hoofdstuk dat niet veranderd is ("A timer that writes every chapter on an interval will fight the other device").

Advies voor QW (dit is "beide versies bewaren als het eenvoudig is", en het ís eenvoudig):
1. Maak de controle **per bestand**: alleen het hoofdstuk dat je opslaat moet ongewijzigd zijn. Wijzigingen in andere hoofdstukken die je niet bewerkt hebt, neem je stil over (en ververs de boom).
2. Alleen als *hetzelfde* hoofdstuk aan beide kanten gewijzigd is: maak eerst je bestaande `conflict_local`-versie, bewaar de schijfversie als nieuw hoofdstuk direct eronder ("— versie van andere computer, 14:32"), en toon een **niet-modale** melding in de statusregel. Geen keuzedialoog.
3. `book.json`: structuurwijzigingen (volgorde, titels) zijn lastiger. Daar mag de huidige expliciete dialoog blijven, maar alleen bij een echte botsing.
4. Je hebt al conflictkopie-detectie voor Dropbox/OneDrive op Integriteit. Dat blijft het vangnet.

**M — kleine robuustheidslessen van NEO:**
- `writeJSON` bewaart de laatste leesbare versie als `.bak`, en `readJSON` valt terug op `.tmp` en daarna `.bak`. QW schrijft al atomair met fsync (goed), maar een `book.json.bak` bij elke manifestwrite is een goedkope extra laag.
- `rebuildBookMeta`: ontbreekt `book.json` helemaal, dan herbouwt NEO het uit de hoofdstukbestanden. QW kan dit als handmatige actie op Integriteit aanbieden ("Boekstructuur herstellen uit hoofdstukbestanden"), dus zonder stille reparatie.
- **Windows Controlled Folder Access** (NEO #212): als Defender de map Documenten beschermt, faalt opslaan stil. QW is Windows-first, dus doe bij de eerste start en bij het kiezen van een werkmap een schrijftest, en geef bij een `PermissionError` een begrijpelijke melding met uitleg ("Windows-beveiliging blokkeert deze map; kies een andere map of sta QuietWriter toe").
- Placeholders van online-only bestanden: NEO lost dat voor iCloud op zonder het hoofdproces te blokkeren. QW heeft dit voor Dropbox al deels in dev.32–36 (fail-closed bij een ontbrekend hoofdstuk). Mooi zo.

**M — ongedaan maken van structuuracties.**
NEO: 50 stappen structureel ongedaan maken. Een ongedaanmaking zet alleen terug wat díe actie veranderde; tekst die je daarna schreef blijft staan of gaat naar Darlings, "met een melding die zegt waar het heen ging" (#377). QW heeft een prullenbak (goed), maar Ctrl+Z na "hoofdstuk verplaatst/verwijderd/samengevoegd" werkt niet. Een volledige structurele undo-stack is veel werk. Het minimum met de meeste waarde: na een structuuractie een melding "Hoofdstuk verwijderd · **Ongedaan maken**" die 10 s blijft staan, plus Ctrl+Z zolang de melding zichtbaar is.

**L — snapshotweergave met "verdwenen woorden".** Als de geschiedenisvergelijking dit nog niet doet: toon in een oude versie welke woorden sindsdien verdwenen zijn, en bied "Alleen dit hoofdstuk terugzetten" naast "Hele boek". NEO maakt vóór elke herstelactie automatisch een snapshot; QW doet iets vergelijkbaars met `conflict_local`. Houd dat vast.

### 4.4 Doelen en voortgang

NEO: dagdoel, boekdoel, woordsprints en een NaNoWriMo-achtige grafiek over 30 dagen ("Get addicted to writing").

QW's ontwerp (`SCHRIJFDOELEN_DESIGN.md`) sluit sprints, streaks en grafieken in v1 bewust uit. Volgens mijn notities wil je voor v2 wel een dagdoel en een grafiek, waarbij je eerst wilt bepalen wat je meet, en schrappen mag niet van de telling aftrekken.

- **Doen (L/M): de grafiek, maar rustig.** Een staafje per dag, alleen zichtbaar als je het voortgangsvenster opent, zonder rood en zonder "achterstand". Je meetregel ("alleen positieve groei tussen geslaagde opslagen") is beter dan NEO's netto-telling: schrappen is revisie, geen falen.
- **Niet doen: sprints.** Een aftellende timer is precies het soort druk dat je rustige-voortgangsprincipe uitsluit. Het voegt ook een UI-staat toe ("sprint loopt") die je kunt vergeten.
- **Niet doen: "today's count survives a sync"-complexiteit.** NEO moest repareren dat de dagtelling over apparaten heen kapot ging (1.4.7). QW houdt dagactiviteit lokaal en opt-in; houd die lokaal, dan heb je dat probleem niet.

### 4.5 Export en publicatie

**H — exportdoel "Inzenden bij uitgeverij of wedstrijd".**
NEO 1.5 heeft *Manuscript Format*: Times New Roman 12, dubbele regelafstand, inspringende alinea's, `#` als scènebreuk, kopregel "Achternaam / TITEL / pagina", een titelpagina met contactgegevens en "ongeveer 90.000 woorden", en geen colofon of opdracht. QW's doelgerichte wizard is hier precies voor gemaakt: een zevende doel naast *e-reader*, *print* en *Word*. Waarom H: het is concreet, vaak nodig voor Nederlandse schrijfwedstrijden en uitgeverijen, en technisch eenvoudig via je bestaande `docx_io`. Let wel: Nederlandse uitgeverijen hebben minder één vaste standaard dan Amerikaanse agenten. Maak lettertype, regelafstand en het wel of niet tonen van de kopregel dus instelbaar binnen het doel.

**L — paperback-PDF (KDP / Brave New Books / Boekscout).**
NEO's implementatie is serieus: vier bijsnijdformaten, rugmarge per paginabereik, even paginatelling, hoofdstukken op een rechterpagina, paginanummers buitenaan en woordafbreking met TeX-patronen (Chromium breekt alleen op macOS af). QW's PDF gaat via `QTextDocument`/`QPdfWriter`, met A4/A5 en **zonder woordafbreking**. Voor Nederlands met lange samenstellingen is uitgevulde tekst zonder afbreking lelijk. Als je dit ooit doet: zachte afbreekstreepjes invoegen met `pyphen` (Hunspell-afbreekpatronen) vóór het opmaken, en spiegelmarges. Dit is groot werk en het risico op klachten "mijn drukproef klopt niet" is reëel. Pas doen als gebruikers erom vragen.

**Doen (M) — kleine exportgemakken uit NEO-issues:**
- Exporteren vanaf de boekenkast (#301). Het menu "Boekacties" in QW heeft nu alleen "Verplaatsen naar".
- Boek dupliceren (#314; vroeg om "alternatieve versie van mijn boek", #281). QW heeft `duplicate_chapter`, maar geen boek dupliceren.
- Hoofdstukken importeren in een **open** boek (#178: bestanden op de outline slepen). QW's import maakt, zoals ik het lees, altijd een nieuw boek.

**Niet doen:**
- **Planken binden tot één boek (omnibus).** Mooi, maar het raakt export, nummering, inhoudsopgave en publicatiepagina's tegelijk. Voor een serieschrijver eerder "later dan nooit", maar nu niet.
- **"Email draft to myself" met SHA-256.** Op Windows zonder mailclient werkt het slecht (NEO #386 moest er een fallback voor bouwen), en een gewone export naar een map doet hetzelfde. Wil je de vingerafdruk, zet hem dan in de exportsamenvatting ("SHA-256 van de tekst").
- **Scenario's en strips** (NEO #362). Ander genre, andere editorregels, ander paginamodel. Het past niet bij "boeken".
- **Voetnoten**: alleen als non-fictieschrijvers erom vragen. Romanschrijvers missen ze zelden, en ze raken elk exportformaat.

### 4.6 AI

NEO gebruikt AI alleen om een **abstract omslagschilderij** te genereren, waarbij het verhaal naar OpenAI gaat (#384/#396 vragen om Gemini en xAI erbij).

- **Niet doen: AI-omslagen.** Er zijn drie redenen. (1) Je filosofie zegt "geen coverdesigner". (2) Het verhaal naar een beeldmodel sturen botst met "geen stille overdracht van manuscriptinhoud" en vraagt om een extra providerconfiguratie. (3) In de schrijverscommunity ligt AI-beeld gevoelig; je promotie leunt juist op "AI die zijn mond houdt".
- **Wel interessant om te volgen:** NEO-discussie #374, een fork die "logt hoe een boek gebouwd is" (tamper-evident bewerkingslog) als bewijs van menselijk schrijven. Dat sluit thematisch prachtig aan bij QW's Meelezer-positie ("de tekst moet echt van jou komen"). **Maar nu niet bouwen**: het is zwaar (cryptografische log, privacy, opslag) en de vraag is nog niet bewezen. Hooguit later een lichte variant: jouw opt-in dagactiviteit plus versiegeschiedenis als exporteerbaar "schrijfverloop".
- De Meelezer zelf hoeft niets van NEO te leren; NEO heeft niets vergelijkbaars en de issues vragen er niet om. Blijf hem klein presenteren, zoals je al wilde.

### 4.7 Boekenkast

QW's boekenkast is al op NEO geïnspireerd (de roadmap noemt het letterlijk) en heeft met privéplanken iets wat NEO mist.
- Doen: exporteren en dupliceren vanaf de kast (zie §4.5).
- Overwegen: **gegenereerde abstracte omslagen zonder AI**. NEO maakt per boek een omslag op basis van een seed (zes stijlen, zes typografische sjablonen), zodat geen twee boeken hetzelfde ogen. Als QW nu voor boeken zonder omslag een egaal sjabloon toont, maakt een seed-variant (kleur en vorm afgeleid van de boek-ID, titel in echte letters) de kast veel levendiger. Dat is goed voor screenshots en kost weinig, omdat je `cover.py` al hebt.
- Niet doen: pseudoniemen als aparte "auteurs" met eigen planken. QW's planken plus privéplanken dekken dat zonder extra concept.

### 4.8 Talen en vertalingen

NEO ging in zes weken naar 14 interfacetalen, bijna allemaal via vertalers van buiten. Wat dat mogelijk maakte:
- `TRANSLATING.md`, voor niet-programmeurs geschreven ("Adding a language is a single file").
- `locales/_template.json` dat met een script wordt ververst, plus `node scripts/i18n.js check fr`, dat ontbrekende en verouderde sleutels meldt.
- **Meervoudsvormen** per taal volgens Unicode CLDR (`one`, `few`, `many`, `other`).
- **Regionale terugval**: `fr-CA` → `fr` → Engels.
- Taalafhankelijke typografie (aanhalingstekens) gekoppeld aan de spellingtaal; NEO #284 (Noors) laat zien dat vertalers zelf zulke regels aanleveren.
- Bij de eerste start de systeemtaal volgen als die beschikbaar is.

Advies voor QW (je wilde dit al: "meer interfacetalen via een contextbestand voor vertalers"):
- **Doen:** `TRANSLATING.md`, een sjabloon met **een korte contextregel per sleutel** (waar staat het, hoeveel ruimte), een `tools/i18n_check.py` dat ontbrekende, ongebruikte en `{placeholder}`-verschillen meldt, en meervoudsvormen voor tellers ("1 hoofdstuk" / "3 hoofdstukken"). Bij 1.796 sleutels vangt zo'n controlescript veel regressies.
- **Doen:** de taal ontdekken uit de bestanden in `locales/` (zodat een nieuwe JSON automatisch in de keuzelijst verschijnt), als dat nu nog een vaste lijst is.
- **Niet doen:** overstappen naar Engelse brontekst als sleutel. NEO doet dat, maar jouw puntsleutels (`settings.appearance.smart_quotes`) zijn stabieler bij tekstwijzigingen en je hebt al 5 × 1.796 vertalingen. Omzetten kost veel en levert niets op.

### 4.9 Mobiel

NEO Pocket (Capacitor) draait dezelfde editor op Android en iOS. Gebruikers houden ervan, en een groot deel van de recente issues gaat erover (#160, #176, #188, #246, #266, #368).

- **Niet doen: een mobiele QW.** PySide6 op mobiel is onpraktisch, het verdubbelt je testoppervlak en je doet je Windows-acceptatie al zelf.
- **Wel overwegen (L): een "inbox" die met elke Markdown-app werkt.** Omdat QW Markdown als bron houdt, kan een boek een bestand `inbox.md` krijgen dat je op je telefoon via Dropbox met elke teksteditor aanvult. QW toont nieuwe inbox-regels dan als losse fragmenten in de Bewaarplaats. Zo profiteer je van je formaatkeuze zonder mobiele app, en het sluit aan bij je wens voor een fragmentbewaarplaats die tussen boeken herbruikbaar is.

### 4.10 Distributie en updates

Dit is volgens mij je grootste tijdvreter.

- NEO: `electron-updater` via GitHub Releases. De installer (NSIS) werkt zichzelf bij; de portable exe niet. Klaar.
- QW: `update_checker`, `update_download`, `update_health`, `update_handoff_*`, `update_real_exe_lab`, `update_real_transaction_lab`, `update_integration_lab`, `update_test_updater`, `update_release_preflight`, `update_pilot_gate`, `updater_process`, `windows_portable_updater`, `side_by_side_update`, `versioned_install`. Samen **~2.250 regels**, plus Ed25519-handtekeningen, journals en rollback. Daarachter zit een reeks van zo'n 30 dev-versies, en het staat nog steeds uit ("production NO-GO").

Het is knap werk, maar het is precies het soort "maanden technisch polijsten zonder nieuwe schrijverswaarde" dat je zelf wilde vermijden. Advies:

1. **Velopack** ([docs](https://docs.velopack.io/getting-started/python)) ondersteunt Python/PyInstaller. Het regelt installatie per gebruiker zonder adminrechten, delta-updates, herstart en rollback. Wat jij met de hand bouwt, doet dit al.
2. Of eenvoudiger: een **Inno Setup-installer** plus jouw bestaande `update_checker` die bij een nieuwe versie de installer downloadt, de SHA-256 controleert, hem start en QW afsluit. Dan blijft er van de updatecode misschien 300 regels over.
3. En/of **winget** (ondersteunt ook portable pakketten): `winget upgrade` regelt updates voor wie dat gebruikt. NEO #230 kreeg hetzelfde advies voor Homebrew.
4. **Haal de lab-modules uit het `quietwriter`-pakket**, ongeacht je keuze. `update_real_exe_lab.py`, `update_integration_lab.py`, `update_test_updater.py` en dergelijke horen in `tools/` of `tests/`, niet in de code die naar gebruikers gaat. Minder code in de exe betekent minder aanvalsoppervlak, minder virusscannerverdenking en een kleinere download.

Houd je portable zip als alternatief (NEO doet hetzelfde: installer *en* portable exe).

### 4.11 Code en architectuur

**NEO: wat ik niet zou overnemen**
- **Eén `app.js` van 17.895 regels** met de hele UI. Het werkt voor Hugh omdat AI-agents met "banners" navigeren, maar het is fragiel. QW's modulestructuur is beter.
- **Tests die niet in CI draaien.** QW's release-gate is beter.
- **HTML als opslag.** Markdown is diffbaarder en leesbaarder buiten de app. Je eigen formaatonderzoek kwam ook op Markdown uit. Blijf daarbij.

**NEO: wat ik wel zou overnemen**
- **`AGENTS.md` (H).** Eén bestand van ongeveer 220 regels met (a) *"Rules that override convenience"*, (b) een tabel van welk bestand wat doet, (c) invarianten per subsysteem (opslag, sync, snapshots, i18n) en (d) "When you change something"-checklists. Jij hebt `PROJECT_GUIDE`, `DEVELOPER_REFERENCE`, `ARCHITECTURE_AND_DATA_SAFETY`, `UI_REFERENCE`, `MANUSCRIPT_SYNTAX` en ruim 100 DEV-/REVIEW-documenten. Voor ChatGPT en Claude is één compact bestand met de harde regels veel effectiever dan twintig documenten. Kandidaat-regels uit NEO die ook voor QW gelden:
  - "Schrijf nooit een hoofdstuk dat niet veranderd is."
  - "UI-decoratie (zoekmarkering, spelling, focus) komt nooit in het hoofdstukbestand." QW doet dit al; leg het vast.
  - "Een nieuwe manier om tekst te verwijderen heeft een herstelpad én een zin in de UI die zegt waar de woorden heen gingen."
  - "Geen stille migratie, geen stille reparatie, geen last-write-wins."
- **Spelling in een apart proces (M).** NEO draait Hunspell (WASM) in een `utilityProcess` met berichten `load/check/suggest/add`. QW gebruikt `spylls` (pure Python, traag) en had al een spellinghang (`SPELLING_HANG_ANALYSE_1.3.1.md`). Een `QThread` helpt niet tegen de GIL. Een `multiprocessing`-worker of `QProcess` met dezelfde vier berichten wel. Je roadmap noemt "suggesties in achtergrondwerker". Maak er een apart **proces** van, geen thread.
- **Foutlog dat gebruikers kunnen meesturen.** NEO: `neo-errors.log` in de bibliotheek, en de bugrapportinstructie zegt "stuur de staart mee". QW heeft `crash_logging`. Zet in CONTRIBUTING en de Over-pagina waar het log staat en dat het geen manuscripttekst bevat.

**QW: eerlijke kritiek op de eigen code**
- **Te veel ceremonie op sommige plekken.** De updater (§4.10) is het duidelijkste voorbeeld. Je profiel zegt "minimal abstraction, fewer files, practical over engineered". Op dat punt wijkt QW af van wat je zelf wilt.
- **Grote bestanden ondanks modularisering:** `editor_page.py` (2.924 regels), `storage.py` (1.967), `settings_page.py` (1.864), `main_window.py` (1.639), `manuscript_editor.py` (1.649). Splitsen is geen doel op zich, maar `settings_page.py` en `editor_page.py` zijn de bestanden waar ChatGPT het vaakst iets zal breken. Splits ze pas als je er toch iets in moet veranderen: bij Instellingen per sectie, bij de editorpagina in "panelen" en "opslag/conflict".
- **Rommel in `documents/`:** ruim 200 bestanden, een `CHANGELOG.md` van 262 KB en meer dan 100 releasenotities en dev-handoffs. Zet DEV-, REVIEW- en RELEASE_NOTES-bestanden in `documents/archive/`, splits de CHANGELOG per minorversie en houd in de root alleen wat iemand vandaag nodig heeft.
- **Sterke punten om te houden:** atomaire writes met fsync en retry bij Windows-locks, fail-closed bij ontbrekende hoofdstukken, een transactioneel zoeken-en-vervangen met journal, tokens in thema's en de expliciete DPI-beoordelingsvragen. Dat is beter dan NEO.

### 4.12 Community en proces

- NEO trok in ongeveer zes weken zo'n 400 issues en PR's. Inmiddels staat er op de issuepagina "Issue creation is restricted in this repository", en Hugh zet ideeën om naar **Discussions** (#235 → #247, #227 → #250). Lessen:
  - Zet **GitHub Discussions** aan met de categorieën *Ideeën*, *Vragen* en *Laat zien*, en houd Issues voor bugs. Dat voorkomt dat je issuelijst een wensenlijst wordt.
  - Maak **issuesjablonen** (bug: OS, versie, wat deed je, staart van het log; idee: welk schrijfprobleem lost het op?). Die tweede vraag is jouw featurecriterium. Laat de indiener het beantwoorden.
- **Grote PR's van buiten** sluit Hugh vaak (#71 "impressive but hard to absorb", #271 "I just built something similar"). Zet in CONTRIBUTING: "Bespreek een idee eerst in Discussions vóór je meer dan ~100 regels schrijft."
- Hugh is geen git-gebruiker en laat agents alles via een `npm run bundle` aanleveren. Dat lijkt op jouw ChatGPT-overdracht. Een vaste overdrachtsvorm (bij jou: zip plus `DEVxx_…md`) is prima; het `AGENTS.md`-advies maakt die overdracht korter.

---

## 5. Bewust niet doen — overzicht met reden

| NEO-feature of -verzoek | Waarom niet voor QW |
|---|---|
| Enter×2 = scènebreuk, Enter×3 = hoofdstuk | Impliciete structuur geeft verwarring (#164, #370); je had al besloten het niet te doen; QW kiest voor expliciet |
| AI-omslagschilderij (OpenAI, Gemini, xAI) | Botst met de privacylaag, met "geen coverdesigner" en met je AI-positionering |
| Scenario's en stripscripts (#362) | Ander product; elk genre brengt een eigen editor- en paginamodel |
| Pocket / mobiele app | Onpraktisch met PySide6 en verdubbelt het testwerk; de inbox-variant (§4.9) is het pragmatische alternatief |
| Woordsprints | Tijdsdruk past niet bij rustige voortgang |
| Automatische hoofdletters (#196) | Breekt in het Nederlands ('s avonds, afkortingen) |
| Tekstkleur en kleurmarkeringen (#116, #387) | Opmaak zonder exportbetekenis; Open punten en scènestatus dekken de behoefte |
| Hoofdstuk "klaar en vergrendeld" (#387) | Extra staat die je vergeet; weinig winst |
| `@naam` in de tekst / hernoemen dat doorwerkt (#153) | Vervuilt het proza; globaal hernoemen raakt gewone woorden |
| Versleepbaar kaartenbord | Een nieuw interactiemodel; liever een overzichtsweergave plus de bestaande lijst |
| Planken binden tot omnibus | Raakt te veel tegelijk; later, als series-schrijvers erom vragen |
| E-mail naar jezelf (⌘E) | Windows zonder mailclient; een export naar een map plus een hash in de samenvatting is genoeg |
| Vim-toetsen, macOS-opzoeken | Niche of niet beschikbaar op Windows |
| Instellingen per apparaat (#323/#246) | **Hoeft niet**: QW gebruikt `QSettings` (per computer); zorg alleen dat weergave-instellingen nooit in `book.json` belanden |
| Engelse tekst als vertaalsleutel | Omzetten kost veel; je puntsleutels zijn stabieler |
| Eén groot UI-bestand, tests buiten CI, HTML-opslag | Technische keuzes waar QW al beter zit |

---

## 6. Voorgestelde volgorde

**1.6.x — kleine winst, weinig risico**
1. Boektitel in de venstertitel (met respect voor privéplanken).
2. Sneltoetsenoverzicht (Ctrl+/).
3. Typografie per taal: `’`, `‘…’`, `–`/`—`, `…`, met tests voor dialoog.
4. Boek dupliceren en exporteren vanaf de boekenkast.
5. Schrijftest en Controlled Folder Access-melding bij het kiezen van de werkmap.
6. `AGENTS.md` schrijven; `documents/` opruimen naar een archief; lab-modules uit het pakket.

**1.7 — data en rust**
1. Geschiedenis als delta + retentie (met een expliciete keuze voor bestaande archieven).
2. Conflicten per hoofdstuk, niet-modaal, beide versies bewaren.
3. Melding "Ongedaan maken" na structuuracties.
4. Updater vervangen door Velopack of installer + eenvoudige check.
5. Spelling-worker als apart proces.

**1.8 — planning dichter bij het verhaal**
1. Scène-ID's op scènebreuken (eerst ontwerpdocument plus syntaxbesluit in `MANUSCRIPT_SYNTAX.md`).
2. Meelopende spooknotitie per scène.
3. "Ongeplande scènes" in Planning (omgekeerd plannen).
4. Personages per hoofdstuk automatisch herkennen (naam + aliassen).
5. Exportdoel "Inzenden".

**Later / op verzoek**
Voorlezen, UI-zoom (eerder als er klachten over DPI komen), rustige 30-dagengrafiek, vertalersproces + meervoudsvormen, seed-omslagen, inbox.md, paperback-PDF met afbreking, voetnoten.

---

## Bijlage A — geraadpleegde NEO-issues en -discussies (steekproef)

| # | Soort | Onderwerp | Status | Relevantie voor QW |
|---|---|---|---|---|
| 3 | issue | vreemde tekens door verborgen bladwijzer | opgelost | Les voor scène-ID-markers (§4.2) |
| 10 | issue | sneltoetsenoverzicht kan meerdere keren open | — | Klein: één instantie |
| 20 | issue | outline met pijltoetsen | opgelost | QW-principe "keyboard first-class" klopt |
| 29 | issue | versienummer niet te vinden | opgelost | QW heeft een Over-pagina ✔ |
| 48 | issue | spellingtaal kiezen | — | QW heeft het ✔ |
| 71 | PR | groot beveiligings-PR niet gemerged | gesloten | Bespreek eerst, dan PR |
| 80 | issue | updaten vanuit de app | opgelost (electron-updater) | §4.10 |
| 90 | PR | hoofdstuktitels zonder "Hoofdstuk n" exporteren | gesloten | Controleer of QW dit in de exportinstellingen heeft |
| 116 | issue | tekstkleur | niet gepland | Mee eens: niet doen |
| 148 | issue | scène in tekst → ook in outline | **open** | §4.2 omgekeerd plannen |
| 153 | issue | cast/personages, @-naam, hernoemen | **open**, omstreden | §4.2 alleen herkennen |
| 164 | issue | proloog/epiloog als deel, nummering van delen | **open** | Controleer QW-publicatiestructuur |
| 196 | issue | automatische hoofdletters | opgelost | Niet doen in het Nederlands |
| 202 | discussie | Markdown-knoppen | open | QW heeft een zwevende opmaakbalk ✔ |
| 212 | issue | Windows Controlled Folder Access | opgelost | **Doen** (§4.3) |
| 219 | commit | stroomuitval haalt boek van de plank | opgelost | `.bak` + herbouwen (§4.3) |
| 230 | issue | Homebrew | gesloten | Analogie: winget |
| 241 / 377 | issue | ongedaan maken van outline/structuur | opgelost | §4.3 |
| 246 / 323 | issue | instellingen per apparaat | opgelost | QW: QSettings ✔ |
| 250 / 337 | discussie/issue | sneltoetsen naar tabbladen | gesloten | Klein; past in sneltoetsenoverzicht |
| 271 | PR | outline als kaarten (extern) | gesloten | Grote externe PR's |
| 281 / 314 | discussie | scènes, drafts, boek dupliceren | beantwoord | §4.5 dupliceren |
| 284 | issue | Noors, typografische regels per taal | **open** | §4.8 |
| 297 / 379 | issue | harde spaties gaan verloren / zichtbaar maken | opgelost | Test QW's roundtrip van U+00A0 |
| 301 | issue | exporteren vanaf de boekenkast | opgelost | **Doen** |
| 316 / 335 | issue | kaarten verwijderen, meerdere selecteren | opgelost | Alleen bij een kaartenbord |
| 326 | discussie | AppImage-updates | open | n.v.t. |
| 349 / 385 | issue | Ctrl+Shift+X werkt niet (AMD-software) | opgelost | Tip in sneltoetsenoverzicht |
| 350 | issue | schaalfactor / toegankelijkheid | **open** | UI-zoom (§4.1) |
| 357 | issue | titel in vensterbalk | opgelost | **Doen** |
| 361 | discussie | snapshots aangekondigd | — | §4.3 |
| 362 | issue | stripscript-modus | **open** | Niet doen |
| 364 / 97 / 275 | issue | zoom | opgelost | §4.1 |
| 366 / 367 | issue | scènekaarten naast de tekst, klik = spring | opgelost | §4.2 |
| 374 | discussie | fork met bewijslog "hoe het boek gebouwd is" | open | Volgen, niet bouwen (§4.6) |
| 380 | issue | notities per hoofdstuk | opgelost | QW: hoofdstukcontext ✔ |
| 384 / 396 | issue/PR | meer providers voor AI-omslagen | **open** | Niet doen |
| 386 | issue | e-mail naar jezelf zonder webmail | opgelost | Niet doen |
| 387 | discussie | hoofdstukken inklappen, "klaar", markeringen | gesloten | Niet doen |
| 392 | issue | paginanummers buitenaan (KDP) | opgelost | Alleen bij paperback |

## Bronnen
- NEO-repository: [github.com/hughhowey/neo](https://github.com/hughhowey/neo) (zip `neo-main` en de git-geschiedenis tot 15-10-2026)
- Afzonderlijke issues: `https://github.com/hughhowey/neo/issues/<nummer>`, voor de nummers in bijlage A
- Velopack voor Python: [docs.velopack.io/getting-started/python](https://docs.velopack.io/getting-started/python)
- QuietWriter: `QuietWriter-1.6.zip` (interne versie 1.5.0-dev.63)
