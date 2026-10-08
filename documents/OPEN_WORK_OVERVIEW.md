# QuietWriter — open werk en ideeën

**Momentopname:** 1.3.0-dev.27  
**Doel:** één neutraal overzicht van wat nog openstaat. De volgorde hieronder is **geen prioritering**. Dit document is juist bedoeld om reviewers onafhankelijk naar waarde, risico en omvang te laten kijken.

## Productideeën en grotere uitbreidingen

### Automatische `.qwbook`-back-ups
- Automatische en handmatige back-ups van een boek.
- Instelbare back-uplocatie en bewaartermijn/retentie.
- Een back-up blijft output en wordt nooit een tweede live bron van hetzelfde boek.
- QuietWriter heeft al versiegeschiedenis; dit is aanvullende bescherming buiten die geschiedenis.

### Planning verder uitbouwen
- Scènes verplaatsen en eenvoudiger herschikken.
- Inklapbare hoofdstukgroepen.
- Compactere scènebewerking.
- Eerste verschijning van personages zichtbaar maken.
- Locaties, relaties en aliassen verder uitwerken.
- Mogelijke vervolgstap voor Planninghulp: open scènes op echte scèneposities/scènebreuken tonen in plaats van alleen als hulp voor een leeg hoofdstuk.
- De huidige handmatige workflow `Idee / Uitgewerkt / Geschreven` behouden; geen automatische gok of een scène "klaar" is.

### Schrijfdoelen — mogelijke vervolgstappen
- Een rustige lijst met recente schrijfactiviteit, alleen als daar behoefte aan blijkt.
- Eventueel een instelbare daggrens voor nachtschrijvers.
- Eventueel schrijf-/werkdagen meenemen in het berekende tempo.
- Eventueel voortgang over meerdere apparaten samenvoegen; v1 houdt activiteit bewust per apparaat bij.
- Geen streaks, badges, schuldgevoel, rode achterstand of andere gamification zonder een heel goede reden.

### Boektypografie
- Voetnoten.
- Poëzie/verzen.
- Gecentreerde tekst.
- Kleinkapitalen.
- Harde spaties en andere literaire opmaak die niet vanzelfsprekend in het huidige manuscriptprofiel past.

### Export en publicatie
- Een echte publicatie-/exportpreview.
- Meer front matter en back matter waar dat nuttig is.
- Verdere polish van begeleid exporteren en publicatie-instellingen.

### AI Meelezer
- Beter zichtbaar/contextueel contextbudget.
- Verdere Ollama-setup en lokale-modelervaring.
- Voorstellen voor feiten en Open punten zonder manuscript automatisch te wijzigen.
- Betere aliasherkenning van personages en begrippen.
- AI blijft meelezer, geen autonome schrijver.

### Diagnostiek
- Een veilige diagnostiekweergave voor support en foutonderzoek, zonder manuscriptinhoud of geheimen onnodig prijs te geven.

### Boekenkast — mogelijke uitbreidingen
- Een subtiele `Nieuw boek`-actie per plank als aanmaken-en-verplaatsen in de praktijk onhandig blijkt.
- Cover-pixmapcache alleen als echte Windows-profielen aantonen dat dit nodig is.
- Oude kaartwidgets direct verbergen vóór `deleteLater()` als ooit zichtbare flikkering optreedt.
- Incrementeel kaart-hergebruik/virtualisatie alleen als zeer grote bibliotheken dat werkelijk nodig maken.

## Gedrag en editorpolish

### Intern kopiëren/plakken met scènebreuk
- Bij een fragment met `***` kan de interne Markdown-insertie worden afgewezen.
- De fallback naar platte tekst kan dan scènebreuk en vet/cursief verliezen.
- Gewone tekst en gewone vet/cursief-copy/paste werken inmiddels wel correct en laten de geplakte tekst niet geselecteerd achter.

### Undo per teken onderzoeken
- In een Qt-harnas leek Undo soms één teken tegelijk terug te gaan.
- Dit gedrag bestond al in oudere builds en kan testplatform-specifiek zijn.
- Op echt Windows nog bepalen of hier productgedrag achter zit.

### Planninghulp bij afkappen
- Bij veel scènes kan een gedeeltelijk getekende scène meetellen als "niet getoond" in `… nog N meer`.
- Keuze nodig: nooit een halve scène tekenen, of een gedeeltelijk zichtbare scène als getoond tellen.

### Planning-uitleg versus geschreven scènes
- Een deel van de uitleg spreekt over "open scènes" terwijl de Planninghulp ook scènes met status `Geschreven` kan tonen.
- Tekst of gedrag uiteindelijk volledig gelijk trekken.

