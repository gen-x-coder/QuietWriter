## 1.7.0 — Planning dichter bij het verhaal

**Voor schrijvers**
- **Exportvoorbeeld** (eerst gepland voor 1.8.0): op de exportpagina en in de laatste stap van de begeleide export staat **Voorbeeld bekijken**. QuietWriter maakt dan precies hetzelfde bestand als bij exporteren, maar in een tijdelijke map: er komt niets in je exportmap en je exportkeuzes worden niet onthouden. Een e-book toont QuietWriter zelf in een venster (hoofdstukken in leesvolgorde, met voetnoten); PDF, Word en Markdown openen in je eigen programma. Is daar geen programma voor, dan zegt QuietWriter waar het bestand staat.
- **Ollama eenvoudiger instellen** (eerst gepland voor 1.8.0): Instellingen → AI Meelezer → *Ollama instellen* kijkt of Ollama draait. Zo niet, dan legt één zin uit wat Ollama is, met **Ollama downloaden** (de officiële pagina) en **Opnieuw zoeken**. Draait Ollama zonder model, dan staat er een korte lijst van vier modellen, het model dat bij het werkgeheugen van deze computer past al gekozen; **Model downloaden** laat Ollama het binnenhalen, met voortgang en **Stoppen**. Daarna staat het model klaar als keuze; pas met Opslaan wordt het bewaard. Ook de eerste start wijst hierheen.
- **Exportvoorbeeld veiliger** (na review): elk voorbeeld krijgt een eigen tijdelijke map, dus een voorbeeld dat nog open staat wordt nooit vervangen. Voorbeelden ouder dan een dag ruimt QuietWriter vanzelf op. Een e-book dat te groot of onverwacht is, opent in een ander programma.
- **Modelkeuze breder** (na test Lucas): het veld *Schrijf- en analysemodel* is ongeveer drie keer zo breed, zodat lange Ollama-namen (`hf.co/…/…:Q5_K_M`) leesbaar zijn. De open lijst is zo breed als de langste naam, en met de muis erop zie je de volledige naam. Ook de tekst van *Ollama instellen* wordt niet meer afgekapt.
- **Markdown-import houdt voetnoten:** `^[…]` in een geïmporteerd Markdown-bestand werd stil platte tekst (de haken vielen weg). Nu blijft het een voetnoot. Gevonden met het nieuwe exportvoorbeeld.
- **Voetnoten veiliger** (na review): typ je in een noot terwijl er elders een noot bij komt of verdwijnt, of terwijl het hoofdstuk van schijf wordt herladen, dan komt je tekst nooit in een andere noot terecht en wordt een wijziging van buiten niet meer overschreven.
- **Woordenboek bijwerken veiliger** (na review): mislukt het halverwege, dan komt het vorige woordenboek atomair terug. Lukt ook dat niet, dan blijft er een reservekopie staan en zegt QuietWriter dat eerlijk.
- **Foutjes opgeruimd** (controle per pagina en paneel):
  - de boektitel boven de tekst wordt netjes ingekort (…) als er weinig ruimte is, in plaats van half achter de tekstbreedte-keuze te verdwijnen;
  - de knop om Inhoud te verbergen dekt "wijzig" in de boom niet meer af;
  - de titel van Zoeken en vervangen staat even hoog als die van de andere panelen;
  - in Spelling zijn de knoppen uitgeschakeld als er niets te doen is (geen woordenboek of geen fouten);
  - een lege Prullenbak houdt de uitleg onder de titel, in plaats van midden op de pagina;
  - Personages zegt wat je kunt doen als er nog niets is, in plaats van een leeg vlak;
  - de koppen Personages, Outline en Notities zijn kleiner dan de paginatitel Planning, zoals in Instellingen;
  - in Instellingen → Uiterlijk valt het lettertypevoorbeeld op een klein scherm niet meer rechts weg;
  - de knop Pop-out van de Meelezer heeft geen los Windows-icoon meer.
