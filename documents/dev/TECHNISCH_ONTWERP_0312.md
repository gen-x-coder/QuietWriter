# Technische voorbereiding 0.31.2 — transactionele boekadoptie en spelling

Deze notitie is bewust een reviewdocument. De hieronder beschreven architectuur is nog niet gewijzigd.

## 1. Eerst: adopt_active_book alles-of-niets

Huidige route: `MainWindow.adopt_active_book()` zet eerst `_active_book`, trackt daarna het boek en roept vervolgens achtereenvolgens Editor, Planning, Boekprofiel, Boekgeheugen, Boekdetails, Media, Integriteit en Export aan. Als een latere adopt-call onverwacht faalt, kan de UI dus theoretisch gedeeltelijk op het nieuwe Book-object staan.

Sinds 0.29.2 behandelen de bekende corrupte UTF-8-bronnen lokaal en veroorzaken die geen exception meer. Dat verkleint het praktische risico, maar verandert het contract niet.

Voorgesteld doel voor de volgende implementatie:
- voorbereiden/preflight mag niets aan de zichtbare UI of revision tracking veranderen;
- pas als alle benodigde diskdata leesbaar/parseerbaar is, wordt één commit naar het nieuwe live Book-object gedaan;
- bij een fout blijft `_active_book` én elke book-facing pagina op de oude toestand;
- dirty/conflict-merge gedrag van Boekdetails, Planning, Boekprofiel en Boekgeheugen moet behouden blijven;
- future-format, blocked-book en corrupt-source herstelroutes mogen niet worden verzwakt;
- geen automatische write als onderdeel van rollback.

Reviewvraag voor Claude: bepaal op basis van de concrete adopt-methoden of een echte prepare/commit API per pagina nodig is, of dat een centrale preflight van alle fallible diskloads voldoende hard kan worden gemaakt. Graag expliciet aangeven welke adopt-methoden tijdens de commit nog kunnen falen of schrijven.

## 2. Huidige spellingsarchitectuur

### Engine
`quietwriter/spell_engine.py` bevat `WordDictionary`:
- Hunspell via spylls indien beschikbaar;
- fallback woordenlijst + difflib-suggesties;
- persoonlijk woordenboek;
- sessie-negeerlijst en persistente negeerlijst;
- `misspellings(text)` retourneert `(woord, start, einde)`.

### Passieve markering
`EditorPage` houdt het woordenboek en de highlighter actief zolang spelling is ingeschakeld. De rechter SpellPanel hoeft daarvoor niet open te zijn.

### SpellPanel
`quietwriter/ui/spell_panel.py` bouwt bij `refresh()` een volledige lijst van fouten in hoofdstuktitel + hoofdstuktekst. `show_current()` selecteert de actuele fout in titel/editor. Het paneel is dus nu primair een lineaire wizard.

Belangrijke bestaande bescherming:
- offsets worden vóór Wijzigen gecontroleerd;
- bij stale offsets wordt opnieuw geankerd op de dichtstbijzijnde gelijke fout;
- corrupte hoofdstukken kunnen niet via spelling worden gewijzigd;
- image paths worden gemaskeerd vóór controle.

### Huidige UX-beperking
De richting is voornamelijk paneel -> editor. Als de gebruiker zelf in de editor een onderstreept woord selecteert of de cursor erin zet, kiest het paneel niet automatisch die specifieke fout. Er is ook geen robuuste hover/contextsuggestie op een individuele fout.

## 3. Gewenst gedrag voor spelling

Voorkeur voor review:
1. cursor of selectie op een fout woord terwijl SpellPanel open is -> paneel springt naar exact die occurrence en toont suggesties;
2. selectie van één fout woord moet hetzelfde doen;
3. lineaire Volgende/Negeren/Wijzigen-flow blijft bestaan;
4. nooit vervangen op stale offsets;
5. geen permanente hover-oplossing tenzij Qt dit zonder fragiele eventfilters/timing kan ondersteunen;
6. contextmenu op een fout woord mag als alternatief worden onderzocht, maar hoeft niet als selectie-sync al goed werkt;
7. programmatische selectie door SpellPanel mag geen recursieve refresh-loop veroorzaken.

Reviewvraag voor Claude: analyseer `spell_panel.py`, de cursor/selection signals van de editor en de highlighter. Stel de kleinste robuuste koppeling voor tussen `cursorPositionChanged`/`selectionChanged` en een nieuwe `SpellPanel.focus_occurrence(...)`. Beoordeel ook of contextmenu of hover technisch meerwaarde heeft of juist onnodige complexiteit toevoegt.

## 4. Nog niet doen

- geen spellingwijzigingen voordat deze analyse is teruggekomen;
- geen fuzzy vervanging zonder occurrence/offset-validatie;
- geen hover bouwen alleen omdat het visueel aantrekkelijk klinkt;
- geen transactionele rollback die tijdens foutafhandeling bestanden opslaat.
