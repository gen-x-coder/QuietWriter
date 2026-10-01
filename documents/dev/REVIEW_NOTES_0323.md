# QuietWriter reviewnotities 0.32.3 — ronde 29

## Doel
0.32.3 sluit de twee tekstintegriteitspunten uit reviewronde 28. De editor gebruikt nu één bronrepresentatie (`_editor_source_text`) voor baseline, dirty-detectie, conflict-lokale tekst en opslaan.

## Verplicht testen in echte PySide6-runtime

1. **Geen valse dirty met bijzondere tekens**
   - Maak/open een hoofdstuk met minimaal U+00A0, U+2028, U+2029 en een UTF-8 BOM aan het begin.
   - Alleen openen, daarna `rehighlight()`, Instellingen openen + Opslaan en een spellingsactie uitvoeren zonder manuscripttekst te wijzigen.
   - Verwacht: `dirty=False`, autosave-timer uit, hoofdstukbytes byte-identiek.

2. **Gewone save bewaart typografische tekens**
   - Tekst: `Hij betaalde 10 euro op p. 5.` plus een U+2028-regel.
   - Typ één gewoon teken en sla op/autosave.
   - Verwacht: beide U+00A0's en U+2028 blijven aanwezig. Gewone Qt-alineascheiding wordt als `\n` opgeslagen.
   - Noteer afzonderlijk wat er met een bestaande BOM gebeurt na een echte tekstwijziging; dit is geen blokkade voor 0.32.3 tenzij er onverwacht bronverlies buiten de bekende Qt-normalisatie optreedt.

3. **Twee-computerscenario met NBSP**
   - Computer A heeft een schoon hoofdstuk met U+00A0 open.
   - Externe wijziging op schijf door computer B.
   - Op A alleen een presentatieactie/Settings-save doen, daarna navigeren.
   - Verwacht: geen vals conflict en A schrijft niets.

4. **Conflictflow bewaart lokale brontekst**
   - Maak lokaal een echte wijziging in een hoofdstuk dat U+00A0/U+2028 bevat en wijzig hetzelfde boek extern.
   - Kies `Mijn versie gebruiken` en controleer History/live bestand.
   - Verwacht: de lokale bron behoudt U+00A0/U+2028.

5. **Regressie ronde 27/28**
   - Herhaal de verplichte 30/30 uit ronde 28 plus spellingsacties (`Negeer overal`, `Toevoegen aan woordenboek`, `Altijd negeren`).
   - De transactionele adopt/conflictflows uit 0.31 mogen niet veranderen.

## Nieuwe tests
- `tests/test_editor_source_text_0323.py`
  - speciale tekens -> geen valse dirty / geen rewrite;
  - echte save -> U+00A0 en U+2028 blijven behouden.

## Kleine observatie die bewust niet in 0.32.3 zit
Alleen Boekgeheugen/Boekprofiel bezoeken kan nog een leeg sjabloonbestand aanmaken. Dat is geen data-integriteitsfout en wordt apart geparkeerd voor een latere polishronde: openen zou idealiter niet schrijven, maar deze bronfix moet klein blijven.