- **Outline bijgeschaafd** (Planning):
  - **Scènes slepen**, binnen een hoofdstuk en naar een ander hoofdstuk of Losse ideeën; een streep laat zien waar de scène komt.
  - Zonder muis: ↑ en ↓, en **Verplaatsen naar ▾** (naar het eind van een ander hoofdstuk).
  - **Ingeklapte hoofdstukgroepen blijven ingeklapt** als je terugkomt (per boek, op deze computer); **Alles inklappen/uitklappen** bovenaan.
  - Rustiger: koppen links uitgelijnd met het aantal scènes erachter, het statuslabel is weer klein, een lege groep zegt dat je er een scène heen kunt slepen.
  - Het scènevenster heeft dezelfde formuliervorm als de rest, en zegt waar je personages aanmaakt als er nog geen zijn.
  - Verplaatsen verandert alleen Planning, nooit je tekst. Let op: de koppeling met de tekst loopt via de volgorde, dus een scène verplaatsen koppelt hem aan een ander stuk tekst.
- **Rustiger en gelijker:** alle pagina's hebben dezelfde marges, dus de titel staat overal op dezelfde plek.
  - **Boekdetails** heeft de vorm van Instellingen gekregen: vetgedrukte namen links, korte velden niet meer schermbreed, en twee groepen (*Boek* en *Publicatie*) boven *Schrijfdoel* en *Boekomslag*.
  - **Boekprofiel, Boekgeheugen en Schrijverspersona** hebben dezelfde zijnavigatie als Instellingen en Planning (geen wit vlak meer).
  - Het **personageformulier** en de **Bewaarplaats** hebben dezelfde veldnamen en sectiekoppen.