### Lege Planning-flyout
- De lege flyout is visueel schoon maar gebruikt dezelfde ruime hoogte als een gevulde flyout.
- Mogelijke polish: bij nul scènes alleen de inhoudshoogte gebruiken.

### Context-subnavigatie
- Planning, hoofdstukken en Instellingen volgen inmiddels grotendeels dezelfde rustige achtergrondregel.
- Andere contextgebonden navigatie later nalopen op dezelfde visuele taal.

## Formulieren en instellingen

### Scrollwielbescherming buiten Instellingen/Boekdetails
De nieuwe Quiet-form controls voorkomen onbedoelde waarde-wijzigingen door scrollen zonder focus. Nog nalopen op formulieren die gewone Qt-controls gebruiken, waaronder:
- Export;
- Scène bewerken;
- Personages;
- Colofon/publicatie.

### Formulierconsistentie
- Oudere formulierpagina's nalopen op dezelfde regel: links naam + uitleg, rechts één controlzone.
- Veldhoogtes, breedtes, spacing en hulpteksthiërarchie verder harmoniseren waar het nog afwijkt.

### Kleine tekst-/labelpolish
- `1 boeken` moet een correcte enkelvoudsvorm krijgen.
- `Thinking uitschakelen` als zowel label als waarde is dubbelop; bijvoorbeeld `Thinking` met `Modelstandaard / Uitgeschakeld` is rustiger.
- Tempo mag bij een klein restant niet `ongeveer 0 per dag` zeggen; minimaal 1 of een andere passende formulering.

## Technische schuld en robuustheid

### WritingProgressStore en twee processen
- De lokale dagtelling wordt als geheel gelezen en teruggeschreven.
- Twee gelijktijdige QuietWriter-processen kunnen daardoor elkaars laatste telling overschrijven.
- Eén proces is momenteel het normale gebruiksscenario.

### Dev-build en updatechecker
- Vergelijking tussen een ontwikkelversie zoals `1.3.0-dev.27` en een uiteindelijke `1.3.0` moet correct bepalen dat de stabiele versie nieuwer is.
- Windows-bestandsversies van dev-builds zijn numeriek eveneens `1.3.0.0`; bepalen of dat voor distributie/reputatie aangepast moet worden.

### Achtergebleven exportlabels
- Na het sluiten/wisselen van een boek kunnen verborgen exportlabels nog metadata van het vorige boek bevatten.
- Bekend oud backlogpunt; geen zichtbaar privacylek in de normale interface, maar intern hoort de context volledig leeg te zijn.

### Testvervuiling
- Qt-testmodus laat cachebestanden achter onder `~/.qttest`.
- Tests kunnen daarnaast een lege standaard-woordenboekmap aanmaken.
- Productdata wordt hiermee niet vervuild, maar de testsuite kan netter opruimen.

### Caches en tijdelijke bestanden
- Oude wees-cachebestanden van eerdere ontwikkelversies eventueel opruimen/versioneren.
- Bij meerdere processen kan een gedeelde tijdelijke bestandsnaam robuuster worden gemaakt.
- Oude cache-items van verwijderde boeken eventueel opruimen; ze bevatten inmiddels alleen gehashte paden.

### Zeer late fout tijdens boek sluiten
- Bij een uitzonderlijke fout laat in het sluitproces kan de app intern half gesloten achterblijven.
- Presentatiemodus wordt daarbij wel veilig teruggezet en privétekst blijft niet zichtbaar.

### Ongebruikte imports
- Na de recente formulieromzettingen zijn enkele imports niet meer nodig. Cosmetische cleanup.

## Documentatie en ontwikkelproces

- Actuele versie-aanduidingen blijven bij iedere build gecontroleerd: publieke versie en ontwikkellijn zijn verschillende dingen.
- Historische release notes/changelogregels blijven historisch en worden niet herschreven om de huidige versie te volgen.
- README.md en README_EN.md worden bewust niet automatisch met iedere ontwikkelbuild aangepast.
- Reviewdocumenten van Claude blijven als onafhankelijke momentopnamen bewaard.

## Bewust geen automatisch werk

Een aantal dingen is bewust géén doel tenzij praktijkgebruik daar aanleiding toe geeft:
- automatische manuscriptwijzigingen door AI;
- automatische detectie dat een geplande scène "Geschreven" is;
- gamification van schrijven;
- complexe Boekenkast-virtualisatie zonder aangetoond performanceprobleem;
- een nieuw manuscriptopslagformaat alleen om één nieuwe feature makkelijker te maken.
