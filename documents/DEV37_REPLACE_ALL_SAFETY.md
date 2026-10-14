# QuietWriter dev.37 — Veiligere bewerking ‘Alles vervangen’

## Uitgangspunt
Gebouwd op de volledige dev.36-reviewsnapshot, **niet** direct op de lokale ontwikkelwerkmap. Alle bronbestanden en branding zijn behouden. De interne versiemetadata waren in deze snapshot nog dev.28; dit is daarom een **reviewversie**, geen nieuwe productie- of GitHub-release.

## Implementatie
- `Library.replace_chapters_guarded`: preflight van de volledige geselecteerde set vóór enige wijziging. Controleert of alle bronhoofdstukken bestaan, UTF-8 leesbaar zijn en exact overeenkomen met de geplande brontekst en de bekende boekrevisie.
- Oorspronkelijke inhoud van alle te wijzigen hoofdstukken wordt vooraf als recovery-materiaal bewaard onder `archive/<boek-id>/replace-recovery-<uuid>`. Deze map ligt buiten de manuscriptmap, maar binnen de werkmap.
- Per bestand gebeurt een atomische bestandsvervanging; bij een gewone schrijfexception worden eerder gewijzigde bestanden teruggezet **alleen als ze nog exact onze geschreven bytes bevatten**. Concurrerende externe edits worden niet overschreven.
- `EditorPage.replace_all_matches` maakt eerst het complete plan, roept één opslagoperatie aan en wijzigt de huidige editorweergave pas na succesvolle afronding. Bij fouten toont de UI een vertaalde melding.
- Nieuwe regressies bewijzen volledige wijziging, afbreken bij ontbrekende bron, afbreken bij gewijzigde bron en compensatie na een fout bij de tweede bestandswijziging.

## Belangrijke beperking
Dit is **geen volledige ACID-transactie** over meerdere bestanden. Een harde crash of stroomuitval tussen bestandsvervangingen kan nog een gedeeltelijke bewerking op schijf achterlaten. De originele kopieën staan dan doorgaans in de recovery-map, maar automatische crash-replay ontbreekt. Ook andere processen/Dropbox kunnen gelijktijdig wijzigen. Een interproceslock, duurzaam transactiejournaal en crashherstel zijn nodig vóór een productieclaim over gegarandeerde atomaire multi-file-operaties. Bewaar de `replace-recovery-*` mappen voorlopig; er is bewust geen automatische opruimroutine.

## Validatie
- Nieuwe test `tests/current/test_replace_batch_dev37.py`.
- Gerichte regressies: 36 geslaagd, 1 overgeslagen; locale/branding: 1725 sleutels in 5 talen, 9 brandingafbeeldingen intact.
- Praktijktest met twee computers blijft uitgesteld op verzoek van gebruiker.
- De nieuwe update-installer blijft uitgeschakeld; bestaande handmatige GitHub-update ongemoeid.

## Visuele Windows-test
Gebruik uitsluitend een **kopie** van je boekenwerkmap. Maak een testboek met drie hoofdstukken die hetzelfde woord bevatten. Zoek in ‘Hele boek’ en kies ‘Alles vervangen’. Controleer dat alle drie hoofdstukken aangepast zijn. Herhaal met één ontbrekend hoofdstukbestand: verwacht een rustige weigering zonder wijzigingen in andere hoofdstukken. Zet het bestand daarna terug vanuit de testkopie.