- **Spelling in voetnoten:** de notenstrook onderstreept onbekende woorden net als de tekst, met hetzelfde woordenboek. Het Spelling-paneel springt bij een fout in een noot naar die noot en *Wijzigen* past hem daar aan.
- **Getalvelden opgeknapt** (Woorddoel, lettergrootte, regelafstand …): de pijltjes staan weer binnen het veld, het getal plakt niet meer tegen de rand en het Woorddoel is niet meer schermbreed.
- **Laatste 30 dagen** (Boekdetails → Schrijfdoel): wie *Vandaag geschreven bijhouden* aan heeft, ziet per dag een staafje met wat er in dit boek bij kwam. Een dag zonder schrijven is een dun grijs streepje. Geen getallen op een as, geen gemiddelde, geen doellijn en geen reeksen; eronder één regel, bijvoorbeeld *9.890 woorden op 14 van de 30 dagen · alleen op deze computer*. Met de muis op een staafje zie je de datum en het aantal. Staat bijhouden uit, dan zegt de regel waar je het aanzet; is er nog niets geteld, dan staan er alleen grijze streepjes.
- **Interfacegrootte** (Instellingen → Uiterlijk): de hele interface groter of kleiner, van 80% tot 175%, bovenop de schaal van Windows. Knoppen, menu's, panelen en tekst groeien allemaal mee. Net als de programmataal geldt een nieuwe keuze na een herstart van QuietWriter.
- **Elk boek een eigen omslag in de Boekenkast.** Een boek zonder eigen omslag krijgt een rustige kleur en een patroon (banen, cirkels, lijnen, stippen, golven, heuvels of bogen) met de titel en de auteur erop. Het patroon hoort bij het boek: het blijft hetzelfde op elke computer, ook als je de titel wijzigt, en een gedupliceerd boek krijgt een ander patroon. Er wordt niets opgeslagen en het gaat niet mee bij exporteren; een eigen omslag (Boekdetails → Omslag kiezen…) gaat altijd voor. Boekdetails toont hetzelfde patroon als voorbeeld.
- **Weten welke scène je schrijft.** Onder de tekst staat in kleine letters welke scène uit Planning bij de plek van je cursor hoort, met de synopsis. Scène 1 is de tekst vóór de eerste scènebreuk (`***`), scène 2 de tekst daarna, enzovoort, in de volgorde van de Outline.
- **Volgende in Planning:** zet je aan het eind van een hoofdstuk een scènebreuk, dan verschijnen eronder de scènes die je nog moet schrijven. Ze verdwijnen zodra je typt en komen nooit in je tekst.
- **In dit hoofdstuk** nummert de scènes, laat zien waar je nu schrijft en springt met *Ga naar deze scène* naar het begin ervan.
- **Omgekeerd plannen:** schreef je eerst en plan je later? Stukken tekst zonder planningscène staan bij *In dit hoofdstuk* en in de Outline. Met *Toevoegen aan Planning* worden het scènes (status Geschreven). Je tekst verandert niet.
- Bij elke scène in *In dit hoofdstuk* staan de eerste woorden van het stuk tekst dat erbij hoort, zodat je meteen ziet of Planning en tekst nog gelijk lopen.
- **Personages in de tekst:** *In dit hoofdstuk* toont welke personages in dit hoofdstuk voorkomen, hoe vaak, en of het hun eerste optreden is. QuietWriter herkent de naam, de voornaam en de namen in het nieuwe veld **Ook bekend als**. Er wordt niets hernoemd of gemarkeerd. Een naam die bij twee personages past (twee keer "Roos") telt voor geen van beide. En als een eerder hoofdstuk onleesbaar is, zegt QuietWriter niet "voor het eerst".
- **Woordenboeken downloaden zonder handwerk:**
  - Bij Instellingen → Spelling (en bij de eerste start) staat **Downloaden…**. Je kiest uit een vaste lijst van 35 woordenboeken, op naam gesorteerd: Nederlands, Engels (GB, VS, Australië, Canada, Zuid-Afrika), Duits (Duitsland, Oostenrijk, Zwitserland), Frans, Spaans (Spanje, Mexico, Argentinië), Italiaans, Portugees (PT/BR), Deens, Zweeds, Pools, Tsjechisch, Slowaaks, Roemeens, Catalaans, Galicisch, Kroatisch, Sloveens, Bulgaars, Russisch, Oekraïens, Litouws, Lets, Ests, Afrikaans, IJslands en Indonesisch (de laatste 23 kwamen erbij in dev14).
  - Bij elk woordenboek staan de maker, de licentie en de grootte.
  - QuietWriter haalt het op bij de LibreOffice-woordenboekbibliotheek, vastgezet op één versie. Elk bestand moet precies kloppen met een vaste controlesom; anders wordt er niets geïnstalleerd.
  - Een download gaat eerst naar een tijdelijke map, en een bestaand woordenboek blijft staan tot het nieuwe compleet is. Je kunt stoppen.
  - Er gaat niets van je tekst mee. Woordenboeken van Office-programma's worden nooit aangeraakt.
  - **Bijwerken:** komt er met een nieuwe QuietWriter een nieuwere versie van een woordenboek dat je hebt gedownload, dan staat er bij Instellingen → Spelling een korte regel en in het downloadvenster "↻ nieuwere versie beschikbaar" met de knop *Bijwerken*. QuietWriter kijkt daarvoor nooit online; zelf toegevoegde woordenboeken worden nooit bijgewerkt.
- **Spelling in Instellingen overzichtelijker:**
  - Eerst kies je het **woordenboek** (QuietWriter zelf, ONLYOFFICE, LibreOffice …), daarna de **taal**; de taallijst toont alleen de talen in dat woordenboek.
  - De technische regel met bron, taalcode en bestandspad is weg.
  - **Verwijderen…** opent een eigen venster met alleen de woordenboeken van QuietWriter (gedownload of zelf toegevoegd), zoals bij Downloaden.
  - Taal- en landnamen staan in de taal van de app ("German — Germany" in het Engels). Ze staan in de taalbestanden, dus een vertaler kan ze ook vertalen.
  - Op alle instellingenpagina's lijnen de keuzelijsten weer recht onder elkaar uit, ook naast langere uitleg.
- **Geen meegeleverd woordenboek meer.** Het Nederlandse OpenTaal-woordenboek zat in de Windows-build; dat is weg, net als `tools/fetch_dictionaries.py`. Je kiest een woordenboek van ONLYOFFICE, LibreOffice of OpenOffice, of downloadt er een (OpenTaal staat in de lijst).
  - Wie bijwerkt en het meegeleverde woordenboek gebruikte, krijgt automatisch hetzelfde taal-woordenboek van een Office-programma als dat er is. Is er geen, dan zegt het Spelling-paneel waar je er een kiest of downloadt.
