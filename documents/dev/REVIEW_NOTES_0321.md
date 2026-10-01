# QuietWriter 0.32.1 — reviewronde 27

## Doel

Controleer dat de twee rode punten uit ronde 26 werkelijk gesloten zijn en dat de nieuwe live zichtbaarheidspreview geen nieuwe stateproblemen introduceert.

## Verplicht runtime testen (echte MainWindow / PySide6)

1. **Startup met spelling uit**
   - Zet `spell_enabled=False`, sluit QuietWriter en bouw/start een nieuwe `MainWindow`.
   - Geen exceptie; editor bruikbaar; spellingsknop verborgen; highlighter niet actief.

2. **Exacte Lucas-reproductie spelling**
   - Open een hoofdstuk met zichtbare rode spellingstrepen.
   - Instellingen → Spelling uit → Opslaan.
   - Zonder hoofdstukwissel of herstart moeten de rode strepen direct verdwijnen.
   - Spellingspaneel sluit als het open stond; spellingsknop is direct weg.
   - Zet weer aan → Opslaan: woordenboek/highlighter en knop komen terug.

3. **AI live preview en commit**
   - Open Instellingen vanuit Boekgeheugen, Boekprofiel en Schrijverspersona.
   - AI uitvinken: rail moet direct aanpassen terwijl Instellingen nog open is.
   - Zonder Opslaan naar een andere pagina: opgeslagen toestand moet terugkomen.
   - Nogmaals AI uit → Opslaan → Terug: bestemming is Inhoud, niet de verborgen pagina.
   - Zet AI weer aan: inhoud van persona/memory/profile byte-identiek.

4. **Geavanceerde opties live preview en commit**
   - Open Instellingen vanuit Integriteit.
   - Uitvinken: Integriteit + gap verdwijnen direct in rail.
   - Zonder Opslaan weggaan: beide keren terug.
   - Uit → Opslaan → Terug: bestemming Inhoud en Integriteit blijft verborgen.

5. **Andere Settings-apply regressie**
   - Wijzig schrijftype/manuscriptstijl en controleer dat het geopende manuscript direct na Opslaan wordt bijgewerkt.
   - Wijzig spellingstaal en controleer dat het woordenboek direct herlaadt.
   - Indien praktisch: wissel AI-provider/model en controleer dat het geopende AI-paneel de opgeslagen instelling gebruikt.

6. **Planning visueel**
   - Planning toont bovenaan `Planning` plus een korte muted uitleg en daaronder pas Personages/Outline/Notities.
   - Controleer lage laptophoogte en of er geen onnodige dubbele titel/te grote witruimte ontstaat.

7. **Algemeen visueel**
   - `Geavanceerde opties gebruiken` staat één keer als rijlabel; rechts staat alleen het vinkje.

## Regressie

- Volledige suite en alle regressiereeksen 9–26.
- Extra aandacht voor 0.31 transactionele adopt/conflictflows: deze release hoort daar niets aan te wijzigen.

## Bekende omgeving

Onze lokale container heeft geen PySide6 en mist de fontresources; de twee bekende fonttests zijn daardoor de enige verwachte lokale failures.