- **Voetnoten.** Ctrl+Alt+F (of Toevoegen → Voetnoot) zet een klein nummer in de tekst en opent onder aan het blad een streep met dat nummer en een knipperende cursor, zoals in een tekstverwerker. Enter brengt je terug naar de tekst; klik op een nummer om de noot te bewerken; Backspace na een nummer haalt de noot weg. In het bestand staat `^[tekst]` (Pandoc-Markdown).
  - DOCX en Inzenden: echte Word-voetnoten onder aan de pagina. EPUB: genummerde noten per hoofdstuk met pop-upondersteuning. PDF: noten onder aan elk hoofdstuk.
  - Een Word-bestand met voetnoten importeren levert dezelfde noten op dezelfde plek.
  - Zoeken, spelling en woordtelling nemen de noottekst mee; de Meelezer ziet hem als `[Voetnoot: …]`.
- **Woordenboek downloaden in een Dropbox-werkmap** gaf bij de eerste start "Toegang geweigerd" (WinError 5). QuietWriter downloadt nu in de tijdelijke map van Windows en zet elk bestand apart op zijn plek, met herpogingen als Dropbox of een virusscanner het even vasthoudt; mislukt het, dan komt het vorige woordenboek terug.
- **Eerste start: spellingscherm opnieuw.** Je ziet de gevonden woordenboeken (eerst woordenboek, dan taal) en kunt er ook meteen een downloaden. Staat er niets op de computer, dan zegt het scherm dat en staat de downloadknop klaar. De gekozen bron wordt nu ook bewaard. Testen kan met `QuietWriter.exe --first-run` (of `python main.py --first-run`).
- **Woordkeus gelijkgetrokken** (`documents/review/VERTAALLIJST_ANALYSE_1.7.0.md`):
  - *Terugzetten* voor prullenbak, versies en back-ups; *Herstellen* blijft voor Integriteit & herstel;
  - *meesturen*;
  - *Spelling*;
  - *Opslaan* voor Meelezer-gesprekken;
  - *Vorige*/*Volgende* in de exportwizard;
  - het Engelse "Open questions" voor de open aandachtspunten van Boekgeheugen.
- Het opstartscherm noemt naast "© 2026 Lucas Bonsel" ook dat QuietWriter vrije software onder GPLv3 is.
- **Instellingen → Vertalingen:** QuietWriter vertalen zonder technische kennis.
  - Links staat een lijst met alle teksten. Rechts staat één tekst tegelijk: groot in een taal die je kent, met daaronder een ruim invoerveld.
  - Met *Vorige*, *Volgende* (of Ctrl+Enter) en *Volgende die nog ontbreekt* ga je door de lijst.
  - Dezelfde tekst op meerdere plekken (zoals "Bijhouden") vertaal je maar één keer.
  - Fouten in de `{plekken}` worden rood gemarkeerd.
  - *Vertaling opslaan* bewaart het in de werkmap. Na een herstart staat de taal bij Programmataal; wat nog ontbreekt, verschijnt in het Engels.
  - *Exporteren* maakt één bestand om te mailen, *Importeren* laadt het weer in.
  - Uitleg voor vertalers en de maker staat in `documents/TRANSLATING.md`. De maker neemt een vertaling op met `tools/merge_translation.py`.
- **Opgelost (oud):** uitlegblokken in de rechterpanelen (vooral Bewaarplaats) konden een groot leeg vlak worden. De tekst houdt nu precies de hoogte die hij nodig heeft.
- *In dit hoofdstuk* heeft geen lange grijze vlakte meer onder de kaarten.
- **Vertalingen nagelopen** (`documents/review/VERTAALLIJST_ANALYSE_1.7.0.md`):
  - de back-upinstellingen en "Bladeren…" stonden in alle andere talen nog in het Nederlands, en een paar Meelezer-meldingen in het Duits, Frans en Spaans;
  - een paar Engelse woorden zijn gelijkgetrokken;
  - een test bewaakt dit voortaan.
- **Zoekresultaten zijn beter te lezen:** per treffer een stukje van de eigen alinea, beginnend bij een heel woord, met het gezochte woord vet. De hoofdstuknaam staat er alleen bij als er een nieuw hoofdstuk begint, en er is geen horizontale schuifbalk meer.
- De knop **Planning** naast Tekstbreedte is weg: dat was dubbelop met *In dit hoofdstuk*. **✓ Klaar** (scène als geschreven markeren) staat nu daar.
- **Opgelost:** een zacht regeleinde (Shift+Enter) gaf in Word en ONLYOFFICE vreemde "SEP"-tekens. Bij Word, Inzenden, e-book en PDF wordt het nu een echt regeleinde. In Markdown was het al goed: daar is `\` aan het eind van een regel de standaardschrijfwijze voor een regeleinde.
- **Nieuw exportdoel: Inzenden bij een uitgeverij of wedstrijd.**
  - Een Word-manuscript in de gangbare opmaak: Times New Roman 12 (of Arial of Courier New), dubbele of anderhalve regelafstand, ingesprongen alinea's, `#` als scènebreuk en elk hoofdstuk op een nieuwe pagina.
  - Een titelpagina met je contactgegevens en het geschatte aantal woorden, plus een kopregel "Achternaam / TITEL / pagina".
  - Kan ook **anoniem**, voor wedstrijden: dan staat je naam nergens in het bestand.
  - Je contactgegevens blijven op je eigen computer en gaan niet mee in het boek.

**Techniek**
- dev17: `PanelHelp` houdt de titelregel op vaste hoogte (in plaats van een stretch onderaan, die de uitlegtekst op Windows 2 px te laag maakte); `_atomic_copy` ruimt ook een half geschreven `.tmp` op (ChatGPT-herreview); de omslagtest telt titelpixels in plaats van kleurtinten (Windows tekent tekst in een pixmap soms zonder overgangen).
- `ui/planning/outline_page.py`: `SceneCard` start een `QDrag` (mime `application/x-quietwriter-scene`), `SceneGroup` neemt drops aan en tekent de invoegstreep; `OutlinePage.drop_scene(scene_id, chapter_id, before_id)` en `move_scene_to` schrijven via `persist_scenes` (bij een mislukte schrijfactie terug naar de vorige volgorde). Ingeklapt: `planning/outline_collapsed/<boek-id>` in de app-instellingen. Brontests `test_outline_dev20_layout`, `test_planning_dev22_layout` en de literal-gate (↑/↓ toegestaan, zoals × en +) bijgewerkt.
- `ui/page_layout.py` (nieuw): `PAGE_MARGINS`, `set_page_margins`, `section_heading`, `field_label`; thema-regels `contextSectionList`, `contextNavHost`, `detailTitle`. Test `test_bookdetails_goal_and_cover_use_settings_style_section_labels` aangepast: de koppen zijn nu sectiekoppen in Instellingen-stijl.
- `dictionary_download.update_available` / `updates_available`: vergelijkt de .dic/.aff van een door QuietWriter gedownload woordenboek (met downloadbriefje) met de SHA-256 in de lijst. 23 talen erbij, elk getest met spylls; niet opgenomen: hu_HU (spylls kan het niet lezen), nb_NO, nn_NO, el_GR en tr_TR (5–9 s laden, 500–870 MB).
- `ManuscriptHighlighter(editor, spelling_source=…)`: een notenveld leest woordenboek en aan/uit van de hoofdtekst; `add_follower` laat de strook mee-onderstrepen na elke `rehighlight` van de hoofdtekst.
- `ui/progress_strip.py` (nieuw) en `WritingProgressStore.recent_days(book_id, 30)`; Boekdetails leest de lokale telling opnieuw bij elke keer tonen. Geen nieuwe opslag.
- `interface_scale.py` (nieuw): instelling `interface_scale` (procent) wordt vóór `QApplication` omgezet in `QT_SCALE_FACTOR`. Een `QT_SCALE_FACTOR` die de gebruiker zelf zette gaat voor; een onleesbare waarde wordt 100%. Qt kan de factor niet tijdens het draaien veranderen, daarom na herstart.
- `ui/generated_cover.py` (nieuw): omslag uit een seed (de boek-ID, zonder ID de titel). De getallen komen rechtstreeks uit SHA-256, dus een nieuwe Python- of Qt-versie verandert een bestaande omslag niet (test pint één uitkomst vast). Per omslagwidget wordt één keer getekend.
- Besluit: géén verborgen scène-ID's in het manuscript (`documents/design/SCENES_IN_TEXT_DESIGN.md`); de syntax verandert niet.
- `scene_segments.py`, `character_mentions.py`, `exporting/submission_exporter.py` (nieuw).
- Planning: veld `aliases` bij personages. Onbekende velden van een nieuwere versie worden voortaan bewaard (`extra`). Let op: wie na 1.7 met 1.6 of ouder een personage opslaat, verliest de bijnamen.
- Exportinstellingen kennen het formaat `submission`; contactgegevens staan in de app-instellingen (`export/submission_contact`), nooit in `export/settings.json`.

## 1.6.1 — Bijwerken eerst zelf testen

**Voor schrijvers**
- Een nieuwe versie wordt ook bij het opstarten gemeld als bijwerken met één klik er nog niet voor is vrijgegeven. De melding zegt dat, en biedt de downloadpagina aan.

- **Beide versies bewaren is terug te draaien:** mislukt een schrijfstap halverwege (schijf vol, Dropbox houdt een bestand vast), dan zet QuietWriter het boek precies terug zoals het was en vraagt het je gewoon wat je wilt. Jouw tekst staat dan al veilig in Versiegeschiedenis.

**Voor de maker (releaseproces)**
- **Testkopie:** een leeg bestand `.quietwriter-update-pilot` naast `QuietWriter.exe` maakt van een portable kopie een testkopie. Die leest `releases.pilot.json` en ziet ook pre-releases. Instellingen → Updates toont "Testkopie".
- **Drie standen per release, allemaal op GitHub:** (1) pre-release met `releases.pilot.json`: alleen de testkopie werkt bij; (2) gewone release: iedereen krijgt een melding en de downloadpagina; (3) `releases.win.json` erbij: iedereen vanaf 1.5.1 werkt met één klik bij. Terugdraaien = `releases.win.json` weghalen.
- `build_exe.cmd` maakt `releases.pilot.json` naast `releases.win.json` en raadt `vpk upload github` af (dat zou stand 1 en 2 overslaan).
- Het pilotbestand telt alleen naast `Update.exe` (niet in `current\`, die bij een update wordt vervangen).
- Onderzoek in `documents/research/UPDATE_UITROL_ONDERZOEK.md`, nagelezen in de broncode van Velopack 1.2.161: hoe GitHub-releases, kanalen en pre-releases worden gelezen.

## 1.6.0 — Rustiger samenwerken met een tweede computer

**Voor schrijvers**
- **Geen conflictvenster meer midden in het schrijven** als je op twee computers werkt:
  - Een ander hoofdstuk werd elders gewijzigd? Dan neemt QuietWriter dat stil over en meldt het rustig in de statusbalk.
  - Hetzelfde hoofdstuk werd hier én elders gewijzigd? Dan bewaart QuietWriter **beide**: jouw tekst blijft staan, de andere versie komt als nieuw hoofdstuk direct eronder ("… (andere computer, 14:32)"), en er staat een veiligheidsversie in Versiegeschiedenis.
  - Het open hoofdstuk werd elders bijgewerkt terwijl je hier niets veranderde? Dan wordt het bijgewerkt zodra je terugkeert naar QuietWriter.
  - Wijzigingen aan de boekstructuur, Planning of profielen vragen nog steeds expliciet wat je wilt.
- **Ongedaan maken na hoofdstuk verwijderen:** een knop in de statusbalk zet het hoofdstuk terug op zijn plek. Daarna kan het nog via de prullenbak.
- **Oude dagversies uitdunnen** (Instellingen → Back-ups → Versiegeschiedenis, standaard aan): na 30 dagen één per week, na een half jaar één per maand. Versies met een ster, versies die je zelf maakt en veiligheidsversies blijven altijd bewaard. Dit voorkomt dat de geschiedenis in je Dropbox-map onbeperkt groeit.
- In Instellingen → Updates staat of deze kopie zichzelf kan bijwerken, en welke testbron eventueel actief is.

**Techniek**
- `Library._verify_for_chapter_save`, `save_chapter_keep_both`, `adopt_external_chapter_text`, `pop_adopted_external_chapters`.
- `Library.daily_versions_to_thin` (pure functie) en `thin_daily_history`. Ze draaien na het aanmaken van een nieuwe dagversie, alleen als `thin_daily_versions` aanstaat (de app zet dat vanuit `history/thin_daily`).
- `MainWindow.show_undo_notice`: een algemene, niet-modale melding met "Ongedaan maken".
- Fout opgelost: een ongeldige stylesheet in de OpenRouter-status (`}}` buiten een f-string) gaf bij elke start "Could not parse stylesheet".

## 1.5.2 — Betrouwbaarder bijwerken en kleine schrijfgemakken

**Voor schrijvers**
- **Typografie tijdens typen**, per boektaal: “aanhalingstekens”, de apostrof (zo’n, auto’s, ’s avonds, ’90), `--` wordt een gedachtestreepje (– in nl/de/fr, — in en/es) en `...` wordt …. Duits krijgt „…“, Frans « … » en Spaans « … ». Eén keer Ctrl+Z zet het gewone teken terug. Uit te zetten in Instellingen (Typografie tijdens typen).
- De **titel van het open boek** staat in de venstertitel en dus in de taakbalk. In Presentatiemodus blijft een boek van een verborgen plank onzichtbaar.
- **Sneltoetsenoverzicht** met Ctrl+/ of F1, en in Instellingen → Uitleg.
- **Boekacties op de boekenkast:** *Exporteren…* opent het boek direct in Exporteren; *Dupliceren* maakt een losse kopie op dezelfde plank (zonder versiegeschiedenis en lokale AI-gesprekken).
- Bij het kiezen van een werkmap controleert QuietWriter of het er mag schrijven, en legt het Windows' *Beveiligde mapcontrole* uit als die dat blokkeert.
- Bijwerken: "Nu controleren" zegt nu ook "Je gebruikt een nieuwere versie dan de laatste stabiele versie op GitHub (…)" in plaats van alleen "nieuwste versie". Download- en toepasfouten hebben eigen, begrijpelijke meldingen.

**Techniek (reviewbevindingen ChatGPT op 1.5.1)**
- `keyring` en zijn afhankelijkheden vastgepind in de runtime-lock; de smoke-test van de exe eist `keyring` (Windows-backend) en `velopack`.
- Updatecontrole en download draaien in een daemonthread in plaats van een QThread: afsluiten tijdens een controle of download kan Qt niet meer laten crashen.
- Stil of handmatig is per bewerking vastgelegd; een handmatige klik tijdens een automatische controle laat het resultaat zien.
- Na normaal afsluiten beëindigt QuietWriter het hele proces (ook als een Meelezer-pop-out openstaat), zodat Velopack niet hoeft te wachten of te forceren.
- `build_exe.cmd` stopt bij een verschil tussen vpk en velopack en controleert `Portable.zip` (Update.exe, current\QuietWriter.exe) en de feed. De Windows-workflow test ook de uitgepakte portable zip.
- `QUIETWRITER_UPDATE_SOURCE`: testen van bijwerken met een lokale map, zonder GitHub (zie `RELEASE_PROCESS.md`).

## 1.5.1 — Zelf bijwerken met Velopack, opgeruimde projectmap

**Voor schrijvers**
- QuietWriter kan zichzelf bijwerken. Bij een nieuwe versie kies je **Nu bijwerken**: QuietWriter downloadt de update, slaat alles op, sluit af en start vanzelf opnieuw. Je boeken en instellingen blijven waar ze zijn.
- QuietWriter blijft portable: uitpakken en starten, geen installatie of beheerdersrechten nodig.
- Oudere kopieën (van vóór 1.5.1) en de bronversie kunnen zichzelf niet bijwerken. Die melden een nieuwe versie en openen de downloadpagina, net als eerst. Na één keer handmatig overstappen op 1.5.1 werkt bijwerken voortaan vanzelf.
- De verborgen updater-proef (`.quietwriter-update-pilot`) en de uitgeschakelde optie "Updates automatisch downloaden" zijn verdwenen.

**Techniek**
- De eigen updater uit de 1.5.0-ontwikkellijn (dev.5 t/m dev.63: ondertekende manifesten, mapwissel, journal, health-check, labs) is vervangen door [Velopack](https://velopack.io). Weg: 16 modules (~2.250 regels), 24 labtools en 32 testbestanden. Nieuw: `quietwriter/self_update.py` als enige plek die Velopack kent.
- `main.py` start Velopack als eerste stap; de oude `--update-health-check` is verdwenen.
- `build_exe.cmd` maakt na PyInstaller met `vpk pack` de portable zip en de updatefeed.
- Werkmapbescherming herkent de Velopack-mapindeling (`current/` naast `Update.exe`).
- Afhankelijkheden: `velopack` erbij, `cryptography` eraf.
- Dubbele aanmaak van de updatecontrole in `MainWindow._apply_feature_visibility` verwijderd.
- Documentatie opgeschoond: actuele documenten in `documents/`, ontwerpen in `documents/design/` en de ontwikkelgeschiedenis in `documents/archive/` (met index). Nieuw: `AGENTS.md` met de vaste regels voor ontwikkelaars en AI-assistenten.

## 1.5.0-ontwikkellijn (dev.1 – dev.63, niet als stabiele versie uitgebracht)

Samenvatting; alle details staan in `archive/CHANGELOG_TOT_1_5_0_DEV63.md`.

- **Synchronisatie (dev.32 – dev.40):** ontbrekend hoofdstuk nooit als leeg behandelen, boekenkast verversen (F5 en elke 8 s), conflictkopieën tonen op Integriteit & herstel, "Alles vervangen" met preflight, herstelmap en crashjournaal, en een alleen-lezen herstelvergelijking.
- **Meelezer (dev.41 – dev.63):** pop-out-werkruimte, gesprekken bewaren en exporteren, handmatig **Onthouden** naar Boekgeheugen met terugleescontrole, OpenRouter-browserlogin (PKCE en Windows Credential Manager), filter voor schrijfmodellen, transparantie over `openrouter/free`, scheiding tussen bronmateriaal en instructies, HTTPS-only links en OpenRouter-endpointbeveiliging.
- **Updater (dev.5 – dev.31):** eigen ondertekende updater gebouwd tot labniveau en nooit ingeschakeld. Vervangen in 1.5.1; zie `HISTORY_AND_LESSONS.md`.
- Focusmodus geprobeerd (dev.41) en op verzoek weer verwijderd (dev.42).

## 1.4.0 — Boekback-ups, Notities en Planning

Automatische en handmatige `.qwbook`-back-ups met retentie en herstel naar een bestaand boek, de pagina Notities met kaarten, meer structuur in Planning, asynchrone spellingsuggesties met tijdsbudget, vertaalde dialoogknoppen en hardening voor kleine schermen.

## 1.3.x — Boekenkast met planken

Meerdere planken, privéplanken en Presentatiemodus, een woordtellingcache, opt-in schrijfdoelen met rustige dagvoortgang, Planninghulp in lege hoofdstukken en Planning tijdens het schrijven.

## 1.2.x — Begeleid exporteren en manuscriptarchitectuur

Exportwizard op doel, Open punten, de centrale `DocumentView`, geversioneerde manuscriptsyntax, het neutrale importdocument en een transactionele DOCX-import.

## 1.0 – 1.1 — Eerste stabiele releases

Darlings/Bewaarplaats, DOCX-import en -export, het `.qwbook`-boekformaat, begeleide eerste start en de Windows-buildhardening.

Volledige geschiedenis per versie: `archive/CHANGELOG_TOT_1_5_0_DEV63.md`.
